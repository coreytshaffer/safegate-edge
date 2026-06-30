import os
import json
import pytest
from datetime import datetime, timezone
from safegate_edge.evidence import export_evidence_bundle, _hash_file

def test_export_evidence_bundle(tmp_path):
    action = {"action_id": "act-1"}
    approval = {"approval_id": "apr-1"}
    vr = {"verification_id": "vrf-1", "decision": "allowed", "reason": "valid"}
    ed = {
        "decision_id": "dec-1",
        "action_id": "act-1",
        "approval_id": "apr-1",
        "verification_id": "vrf-1",
        "decision": "allowed",
        "reason": "valid"
    }
    events = '{"event_id": "evt-1"}\n'
    
    out_dir = str(tmp_path / "smoke")
    
    now = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    
    manifest = export_evidence_bundle(
        action_request=action,
        approval_packet=approval,
        verification_result=vr,
        execution_decision=ed,
        observe_events_jsonl=events,
        output_dir=out_dir,
        policy_snapshot={"policy_id": "default"},
        now=now
    )
    
    # Check 7 files exist
    assert os.path.exists(os.path.join(out_dir, "action_request.json"))
    assert os.path.exists(os.path.join(out_dir, "approval_packet.json"))
    assert os.path.exists(os.path.join(out_dir, "verification_result.json"))
    assert os.path.exists(os.path.join(out_dir, "execution_decision.json"))
    assert os.path.exists(os.path.join(out_dir, "policy_snapshot.json"))
    assert os.path.exists(os.path.join(out_dir, "observe_events.jsonl"))
    assert os.path.exists(os.path.join(out_dir, "evidence_manifest.json"))
    
    # Verify manifest file hashes
    assert len(manifest["files"]) == 6
    
    for f_info in manifest["files"]:
        filepath = os.path.join(out_dir, f_info["path"])
        actual_hash = _hash_file(filepath)
        assert actual_hash == f_info["sha256"], f"Hash mismatch for {f_info['path']}"
