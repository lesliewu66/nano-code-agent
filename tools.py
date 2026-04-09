import subprocess
from pathlib import Path
from config import WORKDIR
from todo import TodoManager
from skill_loader import SKILL_LOADER
from context_compact import compact_tool
from task_system import TASKS
from background_tasks import BG
from agent_teams import (
    TEAM, BUS, VALID_MSG_TYPES, 
    handle_shutdown_request, check_shutdown_status, handle_plan_review,
    scan_unclaimed_tasks, claim_task
)
from worktree_manager import init_worktrees, EVENTS, WORKTREES
init_worktrees()

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
        "name": "task_bind_worktree",
        "description": "Bind a task to a worktree and optionally set owner.",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer", "description": "Task ID"},
            "worktree": {"type": "string", "description": "Worktree name"},
            "owner": {"type": "string", "description": "Owner name (optional)"},
        }, "required": ["task_id", "worktree"]},
    }},
    {"type": "function", "function": {
        "name": "task_unbind_worktree",
        "description": "Unbind worktree from a task.",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer", "description": "Task ID"},
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
    {"type": "function", "function": {
        "name": "spawn_teammate",
        "description": "Spawn a persistent teammate that runs in its own thread. The teammate has its own agent loop and can communicate via messages.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Unique name for the teammate"},
            "role": {"type": "string", "description": "Role description (e.g., 'coder', 'reviewer')"},
            "prompt": {"type": "string", "description": "Initial task/instructions for the teammate"},
        }, "required": ["name", "role", "prompt"]},
    }},
    {"type": "function", "function": {
        "name": "list_teammates",
        "description": "List all teammates with their name, role, and current status.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "send_message",
        "description": "Send a message to a teammate's inbox.",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "string", "description": "Recipient name"},
            "content": {"type": "string", "description": "Message content"},
            "msg_type": {"type": "string", "enum": ["message", "broadcast", "shutdown_request", "shutdown_response", "plan_approval_response"], "description": "Message type"},
        }, "required": ["to", "content"]},
    }},
    {"type": "function", "function": {
        "name": "broadcast",
        "description": "Send a message to all teammates.",
        "parameters": {"type": "object", "properties": {
            "content": {"type": "string", "description": "Message to broadcast"},
        }, "required": ["content"]},
    }},
    {"type": "function", "function": {
        "name": "shutdown_teammate",
        "description": "Shutdown a teammate or all teammates immediately (force shutdown).",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Teammate name (omit to shutdown all)"},
        }},
    }},
    {"type": "function", "function": {
        "name": "shutdown_request",
        "description": "Request a teammate to shut down gracefully (protocol). Teammate can approve/reject. Returns request_id for tracking.",
        "parameters": {"type": "object", "properties": {
            "teammate": {"type": "string", "description": "Teammate name to request shutdown"},
        }, "required": ["teammate"]},
    }},
    {"type": "function", "function": {
        "name": "check_shutdown_status",
        "description": "Check the status of a shutdown request by request_id.",
        "parameters": {"type": "object", "properties": {
            "request_id": {"type": "string", "description": "Request ID from shutdown_request"},
        }, "required": ["request_id"]},
    }},
    {"type": "function", "function": {
        "name": "plan_review",
        "description": "Approve or reject a teammate's plan submission (protocol).",
        "parameters": {"type": "object", "properties": {
            "request_id": {"type": "string", "description": "Plan request ID"},
            "approve": {"type": "boolean", "description": "True to approve, false to reject"},
            "feedback": {"type": "string", "description": "Optional feedback message"},
        }, "required": ["request_id", "approve"]},
    }},
    {"type": "function", "function": {
        "name": "idle",
        "description": "Signal no more work and enter idle state (for autonomous teammates).",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "scan_tasks",
        "description": "Scan for unclaimed tasks on the task board.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "claim_task",
        "description": "Claim a task from the task board by ID.",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer", "description": "Task ID to claim"},
        }, "required": ["task_id"]},
    }},
    {"type": "function", "function": {
        "name": "worktree_create",
        "description": "Create a git worktree for isolated task execution. Each worktree is an independent copy of the repo.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Worktree name (1-40 chars, alphanumeric, ., _, -)"},
            "task_id": {"type": "integer", "description": "Optional task ID to bind"},
            "base_ref": {"type": "string", "description": "Base branch/ref (default: HEAD)"},
        }, "required": ["name"]},
    }},
    {"type": "function", "function": {
        "name": "worktree_list",
        "description": "List all worktrees with their status and task bindings.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "worktree_status",
        "description": "Show git status for a worktree.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Worktree name"},
        }, "required": ["name"]},
    }},
    {"type": "function", "function": {
        "name": "worktree_run",
        "description": "Run a command inside a worktree directory.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Worktree name"},
            "command": {"type": "string", "description": "Shell command to run"},
        }, "required": ["name", "command"]},
    }},
    {"type": "function", "function": {
        "name": "worktree_remove",
        "description": "Remove a worktree. Use force=true for uncommitted changes.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Worktree name"},
            "force": {"type": "boolean", "description": "Force remove even with uncommitted changes"},
        }, "required": ["name"]},
    }},
    {"type": "function", "function": {
        "name": "worktree_keep",
        "description": "Mark a worktree as kept (preserve it).",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Worktree name"},
        }, "required": ["name"]},
    }},
    {"type": "function", "function": {
        "name": "worktree_events",
        "description": "List recent worktree lifecycle events.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "Number of events to show"},
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
    "task_update": lambda **kw: TASKS.update(kw["task_id"], kw.get("status"), kw.get("addBlockedBy"), kw.get("addBlocks"), kw.get("worktree")),
    "task_list":   lambda **kw: TASKS.list_all(),
    "task_get":        lambda **kw: TASKS.get(kw["task_id"]),
    "task_bind_worktree":   lambda **kw: TASKS.bind_worktree(kw["task_id"], kw["worktree"], kw.get("owner", "")),
    "task_unbind_worktree": lambda **kw: TASKS.unbind_worktree(kw["task_id"]),
    "background_run":  lambda **kw: BG.run(kw["command"]),
    "check_background":lambda **kw: BG.check(kw.get("task_id")),
    "spawn_teammate":  lambda **kw: TEAM.spawn(kw["name"], kw["role"], kw["prompt"]),
    "list_teammates":  lambda **kw: TEAM.list_all(),
    "send_message":    lambda **kw: BUS.send("lead", kw["to"], kw["content"], kw.get("msg_type", "message")),
    "read_inbox":      lambda **kw: str(BUS.read_inbox("lead")),
    "broadcast":       lambda **kw: BUS.broadcast("lead", kw["content"], TEAM.member_names()),
    "shutdown_teammate": lambda **kw: TEAM.shutdown(kw.get("name")),
    "shutdown_request": lambda **kw: handle_shutdown_request(kw["teammate"]),
    "check_shutdown_status": lambda **kw: check_shutdown_status(kw.get("request_id", "")),
    "plan_review":     lambda **kw: handle_plan_review(kw["request_id"], kw["approve"], kw.get("feedback", "")),
    "idle":            lambda **kw: "Lead does not idle.",
    "scan_tasks":      lambda **kw: str(scan_unclaimed_tasks()),
    "claim_task":      lambda **kw: claim_task(kw["task_id"], "lead"),
    "worktree_create": lambda **kw: WORKTREES.create(kw["name"], kw.get("task_id"), kw.get("base_ref", "HEAD")),
    "worktree_list":   lambda **kw: WORKTREES.list_all(),
    "worktree_status": lambda **kw: WORKTREES.status(kw["name"]),
    "worktree_run":    lambda **kw: WORKTREES.run(kw["name"], kw["command"]),
    "worktree_remove": lambda **kw: WORKTREES.remove(kw["name"], kw.get("force", False)),
    "worktree_keep":   lambda **kw: WORKTREES.keep(kw["name"]),
    "worktree_events": lambda **kw: EVENTS.list_recent(kw.get("limit", 20)),
}
