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
    "schema_version",
    "approval_id",
    "review_id",
    "action_id",
    "action_hash",
    "approver_id",
    "approved_at",
    "expires_at",
    "approval_status",
    "approval_method",
    "signature_or_attestation_placeholder",
    "policy_id",
    "policy_rule_id",
    "approval_required"
})

KNOWN_APPROVAL_METHODS = {
    "simulated",
    "placeholder_security_key",
    "hardware_security_key",
}

def validate_approval(approval: dict[str, Any]) -> List[str]:
    """Validate an approval packet against the schema.
    Returns a list of errors, or an empty list if valid.
    """
    errors = []
    if not isinstance(approval, dict):
        return ["Approval must be a JSON object"]
    
    missing = APPROVAL_REQUIRED_FIELDS - set(approval.keys())
    if missing:
        errors.append(f"Missing required fields in approval: {sorted(missing)}")
        
    if approval.get("schema_version") != "approval_packet.v1":
        errors.append("Invalid or missing schema_version, expected 'approval_packet.v1'")
        
    status = approval.get("approval_status")
    if status not in ["approved", "denied"]:
        errors.append(f"Invalid approval_status: {status}")
        
    method = approval.get("approval_method")
    if not isinstance(method, str) or method not in KNOWN_APPROVAL_METHODS:
        errors.append(f"approval_method_unknown: '{method}'")
        
    if "action_hash" in approval and not isinstance(approval["action_hash"], str):
        errors.append("Field 'action_hash' must be a string")
        
    return errors

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
        "approval_method",
        "attestation_required",
        "attestation_verified",
        "details"
    ]
    missing = [f for f in required_fields if f not in result]
    if missing:
        errors.append(f"Missing required fields in VerificationResult: {missing}")
        
    if result.get("schema_version") != "verification_result.v1":
        errors.append("Invalid or missing schema_version, expected 'verification_result.v1'")
        
    return errors

HUMAN_REVIEW_REQUIRED_FIELDS = frozenset({
    "schema_version",
    "review_id",
    "action_id",
    "action_hash",
    "action_type",
    "risk_level",
    "policy_id",
    "policy_rule_id",
    "approval_required",
    "human_summary",
    "requested_by",
    "created_at",
    "expires_at",
    "review_status",
    "approval_instructions"
})

def validate_review_packet(packet: dict[str, Any]) -> List[str]:
    errors = []
    if not isinstance(packet, dict):
        return ["HumanReviewPacket must be a JSON object"]
        
    missing = HUMAN_REVIEW_REQUIRED_FIELDS - set(packet.keys())
    if missing:
        errors.append(f"Missing required fields in HumanReviewPacket: {sorted(missing)}")
        
    if packet.get("schema_version") != "human_review_packet.v1":
        errors.append("Invalid or missing schema_version, expected 'human_review_packet.v1'")
        
    return errors
