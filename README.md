# RouteAgent

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A lightweight coding agent with tool-use capabilities and HTTP API, built with OpenAI-compatible LLMs. Designed for extensibility — add new tools, endpoints, and capabilities as you follow tutorials or experiment.

## Features

- **Tool Use**: Execute shell commands, read/write/edit files within a sandboxed workspace
- **HTTP API**: RESTful interface for integration with other tools and automation
- **CLI Mode**: Interactive REPL for direct agent interaction
- **Extensible**: Easy to add new tools and API endpoints
- **Configurable**: Supports any OpenAI-compatible API provider

## Quick Start

### Prerequisites

- Python 3.9+
- An API key from an OpenAI-compatible provider (e.g., [DeepSeek](https://platform.deepseek.com/))

### Installation

```bash
# Clone the repository
git clone https://github.com/lesliewu66/routeAgent.git
cd routeAgent

# Create and configure environment
cp .env.example .env
# Edit .env with your API key — DEEPSEEK_API_KEY=sk-your-key-here

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

All configuration is via environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | Yes | — | Your API key for the LLM provider |
| `DEEPSEEK_BASE_URL` | No | `https://api.deepseek.com` | API base URL (swap for any OpenAI-compatible provider) |
| `MODEL_ID` | No | `deepseek-chat` | Model identifier |
| `HOST` | No | `0.0.0.0` | HTTP server bind address |
| `PORT` | No | `8000` | HTTP server port |
| `COMPACT_THRESHOLD` | No | `50000` | Context compression trigger (characters) |

### CLI Mode

```bash
python main.py --mode cli
```

You'll see an `agent>` prompt. Type natural language commands:

```
agent> List files in the current directory
agent> Read the contents of main.py
agent> exit
```

### HTTP Server Mode

```bash
python main.py --mode server
```

The server starts on `http://localhost:8000` by default.

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "1.0.0"}
```

### List Tools

```bash
curl http://localhost:8000/tools
```

### Chat with the Agent

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List files in current directory"}'
```

## Project Structure

```
routeAgent/
├── route_agent/              # Main package
│   ├── core/                 # Core agent logic
│   │   ├── config.py         # Configuration management
│   │   ├── agent.py          # Agent orchestration + tool loop
│   │   └── tools.py          # Tool registry with file/bash operations
│   ├── api/                  # HTTP API layer
│   │   └── server.py         # FastAPI routes
│   └── tools/                # Extensible tool modules (add yours here)
├── tests/                    # Test suite
│   ├── unit/
│   └── integration/
├── main.py                   # CLI + server entry point
├── pyproject.toml            # Package config and tool settings
└── README.md
```

## Available Tools

| Tool | Description |
|------|-------------|
| `bash` | Execute shell commands (120s timeout, sandboxed to workspace) |
| `read_file` | Read file contents with optional line limit |
| `write_file` | Create or overwrite files |
| `edit_file` | Replace text in existing files |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check route_agent/

# Run tests with coverage
pytest --cov=route_agent
```

## Tutorial Extensions

This project is structured for incremental learning. New capabilities (tools, memory, plugins) can be added as separate modules without modifying existing code. See `route_agent/tools/__init__.py` for the extension pattern.

## License

MIT License — see [LICENSE](LICENSE) for details.
