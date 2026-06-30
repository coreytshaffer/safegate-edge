import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, List, Optional

OBSERVE_SCHEMA_VERSION = "1.0"

def _hash_event_content(event_dict: dict[str, Any]) -> str:
    # Remove event_hash before hashing
    content = {k: v for k, v in event_dict.items() if k != "event_hash"}
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"

def create_observe_event(
    event_type: str,
    sequence: int,
    payload: dict[str, Any],
    action_id: str,
    approval_id: Optional[str] = None,
    verification_id: Optional[str] = None,
    decision_id: Optional[str] = None,
    actor: str = "safegate-system",
    previous_event_hash: Optional[str] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    event = {
        "event_id": f"evt-{uuid.uuid4().hex[:8]}",
        "event_type": event_type,
        "timestamp": now.isoformat(),
        "sequence": sequence,
        "action_id": action_id,
        "approval_id": approval_id,
        "verification_id": verification_id,
        "decision_id": decision_id,
        "actor": actor,
        "payload": payload,
        "previous_event_hash": previous_event_hash,
        "schema_version": OBSERVE_SCHEMA_VERSION,
    }
    
    event["event_hash"] = _hash_event_content(event)
    return event

class EventLogChain:
    def __init__(self):
        self.events: List[dict[str, Any]] = []

    def append(self, 
        event_type: str, 
        payload: dict[str, Any],
        action_id: str,
        approval_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        actor: str = "safegate-system",
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        
        sequence = len(self.events) + 1
        previous_hash = self.events[-1]["event_hash"] if self.events else None
        
        event = create_observe_event(
            event_type=event_type,
            sequence=sequence,
            payload=payload,
            action_id=action_id,
            approval_id=approval_id,
            verification_id=verification_id,
            decision_id=decision_id,
            actor=actor,
            previous_event_hash=previous_hash,
            now=now
        )
        self.events.append(event)
        return event

    def validate_chain(self) -> bool:
        if not self.events:
            return True
        
        for i, event in enumerate(self.events):
            # 1. Validate hash content
            if event["event_hash"] != _hash_event_content(event):
                return False
            # 2. Validate links
            if i == 0:
                if event["previous_event_hash"] is not None:
                    return False
            else:
                if event["previous_event_hash"] != self.events[i-1]["event_hash"]:
                    return False
        return True

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(evt) for evt in self.events) + "\n"
