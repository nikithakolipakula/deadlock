# Quick Start Guide

Get up and running with the Deadlock Detection Toolkit in minutes!

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

```powershell
# Navigate to the project directory
cd c:\repo\niki

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Running Your First Simulation

### Option 1: Simple Generated Scenario

```powershell
python -m simulator.run --simple --verbose
```

This generates and runs a simple 3-process, 3-resource deadlock scenario.

### Option 2: Pre-built Examples

```powershell
# Run simple two-process deadlock
python -m simulator.run --scenario examples/simple_deadlock.json --verbose

# Run with Banker's Algorithm prevention
python -m simulator.run --scenario examples/banker_safe.json --policy bankers --verbose

# Run dining philosophers with recovery
python -m simulator.run --scenario examples/dining_philosophers.json --recovery preempt_low_priority --verbose
```

### Option 3: Step-by-Step Mode

```powershell
python -m simulator.run --scenario examples/simple_deadlock.json --step --verbose
```

Press any key to advance through each event.

## Web Dashboard

Start the interactive web dashboard:

```powershell
python -m visualizer.app
```

Then open your browser to: `http://localhost:8000`

The dashboard allows you to:
- Load and run scenarios interactively
- Step through events one at a time
- View real-time Resource Allocation Graphs
- Monitor system state and deadlock detection

## Running Tests

```powershell
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=engine --cov=simulator --cov=visualizer --cov-report=html

# View coverage report
.\htmlcov\index.html
```

## Creating Custom Scenarios

Create a JSON file with your scenario definition:

```json
{
  "name": "My Custom Scenario",
  "description": "Description here",
  "resources": [
    {"id": "R1", "units": 2},
    {"id": "R2", "units": 1}
  ],
  "processes": [
    {"id": "P1", "max": {"R1": 1, "R2": 1}, "priority": 1},
    {"id": "P2", "max": {"R1": 1, "R2": 1}, "priority": 2}
  ],
  "events": [
    {"time": 0.0, "type": "allocate", "proc": "P1", "res": "R1", "units": 1},
    {"time": 1.0, "type": "allocate", "proc": "P2", "res": "R2", "units": 1},
    {"time": 2.0, "type": "request", "proc": "P1", "res": "R2", "units": 1},
    {"time": 3.0, "type": "request", "proc": "P2", "res": "R1", "units": 1}
  ],
  "prevention_policy": "none",
  "recovery_policy": "none"
}
```

Run your custom scenario:

```powershell
python -m simulator.run --scenario my_scenario.json --verbose
```

## Available Prevention Policies

- `none` - No prevention (default)
- `bankers` - Banker's Algorithm
- `resource_ordering` - Resource ordering to avoid circular wait
- `conservative` - Conservative allocation

## Available Recovery Policies

- `none` - No recovery (default)
- `preempt_low_priority` - Preempt lowest priority process
- `preempt_min_cost` - Preempt process with minimal cost
- `kill_one` - Terminate one process
- `kill_all` - Terminate all deadlocked processes

## Example Commands

```powershell
# Export simulation results
python -m simulator.run --scenario examples/simple_deadlock.json --export results.json

# Run with specific policies
python -m simulator.run --scenario examples/banker_safe.json --policy bankers --recovery preempt_low_priority

# Real-time mode with speed control
python -m simulator.run --scenario examples/dining_philosophers.json --mode realtime --speed 0.5
```

## Programmatic Usage

```python
from engine.state import SystemState
from engine.banker import is_safe_state
from engine.rag import analyze_deadlock

# Create system state
state = SystemState()
state.add_resource("R1", 10)
state.add_process("P1", max_claims={"R1": 5})

# Allocate resources
state.allocate("P1", "R1", 3)

# Check safety
safe, sequence = is_safe_state(state, "P1", {"R1": 1})
print(f"Safe: {safe}, Sequence: {sequence}")

# Analyze for deadlocks
analysis = analyze_deadlock(state)
print(f"Deadlock: {analysis['has_deadlock']}")
```

## Next Steps

- Read the full [README.md](README.md) for detailed information
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Explore the [examples/](examples/) directory for more scenarios
- Review the API documentation in the code

## Troubleshooting

### Import errors
Make sure you've activated the virtual environment and installed all dependencies:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Module not found
Run commands from the project root directory (`c:\repo\niki`)

### Tests failing
Ensure you have dev dependencies installed:
```powershell
pip install -r requirements-dev.txt
```

## Getting Help

- Open an issue on GitHub
- Check the documentation in the code
- Review example scenarios in `examples/`

Happy deadlock hunting! 🔒🔍
