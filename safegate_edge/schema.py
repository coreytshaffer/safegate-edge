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
