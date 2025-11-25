# Deadlock Detection & Recovery Toolkit

A comprehensive toolkit for detecting, preventing, and recovering from deadlocks in real-time. Implements classical algorithms like Banker's Algorithm and provides interactive visualizations of resource allocation graphs.

## Features

- **Real-time Deadlock Detection**: Banker's Algorithm and wait-for graph cycle detection
- **Prevention Strategies**: Resource ordering, conservative allocation, max claim enforcement
- **Recovery Mechanisms**: Process preemption, rollback, and intelligent termination policies
- **Interactive Simulation**: Create custom deadlock scenarios with JSON/YAML configuration
- **Visual Analytics**: Real-time Resource Allocation Graphs (RAG) and event timelines
- **Web Dashboard**: Monitor, control, and analyze deadlock scenarios through an intuitive UI

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Dashboard (UI)                    │
│          FastAPI + React + D3.js Visualization           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                  Simulator & Event API                   │
│         CLI + Scenario Runner + Event Dispatcher         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    Detection Engine                      │
│  State Management │ Banker's Algo │ RAG │ Policies      │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```powershell
# Clone the repository
git clone <repo-url>
cd niki

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Run a Sample Simulation

```powershell
# CLI simulation with step-by-step execution
python -m simulator.run --scenario examples/simple_deadlock.json --policy bankers --step

# Run with auto-recovery
python -m simulator.run --scenario examples/dining_philosophers.json --policy preempt --speed 1.0
```

### Launch Web Dashboard

```powershell
# Start the web server
python -m visualizer.app

# Open browser to http://localhost:8000
```

## Module Overview

### Engine (`engine/`)
Core deadlock detection and policy algorithms:
- `state.py` - System state management (processes, resources, allocations)
- `banker.py` - Banker's Algorithm implementation
- `rag.py` - Resource Allocation Graph construction and cycle detection
- `policies.py` - Prevention and recovery policy implementations

### Simulator (`simulator/`)
Scenario creation and execution:
- `run.py` - CLI entry point for simulations
- `scenario.py` - Scenario file parser and validator
- `dispatcher.py` - Event dispatcher and timeline manager

### Visualizer (`visualizer/`)
Web UI and graph rendering:
- `app.py` - FastAPI server with WebSocket support
- `static/` - React frontend with D3.js visualizations
- `graph_renderer.py` - Graph serialization utilities

### Examples (`examples/`)
Pre-built scenarios demonstrating various deadlock conditions:
- `simple_deadlock.json` - Basic two-process deadlock
- `dining_philosophers.json` - Classic dining philosophers problem
- `banker_safe.json` - Safe state demonstration
- `banker_unsafe.json` - Unsafe state requiring prevention

## Scenario File Format

```json
{
  "resources": [
    {"id": "R1", "units": 2},
    {"id": "R2", "units": 1}
  ],
  "processes": [
    {"id": "P1", "max": {"R1": 1, "R2": 1}},
    {"id": "P2", "max": {"R1": 2, "R2": 1}}
  ],
  "events": [
    {"time": 0, "type": "allocate", "proc": "P1", "res": "R1", "units": 1},
    {"time": 1, "type": "request", "proc": "P2", "res": "R1", "units": 1},
    {"time": 2, "type": "request", "proc": "P1", "res": "R2", "units": 1}
  ]
}
```

## API Usage

```python
from engine.state import SystemState
from engine.banker import is_safe_state
from engine.rag import build_resource_allocation_graph, detect_cycles

# Initialize system state
state = SystemState()
state.add_resource("R1", total_units=3)
state.add_process("P1", max_claims={"R1": 2})

# Check safety with Banker's Algorithm
safe, sequence = is_safe_state(state, process="P1", request={"R1": 1})
if safe:
    print(f"Safe sequence: {sequence}")

# Detect cycles in wait-for graph
rag = build_resource_allocation_graph(state)
cycles = detect_cycles(rag)
if cycles:
    print(f"Deadlock detected: {cycles}")
```

## Testing

```powershell
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=engine --cov=simulator --cov=visualizer tests/

# Run specific test module
pytest tests/test_banker.py -v
```

## Development

```powershell
# Install dev dependencies
pip install -r requirements-dev.txt

# Format code
black .

# Lint
ruff check .

# Type checking
mypy engine/ simulator/ visualizer/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- Banker's Algorithm: E. W. Dijkstra (1965)
- Resource Allocation Graph theory: Holt (1972)
- Dining Philosophers: E. W. Dijkstra (1971)

## Roadmap

- [x] Core detection engine with Banker's Algorithm
- [x] Wait-for graph cycle detection
- [x] CLI simulator with JSON scenarios
- [x] Web dashboard with real-time visualization
- [ ] Distributed deadlock detection (Chandy-Misra-Haas)
- [ ] ML-based risk prediction
- [ ] Performance profiling tools
- [ ] Kubernetes integration for container orchestration
