import json
from config import client, MODEL, SUBAGENT_SYSTEM
from tools import CHILD_TOOLS, TOOL_HANDLERS


def _log(label: str, text: str, color: int = 0) -> None:
    if not text:
        return
    prefix = f"\033[{color}m[{label}]\033[0m"
    for line in text.splitlines():
        print(f"{prefix} {line}")


def run_subagent(prompt: str) -> str:
    sub_messages = [
        {"role": "system", "content": SUBAGENT_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    for _ in range(30):
        print("\033[90m  --- subagent LLM call ---\033[0m")
        response = client.chat.completions.create(
            model=MODEL, messages=sub_messages,
            tools=CHILD_TOOLS, max_tokens=8000,
        )
        message = response.choices[0].message

        reasoning = getattr(message, "reasoning_content", None) or ""
        if reasoning:
            _log("SUBAGENT_THINK", reasoning, color=35)

        content = message.content or ""
        if content:
            _log("SUBAGENT_ASSISTANT", content, color=34)

        sub_messages.append(message.model_dump())

        if not message.tool_calls:
            print("\033[90m  --- subagent done ---\033[0m")
            break

        results = []
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            _log("SUBAGENT_TOOL_CALL", f"{tool_call.function.name}({json.dumps(args, ensure_ascii=False)})", color=36)

            handler = TOOL_HANDLERS.get(tool_call.function.name)
            try:
                output = handler(**args) if handler else f"Unknown tool: {tool_call.function.name}"
            except Exception as e:
                output = f"Error: {e}"

            display = output if len(output) < 4000 else output[:4000] + "\n... (truncated)"
            _log("SUBAGENT_TOOL_RESULT", display, color=33)

            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output,
            })
        sub_messages.extend(results)
    else:
        print("\033[90m  --- subagent hit max rounds ---\033[0m")

    return message.content or "(no summary)"
