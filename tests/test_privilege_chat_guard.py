"""Privilege alert for third-party case discussion."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.privilege.chat_guard import guard_user_message, scan_message_for_privilege_risk


def test_neighbor_triggers_preferred_copy():
    text = (
        "I was discussing my RTB case and eviction strategy with my neighbor yesterday."
    )
    alert = scan_message_for_privilege_risk(text)
    assert alert is not None
    assert "PRIVILEGE ALERT" in alert.format_alert()
    assert "neighbor" in alert.message.lower()
    assert "solicitor-client privilege" in alert.message.lower()
    assert "third party" in alert.message.lower()
    out = guard_user_message(text)
    assert out["alert_text"] is not None
    assert "⚠" in out["alert_text"]
    assert out["requires_ack"] is True


def test_friend_uses_generic_template():
    alert = scan_message_for_privilege_risk(
        "I told my friend everything about the hearing and the evidence."
    )
    assert alert is not None
    assert "friend" in alert.message.lower()
    assert "third party" in alert.message.lower()


def test_no_alert_for_case_facts_alone():
    alert = scan_message_for_privilege_risk(
        "The landlord served a two month notice on November 12."
    )
    assert alert is None


def test_no_alert_talking_to_lawyer():
    alert = scan_message_for_privilege_risk(
        "I discussed the petition strategy with my lawyer this morning."
    )
    assert alert is None


def test_block_send_mode():
    out = guard_user_message(
        "I posted my case details on Facebook for my neighbors to see.",
        block_send=True,
    )
    assert out["allowed"] is False
    assert out["alert"] is not None


if __name__ == "__main__":
    test_neighbor_triggers_preferred_copy()
    test_friend_uses_generic_template()
    test_no_alert_for_case_facts_alone()
    test_no_alert_talking_to_lawyer()
    test_block_send_mode()
    print("OK: 5 privilege chat guard tests passed")
