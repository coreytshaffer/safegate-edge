import pytest
from datetime import datetime, timezone
from safegate_edge.observe import EventLogChain, _hash_event_content

def test_event_hash_chain_validates():
    chain = EventLogChain()
    
    # 1st event
    chain.append("TEST_EVENT_1", {"key": "val1"}, "act-1")
    assert chain.events[0]["previous_event_hash"] is None
    
    # 2nd event
    chain.append("TEST_EVENT_2", {"key": "val2"}, "act-1")
    assert chain.events[1]["previous_event_hash"] == chain.events[0]["event_hash"]
    
    # Chain should validate
    assert chain.validate_chain() is True

def test_event_hash_chain_invalid_link():
    chain = EventLogChain()
    chain.append("TEST_EVENT_1", {}, "act-1")
    chain.append("TEST_EVENT_2", {}, "act-1")
    
    # Break the link
    chain.events[1]["previous_event_hash"] = "invalid"
    assert chain.validate_chain() is False

def test_event_hash_chain_invalid_content():
    chain = EventLogChain()
    chain.append("TEST_EVENT_1", {}, "act-1")
    
    # Mutate content without rehashing
    chain.events[0]["payload"] = {"mutated": True}
    assert chain.validate_chain() is False

def test_deterministic_hashing():
    now = datetime(2026, 7, 1, 12, 10, tzinfo=timezone.utc)
    chain1 = EventLogChain()
    chain1.append("EVENT", {"a": 1, "b": 2}, "act-1", now=now)
    
    chain2 = EventLogChain()
    chain2.append("EVENT", {"b": 2, "a": 1}, "act-1", now=now)
    
    # Force event_id to be the same and recompute hashes
    chain2.events[0]["event_id"] = chain1.events[0]["event_id"]
    chain2.events[0]["event_hash"] = _hash_event_content(chain2.events[0])
    
    assert chain1.events[0]["event_hash"] == chain2.events[0]["event_hash"]
