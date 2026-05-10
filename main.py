#!/usr/bin/env python3
"""RouteAgent - CLI and HTTP server entry point"""
import sys
import argparse
from route_agent.core.config import Config
from route_agent.core.agent import Agent


def run_cli():
    """Run interactive CLI mode"""
    try:
        Config.ensure_dirs()
    except SystemExit as e:
        sys.exit(e.code)
    agent = Agent()
    
    print(f"RouteAgent v1.0.0")
    print(f"Working directory: {Config.WORKDIR}")
    print("Type 'exit' or 'quit' to exit\n")
    
    history = [{"role": "system", "content": agent.system_prompt}]
    
    while True:
        try:
            query = input("\033[36magent> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        
        if query.strip().lower() in ("q", "exit", "quit", ""):
            break
        
        result = agent.run(query, history)
        
        # Print reasoning if available
        if result.get("reasoning"):
            print(f"\033[90m[Reasoning] {result['reasoning'][:200]}...\033[0m")
        
        # Print tool calls
        for tc in result.get("tool_calls", []):
            print(f"\033[33m[Tool] {tc['name']}: {tc['output'][:100]}...\033[0m")
        
        # Print response
        if result["content"]:
            print(f"\n{result['content']}\n")


def run_server():
    """Run HTTP API server"""
    import uvicorn
    from route_agent.api.server import create_app
    
    Config.ensure_dirs()
    app = create_app()
    
    print(f"Starting server on http://{Config.HOST}:{Config.PORT}")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)


def main():
    parser = argparse.ArgumentParser(description="RouteAgent")
    parser.add_argument(
        "--mode",
        choices=["cli", "server"],
        default="cli",
        help="Run mode: cli (interactive) or server (HTTP API)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "cli":
        run_cli()
    else:
        run_server()


if __name__ == "__main__":
    main()
