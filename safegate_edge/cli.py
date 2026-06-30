import argparse
import json
import sys
import os
from typing import Optional, Any

from .canonical import canonical_action_hash
from .verifier import verify_approval
from .observe import EventLogChain
from .decision import create_execution_decision
from .evidence import export_evidence_bundle
from .doctor import run_doctor_checks, print_doctor_results
from .preflight import run_preflight_checks, print_preflight_results

from .review import create_review_packet
from .approve import create_approval_packet

def cmd_doctor(args: argparse.Namespace) -> None:
    try:
        results = run_doctor_checks()
        exit_code = print_doctor_results(results)
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error running doctor checks: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_preflight(args: argparse.Namespace) -> None:
    try:
        results = run_preflight_checks(args.action)
        exit_code = print_preflight_results(results)
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error running preflight checks: {e}", file=sys.stderr)
        sys.exit(1)

def load_json(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(filepath: str, data: Any) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def cmd_hash(args: argparse.Namespace) -> None:
    try:
        action = load_json(args.action)
        action_hash = canonical_action_hash(action)
        print(action_hash)
    except Exception as e:
        print(f"Error computing hash: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_review_create(args: argparse.Namespace) -> None:
    try:
        action = load_json(args.action)
        policy = load_json(args.policy)
        packet = create_review_packet(action, policy)
        
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2, ensure_ascii=False)
            f.write("\n")
            
        print(f"Review packet created at {args.output}")
        sys.exit(0)
    except Exception as e:
        print(f"Error creating review packet: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_approve_create(args: argparse.Namespace) -> None:
    try:
        review_packet = load_json(args.review)
        approvers_registry = load_json(args.approvers)
        
        packet = create_approval_packet(
            review_packet=review_packet,
            approver_id=args.approver,
            approvers_registry=approvers_registry,
            approval_status=args.status
        )
        
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2, ensure_ascii=False)
            f.write("\n")
            
        print(f"Approval packet created at {args.output}")
        sys.exit(0)
    except Exception as e:
        print(f"Error creating approval packet: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_verify(args: argparse.Namespace) -> None:
    try:
        action = load_json(args.action)
        approval = load_json(args.approval) if args.approval else None
        
        policy_path = args.policy
        policy = None
        if os.path.exists(policy_path):
            policy = load_json(policy_path)
            
        result = verify_approval(action, policy, approval)
        
        print(f"decision: {result.get('decision')}")
        print(f"reason: {result.get('reason')}")
        
        if result["decision"] == "blocked":
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Error during verification: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_evidence_export_smoke(args: argparse.Namespace) -> None:
    try:
        original_action = load_json("examples/action_requests/delete_customer_exports_original.json")
        mutated_action = load_json("examples/action_requests/delete_customer_exports_mutated.json")
        valid_approval = load_json("examples/approval_packets/valid_approval.json")
        policy = load_json("examples/config/default_policy.json")
        
        chain = EventLogChain()
        
        # 1. Original action requested
        chain.append("ACTION_REQUESTED", {"action": original_action}, original_action["action_id"])
        
        # 2. Policy snapshot
        chain.append("POLICY_SNAPSHOT_RECORDED", {"policy_id": policy.get("policy_id")}, original_action["action_id"])
        
        # 3. Approval granted
        chain.append("APPROVAL_GRANTED", {"approval": valid_approval}, original_action["action_id"], valid_approval["approval_id"])
        
        # 4. Mutated action attempted/verified
        vr = verify_approval(mutated_action, policy, valid_approval)
        
        # 5. Hash mismatch detected
        chain.append("ACTION_HASH_MISMATCH", vr.get("details", {}), mutated_action["action_id"], valid_approval["approval_id"], vr["verification_id"])
        
        # 6. Execution decision
        ed = create_execution_decision(vr, execution_mode="simulated")
        chain.append("ACTION_BLOCKED", {"decision_id": ed["decision_id"], "reason": ed["reason"]}, mutated_action["action_id"], valid_approval["approval_id"], vr["verification_id"], ed["decision_id"])
        
        # 7. Export evidence
        chain.append("EVIDENCE_EXPORTED", {"output_dir": args.output_dir}, mutated_action["action_id"], valid_approval["approval_id"], vr["verification_id"], ed["decision_id"])
        
        manifest = export_evidence_bundle(
            action_request=mutated_action,
            approval_packet=valid_approval,
            verification_result=vr,
            execution_decision=ed,
            observe_events_jsonl=chain.to_jsonl(),
            output_dir=args.output_dir,
            policy_snapshot=policy
        )
        print(f"Evidence bundle exported to {args.output_dir}")
        print(f"Bundle Hash: {manifest['bundle_hash']}")
    except Exception as e:
        print(f"Error during evidence export smoke: {e}", file=sys.stderr)
        sys.exit(1)

def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="SafeGate Edge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `hash` command
    hash_parser = subparsers.add_parser("hash", help="Compute the canonical hash of an action request")
    hash_parser.add_argument("--action", required=True, help="Path to the action request JSON file")
    hash_parser.set_defaults(func=cmd_hash)

    # `review` command
    review_parser = subparsers.add_parser("review", help="Review packet commands")
    review_subparsers = review_parser.add_subparsers(dest="review_command", required=True)
    
    review_create_parser = review_subparsers.add_parser("create", help="Create a human review packet")
    review_create_parser.add_argument("--action", required=True, help="Path to the action request JSON file")
    review_create_parser.add_argument("--policy", default="examples/config/default_policy.json", help="Path to the policy JSON file")
    review_create_parser.add_argument("--output", required=True, help="Path to write the review packet JSON")
    review_create_parser.set_defaults(func=cmd_review_create)

    # `approve` command
    approve_parser = subparsers.add_parser("approve", help="Approval packet commands")
    approve_subparsers = approve_parser.add_subparsers(dest="approve_command", required=True)
    
    approve_create_parser = approve_subparsers.add_parser("create", help="Create an approval packet from a review packet")
    approve_create_parser.add_argument("--review", required=True, help="Path to the review packet JSON file")
    approve_create_parser.add_argument("--approvers", default="examples/config/approvers.json", help="Path to the approvers registry JSON file")
    approve_create_parser.add_argument("--approver", required=True, help="Approver ID generating the approval")
    approve_create_parser.add_argument("--status", default="approved", choices=["approved", "denied"], help="Approval status")
    approve_create_parser.add_argument("--output", required=True, help="Path to write the generated approval packet JSON")
    approve_create_parser.set_defaults(func=cmd_approve_create)

    # `verify` command
    verify_parser = subparsers.add_parser("verify", help="Verify an action against an approval packet")
    verify_parser.add_argument("--action", required=True, help="Path to the action request JSON file")
    verify_parser.add_argument("--policy", default="examples/config/default_policy.json", help="Path to the policy JSON file")
    verify_parser.add_argument("--approval", help="Path to the approval packet JSON file")
    verify_parser.set_defaults(func=cmd_verify)
    
    # `evidence` command
    evidence_parser = subparsers.add_parser("evidence", help="Evidence bundle commands")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    
    export_smoke_parser = evidence_subparsers.add_parser("export-smoke", help="Export a smoke demo evidence bundle")
    export_smoke_parser.add_argument("--output-dir", required=True, help="Path to export the evidence bundle")
    export_smoke_parser.set_defaults(func=cmd_evidence_export_smoke)

    # `doctor` command
    doctor_parser = subparsers.add_parser("doctor", help="Run diagnostic checks on SafeGate environment")
    doctor_parser.set_defaults(func=cmd_doctor)

    # `preflight` command
    preflight_parser = subparsers.add_parser("preflight", help="Run preflight checks on an action request")
    preflight_parser.add_argument("--action", required=True, help="Path to the action request JSON file")
    preflight_parser.set_defaults(func=cmd_preflight)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
