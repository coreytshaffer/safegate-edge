import json
import pytest
from datetime import datetime, timezone, timedelta
from safegate_edge.approve import create_approval_packet

def load_fixture(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def review_packet():
    # Load original action first to generate review packet
    from safegate_edge.review import create_review_packet
    action = load_fixture("examples/action_requests/delete_customer_exports_original.json")
    policy = load_fixture("examples/config/default_policy.json")
    return create_review_packet(action, policy)

@pytest.fixture
def approvers():
    return load_fixture("examples/config/approvers.json")

def test_create_approval_packet_approved(review_packet, approvers):
    packet = create_approval_packet(review_packet, "corey", approvers, "approved")
    
    assert packet["schema_version"] == "approval_packet.v1"
    assert packet["review_id"] == review_packet["review_id"]
    assert packet["action_hash"] == review_packet["action_hash"]
    assert packet["approver_id"] == "corey"
    assert packet["approval_status"] == "approved"
    assert packet["policy_id"] == review_packet["policy_id"]
    assert packet["policy_rule_id"] == review_packet["policy_rule_id"]
    assert packet["approval_required"] == review_packet["approval_required"]
    assert packet["expires_at"] == review_packet["expires_at"]
    assert packet["approval_id"].startswith("apr-")
    
def test_create_approval_packet_denied(review_packet, approvers):
    packet = create_approval_packet(review_packet, "corey", approvers, "denied")
    
    assert packet["approval_status"] == "denied"
    assert packet["metadata"]["approval_decision"] == "denied"

def test_create_approval_packet_unknown_approver(review_packet, approvers):
    with pytest.raises(ValueError, match="Unknown approver: unknown_user"):
        create_approval_packet(review_packet, "unknown_user", approvers, "approved")
        
def test_create_approval_packet_inactive_approver(review_packet, approvers):
    # Set corey to inactive
    approvers["approvers"][0]["status"] = "inactive"
    with pytest.raises(ValueError, match="Approver is not active: corey"):
        create_approval_packet(review_packet, "corey", approvers, "approved")
        
def test_create_approval_packet_expired_review(review_packet, approvers):
    # Create a time far in the future
    future_time = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat().replace("+00:00", "Z")
    
    with pytest.raises(ValueError, match="Review packet has expired."):
        create_approval_packet(review_packet, "corey", approvers, "approved", now_iso=future_time)

def test_create_approval_packet_invalid_review(approvers):
    with pytest.raises(ValueError, match="Invalid review packet"):
        create_approval_packet({}, "corey", approvers, "approved")
        
def test_create_approval_packet_not_pending(review_packet, approvers):
    review_packet["review_status"] = "approved"
    with pytest.raises(ValueError, match="Review packet is not pending_review"):
        create_approval_packet(review_packet, "corey", approvers, "approved")
