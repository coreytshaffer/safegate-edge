import os
import json
import pytest
from safegate_edge.demo import run_demo

def test_demo_run(tmp_path):
    output_dir = tmp_path / "safegate_demo"
    
    # Run the demo using the default paths
    run_demo(output_dir=str(output_dir))
    
    # Assert all expected artifacts are created
    assert (output_dir / "review_packet.json").exists()
    assert (output_dir / "generated_approval.json").exists()
    assert (output_dir / "generated_denied_approval.json").exists()
    assert (output_dir / "verify_original_allowed.json").exists()
    assert (output_dir / "verify_mutated_blocked.json").exists()
    assert (output_dir / "verify_denied_blocked.json").exists()
    assert (output_dir / "evidence_bundle").is_dir()
    assert (output_dir / "evidence_bundle" / "evidence_manifest.json").exists()
    assert (output_dir / "demo_summary.json").exists()
    assert (output_dir / "README_DEMO.md").exists()
    
    # Assert assertions inside demo_summary.json
    with open(output_dir / "demo_summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)
        
    assertions = summary.get("assertions", {})
    assert assertions.get("review_packet_created") is True
    assert assertions.get("approval_packet_created") is True
    assert assertions.get("denied_approval_packet_created") is True
    assert assertions.get("original_allowed") is True
    assert assertions.get("mutated_blocked") is True
    assert assertions.get("denied_blocked") is True
    assert assertions.get("evidence_bundle_created") is True
    
    results = summary.get("results", {})
    assert results.get("original_decision") == "allowed"
    assert results.get("original_reason") == "valid_approval"
    assert results.get("mutated_decision") == "blocked"
    assert results.get("mutated_reason") == "action_hash_mismatch"
    assert results.get("denied_decision") == "blocked"
    assert results.get("denied_reason") == "approval_not_granted"

def test_demo_run_overwrite_cleans_safely(tmp_path):
    output_dir = tmp_path / "safegate_demo"
    
    # Write a dummy file to simulate preexisting state
    output_dir.mkdir()
    dummy_file = output_dir / "some_user_file.txt"
    dummy_file.write_text("Do not delete me")
    
    # Run demo multiple times to verify idempotence / overwrite safety
    run_demo(output_dir=str(output_dir))
    run_demo(output_dir=str(output_dir))
    
    assert dummy_file.exists() # Shouldn't wipe arbitrary files
    assert dummy_file.read_text() == "Do not delete me"
    assert (output_dir / "demo_summary.json").exists()
