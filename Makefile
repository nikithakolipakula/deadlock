# Makefile for Deadlock Toolkit
# Cross-platform commands using PowerShell

.PHONY: help install test lint format clean run-simple run-server

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make run-simple   - Run simple scenario"
	@echo "  make run-server   - Start web server"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=engine --cov=simulator --cov=visualizer --cov-report=html --cov-report=term

lint:
	ruff check .
	mypy engine/ simulator/ visualizer/ --ignore-missing-imports

format:
	black .
	ruff check . --fix

clean:
	Remove-Item -Recurse -Force -ErrorAction SilentlyContinue __pycache__,*.pyc,.pytest_cache,.mypy_cache,htmlcov,.coverage,dist,build,*.egg-info

run-simple:
	python -m simulator.run --simple --verbose

run-server:
	python -m visualizer.app

run-example:
	python -m simulator.run --scenario examples/simple_deadlock.json --verbose

run-banker:
	python -m simulator.run --scenario examples/banker_safe.json --policy bankers --verbose
