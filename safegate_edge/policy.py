import json
from typing import Any, List, Optional

def load_policy(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_policy(policy: dict[str, Any]) -> List[str]:
    errors = []
    if not isinstance(policy, dict):
        return ["Policy must be a JSON object"]
    if policy.get("schema_version") != "policy.v1":
        errors.append("Invalid or missing schema_version, expected 'policy.v1'")
    if not isinstance(policy.get("rules"), list):
        errors.append("Field 'rules' must be a list")
    return errors

def requires_approval(policy: dict[str, Any], risk_level: str, action_type: Optional[str] = None) -> bool:
    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        return True # Default safe

    for rule in rules:
        if isinstance(rule, dict) and rule.get("risk_level") == risk_level:
            return rule.get("approval_required", True)
            
    # If no rule matches, default to requiring approval for safety
    return True
