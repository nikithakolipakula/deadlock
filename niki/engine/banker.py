"""
Banker's Algorithm Implementation

Implements the Banker's Algorithm for deadlock avoidance by checking
if a resource allocation request leaves the system in a safe state.
"""

from typing import Dict, List, Optional, Tuple
from .state import SystemState


def is_safe_state(
    state: SystemState,
    process: Optional[str] = None,
    request: Optional[Dict[str, int]] = None
) -> Tuple[bool, Optional[List[str]]]:
    """
    Check if the system is in a safe state using Banker's Algorithm.
    
    Args:
        state: Current system state
        process: Optional process making a request (for tentative allocation check)
        request: Optional resource request to check
    
    Returns:
        Tuple of (is_safe, safe_sequence)
        - is_safe: True if system is in safe state
        - safe_sequence: List of process IDs in safe execution order, None if unsafe
    
    Example:
        >>> safe, seq = is_safe_state(state, "P1", {"R1": 1, "R2": 0})
        >>> if safe:
        ...     print(f"Safe sequence: {seq}")
    """
    # Clone state for tentative allocation if request provided
    test_state = state.clone()
    
    if process and request:
        # Validate request doesn't exceed need
        proc = test_state.processes[process]
        for res_id, units in request.items():
            need = proc.need(res_id)
            if units > need:
                return False, None
            
            # Check if resources are available
            available = test_state.get_available(res_id)
            if units > available:
                return False, None
        
        # Perform tentative allocation
        for res_id, units in request.items():
            if not test_state.allocate(process, res_id, units):
                return False, None
    
    # Run safety algorithm
    return find_safe_sequence(test_state)


def find_safe_sequence(state: SystemState) -> Tuple[bool, Optional[List[str]]]:
    """
    Find a safe sequence of process execution if one exists.
    
    Uses the Banker's Algorithm safety check to determine if all processes
    can complete with current available resources.
    
    Args:
        state: Current system state
    
    Returns:
        Tuple of (is_safe, safe_sequence)
    """
    if not state.processes:
        return True, []
    
    # Get all resource IDs
    resource_ids = list(state.resources.keys())
    
    # Track work (available resources) and finish status
    work = {rid: state.resources[rid].available_units for rid in resource_ids}
    finish = {pid: False for pid in state.processes.keys()}
    safe_sequence: List[str] = []
    
    # Keep trying to find processes that can finish
    progress = True
    while progress:
        progress = False
        
        for pid, proc in state.processes.items():
            if finish[pid]:
                continue
            
            # Check if process needs can be satisfied with work
            can_finish = True
            for res_id in resource_ids:
                need = proc.need(res_id)
                if need > work.get(res_id, 0):
                    can_finish = False
                    break
            
            if can_finish:
                # Process can finish - add its allocated resources back to work
                for res_id in resource_ids:
                    allocated = proc.allocated.get(res_id, 0)
                    work[res_id] = work.get(res_id, 0) + allocated
                
                finish[pid] = True
                safe_sequence.append(pid)
                progress = True
    
    # Check if all processes finished
    is_safe = all(finish.values())
    return is_safe, safe_sequence if is_safe else None


def get_banker_decision(
    state: SystemState,
    process_id: str,
    request: Dict[str, int]
) -> Dict:
    """
    Get a detailed decision from Banker's Algorithm.
    
    Returns a dictionary with decision details including:
    - safe: boolean
    - safe_sequence: list of process IDs (if safe)
    - reason: explanation string
    - work_vectors: intermediate work vectors during safety check
    
    Args:
        state: Current system state
        process_id: Process making the request
        request: Resource request
    
    Returns:
        Decision dictionary with analysis details
    """
    # Validate process exists
    if process_id not in state.processes:
        return {
            "safe": False,
            "reason": f"Process {process_id} does not exist",
            "safe_sequence": None
        }
    
    proc = state.processes[process_id]
    
    # Check if request exceeds need
    for res_id, units in request.items():
        need = proc.need(res_id)
        if units > need:
            return {
                "safe": False,
                "reason": f"Request for {res_id} ({units}) exceeds need ({need})",
                "safe_sequence": None
            }
    
    # Check if request exceeds available
    for res_id, units in request.items():
        available = state.get_available(res_id)
        if units > available:
            return {
                "safe": False,
                "reason": f"Request for {res_id} ({units}) exceeds available ({available})",
                "safe_sequence": None
            }
    
    # Run safety check
    is_safe, sequence = is_safe_state(state, process_id, request)
    
    if is_safe:
        return {
            "safe": True,
            "reason": "Request leaves system in safe state",
            "safe_sequence": sequence
        }
    else:
        return {
            "safe": False,
            "reason": "Request would leave system in unsafe state (no safe sequence exists)",
            "safe_sequence": None
        }
