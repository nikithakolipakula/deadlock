# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-25

### Added
- Initial release of Deadlock Detection & Recovery Toolkit
- Core detection engine with Banker's Algorithm
- Wait-for graph cycle detection
- Resource Allocation Graph (RAG) construction and analysis
- Prevention policies:
  - Banker's Algorithm
  - Resource ordering
  - Conservative allocation
- Recovery policies:
  - Preemption (lowest priority)
  - Preemption (minimal cost)
  - Process termination
- CLI simulator with JSON/YAML scenario support
- Web dashboard with real-time visualization
- Example scenarios:
  - Simple two-process deadlock
  - Dining philosophers problem
  - Banker's algorithm demonstrations
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
- Documentation and examples

### Features
- Real-time deadlock detection
- Interactive scenario simulation
- Step-by-step execution mode
- WebSocket-based live updates
- State snapshots and event logging
- Graph visualization support
- Export capabilities

[0.1.0]: https://github.com/yourusername/deadlock-toolkit/releases/tag/v0.1.0
