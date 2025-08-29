# Makefile for encos_sdk

.PHONY: help install test clean lint format run-examples run-cli

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install the package and dependencies"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean up build artifacts"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code"
	@echo "  run-examples - Run example scripts"
	@echo "  run-cli     - Run CLI tool"
	@echo "  help        - Show this help"

# Install package and dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Run tests
test:
	python test_sdk.py

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run linting (if flake8 is available)
lint:
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 encos_sdk/ --count --select=E9,F63,F7,F82 --show-source --statistics; \
		flake8 encos_sdk/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics; \
	else \
		echo "flake8 not found, skipping lint check"; \
	fi

# Format code (if black is available)
format:
	@if command -v black >/dev/null 2>&1; then \
		black encos_sdk/ --line-length=100; \
	else \
		echo "black not found, skipping code formatting"; \
	fi

# Run examples
run-examples:
	python examples.py

# Run CLI tool help
run-cli:
	python cli_tool.py --help

# Development setup
dev-install:
	pip install -r requirements.txt
	pip install -e .[dev,cli]

# Build package
build:
	python setup.py sdist bdist_wheel

# Check package
check:
	python setup.py check --strict --metadata --restructuredtext
