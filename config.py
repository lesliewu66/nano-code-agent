import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

_ = load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("KIMI_API_KEY"),
    base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
)
MODEL = os.getenv("MODEL_ID", "kimi-k2-thinking")
WORKDIR = Path(os.getcwd())
SYSTEM = f"You are a coding agent at {WORKDIR}. Use tools to solve tasks. Act, don't explain. Use the task tool to delegate exploration or subtasks."
SUBAGENT_SYSTEM = f"You are a coding subagent at {WORKDIR}. Complete the given task, then summarize your findings."
