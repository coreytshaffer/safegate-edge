import json
import pytest
from safegate_edge.review import create_review_packet
from safegate_edge.canonical import canonical_action_hash

def load_fixture(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def policy():
    return load_fixture("examples/config/default_policy.json")

@pytest.fixture
def original_action():
    return load_fixture("examples/action_requests/delete_customer_exports_original.json")

@pytest.fixture
def low_risk_action():
    return load_fixture("examples/action_requests/read_customer_exports_low_risk.json")

def test_create_review_packet_known_action(original_action, policy):
    packet = create_review_packet(original_action, policy)
    
    # Check fields
    assert packet["schema_version"] == "human_review_packet.v1"
    assert packet["action_id"] == original_action["action_id"]
    
    expected_hash = canonical_action_hash(original_action)
    assert packet["action_hash"] == expected_hash
    
    assert packet["review_id"].startswith("rev-")
    assert packet["review_id"] == f"rev-{expected_hash.split(':')[-1][:8]}"
    
    assert packet["review_status"] == "pending_review"
    assert packet["expires_at"] == original_action["expires_at"]
    assert packet["approval_required"] is True
    assert packet["policy_id"] == "default"
    assert packet["policy_rule_id"] == "high-risk-approval"
    
    assert "Delete files matching" in packet["human_summary"]
    assert packet["approval_instructions"].startswith("Review the exact action details")
    
    # Check optional fields
    assert packet["target"] == original_action["target"]
    assert packet["command"] == original_action["command"]

def test_create_review_packet_unknown_action(low_risk_action, policy):
    # Change action type to something unknown
    low_risk_action["action_type"] = "unknown.type"
    
    packet = create_review_packet(low_risk_action, policy)
    
    assert packet["approval_required"] is False
    assert packet["policy_rule_id"] == "low-risk-no-approval"
    assert "Requested action 'unknown.type'" in packet["human_summary"]
    assert "Policy does not require approval" in packet["approval_instructions"]

def test_create_review_packet_invalid_action(policy):
    with pytest.raises(ValueError, match="Action validation failed"):
        create_review_packet({}, policy)

def test_create_review_packet_missing_policy(original_action):
    with pytest.raises(ValueError, match="policy_not_found"):
        create_review_packet(original_action, None)

def test_create_review_packet_invalid_policy(original_action):
    with pytest.raises(ValueError, match="policy_invalid"):
        create_review_packet(original_action, {"schema_version": "invalid"})
        
def test_create_review_packet_unknown_risk(original_action, policy):
    original_action["risk_level"] = "unknown_level"
    with pytest.raises(ValueError, match="risk_level_unknown"):
        create_review_packet(original_action, policy)
