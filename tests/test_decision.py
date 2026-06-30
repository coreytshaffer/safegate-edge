import pytest
from datetime import datetime, timezone
from safegate_edge.decision import create_execution_decision

def test_create_execution_decision_allowed():
    vr = {
        "verification_id": "vrf-123",
        "action_id": "act-1",
        "action_hash": "sha256:abc",
        "approval_id": "apr-1",
        "decision": "allowed",
        "reason": "valid_approval",
    }
    
    now = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    decision = create_execution_decision(vr, now=now)
    
    assert decision["decision"] == "allowed"
    assert decision["execution_status"] == "ready_for_execution"
    assert decision["action_id"] == "act-1"
    assert decision["execution_mode"] == "simulated"

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
