# Makefile for encos_sdk

.PHONY: help install clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install the package"
	@echo "  clean       - Clean up build artifacts"
	@echo "  help        - Show this help"

# Install package
install:
	pip install -e .

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
