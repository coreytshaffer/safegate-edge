import uuid
from datetime import datetime, timezone
from typing import Any, Optional
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

def verify_approval(action: dict[str, Any], policy: Optional[dict[str, Any]], approval: Optional[dict[str, Any]] = None, now_iso: Optional[str] = None) -> dict[str, Any]:
    """Verify an action request against an approval packet and a policy."""
    verification_id = f"vrf-{uuid.uuid4().hex}"
    verified_at = _utc_now_iso(now_iso)
    
    # Base structure
    result = {
        "schema_version": "verification_result.v1",
        "verification_id": verification_id,
        "action_id": action.get("action_id"),
        "action_hash": None,
        "approval_id": approval.get("approval_id") if approval else None,
        "decision": "blocked",
        "reason": "unknown_error",
        "verified_at": verified_at,
        "verifier_version": "0.1.0",
        "policy_id": None,
        "policy_rule_id": None,
        "approval_required": None,
        "details": {}
    }
    
    # 1. Validate action schema
    action_errors = validate_action(action)
    if action_errors:
        result["reason"] = "malformed_action"
        result["details"] = {"errors": action_errors}
        return result
        
    try:
        action_hash = canonical_action_hash(action)
        result["action_hash"] = action_hash
    except Exception as e:
        result["reason"] = "hashing_failed"
        result["details"] = {"error": str(e)}
        return result

    # 2. Validate policy presence
    if not policy:
        result["reason"] = "policy_not_found"
        return result

    # 3. Validate policy schema
    policy_errors = policy_module.validate_policy(policy)
    if policy_errors:
        result["reason"] = "policy_invalid"
        result["details"] = {"errors": policy_errors}
        return result
        
    result["policy_id"] = policy.get("policy_id")

    # 4. Validate risk_level
    risk_level = action.get("risk_level")
    known_risks = ["low", "medium", "high", "critical"]
    if risk_level not in known_risks:
        result["reason"] = "risk_level_unknown"
        result["details"] = {"risk_level": risk_level}
        return result

    # 5. Resolve applicable policy rule
    rule = _resolve_policy_rule(policy, risk_level)
    if rule:
        result["policy_rule_id"] = rule.get("rule_id")

    # 6. Determine whether approval is required
    approval_req = policy_module.requires_approval(policy, risk_level, action.get("action_type"))
    result["approval_required"] = approval_req

    # 7. If approval is not required, allow
    if not approval_req:
        result["decision"] = "allowed"
        result["reason"] = "approval_not_required"
        if approval is not None:
            result["details"] = {"approval_present_but_not_required": True}
        return result

    # 8. If approval is required and missing, block
    if not approval:
        result["reason"] = "approval_required_missing"
        return result

    # 9. Run existing approval checks
    approval_errors = validate_approval(approval)
    if approval_errors:
        result["reason"] = "malformed_approval"
        result["details"] = {"errors": approval_errors}
        return result

    if approval.get("approval_status") == "denied":
        result["reason"] = "approval_not_granted"
        return result

    if approval.get("action_hash") != action_hash:
        result["reason"] = "action_hash_mismatch"
        result["details"] = {
            "expected_hash": approval.get("action_hash"),
            "actual_hash": action_hash
        }
        return result

    if approval.get("approval_status") != "approved":
        result["reason"] = "approval_not_granted"
        return result

    if not approval.get("approver_id"):
        result["reason"] = "unknown_approver"
        result["details"] = {"message": "Approver ID is missing or empty"}
        return result

    # Check expiration
    expires_at_str = approval.get("expires_at")
    if expires_at_str:
        # Simple string comparison works for ISO 8601 if we assume UTC
        if verified_at > expires_at_str:
            result["reason"] = "approval_expired"
            result["details"] = {
                "expires_at": expires_at_str,
                "verified_at": verified_at
            }
            return result
            
    result["decision"] = "allowed"
    result["reason"] = "valid_approval"
    return result
