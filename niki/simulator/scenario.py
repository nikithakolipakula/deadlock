"""
Scenario Definition and Loading

Defines the scenario data structures and provides loading from JSON/YAML files.
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import json
import yaml
from pathlib import Path


class EventType(str, Enum):
    """Types of events in a scenario."""
    ALLOCATE = "allocate"
    REQUEST = "request"
    RELEASE = "release"
    ADD_PROCESS = "add_process"
    REMOVE_PROCESS = "remove_process"


class ResourceConfig(BaseModel):
    """Resource configuration."""
    id: str = Field(..., description="Resource identifier")
    units: int = Field(..., gt=0, description="Total units of resource")


class ProcessConfig(BaseModel):
    """Process configuration."""
    id: str = Field(..., description="Process identifier")
    max: Dict[str, int] = Field(default_factory=dict, description="Maximum claims for each resource")
    priority: int = Field(default=0, description="Process priority (lower = lower priority)")
    
    @field_validator('max')
    @classmethod
    def validate_max_claims(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Validate max claims are non-negative."""
        for res_id, units in v.items():
            if units < 0:
                raise ValueError(f"Max claim for {res_id} must be non-negative")
        return v


class Event(BaseModel):
    """An event in the scenario timeline."""
    time: float = Field(..., ge=0, description="Event timestamp")
    type: EventType = Field(..., description="Event type")
    proc: Optional[str] = Field(None, description="Process ID")
    res: Optional[str] = Field(None, description="Resource ID")
    units: Optional[int] = Field(None, ge=0, description="Units to allocate/request/release")
    max: Optional[Dict[str, int]] = Field(None, description="Max claims (for add_process)")
    priority: Optional[int] = Field(None, description="Priority (for add_process)")
    
    @field_validator('type')
    @classmethod
    def validate_event_fields(cls, v: EventType, info) -> EventType:
        """Validate required fields based on event type."""
        # Note: In Pydantic v2, use info.data to access other fields
        return v


class Scenario(BaseModel):
    """Complete scenario definition."""
    name: str = Field(default="Unnamed Scenario", description="Scenario name")
    description: str = Field(default="", description="Scenario description")
    resources: List[ResourceConfig] = Field(..., description="Resource definitions")
    processes: List[ProcessConfig] = Field(..., description="Process definitions")
    events: List[Event] = Field(..., description="Timeline of events")
    
    prevention_policy: str = Field(default="none", description="Prevention policy to use")
    recovery_policy: str = Field(default="none", description="Recovery policy to use")
    
    @field_validator('events')
    @classmethod
    def sort_events_by_time(cls, v: List[Event]) -> List[Event]:
        """Sort events by timestamp."""
        return sorted(v, key=lambda e: e.time)


class ScenarioLoader:
    """Loader for scenario files (JSON/YAML)."""
    
    @staticmethod
    def load_from_file(filepath: str) -> Scenario:
        """
        Load scenario from JSON or YAML file.
        
        Args:
            filepath: Path to scenario file
        
        Returns:
            Scenario instance
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {filepath}")
        
        content = path.read_text()
        
        # Try JSON first, then YAML
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid scenario file format: {e}")
        
        return Scenario(**data)
    
    @staticmethod
    def load_from_dict(data: Dict) -> Scenario:
        """Load scenario from dictionary."""
        return Scenario(**data)
    
    @staticmethod
    def save_to_file(scenario: Scenario, filepath: str, format: str = "json") -> None:
        """
        Save scenario to file.
        
        Args:
            scenario: Scenario to save
            filepath: Output file path
            format: "json" or "yaml"
        """
        path = Path(filepath)
        
        if format == "json":
            content = scenario.model_dump_json(indent=2)
        elif format == "yaml":
            content = yaml.dump(
                scenario.model_dump(),
                default_flow_style=False,
                sort_keys=False
            )
        else:
            raise ValueError(f"Unknown format: {format}")
        
        path.write_text(content)


def create_simple_scenario(
    num_processes: int = 2,
    num_resources: int = 2,
    resource_units: int = 1
) -> Scenario:
    """
    Create a simple deadlock scenario programmatically.
    
    Args:
        num_processes: Number of processes
        num_resources: Number of resources
        resource_units: Units per resource
    
    Returns:
        Scenario instance
    """
    resources = [
        ResourceConfig(id=f"R{i+1}", units=resource_units)
        for i in range(num_resources)
    ]
    
    processes = [
        ProcessConfig(
            id=f"P{i+1}",
            max={f"R{j+1}": 1 for j in range(num_resources)}
        )
        for i in range(num_processes)
    ]
    
    # Create circular wait pattern
    events = []
    time = 0.0
    for i in range(num_processes):
        proc_id = f"P{i+1}"
        res_id = f"R{i+1}"
        next_res_id = f"R{((i+1) % num_resources) + 1}"
        
        # Each process allocates one resource
        events.append(Event(
            time=time,
            type=EventType.ALLOCATE,
            proc=proc_id,
            res=res_id,
            units=1
        ))
        time += 0.5
        
        # Then requests the next resource (creating circular wait)
        events.append(Event(
            time=time,
            type=EventType.REQUEST,
            proc=proc_id,
            res=next_res_id,
            units=1
        ))
        time += 0.5
    
    return Scenario(
        name="Simple Circular Wait Deadlock",
        description=f"Circular wait between {num_processes} processes and {num_resources} resources",
        resources=resources,
        processes=processes,
        events=events
    )
