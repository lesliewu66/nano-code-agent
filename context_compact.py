"""
Context Compact - Three-layer compression pipeline
让 Agent 能永远工作下去，通过策略性地遗忘：
    Layer 1: micro_compact - 静默压缩旧 tool results
    Layer 2: auto_compact  - Token 超限自动总结
    Layer 3: compact tool  - 手动触发总结
"""
import json
import time
from pathlib import Path
from config import WORKDIR, client, MODEL

TRANSCRIPT_DIR = WORKDIR / ".transcripts"
KEEP_RECENT = 3


def estimate_tokens(messages: list) -> int:
    """粗略估算 token: ~4 字符/token"""
    return len(str(messages)) // 4


def micro_compact(messages: list) -> None:
    """
    Layer 1: 静默压缩 - 每轮调用
    将旧的 tool_result 内容替换为占位符
    """
    # 收集所有 tool_result 的索引
    tool_results = []
    for msg_idx, msg in enumerate(messages):
        if msg.get("role") == "tool":
            tool_results.append((msg_idx, msg))
    
    if len(tool_results) <= KEEP_RECENT:
        return
    
    # 构建 tool_use_id -> tool_name 映射
    tool_name_map = {}
    for msg in messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tool_name_map[tc.get("id")] = tc.get("function", {}).get("name", "unknown")
    
    # 清空旧结果（保留最近 KEEP_RECENT 个）
    to_clear = tool_results[:-KEEP_RECENT]
    for msg_idx, msg in to_clear:
        content = msg.get("content", "")
        tool_id = msg.get("tool_call_id", "")
        tool_name = tool_name_map.get(tool_id, "unknown")
        
        # 只压缩长内容
        if isinstance(content, str) and len(content) > 100:
            msg["content"] = f"[Previous: used {tool_name}]"


def auto_compact(messages: list) -> None:
    """
    Layer 2: 自动压缩 - Token 超限时调用
    保存完整转录，用 LLM 总结，替换 messages
    """
    TRANSCRIPT_DIR.mkdir(exist_ok=True)
    transcript_path = TRANSCRIPT_DIR / f"transcript_{int(time.time())}.jsonl"
    
    # 保存完整转录
    with open(transcript_path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    print(f"\033[90m[transcript saved: {transcript_path}]\033[0m")
    
    # 调用 LLM 总结
    conversation_text = json.dumps(messages, default=str)[:80000]
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": (
                "Summarize this conversation for continuity. Include:\n"
                "1) What was accomplished\n"
                "2) Current state\n"
                "3) Key decisions made\n"
                "Be concise but preserve critical details.\n\n" + conversation_text
            )
        }],
        max_tokens=2000,
    )
    summary = response.choices[0].message.content
    
    # 替换所有消息为压缩后的总结
    messages[:] = [
        {
            "role": "user",
            "content": f"[Conversation compressed. Transcript: {transcript_path}]\n\n{summary}"
        },
        {
            "role": "assistant",
            "content": "Understood. I have the context from the summary. Continuing."
        },
    ]


def compact_tool(focus: str = None) -> str:
    """
    Layer 3: 手动压缩工具 - 由 Agent 调用
    返回标记，实际压缩在 agent_loop 中执行
    """
    return "Manual compression requested."
