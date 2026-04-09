# RouteAgent

A lightweight coding agent with HTTP API, built with OpenAI-compatible LLMs.

## Features

- **Tool Use**: Execute bash commands, read/write files
- **HTTP API**: RESTful interface for integration
- **Context Management**: Automatic conversation compression
- **Extensible**: Easy to add new tools

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/routeAgent.git
cd routeAgent

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Configuration

Create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `KIMI_API_KEY`: Your API key
- `KIMI_BASE_URL`: API base URL (default: https://api.moonshot.cn/v1)
- `MODEL_ID`: Model ID (default: kimi-k2-thinking)

### CLI Mode

```bash
python main.py --mode cli
```

### HTTP Server Mode

```bash
python main.py --mode server
# Or
uvicorn route_agent.api.server:create_app --reload
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### List Tools
```bash
curl http://localhost:8000/tools
```

### Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List files in current directory"}'
```

## Project Structure

```
routeAgent/
├── route_agent/          # Main package
│   ├── core/            # Core logic
│   │   ├── config.py    # Configuration
│   │   ├── agent.py     # Agent class
│   │   └── tools.py     # Tool registry
│   ├── api/             # HTTP API
│   │   └── server.py    # FastAPI app
│   └── utils/           # Utilities
├── skills/              # Skill definitions
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## Available Tools

- `bash`: Execute shell commands
- `read_file`: Read file contents
- `write_file`: Write files
- `edit_file`: Replace text in files

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black route_agent/
ruff check route_agent/

# Run tests
pytest
```

## License

MIT License - see LICENSE file
