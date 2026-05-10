# Contributing to RouteAgent

Thank you for your interest! This project is a portfolio / learning project, and contributions, suggestions, and feedback are welcome.

## Getting Started

```bash
# Clone and set up
git clone https://github.com/lesliewu66/routeAgent.git
cd routeAgent
cp .env.example .env
# Edit .env with your API key
pip install -e ".[dev]"
```

## Development Workflow

### Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting:

```bash
ruff check route_agent/ tests/
```

### Testing

Tests use [pytest](https://docs.pytest.org/) with coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=route_agent

# Run specific test file
pytest tests/unit/test_tools.py -v
```

### Pre-commit Checks

Before committing, run:

```bash
ruff check route_agent/ tests/
pytest --cov=route_agent
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes and write/update tests
3. Ensure all checks pass (lint + tests)
4. Submit a PR with a clear description of changes
5. Keep PRs focused — one feature or fix per PR

## Adding a New Tool

See `route_agent/tools/__init__.py` for the extension pattern.

## Adding a New API Endpoint

See `route_agent/api/server.py` for the extension pattern.

## Reporting Issues

Use the GitHub issue templates to report bugs or suggest features.
