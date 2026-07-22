"""
Secure messaging — Model B (controlled legal-workspace encryption) by default.

Model A (true E2EE) and Model B are both supported as flags, but claims must be honest:
  - Model B: TLS + at-rest encryption; server may decrypt in controlled matter service
    for AI under scoped consent. Do NOT call Model B "end-to-end encryption."
  - Model A: client-side keys only; AI only after express decrypted send to AI workspace.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Message:
    message_id: str
    matter_id: str
    sender_id: str
    body: str
    # ciphertext placeholder when e2e_enabled
    body_ciphertext: Optional[str] = None
    e2e: bool = False
    privilege_flagged: bool = False
    classification_prompt: str = ""
    read_at: Optional[str] = None
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "matter_id": self.matter_id,
            "sender_id": self.sender_id,
            "body": None if self.e2e else self.body,
            "body_ciphertext": self.body_ciphertext,
            "e2e": self.e2e,
            "privilege_flagged": self.privilege_flagged,
            "classification_prompt": self.classification_prompt,
            "read_at": self.read_at,
            "created_at": self.created_at,
        }


@dataclass
class SecureMessagingStub:
    messages: list[Message] = field(default_factory=list)
    # Default Model B — honest: not true E2EE
    encryption_model: str = "MODEL_B_WORKSPACE"
    e2e_default: bool = False

    def send(
        self,
        *,
        matter_id: str,
        sender_id: str,
        body: str,
        privilege_flagged: bool = False,
        e2e: Optional[bool] = None,
        classification: str = "",
    ) -> Message:
        use_e2e = self.e2e_default if e2e is None else e2e
        if privilege_flagged:
            prompt = (
                "Marked privileged (suggestion only). Do not forward outside the retainer "
                "without counsel review. Client classification does not conclusively determine privilege."
            )
        else:
            prompt = (
                "Is this message mainly about: (1) legal advice (2) evidence/facts "
                "(3) scheduling (4) billing (5) other? Answer assists triage only."
            )
        ciphertext = None
        stored_body = body
        if use_e2e or self.encryption_model == "MODEL_A_E2EE":
            # Model A scaffold — not production crypto
            ciphertext = hashlib.sha256(body.encode("utf-8")).hexdigest()
            stored_body = ""
            true_e2e = True
        else:
            # Model B: workspace encryption claim — server retains ciphertext-at-rest placeholder
            ciphertext = hashlib.sha256(body.encode("utf-8")).hexdigest()
            true_e2e = False
        msg = Message(
            message_id=f"MSG-{uuid4().hex[:10]}",
            matter_id=matter_id,
            sender_id=sender_id,
            body=stored_body,
            body_ciphertext=ciphertext,
            e2e=true_e2e,
            privilege_flagged=privilege_flagged,
            classification_prompt=prompt or classification,
        )
        self.messages.append(msg)
        return msg

    def mark_read(self, message_id: str) -> Optional[Message]:
        for m in self.messages:
            if m.message_id == message_id:
                m.read_at = _utcnow()
                return m
        return None
