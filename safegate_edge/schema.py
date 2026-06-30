from typing import Any, List

ACTION_REQUIRED_FIELDS = frozenset({
    "action_id",
    "action_type",
    "requester",
    "command",
    "target",
    "working_directory",
    "risk_level",
    "created_at",
    "expires_at",
    "metadata",
})

APPROVAL_REQUIRED_FIELDS = frozenset({
    "approval_id",
    "action_id",
    "action_hash",
    "approver_id",
    "approved_at",
    "expires_at",
    "approval_status",
    "approval_method",
    "signature_or_attestation_placeholder",
    "metadata",
})

def validate_action(action: dict[str, Any]) -> List[str]:
    """Validate an action request against the schema.
    Returns a list of errors, or an empty list if valid.
    """
    errors = []
    if not isinstance(action, dict):
        return ["Action must be a JSON object"]
    
    missing = ACTION_REQUIRED_FIELDS - set(action.keys())
    if missing:
        errors.append(f"Missing required fields in ActionRequest: {sorted(missing)}")
        
    return errors

def validate_approval(approval: dict[str, Any]) -> List[str]:
    """Validate an approval packet against the schema.
    Returns a list of errors, or an empty list if valid.
    """
    errors = []
    if not isinstance(approval, dict):
        return ["Approval must be a JSON object"]
    
    missing = APPROVAL_REQUIRED_FIELDS - set(approval.keys())
    if missing:
        errors.append(f"Missing required fields in ApprovalPacket: {sorted(missing)}")
        
    if "action_hash" in approval and not isinstance(approval["action_hash"], str):
        errors.append("Field 'action_hash' must be a string")
        
    return errors

def validate_verification_result(result: dict[str, Any]) -> List[str]:
    errors = []
    if not isinstance(result, dict):
        return ["VerificationResult must be a JSON object"]
    
    required_fields = [
        "schema_version",
        "verification_id",
        "action_id",
        "action_hash",
        "approval_id",
        "decision",
        "reason",
        "verified_at",
        "verifier_version",
        "policy_id",
        "policy_rule_id",
        "approval_required",
        "details"
    ]
    missing = [f for f in required_fields if f not in result]
    if missing:
        errors.append(f"Missing required fields in VerificationResult: {missing}")
        
    if result.get("schema_version") != "verification_result.v1":
        errors.append("Invalid or missing schema_version, expected 'verification_result.v1'")
        
    return errors
