"""
Tests for Banker's Algorithm
"""

import pytest
from engine.state import SystemState
from engine.banker import is_safe_state, find_safe_sequence, get_banker_decision


def test_safe_state_simple():
    """Test simple safe state."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 7})
    state.add_process("P2", max_claims={"R1": 5})
    
    state.allocate("P1", "R1", 3)
    state.allocate("P2", "R1", 2)
    
    # Available: 5, P1 needs 4, P2 needs 3
    # P2 can finish (need 3 <= available 5)
    # Then P1 can finish with released resources
    is_safe, sequence = find_safe_sequence(state)
    assert is_safe
    assert sequence is not None
    assert len(sequence) == 2


def test_unsafe_state():
    """Test unsafe state detection."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 10})
    state.add_process("P2", max_claims={"R1": 10})
    
    state.allocate("P1", "R1", 5)
    state.allocate("P2", "R1", 5)
    
    # Available: 0, both need 5 more - deadlock
    is_safe, sequence = find_safe_sequence(state)
    assert not is_safe
    assert sequence is None


def test_safe_request():
    """Test safe resource request."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.add_process("P2", max_claims={"R1": 4})
    
    state.allocate("P1", "R1", 2)
    state.allocate("P2", "R1", 2)
    
    # P1 requests 1 more (total would be 3, need would be 2)
    # Available would be 5, still safe
    is_safe, sequence = is_safe_state(state, "P1", {"R1": 1})
    assert is_safe
    assert sequence is not None


def test_unsafe_request():
    """Test unsafe resource request."""
    state = SystemState()
    state.add_resource("R1", 5)
    state.add_process("P1", max_claims={"R1": 4})
    state.add_process("P2", max_claims={"R1": 4})
    
    state.allocate("P1", "R1", 2)
    state.allocate("P2", "R1", 2)
    
    # P1 requests 1 more, would leave 0 available
    # P2 needs 2 more to finish - unsafe
    is_safe, sequence = is_safe_state(state, "P1", {"R1": 1})
    assert not is_safe


def test_request_exceeds_need():
    """Test request exceeding process need."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 3)
    
    # P1 has 3, max is 5, need is 2
    # Requesting 3 exceeds need
    is_safe, sequence = is_safe_state(state, "P1", {"R1": 3})
    assert not is_safe


def test_request_exceeds_available():
    """Test request exceeding available resources."""
    state = SystemState()
    state.add_resource("R1", 5)
    state.add_process("P1", max_claims={"R1": 5})
    
    # Available: 5, requesting 6
    is_safe, sequence = is_safe_state(state, "P1", {"R1": 6})
    assert not is_safe


def test_banker_decision_details():
    """Test detailed Banker's decision."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 2)
    
    decision = get_banker_decision(state, "P1", {"R1": 2})
    assert decision["safe"] is True
    assert decision["safe_sequence"] is not None
    assert "reason" in decision


def test_multiple_resources():
    """Test Banker's algorithm with multiple resources."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_resource("R2", 5)
    state.add_resource("R3", 7)
    
    state.add_process("P1", max_claims={"R1": 7, "R2": 5, "R3": 3})
    state.add_process("P2", max_claims={"R1": 3, "R2": 2, "R3": 2})
    state.add_process("P3", max_claims={"R1": 9, "R2": 0, "R3": 2})
    
    # Allocate initial resources (skip 0 allocations)
    state.allocate("P1", "R2", 1)
    
    state.allocate("P2", "R1", 2)
    
    state.allocate("P3", "R1", 3)
    state.allocate("P3", "R3", 2)
    
    # This is a known safe state from Banker's algorithm examples
    is_safe, sequence = find_safe_sequence(state)
    assert is_safe
    assert len(sequence) == 3
