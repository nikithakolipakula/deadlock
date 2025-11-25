"""
Event Dispatcher

Manages event execution and simulation timeline.
"""

from typing import Dict, List, Optional, Callable
from enum import Enum
import asyncio
from dataclasses import dataclass
import time

from engine.state import SystemState
from engine.rag import analyze_deadlock
from engine.policies import (
    PreventionStrategy,
    RecoveryStrategy,
    get_prevention_policy,
    get_recovery_policy
)
from .scenario import Scenario, Event, EventType


class SimulationMode(Enum):
    """Simulation execution modes."""
    CONTINUOUS = "continuous"  # Run all events automatically
    STEP = "step"  # Step through events one at a time
    REALTIME = "realtime"  # Run with real timestamps


@dataclass
class SimulationSnapshot:
    """Snapshot of simulation state at a point in time."""
    time: float
    event_index: int
    system_state: Dict
    deadlock_analysis: Dict
    last_event: Optional[Dict]
    prevention_result: Optional[Dict]
    recovery_result: Optional[Dict]


class EventDispatcher:
    """
    Dispatches events and manages simulation execution.
    
    Handles event execution, policy enforcement, and state snapshots.
    """
    
    def __init__(
        self,
        scenario: Scenario,
        mode: SimulationMode = SimulationMode.CONTINUOUS,
        speed: float = 1.0
    ):
        """
        Initialize dispatcher.
        
        Args:
            scenario: Scenario to execute
            mode: Simulation mode
            speed: Speed multiplier for realtime mode (1.0 = normal speed)
        """
        self.scenario = scenario
        self.mode = mode
        self.speed = speed
        
        self.state = SystemState()
        self.snapshots: List[SimulationSnapshot] = []
        self.current_event_index = 0
        self.paused = False
        
        # Initialize policies
        prevention_strategy = PreventionStrategy(scenario.prevention_policy)
        recovery_strategy = RecoveryStrategy(scenario.recovery_policy)
        
        self.prevention_policy = get_prevention_policy(prevention_strategy)
        self.recovery_policy = get_recovery_policy(recovery_strategy)
        
        # Callbacks
        self.on_event_callbacks: List[Callable] = []
        self.on_deadlock_callbacks: List[Callable] = []
        self.on_prevention_callbacks: List[Callable] = []
        self.on_recovery_callbacks: List[Callable] = []
        
        # Initialize system state with resources and processes
        self._initialize_state()
    
    def _initialize_state(self) -> None:
        """Initialize system state with resources and processes from scenario."""
        # Add resources
        for resource in self.scenario.resources:
            self.state.add_resource(resource.id, resource.units)
        
        # Add processes
        for process in self.scenario.processes:
            self.state.add_process(
                process.id,
                max_claims=process.max,
                priority=process.priority
            )
        
        # Take initial snapshot
        self._take_snapshot(time=0.0, event_index=-1)
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """Add a callback for specific events."""
        if event_type == "event":
            self.on_event_callbacks.append(callback)
        elif event_type == "deadlock":
            self.on_deadlock_callbacks.append(callback)
        elif event_type == "prevention":
            self.on_prevention_callbacks.append(callback)
        elif event_type == "recovery":
            self.on_recovery_callbacks.append(callback)
    
    def execute_event(self, event: Event) -> Dict:
        """
        Execute a single event.
        
        Returns:
            Dictionary with execution result
        """
        result = {
            "success": False,
            "event": event.model_dump(),
            "message": ""
        }
        
        try:
            if event.type == EventType.ALLOCATE:
                success = self.state.allocate(event.proc, event.res, event.units)
                result["success"] = success
                result["message"] = f"Allocated {event.units} of {event.res} to {event.proc}"
                
            elif event.type == EventType.REQUEST:
                # Check prevention policy first
                if self.prevention_policy:
                    request = {event.res: event.units}
                    allowed, reason = self.prevention_policy.should_allow(
                        self.state, event.proc, request
                    )
                    
                    if not allowed:
                        result["success"] = False
                        result["message"] = f"Request denied by prevention policy: {reason}"
                        result["prevention_blocked"] = True
                        
                        # Trigger prevention callbacks
                        for callback in self.on_prevention_callbacks:
                            callback(event, allowed, reason)
                        
                        return result
                
                # Record request (doesn't allocate immediately)
                success = self.state.request(event.proc, event.res, event.units)
                result["success"] = success
                result["message"] = f"Process {event.proc} requested {event.units} of {event.res}"
                
            elif event.type == EventType.RELEASE:
                success = self.state.release(event.proc, event.res, event.units)
                result["success"] = success
                result["message"] = f"Released {event.units} of {event.res} from {event.proc}"
                
            elif event.type == EventType.ADD_PROCESS:
                self.state.add_process(event.proc, max_claims=event.max or {}, priority=event.priority or 0)
                result["success"] = True
                result["message"] = f"Added process {event.proc}"
                
            elif event.type == EventType.REMOVE_PROCESS:
                self.state.remove_process(event.proc)
                result["success"] = True
                result["message"] = f"Removed process {event.proc}"
            
        except Exception as e:
            result["success"] = False
            result["message"] = f"Error: {str(e)}"
            result["error"] = str(e)
        
        # Trigger event callbacks
        for callback in self.on_event_callbacks:
            callback(event, result)
        
        return result
    
    def check_and_recover_deadlock(self) -> Optional[Dict]:
        """
        Check for deadlock and attempt recovery if needed.
        
        Returns:
            Recovery result dictionary if deadlock detected, None otherwise
        """
        analysis = analyze_deadlock(self.state)
        
        if analysis["has_deadlock"]:
            # Trigger deadlock callbacks
            for callback in self.on_deadlock_callbacks:
                callback(analysis)
            
            # Attempt recovery if policy exists
            if self.recovery_policy:
                success, reason, affected = self.recovery_policy.recover(
                    self.state,
                    analysis["deadlocked_processes"]
                )
                
                recovery_result = {
                    "success": success,
                    "reason": reason,
                    "affected_processes": affected,
                    "analysis": analysis
                }
                
                # Trigger recovery callbacks
                for callback in self.on_recovery_callbacks:
                    callback(recovery_result)
                
                return recovery_result
        
        return None
    
    def _take_snapshot(
        self,
        time: float,
        event_index: int,
        last_event: Optional[Dict] = None,
        prevention_result: Optional[Dict] = None,
        recovery_result: Optional[Dict] = None
    ) -> None:
        """Take a snapshot of current simulation state."""
        snapshot = SimulationSnapshot(
            time=time,
            event_index=event_index,
            system_state=self.state.snapshot(),
            deadlock_analysis=analyze_deadlock(self.state),
            last_event=last_event,
            prevention_result=prevention_result,
            recovery_result=recovery_result
        )
        self.snapshots.append(snapshot)
    
    def step(self) -> Optional[Dict]:
        """
        Execute the next event in the scenario.
        
        Returns:
            Result dictionary, or None if no more events
        """
        if self.current_event_index >= len(self.scenario.events):
            return None
        
        event = self.scenario.events[self.current_event_index]
        result = self.execute_event(event)
        
        # Check for deadlock and attempt recovery
        recovery_result = self.check_and_recover_deadlock()
        
        # Take snapshot
        self._take_snapshot(
            time=event.time,
            event_index=self.current_event_index,
            last_event=result,
            recovery_result=recovery_result
        )
        
        self.current_event_index += 1
        return result
    
    async def run_async(self) -> List[SimulationSnapshot]:
        """Run simulation asynchronously."""
        while self.current_event_index < len(self.scenario.events):
            if self.paused:
                await asyncio.sleep(0.1)
                continue
            
            event = self.scenario.events[self.current_event_index]
            
            # Handle timing based on mode
            if self.mode == SimulationMode.REALTIME:
                if self.current_event_index > 0:
                    prev_event = self.scenario.events[self.current_event_index - 1]
                    delay = (event.time - prev_event.time) / self.speed
                    if delay > 0:
                        await asyncio.sleep(delay)
            
            self.step()
            
            if self.mode == SimulationMode.STEP:
                self.paused = True
        
        return self.snapshots
    
    def run(self) -> List[SimulationSnapshot]:
        """Run simulation synchronously."""
        while self.current_event_index < len(self.scenario.events):
            self.step()
        
        return self.snapshots
    
    def reset(self) -> None:
        """Reset simulation to initial state."""
        self.state = SystemState()
        self.snapshots = []
        self.current_event_index = 0
        self.paused = False
        self._initialize_state()
    
    def get_summary(self) -> Dict:
        """Get simulation summary statistics."""
        total_events = len(self.scenario.events)
        executed_events = self.current_event_index
        deadlock_count = sum(1 for s in self.snapshots if s.deadlock_analysis["has_deadlock"])
        recovery_count = sum(1 for s in self.snapshots if s.recovery_result is not None)
        
        return {
            "total_events": total_events,
            "executed_events": executed_events,
            "deadlock_detected_count": deadlock_count,
            "recovery_attempts": recovery_count,
            "snapshots": len(self.snapshots)
        }
