import json
import os
import shutil
from typing import Any

from .review import create_review_packet
from .approve import create_approval_packet
from .approvers import get_active_approvers, validate_approver_registry
from .verifier import verify_approval
from .observe import EventLogChain
from .decision import create_execution_decision
from .evidence import export_evidence_bundle

def _load_json(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(filepath: str, data: Any) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def _handle_remove_readonly(func, path, exc_info):
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clean_demo_output_dir(output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    known_files = [
        "review_packet.json",
        "generated_approval.json",
        "generated_denied_approval.json",
        "verify_original_allowed.json",
        "verify_mutated_blocked.json",
        "verify_denied_blocked.json",
        "demo_summary.json",
        "README_DEMO.md",
    ]

    for name in known_files:
        path = os.path.join(output_dir, name)
        if os.path.exists(path):
            os.remove(path)

    evidence_dir = os.path.join(output_dir, "evidence_bundle")
    if os.path.exists(evidence_dir):
        shutil.rmtree(evidence_dir, onerror=_handle_remove_readonly)

def run_demo(
    output_dir: str,
    original_action_path: str = "examples/action_requests/delete_customer_exports_original.json",
    mutated_action_path: str = "examples/action_requests/delete_customer_exports_mutated.json",
    policy_path: str = "examples/config/default_policy.json",
    approvers_path: str = "examples/config/approvers.json"
) -> None:
    original_action = _load_json(original_action_path)
    mutated_action = _load_json(mutated_action_path)
    policy = _load_json(policy_path)
    approvers_registry = _load_json(approvers_path)
    registry_errors = validate_approver_registry(approvers_registry)
    if registry_errors:
        raise ValueError(f"Invalid approver registry: {', '.join(registry_errors)}")

    approver_id = None
    for approver in get_active_approvers(approvers_registry):
        methods = approver.get("approval_methods")
        if isinstance(methods, list) and "simulated" in methods:
            candidate_id = approver.get("approver_id")
            if isinstance(candidate_id, str) and candidate_id.strip():
                approver_id = candidate_id
                break
    if approver_id is None:
        raise ValueError("No active approver permits simulated approval")

    review_packet = create_review_packet(original_action, policy)
    # Replay the example at the action's recorded time rather than the wall clock.
    demo_now = review_packet["created_at"]

    approved_packet = create_approval_packet(
        review_packet=review_packet,
        approver_id=approver_id,
        approvers_registry=approvers_registry,
        approval_status="approved",
        approval_method="simulated",
        now_iso=demo_now,
    )

    denied_packet = create_approval_packet(
        review_packet=review_packet,
        approver_id=approver_id,
        approvers_registry=approvers_registry,
        approval_status="denied",
        approval_method="simulated",
        now_iso=demo_now,
    )

    verification_options = dict(approvers_registry=approvers_registry, simulation=True, now_iso=demo_now)
    verify_allowed = verify_approval(original_action, policy, approved_packet, **verification_options)
    verify_mutated = verify_approval(mutated_action, policy, approved_packet, **verification_options)
    verify_denied = verify_approval(original_action, policy, denied_packet, **verification_options)

    expected_outcomes = (
        ("original action", verify_allowed, "simulated_allowed", "valid_simulated_approval"),
        ("changed action", verify_mutated, "blocked", "action_hash_mismatch"),
        ("denied approval", verify_denied, "blocked", "approval_not_granted"),
    )
    for scenario, result, decision, reason in expected_outcomes:
        if (result["decision"], result["reason"]) != (decision, reason):
            raise ValueError(
                f"Demo {scenario} expected {decision} ({reason}), "
                f"got {result['decision']} ({result['reason']})"
            )

    # Preserve the previous run until the new results support the scripted trace.
    clean_demo_output_dir(output_dir)
    _write_json(os.path.join(output_dir, "review_packet.json"), review_packet)
    _write_json(os.path.join(output_dir, "generated_approval.json"), approved_packet)
    _write_json(os.path.join(output_dir, "generated_denied_approval.json"), denied_packet)
    _write_json(os.path.join(output_dir, "verify_original_allowed.json"), verify_allowed)
    _write_json(os.path.join(output_dir, "verify_mutated_blocked.json"), verify_mutated)
    _write_json(os.path.join(output_dir, "verify_denied_blocked.json"), verify_denied)

    # Export evidence for the changed action.
    evidence_dir = os.path.join(output_dir, "evidence_bundle")
        
    chain = EventLogChain()
    chain.append("ACTION_REQUESTED", {"action": original_action}, original_action["action_id"])
    chain.append("POLICY_SNAPSHOT_RECORDED", {"policy_id": policy.get("policy_id")}, original_action["action_id"])
    chain.append("REVIEW_REQUESTED", {"review": review_packet}, original_action["action_id"])
    chain.append("APPROVAL_GRANTED", {"approval": approved_packet}, original_action["action_id"], approved_packet["approval_id"])
    
    # Now simulate the mutated action being intercepted
    chain.append("ACTION_HASH_MISMATCH", verify_mutated.get("details", {}), mutated_action["action_id"], approved_packet["approval_id"], verify_mutated["verification_id"])
    
    ed = create_execution_decision(verify_mutated, execution_mode="simulated")
    chain.append("ACTION_BLOCKED", {"decision_id": ed["decision_id"], "reason": ed["reason"]}, mutated_action["action_id"], approved_packet["approval_id"], verify_mutated["verification_id"], ed["decision_id"])
    
    chain.append("EVIDENCE_EXPORTED", {"output_dir": evidence_dir}, mutated_action["action_id"], approved_packet["approval_id"], verify_mutated["verification_id"], ed["decision_id"])

    export_evidence_bundle(
        action_request=mutated_action,
        approval_packet=approved_packet,
        verification_result=verify_mutated,
        execution_decision=ed,
        observe_events_jsonl=chain.to_jsonl(),
        output_dir=evidence_dir,
        policy_snapshot=policy
    )

    # Write demo_summary.json
    summary = {
        "schema_version": "safegate_demo_summary.v1",
        "demo_id": "safegate-demo-delete-customer-exports",
        "generated_at": demo_now,
        "scenario": "delete_customer_exports",
        "simulation_only": True,
        "assertions": {
            "review_packet_created": os.path.exists(os.path.join(output_dir, "review_packet.json")),
            "approval_packet_created": os.path.exists(os.path.join(output_dir, "generated_approval.json")),
            "denied_approval_packet_created": os.path.exists(os.path.join(output_dir, "generated_denied_approval.json")),
            "original_allowed": verify_allowed.get("decision") == "simulated_allowed",
            "mutated_blocked": verify_mutated.get("decision") == "blocked",
            "denied_blocked": verify_denied.get("decision") == "blocked",
            "evidence_bundle_created": os.path.exists(os.path.join(evidence_dir, "evidence_manifest.json"))
        },
        "results": {
            "original_decision": verify_allowed.get("decision"),
            "original_reason": verify_allowed.get("reason"),
            "mutated_decision": verify_mutated.get("decision"),
            "mutated_reason": verify_mutated.get("reason"),
            "denied_decision": verify_denied.get("decision"),
            "denied_reason": verify_denied.get("reason")
        },
        "hardware_attestation": {
            "implemented": False,
            "note": "SafeGate is hardware-ready, not hardware-verified yet."
        }
    }
    _write_json(os.path.join(output_dir, "demo_summary.json"), summary)

    # Write README_DEMO.md
    readme_content = """# SafeGate Edge Demo Run

## What this demo proves
This demo shows how SafeGate binds a simulated approval to one exact canonical action hash. The original action passes only in simulation. The changed action and denied approval are blocked. Demo results grant no execution authority.

## Scenario
An agent requests to run `rm ./customer_exports/*.csv`. This is a high-risk action according to the loaded policy and requires human approval.
The demo simulates generating a review packet, a human approving it, and subsequent verifications against different execution attempts.

## Generated Artifacts
- **review_packet.json**: The exact payload presented to the human approver.
- **generated_approval.json**: A simulated approval containing the canonical action hash.
- **generated_denied_approval.json**: An example of a rejected request.
- **verify_original_allowed.json**: The result for the exact action in simulation mode.
- **verify_mutated_blocked.json**: The gateway blocking an action that was mutated (e.g. `rm -rf /`) after approval.
- **verify_denied_blocked.json**: The gateway blocking the original action when the approval was explicitly denied.
- **evidence_bundle/**: The full cryptographically-chained evidence bundle exported from the blocked mutation attempt.
- **demo_summary.json**: Machine-readable summary of this demo run.

## Results
- Original Decision: {original_decision} ({original_reason})
- Mutated Decision: {mutated_decision} ({mutated_reason})
- Denied Decision: {denied_decision} ({denied_reason})

## Key Safety Property
The evidence bundle records why the verifier rejected the changed action in this simulation.

## Hardware Attestation Boundary
Policies can require hardware attestation. For this demo, hardware verification is explicitly marked as not implemented to avoid false security claims. SafeGate is hardware-ready, not hardware-verified yet.

## How to Re-run
Run the following command to regenerate this demo packet:
`python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo`
""".format(
        original_decision=verify_allowed.get("decision"),
        original_reason=verify_allowed.get("reason"),
        mutated_decision=verify_mutated.get("decision"),
        mutated_reason=verify_mutated.get("reason"),
        denied_decision=verify_denied.get("decision"),
        denied_reason=verify_denied.get("reason")
    )
    
    with open(os.path.join(output_dir, "README_DEMO.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
