import uuid
from datetime import datetime, timezone
from typing import Any, Optional

DECISION_SCHEMA_VERSION = "1.0"
VERIFIER_VERSION = "0.1.0"

def create_execution_decision(
    verification_result: dict[str, Any],
    execution_mode: str = "simulated",
    policy_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Build an execution decision from a trusted verifier result."""
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    decision = verification_result["decision"]
    reason = verification_result["reason"]
    details = verification_result.get("details", {})
    if decision == "simulated_allowed" or details.get("simulation_only") is True:
        execution_mode = "simulated"

    if decision not in ("allowed", "simulated_allowed"):
        execution_status = "blocked_before_execution"
    elif execution_mode == "simulated":
        decision = "simulated_allowed"
        execution_status = "simulation_only"
    elif (
        reason == "approval_not_required"
        and verification_result.get("approval_required") is False
        and verification_result.get("approval_method") is None
    ):
        execution_status = "ready_for_execution"
    else:
        decision = "blocked"
        reason = "execution_authority_unverified"
        execution_status = "blocked_before_execution"

    return {
        "decision_id": f"dec-{uuid.uuid4().hex[:8]}",
        "action_id": verification_result["action_id"],
        "action_hash": verification_result["action_hash"],
        "approval_id": verification_result["approval_id"],
        "verification_id": verification_result["verification_id"],
        "decision": decision,
        "reason": reason,
        "decided_at": now.isoformat(),
        "execution_mode": execution_mode,
        "execution_status": execution_status,
        "policy_id": policy_id,
        "verifier_version": verification_result.get("verifier_version", VERIFIER_VERSION),
        "details": details,
        "schema_version": DECISION_SCHEMA_VERSION,
    }
