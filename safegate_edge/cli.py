import argparse
import json
import sys
from typing import Optional

from .canonical import canonical_action_hash
from .verifier import verify_approval
from .observe import EventLogChain
from .decision import create_execution_decision
from .evidence import export_evidence_bundle

def load_json(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def cmd_hash(args: argparse.Namespace) -> None:
    try:
        action = load_json(args.action)
        action_hash = canonical_action_hash(action)
        print(action_hash)
    except Exception as e:
        print(f"Error computing hash: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_verify(args: argparse.Namespace) -> None:
    try:
        action = load_json(args.action)
        approval = load_json(args.approval) if args.approval else None
        
        result = verify_approval(action, approval)
        
        print(json.dumps(result, indent=2))
        
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
        
        chain = EventLogChain()
        
        # 1. Original action requested
        chain.append("ACTION_REQUESTED", {"action": original_action}, original_action["action_id"])
        
        # 2. Approval granted
        chain.append("APPROVAL_GRANTED", {"approval": valid_approval}, original_action["action_id"], valid_approval["approval_id"])
        
        # 3. Mutated action attempted/verified
        vr = verify_approval(mutated_action, valid_approval)
        
        # 4. Hash mismatch detected
        chain.append("ACTION_HASH_MISMATCH", vr["details"], mutated_action["action_id"], valid_approval["approval_id"], vr["verification_id"])
        
        # 5. Execution decision
        ed = create_execution_decision(vr, execution_mode="simulated")
        chain.append("ACTION_BLOCKED", {"decision_id": ed["decision_id"], "reason": ed["reason"]}, mutated_action["action_id"], valid_approval["approval_id"], vr["verification_id"], ed["decision_id"])
        
        # 6. Export evidence
        chain.append("EVIDENCE_EXPORTED", {"output_dir": args.output_dir}, mutated_action["action_id"], valid_approval["approval_id"], vr["verification_id"], ed["decision_id"])
        
        manifest = export_evidence_bundle(
            action_request=mutated_action,
            approval_packet=valid_approval,
            verification_result=vr,
            execution_decision=ed,
            observe_events_jsonl=chain.to_jsonl(),
            output_dir=args.output_dir
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

    # `verify` command
    verify_parser = subparsers.add_parser("verify", help="Verify an action against an approval packet")
    verify_parser.add_argument("--action", required=True, help="Path to the action request JSON file")
    verify_parser.add_argument("--approval", help="Path to the approval packet JSON file")
    verify_parser.set_defaults(func=cmd_verify)
    
    # `evidence` command
    evidence_parser = subparsers.add_parser("evidence", help="Evidence bundle commands")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    
    export_smoke_parser = evidence_subparsers.add_parser("export-smoke", help="Export a smoke demo evidence bundle")
    export_smoke_parser.add_argument("--output-dir", required=True, help="Path to export the evidence bundle")
    export_smoke_parser.set_defaults(func=cmd_evidence_export_smoke)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
