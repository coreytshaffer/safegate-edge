import pytest
from safegate_edge.policy import validate_policy, requires_approval

def test_validate_policy():
    valid = {
        "schema_version": "policy.v1",
        "rules": []
    }
    assert validate_policy(valid) == []
    
    invalid = {
        "schema_version": "invalid",
        "rules": []
    }
    assert len(validate_policy(invalid)) == 1

def test_requires_approval():
    pol = {
        "rules": [
            {"risk_level": "high", "approval_required": True},
            {"risk_level": "low", "approval_required": False}
        ]
    }
    
    assert requires_approval(pol, "high") is True
    assert requires_approval(pol, "low") is False
    # default safe for unlisted
    assert requires_approval(pol, "critical") is True
