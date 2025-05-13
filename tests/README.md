# Tide Framework Tests

This directory contains tests for the Tide framework.

## Test Structure

- `test_core/`: Tests for core framework functionality
- `test_integration/`: Integration tests between components
- `test_models/`: Tests for model components

## Running Tests

To run all tests:

```bash
uv run pytest
```

To run specific test files:

```bash
uv run pytest tests/test_core/test_node.py
```

To run specific test classes or methods:

```bash
uv run pytest tests/test_core/test_node.py::TestBaseNode::test_initialization
```

## Writing Tests

When writing tests:

1. Place tests in the appropriate directory based on what they test
2. Use pytest fixtures from conftest.py where possible
3. Clean up resources in your tests to avoid conflicts with other tests
4. Use meaningful assertions that help understand failures

For asynchronous code testing, prefer using proper pytest-async techniques over simple time.sleep() calls where possible. 