import argparse
import json
import sys
from typing import Optional

from .canonical import canonical_action_hash
from .verifier import verify_approval

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
        
        # Output the result as JSON
        print(json.dumps(result, indent=2))
        
        if result["decision"] == "blocked":
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Error during verification: {e}", file=sys.stderr)
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

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
