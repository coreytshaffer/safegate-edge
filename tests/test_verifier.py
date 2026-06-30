import json
from datetime import datetime, timezone
import pytest
from safegate_edge.verifier import verify_approval
from safegate_edge.canonical import canonical_action_hash

def load_fixture(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def original_action():
    return load_fixture("examples/action_requests/delete_customer_exports_original.json")

@pytest.fixture
def valid_approval():
    return load_fixture("examples/approval_packets/valid_approval.json")

def test_verify_valid_approval(original_action, valid_approval):
    now = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    result = verify_approval(original_action, valid_approval, now=now)
    assert result["decision"] == "allowed"
    assert result["reason"] == "valid_approval"

def test_verify_missing_approval(original_action):
    result = verify_approval(original_action, None)
    assert result["decision"] == "blocked"
    assert result["reason"] == "missing_approval"

def test_verify_expired_approval(original_action, valid_approval):
    # Set 'now' to after the approval expires (which is 14:00:00Z)
    now = datetime(2026, 7, 1, 15, 0, tzinfo=timezone.utc)
    result = verify_approval(original_action, valid_approval, now=now)
    assert result["decision"] == "blocked"
    assert result["reason"] == "approval_expired"

def test_verify_hash_mismatch(valid_approval):
    mutated_action = load_fixture("examples/action_requests/delete_customer_exports_mutated.json")
    now = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    result = verify_approval(mutated_action, valid_approval, now=now)
    assert result["decision"] == "blocked"
    assert result["reason"] == "action_hash_mismatch"

def test_verify_malformed_action(valid_approval):
    malformed_action = load_fixture("examples/action_requests/malformed_action_request.json")
    result = verify_approval(malformed_action, valid_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "malformed_action"

def test_verify_malformed_approval(original_action):
    malformed_approval = load_fixture("examples/approval_packets/malformed_approval_packet.json")
    result = verify_approval(original_action, malformed_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "malformed_approval"

def test_verify_unknown_approver(original_action):
    unknown_approver_approval = load_fixture("examples/approval_packets/unknown_approver_approval_packet.json")
    result = verify_approval(original_action, unknown_approver_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "unknown_approver"
