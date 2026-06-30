import sys
import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from safegate_edge.cli import main

def test_cli_hash(capsys):
    main(["hash", "--action", "examples/action_requests/delete_customer_exports_original.json"])
    captured = capsys.readouterr()
    assert captured.out.startswith("sha256:")
    assert len(captured.out.strip()) == 7 + 64

@patch("safegate_edge.verifier.datetime")
def test_cli_verify_allowed(mock_datetime, capsys):
    mock_datetime.now.return_value = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    mock_datetime.fromisoformat = datetime.fromisoformat
    
    # Should exit 0
    with pytest.raises(SystemExit) as e:
        main([
            "verify", 
            "--action", "examples/action_requests/delete_customer_exports_original.json",
            "--approval", "examples/approval_packets/valid_approval.json"
        ])
    assert e.value.code == 0

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
