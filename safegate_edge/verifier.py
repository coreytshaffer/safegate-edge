import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .canonical import canonical_action_hash
from .schema import validate_action, validate_approval

VERIFIER_VERSION = "0.1.0"

def create_verification_result(
    action_id: str,
    action_hash: str,
    approval_id: Optional[str],
    decision: str,
    reason: str,
    details: dict[str, Any],
    now: datetime
) -> dict[str, Any]:
    return {
        "verification_id": f"vrf-{uuid.uuid4().hex[:8]}",
        "action_id": action_id,
        "action_hash": action_hash,
        "approval_id": approval_id or "",
        "decision": decision,
        "reason": reason,
        "verified_at": now.isoformat(),
        "verifier_version": VERIFIER_VERSION,
        "details": details,
    }

def verify_approval(
    action: dict[str, Any],
    approval: Optional[dict[str, Any]],
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Verify that an approval packet authorizes the given action.
    
    Fail-closed: any error, missing data, or ambiguity results in blocked.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # 1. Validate action contract
    action_errors = validate_action(action)
    if action_errors:
        return create_verification_result(
            action_id=action.get("action_id", "unknown"),
            action_hash="unknown",
            approval_id=approval.get("approval_id") if approval else None,
            decision="blocked",
            reason="malformed_action",
            details={"errors": action_errors},
            now=now
        )
        
    action_id = action["action_id"]
    expected_hash = canonical_action_hash(action)

    # 2. Check missing approval
    if approval is None:
        return create_verification_result(
            action_id=action_id,
            action_hash=expected_hash,
            approval_id=None,
            decision="blocked",
            reason="missing_approval",
            details={"message": "No approval packet provided"},
            now=now
        )

    # 3. Validate approval contract
    approval_errors = validate_approval(approval)
    if approval_errors:
        return create_verification_result(
            action_id=action_id,
            action_hash=expected_hash,
            approval_id=approval.get("approval_id", "unknown"),
            decision="blocked",
            reason="malformed_approval",
            details={"errors": approval_errors},
            now=now
        )
        
    approval_id = approval["approval_id"]

    # 4. Check approval status
    if approval.get("approval_status") != "approved":
        return create_verification_result(
            action_id=action_id,
            action_hash=expected_hash,
            approval_id=approval_id,
            decision="blocked",
            reason="approval_not_granted",
            details={"approval_status": approval.get("approval_status")},
            now=now
        )
        
    # 5. Check unknown approver (for now, simply check it exists and isn't empty)
    # We will expand this when we have an approver registry
    if not approval.get("approver_id"):
        return create_verification_result(
            action_id=action_id,
            action_hash=expected_hash,
            approval_id=approval_id,
            decision="blocked",
            reason="unknown_approver",
            details={"message": "Approver ID is missing or empty"},
            now=now
        )

    # 6. Check hash binding
    if approval["action_hash"] != expected_hash:
        return create_verification_result(
            action_id=action_id,
            action_hash=expected_hash,
            approval_id=approval_id,
            decision="blocked",
            reason="action_hash_mismatch",
            details={
                "expected_hash": expected_hash,
                "provided_hash": approval["action_hash"]
            },
            now=now
        )

    # 7. Check expiration
    try:
        expires_at = datetime.fromisoformat(approval["expires_at"])
    except (ValueError, TypeError):
        return create_verification_result(
            action_id=action_id,
            action_hash=expected_hash,
            approval_id=approval_id,
            decision="blocked",
            reason="malformed_approval",
            details={"message": "Invalid expires_at timestamp"},
            now=now
        )

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now >= expires_at:
        return create_verification_result(
            action_id=action_id,
            action_hash=expected_hash,
            approval_id=approval_id,
            decision="blocked",
            reason="approval_expired",
            details={
                "expires_at": expires_at.isoformat(),
                "verified_at": now.isoformat()
            },
            now=now
        )

    # All checks passed
    return create_verification_result(
        action_id=action_id,
        action_hash=expected_hash,
        approval_id=approval_id,
        decision="allowed",
        reason="valid_approval",
        details={"message": "Approval is valid, bound to action, and not expired"},
        now=now
    )
