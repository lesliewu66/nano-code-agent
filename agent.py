import json
from config import client, MODEL
from tools import TOOLS, TOOL_HANDLERS

def agent_loop(messages: list) -> None:
    while True:
        response = client.chat.completions.create(
            model=MODEL, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        message = response.choices[0].message
        messages.append(message.model_dump())
        if not message.tool_calls:
            return
        results = []
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            handler = TOOL_HANDLERS.get(tool_call.function.name)
            output = handler(**args) if handler else f"Unknown tool: {tool_call.function.name}"
            print(f"\033[33m> {tool_call.function.name}: {output[:200]}\033[0m")
            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output,
            })
        messages.extend(results)
