"""
Prevention and Recovery Policies

Implements various deadlock prevention and recovery strategies.
"""

from typing import Dict, List, Optional, Protocol
from enum import Enum
from .state import SystemState


class PreventionStrategy(Enum):
    """Available prevention strategies."""
    NONE = "none"
    BANKERS = "bankers"
    RESOURCE_ORDERING = "resource_ordering"
    CONSERVATIVE_ALLOCATION = "conservative"
    MAX_CLAIM_ENFORCEMENT = "max_claim"


class RecoveryStrategy(Enum):
    """Available recovery strategies."""
    NONE = "none"
    PREEMPT_LOWEST_PRIORITY = "preempt_low_priority"
    PREEMPT_MINIMAL_COST = "preempt_min_cost"
    KILL_ONE = "kill_one"
    KILL_ALL = "kill_all"
    ROLLBACK = "rollback"


class PreventionPolicy(Protocol):
    """Protocol for prevention policies."""
    
    def should_allow(
        self,
        state: SystemState,
        process_id: str,
        request: Dict[str, int]
    ) -> tuple[bool, str]:
        """
        Determine if a request should be allowed.
        
        Returns:
            (allowed, reason)
        """
        ...


class RecoveryPolicy(Protocol):
    """Protocol for recovery policies."""
    
    def recover(
        self,
        state: SystemState,
        deadlocked_processes: List[str]
    ) -> tuple[bool, str, List[str]]:
        """
        Attempt to recover from deadlock.
        
        Returns:
            (success, reason, affected_processes)
        """
        ...


class BankersPreventionPolicy:
    """Prevention policy using Banker's Algorithm."""
    
    def should_allow(
        self,
        state: SystemState,
        process_id: str,
        request: Dict[str, int]
    ) -> tuple[bool, str]:
        """Check if request is safe using Banker's Algorithm."""
        from .banker import is_safe_state
        
        is_safe, sequence = is_safe_state(state, process_id, request)
        
        if is_safe:
            return True, f"Safe state maintained. Safe sequence: {sequence}"
        else:
            return False, "Request would lead to unsafe state"


class ResourceOrderingPolicy:
    """Prevention using resource ordering to avoid circular wait."""
    
    def __init__(self, resource_order: Optional[List[str]] = None):
        """
        Initialize with resource ordering.
        
        Args:
            resource_order: List of resource IDs in order of acquisition
        """
        self.resource_order = resource_order or []
    
    def should_allow(
        self,
        state: SystemState,
        process_id: str,
        request: Dict[str, int]
    ) -> tuple[bool, str]:
        """Check if request follows resource ordering."""
        if not self.resource_order:
            # Auto-generate ordering from resource IDs
            self.resource_order = sorted(state.resources.keys())
        
        process = state.processes[process_id]
        
        # Get highest resource currently held
        held_resources = [r for r in process.allocated.keys() if process.allocated[r] > 0]
        if not held_resources:
            return True, "No resources held, request allowed"
        
        highest_held_idx = max(
            self.resource_order.index(r) for r in held_resources if r in self.resource_order
        )
        
        # Check if requested resources are in order
        for res_id in request.keys():
            if res_id not in self.resource_order:
                continue
            req_idx = self.resource_order.index(res_id)
            if req_idx < highest_held_idx:
                return False, f"Violates resource ordering: requesting {res_id} while holding higher-order resources"
        
        return True, "Follows resource ordering"


class ConservativeAllocationPolicy:
    """Conservative allocation - only allocate if all needs can be met."""
    
    def should_allow(
        self,
        state: SystemState,
        process_id: str,
        request: Dict[str, int]
    ) -> tuple[bool, str]:
        """Check if all current and future needs can be satisfied."""
        process = state.processes[process_id]
        
        # Check if all remaining needs could potentially be satisfied
        for res_id, need in process.total_need().items():
            total_units = state.resources[res_id].total_units
            if need > total_units:
                return False, f"Maximum need for {res_id} ({need}) exceeds total available ({total_units})"
        
        # Check if current request can be satisfied
        for res_id, units in request.items():
            available = state.get_available(res_id)
            if units > available:
                return False, f"Insufficient {res_id} available now"
        
        return True, "Conservative check passed"


