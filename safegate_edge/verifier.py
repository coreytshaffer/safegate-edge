import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from .approvers import validate_approver_registry
from .schema import validate_action, validate_approval
from .canonical import canonical_action_hash
from . import policy as policy_module

def _utc_now_iso(now_iso: Optional[str] = None) -> str:
    if now_iso:
        return now_iso
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _resolve_policy_rule(pol: dict, risk_level: str) -> Optional[dict]:
    rules = pol.get("rules", [])
    for rule in rules:
        if isinstance(rule, dict) and rule.get("risk_level") == risk_level:
            return rule
    return None

def verify_approval(
    action: dict[str, Any],
    policy: Optional[dict[str, Any]],
    approval: Optional[dict[str, Any]] = None,
    now_iso: Optional[str] = None,
    *,
    approvers_registry: Optional[dict[str, Any]] = None,
    simulation: bool = False,
) -> dict[str, Any]:
    """Verify against caller-configured policy and registry; simulation never authorizes execution."""
    verification_id = f"vrf-{uuid.uuid4().hex}"
    verified_at = _utc_now_iso(now_iso)
    simulation = simulation is True
    details = {"simulation_only": True} if simulation else {}
    
    # Base structure
    result = {
        "schema_version": "verification_result.v1",
        "verification_id": verification_id,
        "action_id": action.get("action_id") if isinstance(action, dict) else None,
        "action_hash": None,
        "approval_id": approval.get("approval_id") if isinstance(approval, dict) else None,
        "decision": "blocked",
        "reason": "unknown_error",
        "verified_at": verified_at,
        "verifier_version": "0.1.0",
        "policy_id": None,
        "policy_rule_id": None,
        "approval_required": None,
        "approval_method": None,
        "attestation_required": None,
        "attestation_verified": False,
        "details": details,
    }
    
    # 1. Validate action schema
    action_errors = validate_action(action)
    if action_errors:
        result["reason"] = "malformed_action"
        details["errors"] = action_errors
        return result
        
    try:
        action_hash = canonical_action_hash(action)
        result["action_hash"] = action_hash
    except Exception as e:
        result["reason"] = "hashing_failed"
        details["error"] = str(e)
        return result

    # 2. Validate policy presence
    if not policy:
        result["reason"] = "policy_not_found"
        return result

    # 3. Validate policy schema
    policy_errors = policy_module.validate_policy(policy)
    if policy_errors:
        result["reason"] = "policy_invalid"
        details["errors"] = policy_errors
        return result
        
    result["policy_id"] = policy.get("policy_id")

    # 4. Validate risk_level
    risk_level = action.get("risk_level")
    known_risks = ["low", "medium", "high", "critical"]
    if risk_level not in known_risks:
        result["reason"] = "risk_level_unknown"
        details["risk_level"] = risk_level
        return result

    # 5. Resolve applicable policy rule
    rule = _resolve_policy_rule(policy, risk_level)
    attestation_required = False
    if rule:
        result["policy_rule_id"] = rule.get("rule_id")
        attestation_required = rule.get("attestation_required", False)
        
    result["attestation_required"] = attestation_required

    # 6. Determine whether approval is required
    approval_req = policy_module.requires_approval(policy, risk_level, action.get("action_type")) is not False
    result["approval_required"] = approval_req

    # 7. If approval is not required, allow
    if not approval_req:
        result["decision"] = "simulated_allowed" if simulation else "allowed"
        result["reason"] = "approval_not_required"
        if approval is not None:
            details["approval_present_but_not_required"] = True
        return result

    policy_context = {key: result[key] for key in ("policy_id", "policy_rule_id")}
    if not all(isinstance(value, str) and value.strip() for value in policy_context.values()):
        result["reason"] = "policy_context_unresolved"
        return result

    # 8. If approval is required and missing, block
    if approval is None:
        result["reason"] = "approval_required_missing"
        return result

    # 9. Run existing approval checks
    approval_errors = validate_approval(approval)
    if approval_errors:
        if any("approval_method_unknown" in e for e in approval_errors):
            result["reason"] = "approval_method_unknown"
        else:
            result["reason"] = "malformed_approval"
        details["errors"] = approval_errors
        return result

    if approval.get("approval_status") == "denied":
        result["reason"] = "approval_not_granted"
        return result

    if approval.get("action_hash") != action_hash:
        result["reason"] = "action_hash_mismatch"
        details.update({
            "expected_hash": approval.get("action_hash"),
            "actual_hash": action_hash
        })
        return result

    if any(approval.get(key) != value for key, value in policy_context.items()) or (
        approval.get("approval_required") is not approval_req
    ):
        result["reason"] = "policy_context_mismatch"
        return result

    approval_method = approval.get("approval_method")
    result["approval_method"] = approval_method
    
    if attestation_required:
        if approval_method in ["simulated", "placeholder_security_key"]:
            result["reason"] = "hardware_attestation_required"
            return result
        elif approval_method == "hardware_security_key":
            result["reason"] = "hardware_attestation_not_implemented"
            return result
        else:
            result["reason"] = "hardware_attestation_required"
            return result
            
    approver_id = approval.get("approver_id")
    if not isinstance(approver_id, str) or not approver_id.strip():
        result["reason"] = "unknown_approver"
        return result

    expires_at_str = approval.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        verification_time = datetime.fromisoformat(verified_at.replace("Z", "+00:00"))
        if expires_at.utcoffset() is None or verification_time.utcoffset() is None:
            raise ValueError("Timestamps require a time zone")
    except (AttributeError, ValueError):
        result["reason"] = "malformed_approval"
        details["message"] = "Approval expiration and verification time must be valid timestamps with a time zone"
        return result
    if verification_time >= expires_at:
        result["reason"] = "approval_expired"
        details.update(expires_at=expires_at_str, verified_at=verified_at)
        return result

    if approvers_registry is None:
        result["reason"] = "approver_registry_missing"
        return result
    registry_errors = validate_approver_registry(approvers_registry)
    if registry_errors:
        result["reason"] = "approver_registry_invalid"
        details["errors"] = registry_errors
        return result

    matches = [
        entry for entry in approvers_registry["approvers"]
        if isinstance(entry, dict) and entry.get("approver_id") == approver_id
    ]
    if not matches:
        result["reason"] = "unknown_approver"
        return result
    if len(matches) != 1:
        result["reason"] = "approver_registry_invalid"
        details["message"] = "Approver ID appears more than once in the registry"
        return result

    approver = matches[0]
    if approver.get("status") != "active":
        result["reason"] = "inactive_approver"
        return result
    methods = approver.get("approval_methods")
    if not isinstance(methods, list) or approval_method not in methods:
        result["reason"] = "approval_method_not_permitted"
        return result

    if simulation and approval_method == "simulated":
        result["decision"] = "simulated_allowed"
        result["reason"] = "valid_simulated_approval"
    else:
        # No approval packet method currently authenticates the signed or attested approval.
        result["reason"] = "approval_evidence_unverified"
    return result
