"""
Test configuration and fixtures
"""

import pytest
from engine.state import SystemState


@pytest.fixture
def simple_state():
    """Create a simple system state for testing."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_resource("R2", 5)
    state.add_process("P1", max_claims={"R1": 5, "R2": 3}, priority=1)
    state.add_process("P2", max_claims={"R1": 4, "R2": 2}, priority=2)
    return state


@pytest.fixture
def deadlock_state():
    """Create a state with deadlock."""
    state = SystemState()
    state.add_resource("R1", 1)
    state.add_resource("R2", 1)
    state.add_process("P1", max_claims={"R1": 1, "R2": 1}, priority=1)
    state.add_process("P2", max_claims={"R1": 1, "R2": 1}, priority=2)
    
    # Create circular wait
    state.allocate("P1", "R1", 1)
    state.allocate("P2", "R2", 1)
    state.request("P1", "R2", 1)
    state.request("P2", "R1", 1)
    
    return state