class PreemptLowPriorityRecovery:
    """Recovery by preempting lowest priority process."""
    
    def recover(
        self,
        state: SystemState,
        deadlocked_processes: List[str]
    ) -> tuple[bool, str, List[str]]:
        """Preempt lowest priority process in deadlock."""
        if not deadlocked_processes:
            return False, "No deadlocked processes", []
        
        # Find lowest priority process
        victim = min(
            deadlocked_processes,
            key=lambda pid: state.processes[pid].priority
        )
        
        # Release all resources from victim
        victim_proc = state.processes[victim]
        released = {}
        for res_id, units in list(victim_proc.allocated.items()):
            state.release(victim, res_id, units)
            released[res_id] = units
        
        return True, f"Preempted {victim} (priority={victim_proc.priority}), released {released}", [victim]


class MinimalCostRecovery:
    """Recovery by preempting process with minimal cost."""
    
    def calculate_cost(self, state: SystemState, process_id: str) -> float:
        """
        Calculate cost of preempting a process.
        
        Cost factors:
        - Number of resources held (higher = more costly)
        - Process priority (lower priority = lower cost)
        """
        process = state.processes[process_id]
        resource_count = sum(process.allocated.values())
        priority_factor = 1.0 / (process.priority + 1)  # Lower priority = lower cost
        
        return resource_count * priority_factor
    
    def recover(
        self,
        state: SystemState,
        deadlocked_processes: List[str]
    ) -> tuple[bool, str, List[str]]:
        """Preempt process with minimal cost."""
        if not deadlocked_processes:
            return False, "No deadlocked processes", []
        
        # Find process with minimal cost
        victim = min(
            deadlocked_processes,
            key=lambda pid: self.calculate_cost(state, pid)
        )
        
        cost = self.calculate_cost(state, victim)
        
        # Release all resources from victim
        victim_proc = state.processes[victim]
        released = {}
        for res_id, units in list(victim_proc.allocated.items()):
            state.release(victim, res_id, units)
            released[res_id] = units
        
        return True, f"Preempted {victim} (cost={cost:.2f}), released {released}", [victim]


class KillProcessRecovery:
    """Recovery by terminating one or more processes."""
    
    def __init__(self, kill_all: bool = False):
        """
        Initialize kill policy.
        
        Args:
            kill_all: If True, kill all deadlocked processes. If False, kill one.
        """
        self.kill_all = kill_all
    
    def recover(
        self,
        state: SystemState,
        deadlocked_processes: List[str]
    ) -> tuple[bool, str, List[str]]:
        """Terminate process(es) to break deadlock."""
        if not deadlocked_processes:
            return False, "No deadlocked processes", []
        
        if self.kill_all:
            # Kill all deadlocked processes
            for pid in deadlocked_processes:
                state.remove_process(pid)
            return True, f"Terminated all {len(deadlocked_processes)} deadlocked processes", deadlocked_processes
        else:
            # Kill lowest priority process
            victim = min(
                deadlocked_processes,
                key=lambda pid: state.processes[pid].priority
            )
            state.remove_process(victim)
            return True, f"Terminated process {victim}", [victim]


# Factory functions

def get_prevention_policy(strategy: PreventionStrategy, **kwargs) -> Optional[PreventionPolicy]:
    """Get a prevention policy instance."""
    if strategy == PreventionStrategy.BANKERS:
        return BankersPreventionPolicy()
    elif strategy == PreventionStrategy.RESOURCE_ORDERING:
        return ResourceOrderingPolicy(kwargs.get("resource_order"))
    elif strategy == PreventionStrategy.CONSERVATIVE_ALLOCATION:
        return ConservativeAllocationPolicy()
    elif strategy == PreventionStrategy.NONE:
        return None
    else:
        raise ValueError(f"Unknown prevention strategy: {strategy}")


def get_recovery_policy(strategy: RecoveryStrategy) -> Optional[RecoveryPolicy]:
    """Get a recovery policy instance."""
    if strategy == RecoveryStrategy.PREEMPT_LOWEST_PRIORITY:
        return PreemptLowPriorityRecovery()
    elif strategy == RecoveryStrategy.PREEMPT_MINIMAL_COST:
        return MinimalCostRecovery()
    elif strategy == RecoveryStrategy.KILL_ONE:
        return KillProcessRecovery(kill_all=False)
    elif strategy == RecoveryStrategy.KILL_ALL:
        return KillProcessRecovery(kill_all=True)
    elif strategy == RecoveryStrategy.NONE:
        return None
    else:
        raise ValueError(f"Unknown recovery strategy: {strategy}")
