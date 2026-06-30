import json
from typing import Any, List, Dict

def load_approver_registry(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_approver_registry(registry: dict[str, Any]) -> List[str]:
    """Validate the approver registry schema.
    Returns a list of errors, or an empty list if valid.
    """
    errors = []
    if not isinstance(registry, dict):
        return ["Registry must be a JSON object"]
    if registry.get("schema_version") != "approvers.v1":
        errors.append("Invalid or missing schema_version, expected 'approvers.v1'")
    if not isinstance(registry.get("approvers"), list):
        errors.append("Field 'approvers' must be a list")
    
    return errors

def get_active_approvers(registry: dict[str, Any]) -> List[dict[str, Any]]:
    approvers = registry.get("approvers", [])
    if not isinstance(approvers, list):
        return []
    return [a for a in approvers if isinstance(a, dict) and a.get("status") == "active"]

def has_duplicate_active_approvers(registry: dict[str, Any]) -> bool:
    active_ids = [a.get("approver_id") for a in get_active_approvers(registry)]
    return len(active_ids) != len(set(active_ids))

def is_known_active_approver(registry: dict[str, Any], approver_id: str) -> bool:
    for a in get_active_approvers(registry):
        if a.get("approver_id") == approver_id:
            return True
    return False
