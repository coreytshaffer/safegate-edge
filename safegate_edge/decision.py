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
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    decision = verification_result["decision"]
    
    if decision == "blocked":
        execution_status = "blocked_before_execution"
    else:
        execution_status = "ready_for_execution" # In simulated mode, it stops here

    return {
        "decision_id": f"dec-{uuid.uuid4().hex[:8]}",
        "action_id": verification_result["action_id"],
        "action_hash": verification_result["action_hash"],
        "approval_id": verification_result["approval_id"],
        "verification_id": verification_result["verification_id"],
        "decision": decision,
        "reason": verification_result["reason"],
        "decided_at": now.isoformat(),
        "execution_mode": execution_mode,
        "execution_status": execution_status,
        "policy_id": policy_id,
        "verifier_version": verification_result.get("verifier_version", VERIFIER_VERSION),
        "details": verification_result.get("details", {}),
        "schema_version": DECISION_SCHEMA_VERSION,
    }
