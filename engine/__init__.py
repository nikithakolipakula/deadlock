"""
Deadlock Detection Engine

Core module implementing deadlock detection algorithms, prevention strategies,
and recovery mechanisms.
"""

from .state import SystemState, Process, Resource
from .banker import is_safe_state, find_safe_sequence
from .rag import build_resource_allocation_graph, detect_cycles
from .policies import PreventionPolicy, RecoveryPolicy

__all__ = [
    "SystemState",
    "Process",
    "Resource",
    "is_safe_state",
    "find_safe_sequence",
    "build_resource_allocation_graph",
    "detect_cycles",
    "PreventionPolicy",
    "RecoveryPolicy",
]

__version__ = "0.1.0"
