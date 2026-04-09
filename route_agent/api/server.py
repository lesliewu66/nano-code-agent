"""FastAPI HTTP server"""
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

from ..core.agent import Agent
from ..core.tools import ToolRegistry
from ..core.config import Config


class ChatRequest(BaseModel):
    """Chat request body"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response"""
    response: str
    reasoning: Optional[str] = None
    tools_used: List[dict] = []


class ToolInfo(BaseModel):
    """Tool information"""
    name: str
    description: str


# Global agent instance
_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """Get or create global agent instance"""
    global _agent
    if _agent is None:
        Config.ensure_dirs()
        _agent = Agent()
    return _agent


def create_app() -> FastAPI:
    """Create and configure FastAPI app"""
    app = FastAPI(
        title="RouteAgent API",
        description="A lightweight coding agent with HTTP interface",
        version="1.0.0"
    )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok", "version": "1.0.0"}
    
    @app.get("/tools", response_model=List[ToolInfo])
    async def list_tools():
        """List available tools"""
        agent = get_agent()
        tools = []
        for tool in agent.tools.get_tools_schema():
            func = tool.get("function", {})
            tools.append(ToolInfo(
                name=func.get("name", ""),
                description=func.get("description", "")
            ))
        return tools
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Chat with the agent"""
        agent = get_agent()
        result = agent.run(request.message)
        
        return ChatResponse(
            response=result["content"],
            reasoning=result.get("reasoning"),
            tools_used=result.get("tool_calls", [])
        )
    
    return app
