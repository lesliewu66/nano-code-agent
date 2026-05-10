"""Agent main class"""
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .config import Config
from .tools import ToolRegistry


class Agent:
    """Coding agent with tool use capabilities"""
    
    def __init__(self):
        self.config = Config()
        self.tools = ToolRegistry(self.config.WORKDIR)
        self.client = OpenAI(
            api_key=self.config.API_KEY,
            base_url=self.config.BASE_URL
        )
        self.system_prompt = f"""You are a coding agent at {self.config.WORKDIR}.
Use the available tools to solve tasks efficiently.
- bash: Run shell commands
- read_file: Read file contents
- write_file: Create or overwrite files
- edit_file: Modify existing files

Act directly, minimize explanations."""
    
    def chat(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a chat conversation with full tool-use loop."""
        MAX_TOOL_ITERATIONS = 10

        # Ensure system prompt is first
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        all_tool_calls: List[Dict[str, Any]] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.client.chat.completions.create(
                model=self.config.MODEL,
                messages=messages,
                tools=self.tools.get_tools_schema(),
                max_tokens=8000,
            )

            message = response.choices[0].message

            if not message.tool_calls:
                # Final response — no more tool calls
                messages.append({"role": "assistant", "content": message.content})
                return {
                    "content": message.content or "",
                    "tool_calls": all_tool_calls,
                    "reasoning": getattr(message, "reasoning_content", None) or ""
                }

            # Append properly formatted assistant message with tool_calls
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool and append results
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                output = self.tools.execute(tc.function.name, args)

                all_tool_calls.append({
                    "name": tc.function.name,
                    "arguments": args,
                    "output": output[:500] if len(output) > 500 else output
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": output
                })

            # Loop back: model sees tool results on next API call

        # Max iterations exceeded
        return {
            "content": f"Max iterations ({MAX_TOOL_ITERATIONS}) exceeded. Task may be incomplete.",
            "tool_calls": all_tool_calls,
            "reasoning": ""
        }

    def run(self, user_message: str, history: Optional[List] = None) -> Dict[str, Any]:
        """Run a single turn with user message — delegates to chat() for tool loop."""
        messages = history or []
        messages.append({"role": "user", "content": user_message})
        return self.chat(messages)
