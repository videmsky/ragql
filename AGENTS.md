# Agent Guidelines for ragql

## Build/Test Commands
- **Run main script**: `uv run main.py` or `python3 main.py`
- **Install dependencies**: `uv sync` (manages virtual environment automatically)
- **Add dependencies**: `uv add <package>` for runtime, `uv add --dev <package>` for dev dependencies
- **No test framework configured** - use `uv add --dev pytest` to add testing
- **No linting/formatting tools configured** - consider `uv add --dev ruff` for linting/formatting

## Project Structure
- UV-managed Python project with minimal setup
- Main entry point: `main.py`
- Python 3.13+ required (see pyproject.toml)
- No external dependencies currently
- UV handles virtual environment and dependency management automatically

## Code Style Guidelines
- **Python version**: 3.13+
- **Naming**: Use snake_case for functions/variables, PascalCase for classes
- **Imports**: Standard library first, then third-party, then local imports
- **Functions**: Include docstrings for non-trivial functions
- **Error handling**: Use appropriate exception types, avoid bare except clauses
- **Type hints**: Add type annotations for function parameters and return values
- **Line length**: Keep reasonable (80-100 characters)

## Notes
- This is a minimal UV-managed Python project without established tooling
- Use `uv add --dev` to add development tools like pytest, ruff, and mypy
- UV automatically manages virtual environments and lockfiles
- No existing Cursor/Copilot rules found