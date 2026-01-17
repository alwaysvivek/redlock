# Contributing to redlock-py

First off, thanks for taking the time to contribute!

## Development Setup

1.  **Install Poetry**:
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

2.  **Install Dependencies**:
    ```bash
    poetry install
    ```

3.  **Start Infrastructure**:
    ```bash
    docker-compose up -d
    ```

4.  **Run Tests**:
    ```bash
    poetry run pytest
    ```

## Style Guide

We use strict static analysis. Before submitting a PR, ensure:
-   `ruff check .` passes.
-   `mypy .` passes.
-   `pytest` passes (including integration check).

## Pull Requests

1.  Fork the repo and create your branch from `main`.
2.  If you've added code that should be tested, add tests.
3.  Ensure the test suite passes.
4.  Make sure your code lints.
