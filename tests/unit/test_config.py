"""Tests for Config class"""
import os
from pathlib import Path

from route_agent.core.config import Config


class TestConfigDefaults:
    """Test default configuration values"""

    def test_workdir_is_cwd(self):
        assert Config.WORKDIR == Path(os.getcwd())

    def test_base_url_default(self):
        assert Config.BASE_URL == "https://api.deepseek.com"

    def test_model_default(self):
        assert Config.MODEL == "deepseek-chat"

    def test_host_default(self):
        assert Config.HOST == "0.0.0.0"

    def test_port_default(self):
        assert Config.PORT == 8000

    def test_compact_threshold_default(self):
        assert Config.COMPACT_THRESHOLD == 50000


class TestConfigDirectories:
    """Test directory management"""

    def test_data_dir_exists(self):
        Config.ensure_dirs()
        assert Config.DATA_DIR.exists()
        assert (Config.DATA_DIR / "tasks").exists()
        assert (Config.DATA_DIR / "sessions").exists()
