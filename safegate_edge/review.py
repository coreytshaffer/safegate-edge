from typing import Any, Optional
from datetime import datetime, timezone
from .canonical import canonical_action_hash
from .schema import validate_action, validate_review_packet
from .policy import validate_policy, requires_approval
from .verifier import _resolve_policy_rule

ACTION_SUMMARY_TEMPLATES = {
    "delete_customer_exports": "Delete files matching {target} from {working_directory}.",
    "filesystem.read": "Read files matching {target} from {working_directory}.",
}

def _get_human_summary(action: dict[str, Any]) -> str:
    action_type = action.get("action_type")
    template = ACTION_SUMMARY_TEMPLATES.get(action_type)
    if template:
        # Simple string formatting using action dict keys
        try:
            return template.format(**action)
        except KeyError:
            pass # Fallback if expected keys are missing
            
    return f"Requested action '{action_type}' targeting '{action.get('target', 'unknown')}' from requester '{action.get('requester', 'unknown')}'."

def create_review_packet(action: dict[str, Any], policy: Optional[dict[str, Any]], now: Optional[datetime] = None) -> dict[str, Any]:
    # 1. Validate action
    action_errors = validate_action(action)
    if action_errors:
        raise ValueError(f"Action validation failed: {action_errors}")
        
    action_hash = canonical_action_hash(action)
    
    # 2. Validate policy
    if not policy:
        raise ValueError("policy_not_found: Policy is required to create a review packet")
        
    policy_errors = validate_policy(policy)
    if policy_errors:
        raise ValueError(f"policy_invalid: {policy_errors}")
        
    # 3. Risk Level and Rule Resolution
    risk_level = action.get("risk_level")
    known_risks = ["low", "medium", "high", "critical"]
    if risk_level not in known_risks:
        raise ValueError(f"risk_level_unknown: {risk_level}")
        
    rule = _resolve_policy_rule(policy, risk_level)
    policy_rule_id = rule.get("rule_id") if rule else None
    
    # 4. Determine Approval Requirement
    approval_req = requires_approval(policy, risk_level, action.get("action_type"))
    
    if approval_req:
        instructions = "Review the exact action details and action hash before approving. Approval must bind to this action_hash. If the action changes, SafeGate must block execution."
    else:
        instructions = "Policy does not require approval for this action, but the review packet records the action hash and policy decision for traceability."
        
    # 5. Build Review Packet
    # review_id: rev-<first 8 chars of action hash>
    hash_prefix = action_hash.split(":")[-1][:8]
    review_id = f"rev-{hash_prefix}"
    
    packet = {
        "schema_version": "human_review_packet.v1",
        "review_id": review_id,
        "action_id": action.get("action_id"),
        "action_hash": action_hash,
        "action_type": action.get("action_type"),
        "risk_level": risk_level,
        "policy_id": policy.get("policy_id"),
        "policy_rule_id": policy_rule_id,
        "approval_required": approval_req,
        "human_summary": _get_human_summary(action),
        "requested_by": action.get("requester"),
        "created_at": action.get("created_at"),
        "expires_at": action.get("expires_at"),  # Inherit from action
        "review_status": "pending_review",
        "approval_instructions": instructions,
        
        # Optional useful raw fields
        "target": action.get("target"),
        "command": action.get("command"),
        "working_directory": action.get("working_directory"),
        "metadata": action.get("metadata")
    }
    
    # Validate the generated packet
    packet_errors = validate_review_packet(packet)
    if packet_errors:
        raise ValueError(f"Generated review packet is invalid: {packet_errors}")
        
    return packet
