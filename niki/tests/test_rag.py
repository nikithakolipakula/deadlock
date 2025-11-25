"""
Tests for Resource Allocation Graph
"""

import pytest
from engine.state import SystemState
from engine.rag import (
    build_resource_allocation_graph,
    build_wait_for_graph,
    detect_cycles,
    detect_wait_for_cycles,
    analyze_deadlock
)


def test_rag_construction():
    """Test RAG construction from state."""
    state = SystemState()
    state.add_resource("R1", 2)
    state.add_resource("R2", 1)
    state.add_process("P1", max_claims={"R1": 1, "R2": 1})
    state.add_process("P2", max_claims={"R1": 1, "R2": 1})
    
    state.allocate("P1", "R1", 1)
    state.request("P2", "R1", 1)
    
    rag = build_resource_allocation_graph(state)
    
    assert "P1" in rag.process_nodes
    assert "P2" in rag.process_nodes
    assert "R1" in rag.resource_nodes
    assert "R2" in rag.resource_nodes


def test_rag_no_cycle():
    """Test RAG without cycles."""
    state = SystemState()
    state.add_resource("R1", 2)
    state.add_process("P1", max_claims={"R1": 1})
    state.add_process("P2", max_claims={"R1": 1})
    
    state.allocate("P1", "R1", 1)
    
    rag = build_resource_allocation_graph(state)
    cycles = detect_cycles(rag)
    
    assert len(cycles) == 0


def test_rag_with_cycle():
    """Test RAG with deadlock cycle."""
    state = SystemState()
    state.add_resource("R1", 1)
    state.add_resource("R2", 1)
    state.add_process("P1", max_claims={"R1": 1, "R2": 1})
    state.add_process("P2", max_claims={"R1": 1, "R2": 1})
    
    # Create circular wait
    state.allocate("P1", "R1", 1)
    state.allocate("P2", "R2", 1)
    state.request("P1", "R2", 1)
    state.request("P2", "R1", 1)
    
    rag = build_resource_allocation_graph(state)
    cycles = detect_cycles(rag)
    
    assert len(cycles) > 0


def test_wait_for_graph():
    """Test Wait-For Graph construction."""
    state = SystemState()
    state.add_resource("R1", 1)
    state.add_resource("R2", 1)
    state.add_process("P1", max_claims={"R1": 1, "R2": 1})
    state.add_process("P2", max_claims={"R1": 1, "R2": 1})
    
    state.allocate("P1", "R1", 1)
    state.allocate("P2", "R2", 1)
    state.request("P1", "R2", 1)
    state.request("P2", "R1", 1)
    
    wfg = build_wait_for_graph(state)
    
    # P1 waits for P2 (who holds R2)
    # P2 waits for P1 (who holds R1)
    assert wfg.has_edge("P1", "P2")
    assert wfg.has_edge("P2", "P1")


def test_wait_for_cycle_detection():
    """Test cycle detection in Wait-For Graph."""
    state = SystemState()
    state.add_resource("R1", 1)
    state.add_resource("R2", 1)
    state.add_process("P1", max_claims={"R1": 1, "R2": 1})
    state.add_process("P2", max_claims={"R1": 1, "R2": 1})
    
    state.allocate("P1", "R1", 1)
    state.allocate("P2", "R2", 1)
    state.request("P1", "R2", 1)
    state.request("P2", "R1", 1)
    
    wfg = build_wait_for_graph(state)
    cycles = detect_wait_for_cycles(wfg)
    
    assert len(cycles) > 0
    # Cycle should involve both P1 and P2
    cycle = cycles[0]
    assert "P1" in cycle
    assert "P2" in cycle


def test_deadlock_analysis():
    """Test comprehensive deadlock analysis."""
    state = SystemState()
    state.add_resource("R1", 1)
    state.add_resource("R2", 1)
    state.add_process("P1", max_claims={"R1": 1, "R2": 1})
    state.add_process("P2", max_claims={"R1": 1, "R2": 1})
    
    state.allocate("P1", "R1", 1)
    state.allocate("P2", "R2", 1)
    state.request("P1", "R2", 1)
    state.request("P2", "R1", 1)
    
    analysis = analyze_deadlock(state)
    
    assert analysis["has_deadlock"] is True
    assert len(analysis["deadlocked_processes"]) == 2
    assert "P1" in analysis["deadlocked_processes"]
    assert "P2" in analysis["deadlocked_processes"]
    assert len(analysis["deadlocked_resources"]) >= 1


def test_no_deadlock_analysis():
    """Test analysis when no deadlock exists."""
    state = SystemState()
    state.add_resource("R1", 2)
    state.add_process("P1", max_claims={"R1": 1})
    state.add_process("P2", max_claims={"R1": 1})
    
    state.allocate("P1", "R1", 1)
    
    analysis = analyze_deadlock(state)
    
    assert analysis["has_deadlock"] is False
    assert len(analysis["deadlocked_processes"]) == 0


def test_rag_to_dict():
    """Test RAG serialization to dictionary."""
    state = SystemState()
    state.add_resource("R1", 1)
    state.add_process("P1", max_claims={"R1": 1})
    state.allocate("P1", "R1", 1)
    
    rag = build_resource_allocation_graph(state)
    rag_dict = rag.to_dict()
    
    assert "nodes" in rag_dict
    assert "edges" in rag_dict
    assert len(rag_dict["nodes"]) == 2  # P1 and R1
    assert len(rag_dict["edges"]) == 1  # R1 -> P1 (assignment)
