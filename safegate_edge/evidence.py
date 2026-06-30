import json
import os
import hashlib
from typing import Any, Optional
from datetime import datetime, timezone

def _hash_file(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return "sha256:" + hasher.hexdigest()

def _write_json(filepath: str, data: Any) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def _write_text(filepath: str, data: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(data)

def export_evidence_bundle(
    action_request: dict[str, Any],
    approval_packet: Optional[dict[str, Any]],
    verification_result: dict[str, Any],
    execution_decision: dict[str, Any],
    observe_events_jsonl: str,
    output_dir: str,
    policy_snapshot: Optional[dict[str, Any]] = None,
    now: Optional[datetime] = None
) -> dict[str, Any]:
    
    os.makedirs(output_dir, exist_ok=True)
    
    files_to_write = {
        "action_request.json": action_request,
        "verification_result.json": verification_result,
        "execution_decision.json": execution_decision
    }
    
    if approval_packet is not None:
        files_to_write["approval_packet.json"] = approval_packet
    else:
        files_to_write["approval_packet.json"] = {
            "approval_packet": None,
            "reason": verification_result.get("reason", "unknown")
        }
        
    if policy_snapshot is not None:
        files_to_write["policy_snapshot.json"] = policy_snapshot
    else:
        files_to_write["policy_snapshot.json"] = {
            "policy": None,
            "reason": "policy_not_found"
        }

    for filename, data in files_to_write.items():
        _write_json(os.path.join(output_dir, filename), data)
        
    _write_text(os.path.join(output_dir, "observe_events.jsonl"), observe_events_jsonl)
    
    manifest_files = []
    expected_filenames = [
        "action_request.json", 
        "approval_packet.json", 
        "verification_result.json", 
        "execution_decision.json", 
        "policy_snapshot.json",
        "observe_events.jsonl"
    ]
    
    for filename in expected_filenames:
        filepath = os.path.join(output_dir, filename)
        manifest_files.append({
            "path": filename,
            "sha256": _hash_file(filepath)
        })
        
    export_time = now or datetime.now(timezone.utc)
        
    manifest = {
        "schema_version": "evidence_manifest.v1",
        "exported_at": export_time.isoformat().replace("+00:00", "Z"),
        "files": manifest_files
    }
    
    # Calculate bundle hash
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    bundle_hash = "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()
    
    manifest["bundle_hash"] = bundle_hash
    
    _write_json(os.path.join(output_dir, "evidence_manifest.json"), manifest)
    
    return manifest
