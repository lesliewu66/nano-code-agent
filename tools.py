import subprocess
from pathlib import Path
from config import WORKDIR
from todo import TodoManager
from skill_loader import SKILL_LOADER
from context_compact import compact_tool
from task_system import TASKS
from background_tasks import BG

TODO = TodoManager()

BASE_TOOLS = [
    {"type": "function", "function": {
        "name": "bash",
        "description": "Run a shell command.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read file contents.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]},
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write content to file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
    }},
    {"type": "function", "function": {
        "name": "edit_file",
        "description": "Replace exact text in file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]},
    }},
    {"type": "function", "function": {
        "name": "todo",
        "description": "Update task list. Track progress on multi-step tasks.",
        "parameters": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}}, "required": ["id", "text", "status"]}}}, "required": ["items"]},
    }},
]

CHILD_TOOLS = BASE_TOOLS

TOOLS = BASE_TOOLS + [
    {"type": "function", "function": {
        "name": "task",
        "description": "Spawn a subagent with fresh context. It shares the filesystem but not conversation history. Use this to delegate exploration or subtasks.",
        "parameters": {"type": "object", "properties": {
            "prompt": {"type": "string", "description": "Detailed instructions for the subagent."},
            "description": {"type": "string", "description": "Short description of the task for logging."},
        }, "required": ["prompt"]},
    }},
    {"type": "function", "function": {
        "name": "load_skill",
        "description": "Load specialized knowledge by name. Call this before tackling unfamiliar topics.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Skill name to load"},
        }, "required": ["name"]},
    }},
    {"type": "function", "function": {
        "name": "compact",
        "description": "Trigger manual conversation compression. Use when context is getting too long.",
        "parameters": {"type": "object", "properties": {
            "focus": {"type": "string", "description": "What to preserve in the summary (optional)"},
        }},
    }},
    {"type": "function", "function": {
        "name": "task_create",
        "description": "Create a new persistent task with optional description.",
        "parameters": {"type": "object", "properties": {
            "subject": {"type": "string", "description": "Short task title"},
            "description": {"type": "string", "description": "Detailed description"},
        }, "required": ["subject"]},
    }},
    {"type": "function", "function": {
        "name": "task_update",
        "description": "Update a task's status or dependencies. When status becomes 'completed', dependencies are auto-cleared.",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer", "description": "Task ID to update"},
            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "New status"},
            "addBlockedBy": {"type": "array", "items": {"type": "integer"}, "description": "Task IDs this task depends on"},
            "addBlocks": {"type": "array", "items": {"type": "integer"}, "description": "Task IDs blocked by this task"},
        }, "required": ["task_id"]},
    }},
    {"type": "function", "function": {
        "name": "task_list",
        "description": "List all tasks with their status and blockers.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "task_get",
        "description": "Get full details of a specific task by ID.",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer", "description": "Task ID to retrieve"},
        }, "required": ["task_id"]},
    }},
    {"type": "function", "function": {
        "name": "background_run",
        "description": "Run a command in background thread. Returns task_id immediately. Use for long-running commands (builds, tests, downloads).",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "Shell command to run in background"},
        }, "required": ["command"]},
    }},
    {"type": "function", "function": {
        "name": "check_background",
        "description": "Check background task status. Omit task_id to list all tasks.",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "string", "description": "Task ID to check (optional)"},
        }},
    }},
]

def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"

def run_read(path: str, limit: int | None = None) -> str:
    try:
        text = safe_path(path).read_text()
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"

def run_write(path: str, content: str) -> str:
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        fp = safe_path(path)
        content = fp.read_text()
        if old_text not in content:
            return f"Error: Text not found in {path}"
        fp.write_text(content.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"

TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
    "todo":       lambda **kw: TODO.update(kw["items"]),
    "load_skill": lambda **kw: SKILL_LOADER.get_content(kw["name"]),
    "compact":     lambda **kw: compact_tool(kw.get("focus")),
    "task_create": lambda **kw: TASKS.create(kw["subject"], kw.get("description", "")),
    "task_update": lambda **kw: TASKS.update(kw["task_id"], kw.get("status"), kw.get("addBlockedBy"), kw.get("addBlocks")),
    "task_list":   lambda **kw: TASKS.list_all(),
    "task_get":        lambda **kw: TASKS.get(kw["task_id"]),
    "background_run":  lambda **kw: BG.run(kw["command"]),
    "check_background":lambda **kw: BG.check(kw.get("task_id")),
}
