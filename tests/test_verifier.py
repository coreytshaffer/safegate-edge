import json
from datetime import datetime, timezone
import pytest
from safegate_edge.verifier import verify_approval


VERIFICATION_TIME = "2026-07-01T12:10:00Z"

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

@pytest.fixture
def valid_approval():
    return load_fixture("examples/approval_packets/valid_approval.json")

@pytest.fixture
def trusted_registry():
    registry = load_fixture("examples/config/approvers.json")
    registry["approvers"][0]["approval_methods"] = [
        "simulated",
        "placeholder_security_key",
        "hardware_security_key",
    ]
    return registry


def test_verify_simulated_approval(original_action, policy, valid_approval, trusted_registry):
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "simulated_allowed"
    assert result["reason"] == "valid_simulated_approval"
    assert result["details"]["simulation_only"] is True
    assert result["policy_id"] == "default"
    assert result["policy_rule_id"] == "high-risk-approval"
    assert result["approval_required"] is True


@pytest.mark.parametrize("method", ["simulated", "placeholder_security_key"])
def test_verify_default_rejects_unverified_evidence(
    original_action, policy, valid_approval, trusted_registry, method,
):
    valid_approval["approval_method"] = method
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == "approval_evidence_unverified"


@pytest.mark.parametrize(
    ("registry", "reason"),
    [(None, "approver_registry_missing"), ({}, "approver_registry_invalid")],
)
def test_verify_requires_trusted_registry(original_action, policy, valid_approval, registry, reason):
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == reason


@pytest.mark.parametrize(
    "field", ["policy_id", "policy_rule_id", "approval_required"],
)
def test_verify_requires_matching_policy_context(
    original_action, policy, valid_approval, trusted_registry, field,
):
    changed_value = False if field == "approval_required" else "different-context"
    valid_approval[field] = changed_value
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == "policy_context_mismatch"


def test_verify_rejects_unresolved_policy_rule(original_action, policy, valid_approval, trusted_registry):
    policy["rules"] = []
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == "policy_context_unresolved"

def test_verify_missing_policy(original_action, valid_approval):
    result = verify_approval(original_action, None, valid_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "policy_not_found"

def test_verify_invalid_policy(original_action, valid_approval):
    invalid_policy = {"schema_version": "invalid"}
    result = verify_approval(original_action, invalid_policy, valid_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "policy_invalid"

def test_verify_unknown_risk_level(original_action, policy, valid_approval):
    original_action["risk_level"] = "unknown_risk"
    result = verify_approval(original_action, policy, valid_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "risk_level_unknown"

def test_verify_high_risk_missing_approval(original_action, policy):
    result = verify_approval(original_action, policy, None)
    assert result["decision"] == "blocked"
    assert result["reason"] == "approval_required_missing"

def test_verify_low_risk_missing_approval(low_risk_action, policy):
    result = verify_approval(low_risk_action, policy, None)
    assert result["decision"] == "allowed"
    assert result["reason"] == "approval_not_required"
    assert result["policy_id"] == "default"
    assert result["policy_rule_id"] == "low-risk-no-approval"
    assert result["approval_required"] is False


def test_verify_approval_free_policy_without_ids(low_risk_action):
    policy = {
        "schema_version": "policy.v1",
        "rules": [{"risk_level": "low", "approval_required": False}],
    }

    result = verify_approval(low_risk_action, policy)

    assert result["decision"] == "allowed"
    assert result["reason"] == "approval_not_required"
    assert result["approval_required"] is False


def test_verify_low_risk_with_approval(low_risk_action, policy, valid_approval):
    result = verify_approval(low_risk_action, policy, valid_approval)
    assert result["decision"] == "allowed"
    assert result["reason"] == "approval_not_required"
    assert result["details"]["approval_present_but_not_required"] is True

@pytest.mark.parametrize(
    ("method", "reason"),
    [
        ("simulated", "hardware_attestation_required"),
        ("placeholder_security_key", "hardware_attestation_required"),
        ("hardware_security_key", "hardware_attestation_not_implemented"),
    ],
)
def test_verify_approval_attestation_required(
    original_action, policy, valid_approval, trusted_registry, method, reason,
):
    policy["rules"][0]["attestation_required"] = True
    valid_approval["approval_method"] = method
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == reason
    assert result["attestation_required"] is True
    assert result["attestation_verified"] is False

def test_verify_expired_approval(original_action, policy, valid_approval, trusted_registry):
    # Set 'now' to after the approval expires (which is 14:00:00Z)
    now = datetime(2026, 7, 1, 15, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=now,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == "approval_expired"

def test_verify_hash_mismatch(policy, valid_approval):
    mutated_action = load_fixture("examples/action_requests/delete_customer_exports_mutated.json")
    now = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    result = verify_approval(mutated_action, policy, valid_approval, now_iso=now)
    assert result["decision"] == "blocked"
    assert result["reason"] == "action_hash_mismatch"

def test_verify_malformed_action(policy, valid_approval):
    malformed_action = load_fixture("examples/action_requests/malformed_action_request.json")
    result = verify_approval(malformed_action, policy, valid_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "malformed_action"

def test_verify_malformed_approval(original_action, policy):
    malformed_approval = load_fixture("examples/approval_packets/malformed_approval_packet.json")
    result = verify_approval(original_action, policy, malformed_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "malformed_approval"

def test_verify_unknown_approver(original_action, policy, valid_approval, trusted_registry):
    trusted_registry["approvers"] = []
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == "unknown_approver"


def test_verify_inactive_approver(original_action, policy, valid_approval, trusted_registry):
    trusted_registry["approvers"][0]["status"] = "inactive"
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == "inactive_approver"


def test_verify_requires_permitted_approval_method(original_action, policy, valid_approval, trusted_registry):
    trusted_registry["approvers"][0]["approval_methods"] = ["placeholder_security_key"]
    result = verify_approval(
        original_action, policy, valid_approval, now_iso=VERIFICATION_TIME,
        approvers_registry=trusted_registry, simulation=True,
    )
    assert result["decision"] == "blocked"
    assert result["reason"] == "approval_method_not_permitted"

def test_verify_approval_method_unknown(original_action, policy, valid_approval):
    valid_approval["approval_method"] = "unknown_method"
    result = verify_approval(original_action, policy, valid_approval)
    assert result["decision"] == "blocked"
    assert result["reason"] == "approval_method_unknown"
