import pytest
from safegate_edge.schema import validate_action, validate_approval

def test_validate_action_valid():
    action = {
        "action_id": "1", "action_type": "type", "requester": "req", 
        "command": "cmd", "target": "tgt", "working_directory": "wd", 
        "risk_level": "high", "created_at": "2026-07-01T12:00:00Z", 
        "expires_at": "2026-07-01T13:00:00Z", "metadata": {}
    }
    assert validate_action(action) == []

def test_validate_action_missing_fields():
    action = {"action_id": "1"}
    errors = validate_action(action)
    assert len(errors) == 1
    assert "Missing required fields" in errors[0]

def test_validate_approval_valid():
    approval = {
        "schema_version": "approval_packet.v1",
        "approval_id": "1", "review_id": "1", "action_id": "1", "action_hash": "sha256:abc",
        "approver_id": "human", "approved_at": "2026-07-01T12:00:00Z",
        "expires_at": "2026-07-01T13:00:00Z", "approval_status": "approved",
        "approval_method": "simulated", "signature_or_attestation_placeholder": "xyz",
        "policy_id": "default", "policy_rule_id": "rule", "approval_required": True,
        "metadata": {}
    }
    assert validate_approval(approval) == []
    
    approval["approval_method"] = "placeholder_security_key"
    assert validate_approval(approval) == []
    
    approval["approval_method"] = "hardware_security_key"
    assert validate_approval(approval) == []
    
    approval["approval_method"] = "unknown_method"
    errors = validate_approval(approval)
    assert len(errors) == 1
    assert "approval_method_unknown: 'unknown_method'" in errors[0]

def test_validate_approval_malformed_hash():
    approval = {
        "schema_version": "approval_packet.v1",
        "approval_id": "1", "review_id": "1", "action_id": "1", "action_hash": 123,
        "approver_id": "human", "approved_at": "2026-07-01T12:00:00Z",
        "expires_at": "2026-07-01T13:00:00Z", "approval_status": "approved",
        "approval_method": "simulated", "signature_or_attestation_placeholder": "xyz",
        "policy_id": "default", "policy_rule_id": "rule", "approval_required": True,
        "metadata": {}
    }
    errors = validate_approval(approval)
    assert len(errors) == 1
    assert "Field 'action_hash' must be a string" in errors[0]
