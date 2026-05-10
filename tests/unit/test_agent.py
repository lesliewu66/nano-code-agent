"""Tests for Agent class"""
from unittest.mock import MagicMock, patch

from route_agent.core.agent import Agent


class FakeChoice:
    def __init__(self, message):
        self.message = message


class FakeMessage:
    def __init__(self, content, tool_calls=None, reasoning_content=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.reasoning_content = reasoning_content


class FakeResponse:
    def __init__(self, choices):
        self.choices = choices


class TestAgent:
    """Test agent message handling and loop"""

    def setup_method(self):
        with patch("route_agent.core.agent.OpenAI"):
            self.agent = Agent()
            self.agent.client = MagicMock()

    def test_chat_returns_content(self):
        fake_msg = FakeMessage(content="Hello from agent")
        self.agent.client.chat.completions.create.return_value = FakeResponse(
            [FakeChoice(fake_msg)]
        )
        result = self.agent.chat([{"role": "user", "content": "hi"}])
        assert result["content"] == "Hello from agent"
        assert result["tool_calls"] == []
        assert result["reasoning"] == ""

    def test_chat_handles_empty_content(self):
        fake_msg = FakeMessage(content=None)
        self.agent.client.chat.completions.create.return_value = FakeResponse(
            [FakeChoice(fake_msg)]
        )
        result = self.agent.chat([{"role": "user", "content": "hi"}])
        assert result["content"] == ""

    def test_run_appends_to_history(self):
        fake_msg = FakeMessage(content="Reply")
        self.agent.client.chat.completions.create.return_value = FakeResponse(
            [FakeChoice(fake_msg)]
        )
        history = [{"role": "system", "content": "You are a bot."}]
        result = self.agent.run("Hello", history)
        assert result["content"] == "Reply"

    def test_run_without_history(self):
        fake_msg = FakeMessage(content="OK")
        self.agent.client.chat.completions.create.return_value = FakeResponse(
            [FakeChoice(fake_msg)]
        )
        result = self.agent.run("Hello")
        assert result["content"] == "OK"
