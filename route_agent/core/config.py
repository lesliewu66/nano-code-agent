"""Configuration management"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # Paths
    WORKDIR = Path(os.getcwd())
    DATA_DIR = WORKDIR / ".data"

    # LLM
    MODEL = os.getenv("MODEL_ID", "deepseek-chat")
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # Context
    COMPACT_THRESHOLD = int(os.getenv("COMPACT_THRESHOLD", "50000"))

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    @classmethod
    def validate(cls):
        """Validate required configuration at startup. Exits with code 1 if invalid."""
        if not cls.API_KEY:
            print("Error: DEEPSEEK_API_KEY is not set.")
            print("Create a .env file in the project root with:")
            print("  DEEPSEEK_API_KEY=your-api-key-here")
            print("See .env.example for all available options.")
            raise SystemExit(1)

    @classmethod
    def ensure_dirs(cls):
        """Ensure required directories exist"""
        cls.validate()
        cls.DATA_DIR.mkdir(exist_ok=True)
        (cls.DATA_DIR / "tasks").mkdir(exist_ok=True)
        (cls.DATA_DIR / "sessions").mkdir(exist_ok=True)
