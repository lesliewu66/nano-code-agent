"""Configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WORKDIR = Path(os.getcwd())
DATA_DIR = WORKDIR / ".data"
DATA_DIR.mkdir(exist_ok=True)

# LLM Config
MODEL = os.getenv("MODEL_ID", "kimi-k2-thinking")
API_KEY = os.getenv("KIMI_API_KEY")
BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
