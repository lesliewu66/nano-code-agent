"""
Agent Teams - Persistent named agents with file-based JSONL inboxes
Each teammate runs its own agent loop in a separate thread.
Communication via append-only inboxes.
"""
import json
import os
import subprocess
import threading
import time
from pathlib import Path

# Avoid circular import - use os.getcwd() instead of config.WORKDIR
WORKDIR = Path(os.getcwd())
TEAM_DIR = WORKDIR / ".team"
INBOX_DIR = TEAM_DIR / "inbox"
TASKS_DIR = WORKDIR / ".tasks"

# Idle polling settings
POLL_INTERVAL = 5      # seconds between polls
IDLE_TIMEOUT = 60      # max idle time before shutdown

VALID_MSG_TYPES = {
    "message",
    "broadcast", 
    "shutdown_request",
    "shutdown_response",
    "plan_approval_response",
}

# -- Protocol request trackers: correlate by request_id --
shutdown_requests = {}  # request_id -> {"target": name, "status": "pending|approved|rejected"}
plan_requests = {}      # request_id -> {"from": name, "plan": text, "status": "pending|..."}
_tracker_lock = threading.Lock()
_claim_lock = threading.Lock()  # for task claiming


class MessageBus:
    """JSONL inbox per teammate"""
    
    def __init__(self, inbox_dir: Path):
        self.dir = inbox_dir
        self.dir.mkdir(parents=True, exist_ok=True)
    
    def send(self, sender: str, to: str, content: str,
             msg_type: str = "message", extra: dict = None) -> str:
        if msg_type not in VALID_MSG_TYPES:
            return f"Error: Invalid type '{msg_type}'. Valid: {VALID_MSG_TYPES}"
        
        msg = {
            "type": msg_type,
            "from": sender,
            "content": content,
            "timestamp": time.time(),
        }
        if extra:
            msg.update(extra)
        
        inbox_path = self.dir / f"{to}.jsonl"
        with open(inbox_path, "a") as f:
            f.write(json.dumps(msg) + "\n")
        return f"Sent {msg_type} to {to}"
    
    def read_inbox(self, name: str) -> list:
        """Read and drain inbox"""
        inbox_path = self.dir / f"{name}.jsonl"
        if not inbox_path.exists():
            return []
        
        messages = []
        content = inbox_path.read_text().strip()
        if content:
            for line in content.splitlines():
                if line:
                    messages.append(json.loads(line))
        
        # Clear inbox after reading
        inbox_path.write_text("")
        return messages
    
    def broadcast(self, sender: str, content: str, teammates: list) -> str:
        count = 0
        for name in teammates:
            if name != sender:
                self.send(sender, name, content, "broadcast")
                count += 1
        return f"Broadcast to {count} teammates"


