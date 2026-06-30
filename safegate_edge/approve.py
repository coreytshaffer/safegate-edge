from typing import Any, Optional
from datetime import datetime, timezone
import hashlib

from .schema import validate_review_packet, validate_approval

def _get_utc_now_iso(now_iso: Optional[str] = None) -> str:
    if now_iso:
        return now_iso
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def create_approval_packet(
    review_packet: dict[str, Any],
    approver_id: str,
    approvers_registry: dict[str, Any],
    approval_status: str = "approved",
    now_iso: Optional[str] = None
) -> dict[str, Any]:
    
    # 1. Validate Review Packet
    review_errors = validate_review_packet(review_packet)
    if review_errors:
        raise ValueError(f"Invalid review packet: {review_errors}")
        
    if review_packet.get("review_status") != "pending_review":
        raise ValueError(f"Review packet is not pending_review: {review_packet.get('review_status')}")
        
    # 2. Expiration Check
    current_time_iso = _get_utc_now_iso(now_iso)
    expires_at = review_packet.get("expires_at")
    if expires_at and current_time_iso > expires_at:
        raise ValueError("Review packet has expired.")
        
    # 3. Validate Approver
    if "approvers" not in approvers_registry:
        raise ValueError("Invalid approvers registry format.")
        
    approvers = approvers_registry["approvers"]
    approver = next((a for a in approvers if a.get("approver_id") == approver_id), None)
    
    if not approver:
        raise ValueError(f"Unknown approver: {approver_id}")
        
    if approver.get("status") != "active":
        raise ValueError(f"Approver is not active: {approver_id}")
        
    # 4. Status Check
    if approval_status not in ["approved", "denied"]:
        raise ValueError(f"Invalid approval_status: {approval_status}")
        
    # 5. Generate deterministic ID
    # apr-<first 8 chars of sha256(review_id + approver_id + approval_status + action_hash)>
    review_id = review_packet.get("review_id", "")
    action_hash = review_packet.get("action_hash", "")
    id_seed = f"{review_id}{approver_id}{approval_status}{action_hash}".encode("utf-8")
    hash_prefix = hashlib.sha256(id_seed).hexdigest()[:8]
    approval_id = f"apr-{hash_prefix}"
    
    # 6. Build Approval Packet
    packet = {
        "schema_version": "approval_packet.v1",
        "approval_id": approval_id,
        "review_id": review_id,
        "action_id": review_packet.get("action_id"),
        "action_hash": action_hash,
        "approver_id": approver_id,
        "approved_at": current_time_iso,
        "expires_at": expires_at,
        "approval_status": approval_status,
        "approval_method": "simulated",
        "signature_or_attestation_placeholder": "PLACEHOLDER",
        "policy_id": review_packet.get("policy_id"),
        "policy_rule_id": review_packet.get("policy_rule_id"),
        "approval_required": review_packet.get("approval_required"),
        "metadata": {}
    }
    
    if approval_status == "denied":
        packet["metadata"]["approval_decision"] = "denied"
        
    # Validate generated packet
    packet_errors = validate_approval(packet)
    if packet_errors:
        raise ValueError(f"Generated approval packet is invalid: {packet_errors}")
        
    return packet
