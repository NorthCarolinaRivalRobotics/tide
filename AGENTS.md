# AI Agent Onboarding Guide: Tide Project

This document provides instructions for an AI agent to set up and work with the Tide project.

## Project Overview

Tide is a lightweight, strongly-typed framework for robotics based on Zenoh, with opinionated namespacing. It allows for building robot control systems with nodes that communicate over a shared Zenoh session using an asyncio-based architecture. Key features include:

- Opinionated namespacing: `/{robot_id}/{group}/{topic}`
- Zero-config networking via Zenoh peer discovery.
- Strongly-typed messages using Pydantic models.
- Callback-based message handling.
- A command-line interface (`tide`) for project management.

## Environment Setup

This project uses `uv` for Python package management and task running.

1.  **Install Dependencies**:
    To set up the development environment and install all necessary dependencies, execute the `install-deps.bash` script located in the project root:

    ```bash
    chmod +x install-deps.bash
    ./install-deps.bash
    ```
    This script will:
    *   Install `uv` if it's not already present.
    *   Use `uv sync` to install all project dependencies as defined in `uv.lock`.

## Running the Project

The project is typically run using the `tide` CLI or by directly executing Python scripts with `uv run`.

### Using the Tide CLI

The Tide framework includes a CLI for managing projects. For example, to start a Tide project (assuming a `config.yaml` is present):

```bash
tide up
```

Or to specify a custom configuration:

```bash
tide up --config path/to/your_config.yaml
```

To check the status of running Tide nodes:

```bash
tide status
```

### Running Python Scripts

You can run individual Python scripts using `uv run`:

```bash
uv run python_script_name.py
```
For example, to run the main entry point of a project (if structured as such):
```bash
uv run main.py
```

## Running Tests

Tests are written using `pytest`. To execute the test suite:

```bash
uv run pytest
```

## Run with Coverage 

```bash
uv run pytest --cov --cov-report=xml --cov-report=term-missing
```

## Key Files and Directories

-   `pyproject.toml`: Defines project metadata and dependencies for `uv`.
-   `uv.lock`: Pinned versions of all dependencies.
-   `install-deps.bash`: Script for initial environment setup.
-   `tide/`: Contains the core framework code.
-   `cli/`: Contains the command-line interface code.
-   `models/`: Contains Pydantic models for message types.
-   `examples/`: Contains example usage of the Tide framework.
-   `tests/`: Contains project tests.
-   `config/` (in generated projects): Typically contains node configurations (e.g., `config.yaml`).
-   `nodes/` (in generated projects): Typically contains custom robot node implementations. 


## Project Standards
- When making breaking changes you must also update documentation (doc strings or .md files in /docs).
- If you make public facing api changes then you should also make sure the examples are properly up to date.

### Integration Testing Guidelines

Integration tests should exercise real Zenoh communication. Avoid standalone
"dummy" publishers in unit tests. Instead, launch nodes through a configuration
using `launch_from_config()` (or the `tide up` CLI) so the entire Tide process
is involved in the test.

### Testing Consistency

Hypothesis-based tests may generate example databases in `.hypothesis/`
directories. Do **not** add these directories to `.gitignore`; keeping them
ensures repeatable test runs across environments.