class TeammateManager:
    """Persistent named agents with config.json"""
    
    def __init__(self, team_dir: Path, message_bus: MessageBus):
        self.dir = team_dir
        self.dir.mkdir(exist_ok=True)
        self.config_path = self.dir / "config.json"
        self.config = self._load_config()
        self.bus = message_bus
        self.threads = {}
        self._shutdown_event = threading.Event()
    
    def _load_config(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {"team_name": "default", "members": []}
    
    def _save_config(self):
        self.config_path.write_text(json.dumps(self.config, indent=2))
    
    def _find_member(self, name: str) -> dict:
        for m in self.config["members"]:
            if m["name"] == name:
                return m
        return None
    
    def spawn(self, name: str, role: str, prompt: str, 
              api_key: str = None, base_url: str = None, model: str = None) -> str:
        """Spawn a teammate in a background thread"""
        member = self._find_member(name)
        if member:
            if member["status"] not in ("idle", "shutdown"):
                return f"Error: '{name}' is currently {member['status']}"
            member["status"] = "working"
            member["role"] = role
        else:
            member = {"name": name, "role": role, "status": "working"}
            self.config["members"].append(member)
        
        self._save_config()
        
        # Import here to avoid circular import at module level
        from config import client as cfg_client, MODEL as cfg_model
        
        client = cfg_client
        use_model = model or cfg_model
        
        thread = threading.Thread(
            target=self._teammate_loop,
            args=(name, role, prompt, client, use_model),
            daemon=True,
        )
        self.threads[name] = thread
        thread.start()
        return f"Spawned '{name}' (role: {role})"
    
    def _set_status(self, name: str, status: str):
        """Update member status"""
        member = self._find_member(name)
        if member:
            member["status"] = status
            self._save_config()
    
    def _teammate_loop(self, name: str, role: str, prompt: str, client, model: str):
        """Autonomous teammate loop with WORK and IDLE phases"""
        from tools import TOOLS as BASE_TOOLS
        
        team_name = self.config["team_name"]
        sys_prompt = (
            f"You are '{name}', role: {role}, team: {team_name}, at {WORKDIR}. "
            f"You are an autonomous teammate. "
            f"Use idle tool when you have no more work. You will auto-claim new tasks. "
            f"Use send_message to communicate. "
            f"For major work, submit a plan via plan_approval tool first. "
            f"Respond to shutdown_request with shutdown_response tool."
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        # Extended tools for autonomous agents
        tools = BASE_TOOLS + [
            {"type": "function", "function": {
                "name": "send_message",
                "description": "Send message to a teammate or lead.",
                "parameters": {"type": "object", "properties": {
                    "to": {"type": "string"},
                    "content": {"type": "string"},
                    "msg_type": {"type": "string", "enum": list(VALID_MSG_TYPES)},
                }, "required": ["to", "content"]},
            }},
            {"type": "function", "function": {
                "name": "read_inbox",
                "description": "Read and drain your inbox.",
                "parameters": {"type": "object", "properties": {}},
            }},
            {"type": "function", "function": {
                "name": "shutdown_response",
                "description": "Respond to a shutdown request.",
                "parameters": {"type": "object", "properties": {
                    "request_id": {"type": "string"},
                    "approve": {"type": "boolean"},
                    "reason": {"type": "string"},
                }, "required": ["request_id", "approve"]},
            }},
            {"type": "function", "function": {
                "name": "plan_approval",
                "description": "Submit a plan for lead approval.",
                "parameters": {"type": "object", "properties": {
                    "plan": {"type": "string"},
                }, "required": ["plan"]},
            }},
            {"type": "function", "function": {
                "name": "idle",
                "description": "Signal that you have no more work. Enters idle polling phase.",
                "parameters": {"type": "object", "properties": {}},
            }},
            {"type": "function", "function": {
                "name": "claim_task",
                "description": "Claim a task from the task board by ID.",
                "parameters": {"type": "object", "properties": {
                    "task_id": {"type": "integer"},
                }, "required": ["task_id"]},
            }},
        ]
        
        # Main loop: WORK -> IDLE -> WORK or SHUTDOWN
        while True:
            # -- WORK PHASE --
            idle_requested = self._work_phase(name, role, team_name, messages, 
                                               sys_prompt, tools, client, model)
            
            if not idle_requested:
                # Natural end (no idle tool called)
                self._set_status(name, "idle")
                break
            
            # -- IDLE PHASE --
            self._set_status(name, "idle")
            resume = self._idle_phase(name, role, team_name, messages)
            
            if not resume:
                # Timeout or shutdown
                self._set_status(name, "shutdown")
                break
            
            # Resume work
            self._set_status(name, "working")
    
    def _work_phase(self, name: str, role: str, team_name: str, messages: list,
                    sys_prompt: str, tools: list, client, model: str) -> bool:
        """Work phase: execute tasks until idle or done. Returns True if idle requested."""
        for _ in range(50):  # Max 50 rounds per work phase
            if self._shutdown_event.is_set():
                return False
            
            # Check inbox
            inbox = self.bus.read_inbox(name)
            for msg in inbox:
                if msg.get("type") == "shutdown_request":
                    return False
                messages.append({"role": "user", "content": json.dumps(msg)})
            
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": sys_prompt}] + messages,
                    tools=tools,
                    max_tokens=8000,
                )
            except Exception as e:
                print(f"[{name}] Error: {e}")
                return False
            
            message = response.choices[0].message
            messages.append(message.model_dump())
            
            if not message.tool_calls:
                return False  # Natural end
            
            results = []
            idle_requested = False
            
            for tool_call in message.tool_calls:
                output = self._exec_tool(name, tool_call)
                if tool_call.function.name == "idle":
                    idle_requested = True
                results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": output,
                })
            
            messages.extend(results)
            
            if idle_requested:
                return True
        
        return False
    
    def _idle_phase(self, name: str, role: str, team_name: str, messages: list) -> bool:
        """Idle phase: poll for inbox messages and unclaimed tasks. Returns True to resume work."""
        polls = IDLE_TIMEOUT // max(POLL_INTERVAL, 1)
        
        for _ in range(polls):
            time.sleep(POLL_INTERVAL)
            
            # Check for messages
            inbox = self.bus.read_inbox(name)
            if inbox:
                for msg in inbox:
                    if msg.get("type") == "shutdown_request":
                        return False
                    messages.append({"role": "user", "content": json.dumps(msg)})
                return True  # Resume work
            
            # Check for unclaimed tasks
            unclaimed = scan_unclaimed_tasks()
            if unclaimed:
                task = unclaimed[0]
                claim_task(task["id"], name)
                
                # Re-inject identity if context is short (simulating compression recovery)
                if len(messages) <= 3:
                    messages.insert(0, make_identity_block(name, role, team_name))
                    messages.insert(1, {"role": "assistant", "content": f"I am {name}. Continuing."})
                
                task_prompt = (
                    f"<auto-claimed>Task #{task['id']}: {task['subject']}\n"
                    f"{task.get('description', '')}</auto-claimed>"
                )
                messages.append({"role": "user", "content": task_prompt})
                messages.append({"role": "assistant", "content": f"Claimed task #{task['id']}. Working on it."})
                return True  # Resume work
        
        # Timeout
        return False
    
    def _exec_tool(self, name: str, tool_call) -> str:
        """Execute a tool call and return output"""
        args = json.loads(tool_call.function.arguments)
        tool_name = tool_call.function.name
        
        if tool_name == "send_message":
            return self.bus.send(name, args["to"], args["content"], 
                                args.get("msg_type", "message"))
        elif tool_name == "read_inbox":
            return json.dumps(self.bus.read_inbox(name), indent=2)
        elif tool_name == "idle":
            return "Entering idle phase. Will poll for new tasks."
        elif tool_name == "claim_task":
            return claim_task(args["task_id"], name)
        elif tool_name == "shutdown_response":
            req_id = args["request_id"]
            approve = args["approve"]
            with _tracker_lock:
                if req_id in shutdown_requests:
                    shutdown_requests[req_id]["status"] = "approved" if approve else "rejected"
            self.bus.send(name, "lead", args.get("reason", ""),
                         "shutdown_response", {"request_id": req_id, "approve": approve})
            return f"Shutdown {'approved' if approve else 'rejected'}"
        elif tool_name == "plan_approval":
            plan_text = args.get("plan", "")
            req_id = f"plan_{name}_{int(time.time())}"
            with _tracker_lock:
                plan_requests[req_id] = {"from": name, "plan": plan_text, "status": "pending"}
            self.bus.send(name, "lead", plan_text, "plan_approval_response",
                         {"request_id": req_id, "plan": plan_text})
            return f"Plan submitted (request_id={req_id})."
        else:
            # Base tools
            from tools import TOOL_HANDLERS
            handler = TOOL_HANDLERS.get(tool_name)
            try:
                return handler(**args) if handler else f"Unknown: {tool_name}"
            except Exception as e:
                return f"Error: {e}"
    
    def list_all(self) -> str:
        if not self.config["members"]:
            return "No teammates."
        lines = [f"Team: {self.config['team_name']}"]
        for m in self.config["members"]:
            lines.append(f"  {m['name']} ({m['role']}): {m['status']}")
        return "\n".join(lines)
    
    def member_names(self) -> list:
        return [m["name"] for m in self.config["members"]]
    
    def shutdown(self, name: str = None):
        """Shutdown teammate(s)"""
        if name:
            member = self._find_member(name)
            if member:
                member["status"] = "shutdown"
                self._save_config()
                return f"Shutdown '{name}'"
            return f"Error: '{name}' not found"
        else:
            for m in self.config["members"]:
                m["status"] = "shutdown"
            self._save_config()
            self._shutdown_event.set()
            return "Shutdown all teammates"


