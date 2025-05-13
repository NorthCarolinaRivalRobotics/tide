# Tide Framework Tests

This directory contains comprehensive tests for the Tide framework, including:

- Unit tests for core functionality
- Tests for message models and serialization
- Integration tests for node communication
- Property-based tests using Hypothesis

## Running Tests

To run all tests:

```bash
uv run pytest
```

To run a specific test module:

```bash
uv run pytest tests/test_core/test_node.py
```

To run tests with verbose output:

```bash
uv run pytest -v
```

## Test Structure

- `test_core/`: Tests for the core functionality (node, utils)
- `test_models/`: Tests for message models and serialization
- `test_integration/`: Tests for multi-node communication

## Property-Based Testing

Some tests use Hypothesis for property-based testing, which generates a diverse range of inputs to test functionality more thoroughly.

These tests are marked with `@given` decorators and typically verify that certain properties hold across a range of inputs.

## Test Coverage

To run tests with coverage:

```bash
uv run pytest --cov=tide
```

For HTML coverage report:

```bash
uv run pytest --cov=tide --cov-report=html
``` 