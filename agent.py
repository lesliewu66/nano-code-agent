import json
from config import client, MODEL
from tools import TOOLS, TOOL_HANDLERS
from subagent import run_subagent

def _log(label: str, text: str, color: int = 0) -> None:
    if not text:
        return
    prefix = f"\033[{color}m[{label}]\033[0m"
    for line in text.splitlines():
        print(f"{prefix} {line}")

def agent_loop(messages: list) -> None:
    rounds_since_todo = 0
    while True:
        print("\033[90m--- LLM call ---\033[0m")
        response = client.chat.completions.create(
            model=MODEL, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        message = response.choices[0].message

        # thinking / reasoning
        reasoning = getattr(message, "reasoning_content", None) or ""
        if reasoning:
            _log("THINK", reasoning, color=35)

        content = message.content or ""
        if content:
            _log("ASSISTANT", content, color=34)

        messages.append(message.model_dump())

        if not message.tool_calls:
            print("\033[90m--- done (no tools) ---\033[0m")
            return

        results = []
        used_todo = False
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            _log("TOOL_CALL", f"{tool_call.function.name}({json.dumps(args, ensure_ascii=False)})", color=36)

            if tool_call.function.name == "task":
                desc = args.get("description", "subtask")
                print(f"\033[90m  >> dispatching subagent: {desc}\033[0m")
                output = run_subagent(args["prompt"])
            else:
                handler = TOOL_HANDLERS.get(tool_call.function.name)
                try:
                    output = handler(**args) if handler else f"Unknown tool: {tool_call.function.name}"
                except Exception as e:
                    output = f"Error: {e}"

            # print full output but cap extremely long ones
            display = output if len(output) < 4000 else output[:4000] + "\n... (truncated)"
            _log("TOOL_RESULT", display, color=33)

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
