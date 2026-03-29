import json
from config import client, MODEL
from tools import TOOLS, TOOL_HANDLERS

def agent_loop(messages: list) -> None:
    rounds_since_todo = 0
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
        used_todo = False
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            handler = TOOL_HANDLERS.get(tool_call.function.name)
            try:
                output = handler(**args) if handler else f"Unknown tool: {tool_call.function.name}"
            except Exception as e:
                output = f"Error: {e}"
            print(f"\033[33m> {tool_call.function.name}: {output[:200]}\033[0m")
            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output,
            })
            if tool_call.function.name == "todo":
                used_todo = True
        rounds_since_todo = 0 if used_todo else rounds_since_todo + 1
        messages.extend(results)
        if rounds_since_todo >= 3:
            messages.append({"role": "user", "content": "<reminder>Update your todos.</reminder>"})
