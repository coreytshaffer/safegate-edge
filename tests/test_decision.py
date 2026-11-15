import json
from pathlib import Path

import pytest
from datetime import datetime, timezone
from safegate_edge.decision import create_execution_decision

@pytest.mark.parametrize(
    ("execution_mode", "expected_decision", "expected_status"),
    [
        ("live", "allowed", "ready_for_execution"),
        ("simulated", "simulated_allowed", "simulation_only"),
    ],
)
def test_create_execution_decision_approval_free(execution_mode, expected_decision, expected_status):
    vr = {
        "verification_id": "vrf-123",
        "action_id": "act-1",
        "action_hash": "sha256:abc",
        "approval_id": None,
        "decision": "allowed",
        "reason": "approval_not_required",
        "approval_required": False,
        "approval_method": None,
    }
    
    now = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    decision = create_execution_decision(vr, execution_mode=execution_mode, now=now)
    
    assert decision["decision"] == expected_decision
    assert decision["execution_status"] == expected_status
    assert decision["action_id"] == "act-1"
    assert decision["execution_mode"] == execution_mode


def test_archived_demo_verification_cannot_authorize_live_execution():
    archived_result = Path(__file__).resolve().parents[1] / (
        "examples/demo_runs/safegate_demo/verify_original_allowed.json"
    )
    verification = json.loads(archived_result.read_text(encoding="utf-8"))

    decision = create_execution_decision(verification, execution_mode="live")

    assert decision["decision"] == "blocked"
    assert decision["reason"] == "execution_authority_unverified"
    assert decision["execution_status"] == "blocked_before_execution"


@pytest.mark.parametrize(
    ("verification_decision", "reason", "expected_status"),
    [
        ("simulated_allowed", "valid_simulated_approval", "simulation_only"),
        ("blocked", "approval_not_granted", "blocked_before_execution"),
    ],
)
def test_simulated_verification_cannot_produce_live_execution(verification_decision, reason, expected_status):
    verification_result = {
        "verification_id": "vrf-123",
        "action_id": "act-1",
        "action_hash": "sha256:abc",
        "approval_id": "apr-1",
        "decision": verification_decision,
        "reason": reason,
        "details": {"simulation_only": True},
    }

    decision = create_execution_decision(verification_result, execution_mode="live")

    assert decision["decision"] == verification_decision
    assert decision["execution_status"] == expected_status
    assert decision["execution_mode"] == "simulated"
    assert decision["details"]["simulation_only"] is True

def test_create_execution_decision_blocked():
    vr = {
        "verification_id": "vrf-123",
        "action_id": "act-1",
        "action_hash": "sha256:abc",
        "approval_id": "apr-1",
        "decision": "blocked",
        "reason": "action_hash_mismatch",
    }
    
    decision = create_execution_decision(vr)
    assert decision["decision"] == "blocked"
    assert decision["execution_status"] == "blocked_before_execution"