# -- Task board scanning for autonomous agents --
def scan_unclaimed_tasks() -> list:
    """Scan .tasks/ for pending, unclaimed, unblocked tasks"""
    TASKS_DIR.mkdir(exist_ok=True)
    unclaimed = []
    for f in sorted(TASKS_DIR.glob("task_*.json")):
        task = json.loads(f.read_text())
        if (task.get("status") == "pending"
                and not task.get("owner")
                and not task.get("blockedBy")):
            unclaimed.append(task)
    return unclaimed


def claim_task(task_id: int, owner: str) -> str:
    """Claim a task for an agent"""
    with _claim_lock:
        path = TASKS_DIR / f"task_{task_id}.json"
        if not path.exists():
            return f"Error: Task {task_id} not found"
        task = json.loads(path.read_text())
        task["owner"] = owner
        task["status"] = "in_progress"
        path.write_text(json.dumps(task, indent=2))
    return f"Claimed task #{task_id} for {owner}"


# -- Identity re-injection after compression --
def make_identity_block(name: str, role: str, team_name: str) -> dict:
    """Create identity block for context re-injection"""
    return {
        "role": "user",
        "content": f"<identity>You are '{name}', role: {role}, team: {team_name}. Continue your work.</identity>",
    }


# Global instances
BUS = MessageBus(INBOX_DIR)
TEAM = TeammateManager(TEAM_DIR, BUS)


# -- Lead protocol handlers --
def handle_shutdown_request(teammate: str) -> str:
    """Lead requests a teammate to shut down gracefully"""
    import uuid
    req_id = str(uuid.uuid4())[:8]
    with _tracker_lock:
        shutdown_requests[req_id] = {"target": teammate, "status": "pending"}
    BUS.send(
        "lead", teammate, "Please shut down gracefully.",
        "shutdown_request", {"request_id": req_id}
    )
    return f"Shutdown request {req_id} sent to '{teammate}' (status: pending)"


def check_shutdown_status(request_id: str) -> str:
    """Check the status of a shutdown request"""
    with _tracker_lock:
        req = shutdown_requests.get(request_id)
        if not req:
            return json.dumps({"error": "Request not found"})
        return json.dumps(req)


def handle_plan_review(request_id: str, approve: bool, feedback: str = "") -> str:
    """Lead approves or rejects a teammate's plan"""
    with _tracker_lock:
        req = plan_requests.get(request_id)
    if not req:
        return f"Error: Unknown plan request_id '{request_id}'"
    
    with _tracker_lock:
        req["status"] = "approved" if approve else "rejected"
    
    BUS.send(
        "lead", req["from"], feedback, "plan_approval_response",
        {"request_id": request_id, "approve": approve, "feedback": feedback}
    )
    return f"Plan {req['status']} for '{req['from']}'"
