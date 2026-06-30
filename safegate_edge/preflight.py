import os
import json
from typing import List
from .doctor import CheckResult, print_doctor_results
from . import schema, canonical, approvers, policy

def run_preflight_checks(action_path: str) -> List[CheckResult]:
    results = []

    # 1. Action file exists
    if not os.path.exists(action_path):
        results.append(CheckResult("action_exists", "action file exists", "FAIL", f"File '{action_path}' not found."))
        return results
    results.append(CheckResult("action_exists", "action file exists", "PASS", "Action file found."))

    # 2. Action JSON parses
    try:
        with open(action_path, "r", encoding="utf-8") as f:
            action_data = json.load(f)
        results.append(CheckResult("action_parses", "action JSON parses", "PASS", "Action is valid JSON."))
    except Exception as e:
        results.append(CheckResult("action_parses", "action JSON parses", "FAIL", f"JSON parsing failed: {e}"))
        return results

    # 3. Action schema valid
    errs = schema.validate_action(action_data)
    if errs:
        results.append(CheckResult("action_schema", "action schema valid", "FAIL", f"Schema invalid: {errs}"))
        return results
    results.append(CheckResult("action_schema", "action schema valid", "PASS", "Action schema is valid."))

    # 4. Action type recognized
    action_type = action_data.get("action_type")
    known_types = ["filesystem.delete", "filesystem.read", "filesystem.write", "network.request"]
    if action_type in known_types:
        results.append(CheckResult("action_type", "action_type recognized", "PASS", f"Type '{action_type}' is known."))
    else:
        results.append(CheckResult("action_type", "action_type recognized", "WARN", f"Type '{action_type}' is unknown."))

    # 5. Risk level recognized
    risk_level = action_data.get("risk_level")
    known_risks = ["low", "medium", "high", "critical"]
    if risk_level in known_risks:
        results.append(CheckResult("risk_level", "risk_level recognized", "PASS", f"Risk level '{risk_level}' is valid."))
    else:
        results.append(CheckResult("risk_level", "risk_level recognized", "FAIL", f"Unknown risk level '{risk_level}'."))

    # 6. Approval requirement determined
    pol = None
    policy_path = "examples/config/default_policy.json"
    if os.path.exists(policy_path):
        try:
            pol = policy.load_policy(policy_path)
        except Exception:
            pass
            
    if pol:
        req = policy.requires_approval(pol, risk_level, action_type)
        results.append(CheckResult("approval_req", "approval requirement determined", "PASS", f"Approval required: {req}"))
    else:
        req = True # Default safe
        results.append(CheckResult("approval_req", "approval requirement determined", "WARN", "Policy not found, defaulting to approval required."))

    # 7. Action hash computable
    try:
        h = canonical.canonical_action_hash(action_data)
        results.append(CheckResult("action_hash", "action hash computable", "PASS", f"Hash: {h}"))
    except Exception as e:
        results.append(CheckResult("action_hash", "action hash computable", "FAIL", f"Failed to compute hash: {e}"))

    # 8. Approver registry available
    reg_path = "examples/config/approvers.json"
    reg = None
    if os.path.exists(reg_path):
        try:
            reg = approvers.load_approver_registry(reg_path)
            results.append(CheckResult("registry_avail", "approver registry available", "PASS", "Registry loaded."))
        except Exception as e:
            results.append(CheckResult("registry_avail", "approver registry available", "FAIL", f"Failed to load registry: {e}"))
    else:
        results.append(CheckResult("registry_avail", "approver registry available", "FAIL", "Approver registry not found."))

    # 9. At least one active approver available when approval is required
    if req:
        if reg:
            active = approvers.get_active_approvers(reg)
            if active:
                results.append(CheckResult("active_approver_avail", "active approver available for required approval", "PASS", f"Found {len(active)} active approvers."))
            else:
                results.append(CheckResult("active_approver_avail", "active approver available for required approval", "FAIL", "No active approvers found to approve this action."))
        else:
            results.append(CheckResult("active_approver_avail", "active approver available for required approval", "FAIL", "Registry missing, cannot find approvers."))
    else:
        results.append(CheckResult("active_approver_avail", "active approver available for required approval", "PASS", "Approval not required."))

    # 10. Evidence output path writable
    evidence_path = "examples/evidence_bundles/smoke"
    try:
        os.makedirs(evidence_path, exist_ok=True)
        test_file = os.path.join(evidence_path, ".preflight_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        results.append(CheckResult("evidence_writable", "evidence output path writable", "PASS", f"Can write to {evidence_path}."))
    except Exception as e:
        results.append(CheckResult("evidence_writable", "evidence output path writable", "FAIL", f"Cannot write to {evidence_path}: {e}"))

    return results

def print_preflight_results(results: List[CheckResult]) -> int:
    return print_doctor_results(results, title="Preflight check complete.")
