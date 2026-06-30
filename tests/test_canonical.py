import json
from safegate_edge.canonical import canonicalize_action, canonical_action_hash

def test_canonicalize_sorts_keys():
    action1 = {"b": 1, "a": 2}
    action2 = {"a": 2, "b": 1}
    assert canonicalize_action(action1) == canonicalize_action(action2)
    assert canonical_action_hash(action1) == canonical_action_hash(action2)

def test_canonical_hash_changes_on_mutation():
    action1 = {"command": "rm file", "target": "file"}
    action2 = {"command": "rm -rf file", "target": "file"}
    assert canonical_action_hash(action1) != canonical_action_hash(action2)

def test_canonical_hash_format():
    action = {"a": 1}
    hash_val = canonical_action_hash(action)
    assert hash_val.startswith("sha256:")
    assert len(hash_val) == 7 + 64 # sha256: + 64 hex chars
