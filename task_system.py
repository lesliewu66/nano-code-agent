"""
Task System - Persistent tasks with dependency graph
Tasks survive context compression because they're stored in .tasks/ as JSON.
"""
import json
import os
from pathlib import Path

TASKS_DIR = Path(os.getcwd()) / ".tasks"


class TaskManager:
    """CRUD with dependency graph, persisted as JSON files."""
    
    def __init__(self, tasks_dir: Path):
        self.dir = tasks_dir
        self.dir.mkdir(exist_ok=True)
        self._next_id = self._max_id() + 1
    
    def _max_id(self) -> int:
        ids = [int(f.stem.split("_")[1]) for f in self.dir.glob("task_*.json")]
        return max(ids) if ids else 0
    
    def _load(self, task_id: int) -> dict:
        path = self.dir / f"task_{task_id}.json"
        if not path.exists():
            raise ValueError(f"Task {task_id} not found")
        return json.loads(path.read_text())
    
    def _save(self, task: dict):
        path = self.dir / f"task_{task['id']}.json"
        path.write_text(json.dumps(task, indent=2))
    
    def create(self, subject: str, description: str = "") -> str:
        """Create a new task."""
        task = {
            "id": self._next_id,
            "subject": subject,
            "description": description,
            "status": "pending",
            "blockedBy": [],
            "blocks": [],
            "owner": "",
        }
        self._save(task)
        self._next_id += 1
        return json.dumps(task, indent=2)
    
    def get(self, task_id: int) -> str:
        """Get full details of a task."""
        return json.dumps(self._load(task_id), indent=2)
    
    def update(self, task_id: int, status: str = None,
               addBlockedBy: list = None, addBlocks: list = None) -> str:
        """Update task status or dependencies."""
        task = self._load(task_id)
        
        if status:
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError(f"Invalid status: {status}")
            task["status"] = status
            # When a task is completed, remove it from all other tasks' blockedBy
            if status == "completed":
                self._clear_dependency(task_id)
        
        if addBlockedBy:
            task["blockedBy"] = list(set(task["blockedBy"] + addBlockedBy))
        
        if addBlocks:
            task["blocks"] = list(set(task["blocks"] + addBlocks))
            # Bidirectional: also update the blocked tasks' blockedBy lists
            for blocked_id in addBlocks:
                try:
                    blocked = self._load(blocked_id)
                    if task_id not in blocked["blockedBy"]:
                        blocked["blockedBy"].append(task_id)
                        self._save(blocked)
                except ValueError:
                    pass  # Blocked task doesn't exist
        
        self._save(task)
        return json.dumps(task, indent=2)
    
    def _clear_dependency(self, completed_id: int):
        """Remove completed_id from all other tasks' blockedBy lists."""
        for f in self.dir.glob("task_*.json"):
            task = json.loads(f.read_text())
            if completed_id in task.get("blockedBy", []):
                task["blockedBy"].remove(completed_id)
                self._save(task)
    
    def list_all(self) -> str:
        """List all tasks with status summary."""
        tasks = []
        for f in sorted(self.dir.glob("task_*.json")):
            tasks.append(json.loads(f.read_text()))
        
        if not tasks:
            return "No tasks."
        
        lines = []
        for t in tasks:
            marker = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(t["status"], "[?]")
            blocked = f" (blocked by: {t['blockedBy']})" if t.get("blockedBy") else ""
            lines.append(f"{marker} #{t['id']}: {t['subject']}{blocked}")
        
        return "\n".join(lines)


# Global task manager instance
TASKS = TaskManager(TASKS_DIR)
