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
        """Process a chat conversation with tool support"""
        # Ensure system prompt is first
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": self.system_prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.MODEL,
            messages=messages,
            tools=self.tools.get_tools_schema(),
            max_tokens=8000,
        )
        
        message = response.choices[0].message
        result = {
            "content": message.content or "",
            "tool_calls": [],
            "reasoning": getattr(message, "reasoning_content", None) or ""
        }
        
        # Handle tool calls
        if message.tool_calls:
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                output = self.tools.execute(tc.function.name, args)
                result["tool_calls"].append({
                    "name": tc.function.name,
                    "arguments": args,
                    "output": output[:500] if len(output) > 500 else output
                })
        
        return result
    
    def run(self, user_message: str, history: Optional[List] = None) -> Dict[str, Any]:
        """Run a single turn with user message"""
        messages = history or []
        messages.append({"role": "user", "content": user_message})
        
        result = self.chat(messages)
        
        # Add assistant response to history
        messages.append({
            "role": "assistant",
            "content": result["content"],
            "tool_calls": result["tool_calls"]
        })
        
        return result
