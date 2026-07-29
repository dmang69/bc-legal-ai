#!/usr/bin/env python3
"""Production smoke: health + auth + matter + chat + logout.

Usage:
  python scripts/production_smoke.py --base http://127.0.0.1:8000
Exit 0 on success.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import uuid


def req(method: str, url: str, body: dict | None = None, token: str | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> {e.code}: {detail}") from e


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8000")
    args = p.parse_args()
    base = args.base.rstrip("/")

    health = req("GET", f"{base}/health")
    assert health.get("status") in ("ok", "unsafe"), health
    live = req("GET", f"{base}/health/live")
    assert live.get("status") == "ok", live

    email = f"smoke_{uuid.uuid4().hex[:10]}@synthetic.invalid"
    session = req(
        "POST",
        f"{base}/v1/platform/auth/register",
        {
            "org_name": "Smoke Org",
            "email": email,
            "password": "securepass99",
            "display_name": "Smoke",
        },
    )
    token = session.get("token")
    assert token, session

    me = req("GET", f"{base}/v1/platform/auth/me", token=token)
    assert me.get("email") == email, me

    matter = req(
        "POST",
        f"{base}/v1/platform/matters",
        {"title": "Smoke matter", "synthetic": True},
        token=token,
    )
    assert matter.get("matter_id"), matter

    conv = req(
        "POST",
        f"{base}/v1/platform/conversations",
        {"title": "Smoke chat", "chat_type": "general"},
        token=token,
    )
    cid = conv.get("conversation_id")
    assert cid, conv

    msg = req(
        "POST",
        f"{base}/v1/platform/conversations/{cid}/messages",
        {
            "content": "/summarize: Production smoke test message for stability.",
            "provider": "safe_local",
        },
        token=token,
    )
    assert msg.get("assistant", {}).get("content"), msg

    suite = req("GET", f"{base}/v1/platform/ai/suite", token=token)
    assert "providers" in suite or suite.get("product"), suite

    out = req("POST", f"{base}/v1/platform/auth/logout", {}, token=token)
    assert out.get("status") == "ok", out

    print("production_smoke: OK")
    print(
        json.dumps(
            {
                "health": health.get("status"),
                "db": health.get("db_backend"),
                "matter_id": matter.get("matter_id"),
                "conversation_id": cid,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"production_smoke: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
