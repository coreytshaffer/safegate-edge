import json
import os
import hashlib
from datetime import datetime, timezone

def canonicalize(action):
    return json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def hash_action(action):
    digest = hashlib.sha256(canonicalize(action).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    # Base action
    original_action = {
        "action_id": "act-123456",
        "action_type": "delete_customer_exports",
        "requester": "agent-alpha",
        "command": "rm ./customer_exports/*.csv",
        "target": "./customer_exports/*.csv",
        "working_directory": "/app/data",
        "risk_level": "high",
        "created_at": "2026-07-01T12:00:00Z",
        "expires_at": "2026-07-01T13:00:00Z",
        "metadata": {"ticket": "ENG-402"}
    }
    
    # Mutated action
    mutated_action = original_action.copy()
    mutated_action["command"] = "rm -rf ./customer_exports/"
    mutated_action["target"] = "./customer_exports/"
    
    # Malformed action
    malformed_action = original_action.copy()
    del malformed_action["action_type"]

    original_hash = hash_action(original_action)
    mutated_hash = hash_action(mutated_action)

    # Valid approval (bound to original action)
    valid_approval = {
        "approval_id": "apr-abcdef",
        "action_id": "act-123456",
        "action_hash": original_hash,
        "approver_id": "human-admin-01",
        "approved_at": "2026-07-01T12:05:00Z",
        "expires_at": "2026-07-01T14:00:00Z", # Far in the future relative to the action
        "approval_status": "approved",
        "approval_method": "yubikey-piv",
        "signature_or_attestation_placeholder": "PLACEHOLDER",
        "metadata": {"reason": "Routine cleanup verified"}
    }
    
    # Expired approval
    expired_approval = valid_approval.copy()
    expired_approval["expires_at"] = "2026-07-01T12:10:00Z" # Will be expired if 'now' is after 12:10
    
    # Hash mismatch approval (bound to mutated action, but verified against original)
    mismatch_approval = valid_approval.copy()
    mismatch_approval["action_hash"] = mutated_hash
    
    # Unknown approver
    unknown_approver = valid_approval.copy()
    unknown_approver["approver_id"] = ""
    
    # Malformed approval
    malformed_approval = valid_approval.copy()
    del malformed_approval["approver_id"]

    # Save action requests
    save_json("examples/action_requests/delete_customer_exports_original.json", original_action)
    save_json("examples/action_requests/delete_customer_exports_mutated.json", mutated_action)
    save_json("examples/action_requests/malformed_action_request.json", malformed_action)
    
    # Create valid_action_request.json alias just to satisfy tests/list
    save_json("examples/action_requests/valid_action_request.json", original_action)

    # Save approval packets
    save_json("examples/approval_packets/valid_approval.json", valid_approval)
    save_json("examples/approval_packets/expired_approval_packet.json", expired_approval)
    save_json("examples/approval_packets/hash_mismatch_approval_packet.json", mismatch_approval)
    # SGE-003 Fixtures
    approvers = {
        "schema_version": "approvers.v1",
        "approvers": [
            {
                "approver_id": "corey",
                "display_name": "Corey",
                "status": "active",
                "approval_methods": ["placeholder_security_key"],
                "public_key_fingerprint": "placeholder-fingerprint-corey",
                "created_at": "2026-06-29T00:00:00Z",
                "rotated_at": None,
                "metadata": {}
            }
        ]
    }
    save_json("examples/config/approvers.json", approvers)

    policy = {
        "schema_version": "policy.v1",
        "policy_id": "default",
        "rules": [
            {
                "risk_level": "high",
                "approval_required": True
            },
            {
                "risk_level": "critical",
                "approval_required": True
            }
        ]
    }
    save_json("examples/config/default_policy.json", policy)

if __name__ == "__main__":
    main()
