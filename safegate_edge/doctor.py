import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CheckResult:
    check_id: str
    label: str
    status: str # "PASS", "WARN", "FAIL"
    message: str
    details: Optional[dict] = None

def run_doctor_checks() -> List[CheckResult]:
    results = []

    # 1. Package imports
    try:
        from . import schema, canonical, verifier, observe, decision, evidence, approvers, policy
        results.append(CheckResult("import_core", "SafeGate core modules importable", "PASS", "All core modules loaded successfully."))
    except Exception as e:
        results.append(CheckResult("import_core", "SafeGate core modules importable", "FAIL", f"Import error: {e}"))
        return results # Stop if core fails

    # 2. Config/policy availability
    policy_path = "examples/config/default_policy.json"
    if os.path.exists(policy_path):
        try:
            pol = policy.load_policy(policy_path)
            errs = policy.validate_policy(pol)
            if not errs:
                results.append(CheckResult("policy_exists", "Default policy available", "PASS", f"Policy '{policy_path}' is valid."))
            else:
                results.append(CheckResult("policy_exists", "Default policy available", "FAIL", f"Policy invalid: {errs}"))
        except Exception as e:
            results.append(CheckResult("policy_exists", "Default policy available", "FAIL", f"Failed to parse policy: {e}"))
    else:
        results.append(CheckResult("policy_exists", "Default policy available", "WARN", "Default policy file not found."))

    # 3. Examples directory exists
    if os.path.exists("examples") and os.path.isdir("examples"):
        results.append(CheckResult("examples_dir", "Examples directory exists", "PASS", "Found 'examples' directory."))
    else:
        results.append(CheckResult("examples_dir", "Examples directory exists", "WARN", "Missing 'examples' directory."))

    # 4. Evidence output path writable
    evidence_path = "examples/evidence_bundles/smoke"
    try:
        os.makedirs(evidence_path, exist_ok=True)
        test_file = os.path.join(evidence_path, ".doctor_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        results.append(CheckResult("evidence_writable", "Evidence output path writable", "PASS", f"Can write to {evidence_path}."))
    except Exception as e:
        results.append(CheckResult("evidence_writable", "Evidence output path writable", "FAIL", f"Cannot write to {evidence_path}: {e}"))

    # 5. Approver registry valid
    registry_path = "examples/config/approvers.json"
    reg = None
    if os.path.exists(registry_path):
        try:
            reg = approvers.load_approver_registry(registry_path)
            errs = approvers.validate_approver_registry(reg)
            if not errs:
                results.append(CheckResult("approver_registry", "Approver registry parses", "PASS", "Registry loaded and valid."))
            else:
                results.append(CheckResult("approver_registry", "Approver registry parses", "FAIL", f"Registry invalid: {errs}"))
        except Exception as e:
            results.append(CheckResult("approver_registry", "Approver registry parses", "FAIL", f"Failed to parse registry: {e}"))
    else:
        results.append(CheckResult("approver_registry", "Approver registry exists", "FAIL", "Approver registry not found."))

    # 6. Approver registry checks
    if reg:
        active = approvers.get_active_approvers(reg)
        if active:
            results.append(CheckResult("active_approver", "At least one active approver exists", "PASS", f"Found {len(active)} active approvers."))
        else:
            results.append(CheckResult("active_approver", "At least one active approver exists", "FAIL", "No active approvers found."))
            
        if not approvers.has_duplicate_active_approvers(reg):
            results.append(CheckResult("duplicate_approver", "No duplicate active approver_id values", "PASS", "No duplicates."))
        else:
            results.append(CheckResult("duplicate_approver", "No duplicate active approver_id values", "FAIL", "Duplicate approver_ids found."))
            
        methods_ok = all(isinstance(a.get("approval_methods"), list) and len(a["approval_methods"]) > 0 for a in active)
        if methods_ok:
            results.append(CheckResult("approval_methods", "Active approvers have approval_methods", "PASS", "All active approvers have configured methods."))
        else:
            results.append(CheckResult("approval_methods", "Active approvers have approval_methods", "FAIL", "Some active approvers lack approval_methods."))
            
        placeholders = [a for a in active if "placeholder" in str(a.get("public_key_fingerprint", ""))]
        if placeholders:
            results.append(CheckResult("fingerprint_placeholder", "Placeholder approver fingerprint detected", "WARN", "One or more approvers use a placeholder fingerprint."))
        else:
            results.append(CheckResult("fingerprint_placeholder", "Placeholder approver fingerprint detected", "PASS", "No placeholder fingerprints detected."))

        # 6a. Hardware attestation configuration
        all_methods = set()
        for a in active:
            methods = a.get("approval_methods", [])
            all_methods.update(methods)
            
        has_real_hardware = "hardware_security_key" in all_methods
        
        if not has_real_hardware:
            results.append(CheckResult(
                "hardware_attestation_configured", 
                "Hardware attestation not configured", 
                "WARN", 
                "Only simulated or placeholder approval methods are available in the approver registry."
            ))
        else:
            results.append(CheckResult(
                "hardware_attestation_configured",
                "Hardware approval method reserved",
                "WARN",
                "hardware_security_key is configured, but hardware attestation verification is not implemented yet."
            ))

    # 7. Fixture hashes can be recomputed
    action_fixture = "examples/action_requests/delete_customer_exports_original.json"
    if os.path.exists(action_fixture):
        import json
        with open(action_fixture, "r", encoding="utf-8") as f:
            action_data = json.load(f)
        try:
            h = canonical.canonical_action_hash(action_data)
            results.append(CheckResult("fixture_hash", "Fixture hashes can be recomputed", "PASS", f"Computed hash: {h}"))
        except Exception as e:
            results.append(CheckResult("fixture_hash", "Fixture hashes can be recomputed", "FAIL", f"Failed to compute hash: {e}"))
    else:
        results.append(CheckResult("fixture_hash", "Fixture hashes can be recomputed", "WARN", "Action fixture not found to test hashing."))

    return results

def print_doctor_results(results: List[CheckResult], title="Doctor check complete.") -> int:
    exit_code = 0
    for r in results:
        status_str = f"[{r.status}]"
        print(f"{status_str: <7} {r.label}")
        if r.status == "FAIL":
            exit_code = 1
            print(f"        -> {r.message}")
        elif r.status == "WARN":
            print(f"        -> {r.message}")
            
    print(f"\n{title}")
    return exit_code
