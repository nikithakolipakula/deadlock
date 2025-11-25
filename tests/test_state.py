"""
Tests for State Management
"""

import pytest
from engine.state import SystemState, Resource, Process


def test_resource_creation():
    """Test resource creation and validation."""
    res = Resource(id="R1", total_units=5, available_units=5)
    assert res.id == "R1"
    assert res.total_units == 5
    assert res.available_units == 5


def test_resource_invalid():
    """Test invalid resource creation."""
    with pytest.raises(ValueError):
        Resource(id="R1", total_units=-1, available_units=0)
    
    with pytest.raises(ValueError):
        Resource(id="R1", total_units=5, available_units=10)


def test_process_need_calculation():
    """Test process need calculation."""
    proc = Process(
        id="P1",
        max_claims={"R1": 5, "R2": 3},
        allocated={"R1": 2, "R2": 1}
    )
    
    assert proc.need("R1") == 3
    assert proc.need("R2") == 2
    assert proc.need("R3") == 0  # Not in max_claims


def test_system_state_add_resource():
    """Test adding resources to system."""
    state = SystemState()
    state.add_resource("R1", 10)
    
    assert "R1" in state.resources
    assert state.resources["R1"].total_units == 10
    assert state.resources["R1"].available_units == 10


def test_system_state_add_process():
    """Test adding processes to system."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    
    assert "P1" in state.processes
    assert state.processes["P1"].max_claims["R1"] == 5


def test_allocate_resources():
    """Test resource allocation."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    
    success = state.allocate("P1", "R1", 3)
    assert success
    assert state.processes["P1"].allocated["R1"] == 3
    assert state.resources["R1"].available_units == 7


def test_allocate_exceeds_available():
    """Test allocation exceeding available units."""
    state = SystemState()
    state.add_resource("R1", 5)
    state.add_process("P1", max_claims={"R1": 5})
    
    # Try to allocate more than available
    success = state.allocate("P1", "R1", 10)
    assert not success


def test_allocate_exceeds_max_claim():
    """Test allocation exceeding max claim."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    
    success = state.allocate("P1", "R1", 6)
    assert not success


def test_release_resources():
    """Test resource release."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 3)
    
    success = state.release("P1", "R1", 2)
    assert success
    assert state.processes["P1"].allocated["R1"] == 1
    assert state.resources["R1"].available_units == 9


def test_release_more_than_allocated():
    """Test releasing more than allocated."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 2)
    
    success = state.release("P1", "R1", 5)
    assert not success


def test_request_resources():
    """Test resource request."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    
    success = state.request("P1", "R1", 3)
    assert success
    assert state.processes["P1"].requested["R1"] == 3


def test_request_exceeds_need():
    """Test request exceeding need."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 3)
    
    success = state.request("P1", "R1", 5)  # Need is 2, requesting 5
    assert not success


def test_remove_process():
    """Test process removal."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 3)
    
    state.remove_process("P1")
    assert "P1" not in state.processes
    assert state.resources["R1"].available_units == 10  # Resources released


def test_state_snapshot():
    """Test state snapshot."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 3)
    
    snapshot = state.snapshot()
    assert "resources" in snapshot
    assert "processes" in snapshot
    assert snapshot["resources"]["R1"]["available"] == 7
    assert snapshot["processes"]["P1"]["allocated"]["R1"] == 3


def test_state_clone():
    """Test state cloning."""
    state = SystemState()
    state.add_resource("R1", 10)
    state.add_process("P1", max_claims={"R1": 5})
    state.allocate("P1", "R1", 3)
    
    cloned = state.clone()
    assert cloned is not state
    assert cloned.resources["R1"].available_units == 7
    
    # Modify clone
    cloned.allocate("P1", "R1", 2)
    
    # Original should be unchanged
    assert state.resources["R1"].available_units == 7
    assert cloned.resources["R1"].available_units == 5
