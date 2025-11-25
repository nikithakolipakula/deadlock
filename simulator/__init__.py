"""
Simulator Module

CLI and programmatic simulator for deadlock scenarios.
"""

from .scenario import Scenario, ScenarioLoader, EventType
from .dispatcher import EventDispatcher, SimulationMode
from .run import main

__all__ = [
    "Scenario",
    "ScenarioLoader",
    "EventType",
    "EventDispatcher",
    "SimulationMode",
    "main",
]
