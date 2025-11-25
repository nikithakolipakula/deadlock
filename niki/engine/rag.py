"""
Resource Allocation Graph (RAG) Construction and Cycle Detection

Builds and analyzes Resource Allocation Graphs to detect deadlocks
through cycle detection algorithms.
"""

from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
from .state import SystemState


class ResourceAllocationGraph:
    """
    Resource Allocation Graph representation.
    
    Nodes: Processes (P1, P2, ...) and Resources (R1, R2, ...)
    Edges: 
        - Request: Process -> Resource (process requests resource)
        - Assignment: Resource -> Process (resource assigned to process)
    """
    
    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self.process_nodes: Set[str] = set()
        self.resource_nodes: Set[str] = set()
    
    def add_process(self, process_id: str) -> None:
        """Add a process node to the graph."""
        self.graph.add_node(process_id, node_type="process")
        self.process_nodes.add(process_id)
    
    def add_resource(self, resource_id: str, units: int = 1) -> None:
        """Add a resource node to the graph."""
        self.graph.add_node(resource_id, node_type="resource", units=units)
        self.resource_nodes.add(resource_id)
    
    def add_request_edge(self, process_id: str, resource_id: str, units: int = 1) -> None:
        """Add a request edge from process to resource."""
        self.graph.add_edge(
            process_id,
            resource_id,
            edge_type="request",
            units=units
        )
    
    def add_assignment_edge(self, resource_id: str, process_id: str, units: int = 1) -> None:
        """Add an assignment edge from resource to process."""
        self.graph.add_edge(
            resource_id,
            process_id,
            edge_type="assignment",
            units=units
        )
    
    def to_dict(self) -> Dict:
        """Convert graph to dictionary representation for JSON serialization."""
        nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            nodes.append({
                "id": node_id,
                "type": node_data.get("node_type", "unknown"),
                "units": node_data.get("units", 1)
            })
        
        edges = []
        for source, target in self.graph.edges():
            edge_data = self.graph.edges[source, target]
            edges.append({
                "from": source,
                "to": target,
                "type": edge_data.get("edge_type", "unknown"),
                "units": edge_data.get("units", 1)
            })
        
        return {"nodes": nodes, "edges": edges}


def build_resource_allocation_graph(state: SystemState) -> ResourceAllocationGraph:
    """
    Build a Resource Allocation Graph from system state.
    
    Args:
        state: Current system state
    
    Returns:
        ResourceAllocationGraph instance
    """
    rag = ResourceAllocationGraph()
    
    # Add resource nodes
    for resource_id, resource in state.resources.items():
        rag.add_resource(resource_id, resource.total_units)
    
    # Add process nodes and edges
    for process_id, process in state.processes.items():
        rag.add_process(process_id)
        
        # Add assignment edges (resource -> process) for allocated resources
        for resource_id, units in process.allocated.items():
            if units > 0:
                rag.add_assignment_edge(resource_id, process_id, units)
        
        # Add request edges (process -> resource) for requested resources
        for resource_id, units in process.requested.items():
            if units > 0:
                rag.add_request_edge(process_id, resource_id, units)
    
    return rag


def build_wait_for_graph(state: SystemState) -> nx.DiGraph:
    """
    Build a Wait-For Graph from system state.
    
    Wait-For Graph is a simplified version where only process nodes exist,
    and an edge P1 -> P2 means P1 is waiting for a resource held by P2.
    
    Args:
        state: Current system state
    
    Returns:
        NetworkX directed graph with process nodes only
    """
    wfg = nx.DiGraph()
    
    # Add all process nodes
    for process_id in state.processes.keys():
        wfg.add_node(process_id)
    
    # For each process, check what it's waiting for
    for proc_id, process in state.processes.items():
        for res_id, requested_units in process.requested.items():
            if requested_units == 0:
                continue
            
            # Find which processes hold this resource
            for other_proc_id, other_process in state.processes.items():
                if other_proc_id == proc_id:
                    continue
                
                allocated_units = other_process.allocated.get(res_id, 0)
                if allocated_units > 0:
                    # proc_id is waiting for resource held by other_proc_id
                    wfg.add_edge(proc_id, other_proc_id, resource=res_id)
    
    return wfg


def detect_cycles(rag: ResourceAllocationGraph) -> List[List[str]]:
    """
    Detect cycles in a Resource Allocation Graph.
    
    A cycle indicates a potential deadlock.
    
    Args:
        rag: Resource Allocation Graph
    
    Returns:
        List of cycles, where each cycle is a list of node IDs
    """
    try:
        cycles = list(nx.simple_cycles(rag.graph))
        return cycles
    except nx.NetworkXNoCycle:
        return []


def detect_wait_for_cycles(wfg: nx.DiGraph) -> List[List[str]]:
    """
    Detect cycles in a Wait-For Graph.
    
    Args:
        wfg: Wait-For Graph
    
    Returns:
        List of cycles, where each cycle is a list of process IDs
    """
    try:
        cycles = list(nx.simple_cycles(wfg))
        return cycles
    except nx.NetworkXNoCycle:
        return []


def analyze_deadlock(state: SystemState) -> Dict:
    """
    Comprehensive deadlock analysis using both RAG and Wait-For Graph.
    
    Args:
        state: Current system state
    
    Returns:
        Dictionary with analysis results:
        - has_deadlock: boolean
        - rag_cycles: cycles in Resource Allocation Graph
        - wait_for_cycles: cycles in Wait-For Graph
        - deadlocked_processes: set of processes involved in deadlock
        - deadlocked_resources: set of resources involved in deadlock
    """
    rag = build_resource_allocation_graph(state)
    wfg = build_wait_for_graph(state)
    
    rag_cycles = detect_cycles(rag)
    wfg_cycles = detect_wait_for_cycles(wfg)
    
    # Collect all processes involved in cycles
    deadlocked_processes: Set[str] = set()
    for cycle in wfg_cycles:
        deadlocked_processes.update(cycle)
    
    # Collect all resources involved in RAG cycles
    deadlocked_resources: Set[str] = set()
    for cycle in rag_cycles:
        for node in cycle:
            if node in rag.resource_nodes:
                deadlocked_resources.add(node)
    
    has_deadlock = len(wfg_cycles) > 0
    
    return {
        "has_deadlock": has_deadlock,
        "rag_cycles": rag_cycles,
        "wait_for_cycles": wfg_cycles,
        "deadlocked_processes": list(deadlocked_processes),
        "deadlocked_resources": list(deadlocked_resources),
        "rag_dict": rag.to_dict(),
        "process_count": len(state.processes),
        "resource_count": len(state.resources)
    }


def get_strongly_connected_components(rag: ResourceAllocationGraph) -> List[Set[str]]:
    """
    Find strongly connected components in the RAG.
    
    SCCs can help identify potential deadlock groups.
    
    Args:
        rag: Resource Allocation Graph
    
    Returns:
        List of sets, where each set contains node IDs in an SCC
    """
    sccs = list(nx.strongly_connected_components(rag.graph))
    # Filter out single-node SCCs without self-loops
    return [scc for scc in sccs if len(scc) > 1 or rag.graph.has_edge(list(scc)[0], list(scc)[0])]
