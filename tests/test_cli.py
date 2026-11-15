import json
import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from safegate_edge.cli import main

def test_cli_hash(capsys):
    main(["hash", "--action", "examples/action_requests/delete_customer_exports_original.json"])
    captured = capsys.readouterr()
    assert captured.out.startswith("sha256:")
    assert len(captured.out.strip()) == 7 + 64

def test_cli_verify_approval_free_action(capsys):
    with pytest.raises(SystemExit) as e:
        main([
            "verify",
            "--action", "examples/action_requests/read_customer_exports_low_risk.json",
        ])
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "decision: allowed" in captured.out
    assert "reason: approval_not_required" in captured.out


@patch("safegate_edge.verifier.datetime")
def test_cli_verify_default_rejects_simulated_approval(mock_datetime, capsys):
    mock_datetime.now.return_value = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    mock_datetime.fromisoformat = datetime.fromisoformat

    with pytest.raises(SystemExit) as e:
        main([
            "verify",
            "--action", "examples/action_requests/delete_customer_exports_original.json",
            "--approval", "examples/approval_packets/valid_approval.json",
        ])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "decision: blocked" in captured.out
    assert "reason: approval_evidence_unverified" in captured.out


@patch("safegate_edge.verifier.datetime")
def test_cli_verify_uses_configured_registry(mock_datetime, capsys, tmp_path):
    mock_datetime.now.return_value = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    mock_datetime.fromisoformat = datetime.fromisoformat
    empty_registry = tmp_path / "approvers.json"
    empty_registry.write_text(json.dumps({"schema_version": "approvers.v1", "approvers": []}), encoding="utf-8")

    with pytest.raises(SystemExit) as e:
        main([
            "verify",
            "--action", "examples/action_requests/delete_customer_exports_original.json",
            "--approval", "examples/approval_packets/valid_approval.json",
            "--approvers", str(empty_registry),
        ])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "decision: blocked" in captured.out
    assert "reason: unknown_approver" in captured.out


@patch("safegate_edge.verifier.datetime")
def test_cli_verify_invalid_registry_only_blocks_when_approval_is_required(mock_datetime, capsys, tmp_path):
    mock_datetime.now.return_value = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    mock_datetime.fromisoformat = datetime.fromisoformat
    invalid_registry = tmp_path / "approvers.json"
    invalid_registry.write_text("{", encoding="utf-8")
    verify = ["verify", "--approvers", str(invalid_registry)]

    with pytest.raises(SystemExit) as e:
        main([*verify, "--action", "examples/action_requests/read_customer_exports_low_risk.json"])
    assert e.value.code == 0
    assert "reason: approval_not_required" in capsys.readouterr().out

    with pytest.raises(SystemExit) as e:
        main([
            *verify,
            "--action", "examples/action_requests/delete_customer_exports_original.json",
            "--approval", "examples/approval_packets/valid_approval.json",
        ])
    assert e.value.code == 1
    assert "reason: approver_registry_invalid" in capsys.readouterr().out


@patch("safegate_edge.verifier.datetime")
def test_cli_verify_blocked_mismatch(mock_datetime, capsys):
    mock_datetime.now.return_value = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    mock_datetime.fromisoformat = datetime.fromisoformat
    
    # Should exit 1
    with pytest.raises(SystemExit) as e:
        main([
            "verify", 
            "--action", "examples/action_requests/delete_customer_exports_mutated.json",
            "--approval", "examples/approval_packets/valid_approval.json"
        ])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "decision: blocked" in captured.out
    assert "reason: action_hash_mismatch" in captured.out
