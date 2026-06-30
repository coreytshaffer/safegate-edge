import hashlib
import json
from typing import Any

def canonicalize_action(action_request: dict[str, Any]) -> str:
    """Produce a deterministic canonical JSON string for an action.
    
    Canonical form: sorted keys recursively, compact separators, UTF-8.
    """
    return json.dumps(action_request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def canonical_action_hash(action_request: dict[str, Any]) -> str:
    """Compute the SHA-256 hash of the canonical action representation.
    
    Returns:
        A string in the format "sha256:<hex_digest>"
    """
    canonical = canonicalize_action(action_request)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
