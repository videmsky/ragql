# Agent Guidelines for ragql

## Build/Test Commands
- **Install dependencies**: `uv sync` (manages virtual environment automatically)
- **Run main script**: `uv run python -m ragql.cli` or `ragql` (after install)
- **Run tests**: `uv run pytest` (pytest available in dev dependencies)
- **Run single test**: `uv run pytest tests/test_filename.py::test_function_name`
- **Linting**: `uv run ruff check .` (ruff available in dev dependencies)
- **Formatting**: `uv run black .` (black available in dev dependencies) 
- **Type checking**: `uv run mypy src/ragql` (mypy available in dev dependencies)

## Project Structure
- UV-managed Python project with LangChain, Mistral AI, and Neon PostgreSQL
- Main package: `src/ragql/` with CLI entry point at `ragql.cli:main`
- Tests directory: `tests/` (minimal setup currently)
- Python 3.13+ required, uses modern dependency management

## Code Style Guidelines
- **Python version**: 3.13+
- **Formatting**: Black-compatible (line length ~88 chars)
- **Linting**: Ruff for fast Python linting
- **Type hints**: Use type annotations for all function parameters and returns
- **Imports**: Standard library, third-party (langchain, click, etc.), then local imports
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Docstrings**: Google style docstrings for public functions and classes
- **Error handling**: Use specific exception types, avoid bare except clauses
- **Async code**: Use async/await pattern with proper error handling for database operations

## Notes
- RAG-based text-to-SQL system using Mistral AI and PostgreSQL
- UV handles virtual environments and lockfiles automatically
- Dev dependencies include pytest, black, ruff, and mypy for complete development workflow
