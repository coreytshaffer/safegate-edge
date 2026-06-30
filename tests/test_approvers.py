import pytest
from safegate_edge.approvers import validate_approver_registry, get_active_approvers, has_duplicate_active_approvers

def test_validate_approver_registry():
    valid = {
        "schema_version": "approvers.v1",
        "approvers": []
    }
    assert validate_approver_registry(valid) == []
    
    invalid_schema = {
        "schema_version": "invalid",
        "approvers": []
    }
    assert len(validate_approver_registry(invalid_schema)) == 1
    
    missing_approvers = {
        "schema_version": "approvers.v1"
    }
    assert len(validate_approver_registry(missing_approvers)) == 1

def test_get_active_approvers():
    reg = {
        "schema_version": "approvers.v1",
        "approvers": [
            {"approver_id": "a1", "status": "active"},
            {"approver_id": "a2", "status": "inactive"}
        ]
    }
    active = get_active_approvers(reg)
    assert len(active) == 1
    assert active[0]["approver_id"] == "a1"

def test_has_duplicate_active_approvers():
    reg_no_dupes = {
        "approvers": [
            {"approver_id": "a1", "status": "active"},
            {"approver_id": "a2", "status": "active"}
        ]
    }
    assert not has_duplicate_active_approvers(reg_no_dupes)
    
    reg_dupes = {
        "approvers": [
            {"approver_id": "a1", "status": "active"},
            {"approver_id": "a1", "status": "active"}
        ]
    }
    assert has_duplicate_active_approvers(reg_dupes)
