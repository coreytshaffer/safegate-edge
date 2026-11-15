import json

import pytest

from safegate_edge.cli import main
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
    assert results.get("original_decision") == "simulated_allowed"
    assert results.get("original_reason") == "valid_simulated_approval"
    assert results.get("mutated_decision") == "blocked"
    assert results.get("mutated_reason") == "action_hash_mismatch"
    assert results.get("denied_decision") == "blocked"
    assert results.get("denied_reason") == "approval_not_granted"

    original_result = json.loads((output_dir / "verify_original_allowed.json").read_text(encoding="utf-8"))
    assert original_result["decision"] == "simulated_allowed"
    assert original_result["details"]["simulation_only"] is True

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


def _write_registry(tmp_path, approvers):
    registry = tmp_path / "approvers.json"
    registry.write_text(
        json.dumps({"schema_version": "approvers.v1", "approvers": approvers}),
        encoding="utf-8",
    )
    return registry


def test_demo_selects_an_active_approver_permitted_to_simulate(tmp_path):
    registry = _write_registry(tmp_path, [
        {"approver_id": "inactive", "status": "inactive", "approval_methods": ["simulated"]},
        {"approver_id": "hardware", "status": "active", "approval_methods": ["hardware_security_key"]},
        {"approver_id": "simulator", "status": "active", "approval_methods": ["simulated"]},
    ])
    output_dir = tmp_path / "demo"

    run_demo(output_dir=str(output_dir), approvers_path=str(registry))

    approval = json.loads((output_dir / "generated_approval.json").read_text(encoding="utf-8"))
    original = json.loads((output_dir / "verify_original_allowed.json").read_text(encoding="utf-8"))
    assert approval["approver_id"] == "simulator"
    assert original["decision"] == "simulated_allowed"
    assert original["reason"] == "valid_simulated_approval"


def test_demo_requires_an_active_approver_permitted_to_simulate(tmp_path):
    registry = _write_registry(tmp_path, [
        {"approver_id": "hardware", "status": "active", "approval_methods": ["hardware_security_key"]},
    ])
    output_dir = tmp_path / "demo"

    with pytest.raises(ValueError, match="No active approver permits simulated approval"):
        run_demo(output_dir=str(output_dir), approvers_path=str(registry))

    assert not output_dir.exists()


@pytest.mark.parametrize(("step", "unexpected", "scenario"), [
    (0, ("simulated_allowed", "approval_not_required"), "original action"),
    (1, ("simulated_allowed", "action_hash_mismatch"), "changed action"),
    (2, ("blocked", "approval_required_missing"), "denied approval"),
])
def test_demo_cli_rejects_unexpected_outcomes_before_replacing_outputs(
    tmp_path, monkeypatch, capsys, step, unexpected, scenario,
):
    outcomes = [
        ("simulated_allowed", "valid_simulated_approval"),
        ("blocked", "action_hash_mismatch"),
        ("blocked", "approval_not_granted"),
    ]
    outcomes[step] = unexpected
    results = iter({"decision": decision, "reason": reason} for decision, reason in outcomes)
    monkeypatch.setattr("safegate_edge.demo.verify_approval", lambda *args, **kwargs: next(results))

    output_dir = tmp_path / "demo"
    evidence = output_dir / "evidence_bundle" / "evidence_manifest.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("previous evidence", encoding="utf-8")
    summary = output_dir / "demo_summary.json"
    summary.write_text("previous summary", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        main(["demo", "run", "--output-dir", str(output_dir)])

    assert error.value.code == 1
    captured = capsys.readouterr()
    assert f"Demo {scenario} expected" in captured.err
    assert f"got {unexpected[0]} ({unexpected[1]})" in captured.err
    assert "completed successfully" not in captured.out
    assert evidence.read_text(encoding="utf-8") == "previous evidence"
    assert summary.read_text(encoding="utf-8") == "previous summary"
    assert not (output_dir / "verify_original_allowed.json").exists()
