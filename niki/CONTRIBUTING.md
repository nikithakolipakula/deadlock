# Contributing to Deadlock Detection Toolkit

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/deadlock-toolkit.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `.\venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (Unix)
5. Install dependencies: `pip install -r requirements-dev.txt`

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest tests/`
4. Run linters: `black . && ruff check .`
5. Commit your changes: `git commit -m "Description of changes"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for all public functions and classes
- Keep line length to 100 characters
- Use `black` for formatting
- Use `ruff` for linting

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Use pytest fixtures for common test setup

## Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in present tense (Add, Fix, Update, etc.)
- Reference issue numbers when applicable

## Pull Request Process

1. Update README.md with details of significant changes
2. Update documentation if you've changed APIs
3. The PR will be merged once you have approval from maintainers

## Reporting Bugs

- Use the GitHub issue tracker
- Describe the bug clearly
- Include steps to reproduce
- Provide system information (OS, Python version)
- Include error messages and stack traces

## Feature Requests

- Use the GitHub issue tracker
- Clearly describe the feature and its use case
- Explain why it would be useful

## Questions?

Open an issue with the "question" label.
