import pytest
import os
import json
from safegate_edge.preflight import run_preflight_checks

def test_run_preflight_checks(tmp_path):
    action_path = tmp_path / "action.json"
    action_path.write_text(json.dumps({
        "schema_version": "action.v1",
        "action_id": "act-1",
        "timestamp": "2026-06-29T00:00:00Z",
        "action_type": "filesystem.delete",
        "risk_level": "high",
        "payload": {}
    }))
    
    # We just want to ensure it runs and returns CheckResults without crashing
    results = run_preflight_checks(str(action_path))
    assert isinstance(results, list)
    assert len(results) > 0
    assert results[0].check_id == "action_exists"
    assert results[0].status == "PASS"

def test_preflight_missing_file():
    results = run_preflight_checks("nonexistent.json")
    assert len(results) == 1
    assert results[0].status == "FAIL"
