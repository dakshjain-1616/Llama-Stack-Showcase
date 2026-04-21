"""Tests for LlamaStackClient."""
import os
from unittest.mock import MagicMock, patch

import pytest

from src.client import LlamaStackClient, Message, create_client


def test_default_model_is_llama_4_scout():
    c = LlamaStackClient(api_key="dummy")
    assert "llama-4-scout" in c.model.lower()


def test_default_temperature_is_0_7():
    c = LlamaStackClient(api_key="dummy")
    assert c.temperature == 0.7


def test_default_max_tokens_is_4096():
    c = LlamaStackClient(api_key="dummy")
    assert c.max_tokens == 4096


def test_default_base_url_is_openrouter_or_together():
    c = LlamaStackClient(api_key="dummy")
    assert "openrouter.ai" in c.base_url or "together.xyz" in c.base_url


def test_custom_model_and_params():
    c = LlamaStackClient(api_key="k", model="foo/bar", temperature=0.1, max_tokens=128)
    assert c.model == "foo/bar"
    assert c.temperature == 0.1
    assert c.max_tokens == 128


def test_api_key_falls_back_to_env(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("TOGETHER_API_KEY", "env-key")
    c = LlamaStackClient()
    assert c.api_key == "env-key"


def test_openrouter_env_takes_precedence(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("TOGETHER_API_KEY", "tg-key")
    c = LlamaStackClient()
    assert c.api_key == "or-key"
    assert "openrouter.ai" in c.base_url


def test_message_dataclass():
    m = Message(role="user", content="hi")
    assert m.role == "user"
    assert m.content == "hi"
    assert m.tool_calls is None


def test_create_client_factory():
    c = create_client(api_key="k")
    assert isinstance(c, LlamaStackClient)


def test_simple_chat_returns_error_string_when_chat_fails():
    c = LlamaStackClient(api_key="dummy")
    # Force the openai client attribute to raise when called (simulate auth failure)
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.side_effect = Exception("no api key")
    c.client = mock_openai
    out = c.simple_chat("hello")
    assert isinstance(out, str)
    assert out.startswith("Error:")


def test_format_response_shape():
    c = LlamaStackClient(api_key="k")

    fake_message = MagicMock()
    fake_message.content = "hello there"
    fake_message.role = "assistant"
    fake_message.tool_calls = None

    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_choice.finish_reason = "stop"

    fake_response = MagicMock()
    fake_response.choices = [fake_choice]

    out = c._format_response(fake_response)
    assert out["success"] is True
    assert out["content"] == "hello there"
    assert out["role"] == "assistant"
    assert out["finish_reason"] == "stop"
    assert "tool_calls" not in out


def test_format_response_no_choices():
    c = LlamaStackClient(api_key="k")
    fake_response = MagicMock()
    fake_response.choices = []
    out = c._format_response(fake_response)
    assert out["success"] is False
    assert "error" in out


def test_format_response_includes_tool_calls():
    c = LlamaStackClient(api_key="k")
    tc = MagicMock()
    tc.id = "call_1"
    tc.type = "function"
    tc.function.name = "web_search"
    tc.function.arguments = '{"query": "x"}'

    msg = MagicMock()
    msg.content = None
    msg.role = "assistant"
    msg.tool_calls = [tc]

    choice = MagicMock()
    choice.message = msg
    choice.finish_reason = "tool_calls"

    resp = MagicMock()
    resp.choices = [choice]
    out = c._format_response(resp)
    assert out["tool_calls"][0]["function"]["name"] == "web_search"


def test_chat_with_tools_yields_response_event():
    c = LlamaStackClient(api_key="k")
    # mock chat() directly
    c.chat = MagicMock(return_value={
        "success": True,
        "content": "hi",
        "role": "assistant",
        "finish_reason": "stop",
    })

    events = list(c.chat_with_tools("sys", "user", tools=[]))
    assert any(e["step"] == "response" for e in events)


def test_chat_with_tools_yields_error_event():
    c = LlamaStackClient(api_key="k")
    c.chat = MagicMock(return_value={"error": "boom"})
    events = list(c.chat_with_tools("sys", "user", tools=[]))
    assert events[0]["step"] == "error"
    assert events[0]["content"] == "boom"


def test_chat_with_tools_calls_logger_callback():
    c = LlamaStackClient(api_key="k")
    c.chat = MagicMock(return_value={
        "success": True, "content": "ok", "role": "assistant", "finish_reason": "stop",
    })
    messages = []
    list(c.chat_with_tools("s", "u", tools=[], logger_callback=messages.append))
    assert messages  # at least one log message captured


def test_chat_error_path_returns_dict_without_raising():
    c = LlamaStackClient(api_key="k")
    c.client = MagicMock()
    c.client.chat.completions.create.side_effect = RuntimeError("network down")
    out = c.chat([{"role": "user", "content": "hi"}])
    assert out["success"] is False
    assert "network down" in out["error"]
