.PHONY: install install-dev test lint clean build upload

# Install runtime dependencies
install:
	pip install .

# Install both runtime and development dependencies
install-dev:
	pip install .[dev]

# Run tests
test:
	pytest

# Lint the codebase with Ruff
lint:
	ruff check logos_shift_client

# Clean up build artifacts
clean:
	rm -rf dist build *.egg-info

# Build the package
build: clean
	python setup.py sdist bdist_wheel

# Upload the package to PyPI
upload:
	twine upload dist/*

# Run all the above commands (except upload) in order
all: install-dev lint test build

