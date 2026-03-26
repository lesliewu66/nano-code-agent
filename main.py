#!/usr/bin/env python3
from config import SYSTEM
from agent import agent_loop

if __name__ == "__main__":
    history = [{"role": "system", "content": SYSTEM}]
    while True:
        try:
            query = input("\033[36ms02 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        last_message = history[-1]
        if isinstance(last_message, dict):
            content = last_message.get("content")
            if content:
                print(content)
        print()
