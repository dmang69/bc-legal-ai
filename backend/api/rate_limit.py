"""In-process sliding-window rate limiter for auth and public abuse controls.

Process-local only — suitable for single-worker dev and internal alpha.
Multi-worker / multi-host deployments must replace this with Redis (or
equivalent) before production.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Optional

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class RateLimitRule:
    """Maximum `limit` events within `window_seconds` for a key."""

    limit: int
    window_seconds: float
    name: str = "default"


class SlidingWindowRateLimiter:
    """Thread-safe sliding window keyed by arbitrary strings."""

    def __init__(self) -> None:
        self._events: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def hit(self, key: str, rule: RateLimitRule) -> tuple[bool, int, float]:
        """Record a hit. Returns (allowed, remaining, retry_after_seconds)."""
        now = time.monotonic()
        window_start = now - rule.window_seconds
        with self._lock:
            q = self._events[key]
            while q and q[0] < window_start:
                q.popleft()
            if len(q) >= rule.limit:
                retry = max(0.0, rule.window_seconds - (now - q[0]))
                return False, 0, retry
            q.append(now)
            remaining = max(0, rule.limit - len(q))
            return True, remaining, 0.0


_limiter = SlidingWindowRateLimiter()

# Overridable by tests; env is read on each call so pytest env changes apply.
_AUTH_LOGIN_OVERRIDE: Optional[RateLimitRule] = None
_AUTH_REGISTER_OVERRIDE: Optional[RateLimitRule] = None


def auth_login_rule() -> RateLimitRule:
    if _AUTH_LOGIN_OVERRIDE is not None:
        return _AUTH_LOGIN_OVERRIDE
    return RateLimitRule(
        limit=int(os.environ.get("ALA_RATE_LIMIT_LOGIN", "20")),
        window_seconds=float(os.environ.get("ALA_RATE_LIMIT_LOGIN_WINDOW", "60")),
        name="auth.login",
    )


def auth_register_rule() -> RateLimitRule:
    if _AUTH_REGISTER_OVERRIDE is not None:
        return _AUTH_REGISTER_OVERRIDE
    return RateLimitRule(
        limit=int(os.environ.get("ALA_RATE_LIMIT_REGISTER", "10")),
        window_seconds=float(os.environ.get("ALA_RATE_LIMIT_REGISTER_WINDOW", "60")),
        name="auth.register",
    )


# Back-compat names (resolved at call sites via getters preferred)
AUTH_LOGIN_RULE = auth_login_rule()
AUTH_REGISTER_RULE = auth_register_rule()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    return _limiter


def reset_rate_limiter() -> None:
    """Test helper — clear all counters and rule overrides."""
    global _AUTH_LOGIN_OVERRIDE, _AUTH_REGISTER_OVERRIDE
    _limiter.reset()
    _AUTH_LOGIN_OVERRIDE = None
    _AUTH_REGISTER_OVERRIDE = None


def set_auth_rules_for_tests(
    *,
    login: Optional[RateLimitRule] = None,
    register: Optional[RateLimitRule] = None,
) -> None:
    """Test helper — pin rules without depending on import-time env."""
    global _AUTH_LOGIN_OVERRIDE, _AUTH_REGISTER_OVERRIDE
    _AUTH_LOGIN_OVERRIDE = login
    _AUTH_REGISTER_OVERRIDE = register


def client_key(request: Request, *, suffix: str = "") -> str:
    """Best-effort client identity for rate limiting (IP + optional suffix)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    base = f"{ip}"
    return f"{base}:{suffix}" if suffix else base


def enforce_rate_limit(
    request: Request,
    rule: RateLimitRule,
    *,
    extra_key: str = "",
) -> None:
    """Raise HTTP 429 when the sliding window is exhausted."""
    key = f"{rule.name}:{client_key(request, suffix=extra_key)}"
    allowed, remaining, retry_after = _limiter.hit(key, rule)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "rule": rule.name,
                "retry_after_seconds": round(retry_after, 2),
            },
            headers={"Retry-After": str(max(1, int(retry_after + 0.999)))},
        )
    # Stash for optional response headers (middleware may read later)
    request.state.rate_limit_remaining = remaining  # type: ignore[attr-defined]
    request.state.rate_limit_rule = rule.name  # type: ignore[attr-defined]


def rate_limit_enabled() -> bool:
    """Allow tests to disable via ALA_RATE_LIMIT_DISABLED=1."""
    return os.environ.get("ALA_RATE_LIMIT_DISABLED", "").strip() not in (
        "1",
        "true",
        "yes",
    )


def maybe_enforce_rate_limit(
    request: Optional[Request],
    rule: RateLimitRule,
    *,
    extra_key: str = "",
) -> None:
    if not rate_limit_enabled():
        return
    if request is None:
        return
    enforce_rate_limit(request, rule, extra_key=extra_key)
