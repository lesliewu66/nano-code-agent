"""Tool registry - essential tools only"""
import subprocess
from pathlib import Path
from typing import Callable, Dict, Any


class ToolRegistry:
    """Registry of available tools"""
    
    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.handlers: Dict[str, Callable] = {}
        self._register_defaults()
    
    def _safe_path(self, p: str) -> Path:
        """Ensure path is within workspace"""
        path = (self.workdir / p).resolve()
        if not path.is_relative_to(self.workdir):
            raise ValueError(f"Path escapes workspace: {p}")
        return path
    
    def _register_defaults(self):
        """Register default tools"""
        self.handlers = {
            "bash": self._bash,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "edit_file": self._edit_file,
        }
    
    def _bash(self, command: str, **kwargs) -> str:
        """Execute shell command"""
        dangerous = ["rm -rf /", "sudo", "shutdown", "reboot"]
        if any(d in command for d in dangerous):
            return "Error: Dangerous command blocked"
        try:
            r = subprocess.run(
                command, shell=True, cwd=self.workdir,
                capture_output=True, text=True, timeout=120
            )
            out = (r.stdout + r.stderr).strip()
            return out[:50000] if out else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Timeout (120s)"
    
    def _read_file(self, path: str, limit: int = None, **kwargs) -> str:
        """Read file contents"""
        try:
            text = self._safe_path(path).read_text()
            lines = text.splitlines()
            if limit and limit < len(lines):
                lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
            return "\n".join(lines)[:50000]
        except Exception as e:
            return f"Error: {e}"
    
    def _write_file(self, path: str, content: str, **kwargs) -> str:
        """Write file"""
        try:
            fp = self._safe_path(path)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)
            return f"Wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error: {e}"
    
    def _edit_file(self, path: str, old_text: str, new_text: str, **kwargs) -> str:
        """Edit file by replacing text"""
        try:
            fp = self._safe_path(path)
            content = fp.read_text()
            if old_text not in content:
                return f"Error: Text not found in {path}"
            fp.write_text(content.replace(old_text, new_text, 1))
            return f"Edited {path}"
        except Exception as e:
            return f"Error: {e}"
    
    def get_tools_schema(self) -> list:
        """Get OpenAI-compatible tools schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Run a shell command",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string"}},
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read file contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "limit": {"type": "integer"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Replace text in file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "old_text": {"type": "string"},
                            "new_text": {"type": "string"}
                        },
                        "required": ["path", "old_text", "new_text"]
                    }
                }
            },
        ]
    
    def execute(self, name: str, arguments: dict) -> str:
        """Execute a tool by name"""
        handler = self.handlers.get(name)
        if not handler:
            return f"Error: Unknown tool '{name}'"
        try:
            return handler(**arguments)
        except Exception as e:
            return f"Error: {e}"
