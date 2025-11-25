"""
System State Management

Manages processes, resources, and their allocations in the deadlock detection system.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class Resource:
    """Represents a system resource with available units."""
    
    id: str
    total_units: int
    available_units: int
    
    def __post_init__(self) -> None:
        if self.total_units < 0:
            raise ValueError(f"Total units must be non-negative, got {self.total_units}")
        if self.available_units > self.total_units:
            raise ValueError(
                f"Available units ({self.available_units}) cannot exceed total ({self.total_units})"
            )


@dataclass
class Process:
    """Represents a process with resource claims and allocations."""
    
    id: str
    max_claims: Dict[str, int] = field(default_factory=dict)
    allocated: Dict[str, int] = field(default_factory=dict)
    requested: Dict[str, int] = field(default_factory=dict)
    priority: int = 0
    
    def need(self, resource_id: str) -> int:
        """Calculate remaining need for a resource."""
        max_claim = self.max_claims.get(resource_id, 0)
        current_alloc = self.allocated.get(resource_id, 0)
        return max_claim - current_alloc
    
    def total_need(self) -> Dict[str, int]:
        """Calculate total remaining need for all resources."""
        all_resources = set(self.max_claims.keys()) | set(self.allocated.keys())
        return {res: self.need(res) for res in all_resources}


class SystemState:
    """
    Manages the complete system state including all processes and resources.
    
    Provides methods for allocation, deallocation, and state queries.
    """
    
    def __init__(self) -> None:
        self.resources: Dict[str, Resource] = {}
        self.processes: Dict[str, Process] = {}
        self.event_log: List[Dict] = []
    
    def add_resource(self, resource_id: str, total_units: int) -> None:
        """Add a new resource to the system."""
        if resource_id in self.resources:
            raise ValueError(f"Resource {resource_id} already exists")
        self.resources[resource_id] = Resource(
            id=resource_id,
            total_units=total_units,
            available_units=total_units
        )
        self._log_event("resource_added", resource=resource_id, units=total_units)
    
    def add_process(
        self,
        process_id: str,
        max_claims: Dict[str, int],
        priority: int = 0
    ) -> None:
        """Add a new process to the system."""
        if process_id in self.processes:
            raise ValueError(f"Process {process_id} already exists")
        
        # Validate max claims against available resources
        for res_id, units in max_claims.items():
            if res_id not in self.resources:
                raise ValueError(f"Resource {res_id} does not exist")
            if units > self.resources[res_id].total_units:
                raise ValueError(
                    f"Process {process_id} max claim for {res_id} ({units}) "
                    f"exceeds total units ({self.resources[res_id].total_units})"
                )
        
        self.processes[process_id] = Process(
            id=process_id,
            max_claims=max_claims,
            priority=priority
        )
        self._log_event("process_added", process=process_id, max_claims=max_claims)
    
    def request(self, process_id: str, resource_id: str, units: int) -> bool:
        """
        Process requests resources.
        
        Returns True if request is recorded, False if invalid.
        Does not allocate - just records the request.
        """
        self._validate_process_and_resource(process_id, resource_id)
        process = self.processes[process_id]
        
        if units <= 0:
            raise ValueError(f"Request units must be positive, got {units}")
        
        # Check if request exceeds need
        need = process.need(resource_id)
        if units > need:
            self._log_event(
                "request_rejected",
                process=process_id,
                resource=resource_id,
                units=units,
                reason="exceeds_need"
            )
            return False
        
        # Record request
        process.requested[resource_id] = process.requested.get(resource_id, 0) + units
        self._log_event("request", process=process_id, resource=resource_id, units=units)
        return True
    
    def allocate(self, process_id: str, resource_id: str, units: int) -> bool:
        """
        Allocate resources to a process.
        
        Returns True if allocation successful, False otherwise.
        """
        self._validate_process_and_resource(process_id, resource_id)
        process = self.processes[process_id]
        resource = self.resources[resource_id]
        
        if units < 0:
            raise ValueError(f"Allocation units must be non-negative, got {units}")
        
        # Allow 0 allocations (no-op, useful for initialization)
        if units == 0:
            self._log_event("allocation_skipped", process=process_id, resource=resource_id, units=0)
            return True
        
        # Check availability
        if units > resource.available_units:
            self._log_event(
                "allocation_failed",
                process=process_id,
                resource=resource_id,
                units=units,
                reason="insufficient_available"
            )
            return False
        
        # Check against max claims
        current_alloc = process.allocated.get(resource_id, 0)
        max_claim = process.max_claims.get(resource_id, 0)
        if current_alloc + units > max_claim:
            self._log_event(
                "allocation_failed",
                process=process_id,
                resource=resource_id,
                units=units,
                reason="exceeds_max_claim"
            )
            return False
        
        # Perform allocation
        process.allocated[resource_id] = current_alloc + units
        resource.available_units -= units
        
        # Clear request if fulfilled
        if resource_id in process.requested:
            process.requested[resource_id] = max(0, process.requested[resource_id] - units)
            if process.requested[resource_id] == 0:
                del process.requested[resource_id]
        
        self._log_event("allocation", process=process_id, resource=resource_id, units=units)
        return True
    
    def release(self, process_id: str, resource_id: str, units: int) -> bool:
        """
        Release resources from a process.
        
        Returns True if release successful, False otherwise.
        """
        self._validate_process_and_resource(process_id, resource_id)
        process = self.processes[process_id]
        resource = self.resources[resource_id]
        
        if units <= 0:
            raise ValueError(f"Release units must be positive, got {units}")
        
        current_alloc = process.allocated.get(resource_id, 0)
        if units > current_alloc:
            self._log_event(
                "release_failed",
                process=process_id,
                resource=resource_id,
                units=units,
                reason="insufficient_allocation"
            )
            return False
        
        # Perform release
        process.allocated[resource_id] = current_alloc - units
        if process.allocated[resource_id] == 0:
            del process.allocated[resource_id]
        resource.available_units += units
        
        self._log_event("release", process=process_id, resource=resource_id, units=units)
        return True
    
    def remove_process(self, process_id: str) -> None:
        """Remove a process and release all its resources."""
        if process_id not in self.processes:
            raise ValueError(f"Process {process_id} does not exist")
        
        process = self.processes[process_id]
        
        # Release all allocated resources
        for resource_id, units in list(process.allocated.items()):
            self.release(process_id, resource_id, units)
        
        del self.processes[process_id]
        self._log_event("process_removed", process=process_id)
    
    def get_available(self, resource_id: str) -> int:
        """Get available units of a resource."""
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} does not exist")
        return self.resources[resource_id].available_units
    
    def clone(self) -> "SystemState":
        """Create a deep copy of the current state."""
        return deepcopy(self)
    
    def snapshot(self) -> Dict:
        """Create a JSON-serializable snapshot of current state."""
        return {
            "resources": {
                rid: {
                    "total": res.total_units,
                    "available": res.available_units
                }
                for rid, res in self.resources.items()
            },
            "processes": {
                pid: {
                    "max_claims": proc.max_claims,
                    "allocated": proc.allocated,
                    "requested": proc.requested,
                    "need": proc.total_need(),
                    "priority": proc.priority
                }
                for pid, proc in self.processes.items()
            }
        }
    
    def _validate_process_and_resource(self, process_id: str, resource_id: str) -> None:
        """Validate that process and resource exist."""
        if process_id not in self.processes:
            raise ValueError(f"Process {process_id} does not exist")
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} does not exist")
    
    def _log_event(self, event_type: str, **kwargs) -> None:
        """Log an event to the event log."""
        self.event_log.append({
            "type": event_type,
            "timestamp": len(self.event_log),
            **kwargs
        })
