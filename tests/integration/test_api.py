"""Integration tests for API server"""
from fastapi.testclient import TestClient

from route_agent.api.server import create_app


class TestAPI:
    """Test FastAPI endpoints"""

    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health_check(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"

    def test_list_tools(self):
        response = self.client.get("/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        names = [t["name"] for t in tools]
        assert "bash" in names
        assert "read_file" in names
        assert "write_file" in names
        assert "edit_file" in names

    def test_chat_endpoint_invalid_body(self):
        response = self.client.post("/chat", json={})
        assert response.status_code == 422

    def test_chat_endpoint_missing_message(self):
        response = self.client.post("/chat", json={"session_id": "abc"})
        assert response.status_code == 422
