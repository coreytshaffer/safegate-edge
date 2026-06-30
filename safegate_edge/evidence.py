import json
import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, List, Optional

MANIFEST_SCHEMA_VERSION = "1.0"
SAFEGATE_VERSION = "0.1.0"

def _hash_file(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"

def _save_json(filepath: str, data: Any) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
def _save_text(filepath: str, text: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

def export_evidence_bundle(
    action_request: dict[str, Any],
    approval_packet: Optional[dict[str, Any]],
    verification_result: dict[str, Any],
    execution_decision: dict[str, Any],
    observe_events_jsonl: str,
    output_dir: str,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    os.makedirs(output_dir, exist_ok=True)
    
    files_to_hash = []
    
    # 1. Action Request
    action_path = os.path.join(output_dir, "action_request.json")
    _save_json(action_path, action_request)
    files_to_hash.append(("action_request.json", action_path, "application/json"))
    
    # 2. Approval Packet
    if approval_packet:
        approval_path = os.path.join(output_dir, "approval_packet.json")
        _save_json(approval_path, approval_packet)
        files_to_hash.append(("approval_packet.json", approval_path, "application/json"))
        
    # 3. Verification Result
    vr_path = os.path.join(output_dir, "verification_result.json")
    _save_json(vr_path, verification_result)
    files_to_hash.append(("verification_result.json", vr_path, "application/json"))
    
    # 4. Execution Decision
    ed_path = os.path.join(output_dir, "execution_decision.json")
    _save_json(ed_path, execution_decision)
    files_to_hash.append(("execution_decision.json", ed_path, "application/json"))
    
    # 5. Observe Events
    events_path = os.path.join(output_dir, "observe_events.jsonl")
    _save_text(events_path, observe_events_jsonl)
    files_to_hash.append(("observe_events.jsonl", events_path, "application/jsonl"))
    
    # Calculate file hashes
    manifest_files = []
    for filename, filepath, content_type in files_to_hash:
        manifest_files.append({
            "path": filename,
            "sha256": _hash_file(filepath),
            "content_type": content_type
        })
        
    # 6. Evidence Manifest
    manifest = {
        "bundle_id": f"evb-{uuid.uuid4().hex[:8]}",
        "generated_at": now.isoformat(),
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "safegate_version": SAFEGATE_VERSION,
        "action_id": execution_decision["action_id"],
        "approval_id": execution_decision.get("approval_id"),
        "verification_id": execution_decision["verification_id"],
        "decision_id": execution_decision["decision_id"],
        "decision": execution_decision["decision"],
        "reason": execution_decision["reason"],
        "files": manifest_files,
    }
    
    # Compute bundle hash excluding bundle_hash itself
    canonical_manifest = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical_manifest.encode("utf-8")).hexdigest()
    manifest["bundle_hash"] = f"sha256:{digest}"
    
    manifest_path = os.path.join(output_dir, "evidence_manifest.json")
    _save_json(manifest_path, manifest)
    
    return manifest
