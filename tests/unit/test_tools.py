"""Tests for ToolRegistry class"""
import tempfile
from pathlib import Path

from route_agent.core.tools import ToolRegistry


class TestToolRegistry:
    """Test tool registration and execution"""

    def setup_method(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.registry = ToolRegistry(self.tmpdir)

    def test_has_default_tools(self):
        schema = self.registry.get_tools_schema()
        names = [t["function"]["name"] for t in schema]
        assert "bash" in names
        assert "read_file" in names
        assert "write_file" in names
        assert "edit_file" in names

    def test_unknown_tool(self):
        result = self.registry.execute("nonexistent", {})
        assert "Error" in result
        assert "Unknown tool" in result

    def test_safe_path_inside_workspace(self):
        p = self.registry._safe_path("test.txt")
        assert p == (self.tmpdir / "test.txt").resolve()

    def test_safe_path_rejects_escape(self):
        import pytest
        with pytest.raises(ValueError, match="escapes workspace"):
            self.registry._safe_path("../outside.txt")

    def test_bash_blocked_command(self):
        result = self.registry._bash("rm -rf /")
        assert "blocked" in result

    def test_read_file_not_found(self):
        result = self.registry.execute("read_file", {"path": "nonexistent.txt"})
        assert "Error" in result

    def test_write_and_read_file(self):
        write_result = self.registry.execute("write_file", {
            "path": "hello.txt",
            "content": "Hello, World!"
        })
        assert "Wrote" in write_result

        read_result = self.registry.execute("read_file", {"path": "hello.txt"})
        assert "Hello, World!" in read_result

    def test_edit_file(self):
        self.registry.execute("write_file", {
            "path": "edit_test.txt",
            "content": "Old content"
        })
        edit_result = self.registry.execute("edit_file", {
            "path": "edit_test.txt",
            "old_text": "Old",
            "new_text": "New"
        })
        assert "Edited" in edit_result

        content = (self.tmpdir / "edit_test.txt").read_text()
        assert content == "New content"

    def test_edit_file_text_not_found(self):
        self.registry.execute("write_file", {
            "path": "no_match.txt",
            "content": "Some content"
        })
        result = self.registry.execute("edit_file", {
            "path": "no_match.txt",
            "old_text": "DoesNotExist",
            "new_text": "Replacement"
        })
        assert "Error" in result
        assert "not found" in result
