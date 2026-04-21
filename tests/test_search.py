"""Tests for WebSearchTool."""
from unittest.mock import MagicMock, patch

import pytest

from src.tools.search import WebSearchTool, create_search_tool


def _fake_ddgs_results():
    return [
        {"title": "Python", "href": "https://python.org", "body": "Official site"},
        {"title": "PyPI", "href": "https://pypi.org", "body": "Package index"},
    ]


def test_construction_without_callback():
    tool = WebSearchTool()
    assert tool.logger_callback is None
    assert tool.ddgs is not None


def test_construction_with_callback():
    cb = MagicMock()
    tool = WebSearchTool(logger_callback=cb)
    assert tool.logger_callback is cb


def test_factory_create_search_tool():
    t = create_search_tool()
    assert isinstance(t, WebSearchTool)


def test_search_returns_formatted_results():
    tool = WebSearchTool()
    tool.ddgs = MagicMock()
    tool.ddgs.text.return_value = iter(_fake_ddgs_results())

    results = tool.search("python", max_results=2)
    assert len(results) == 2
    assert results[0]["index"] == 1
    assert results[0]["title"] == "Python"
    assert results[0]["href"] == "https://python.org"
    assert results[0]["body"] == "Official site"
    assert results[1]["index"] == 2


def test_search_handles_missing_fields():
    tool = WebSearchTool()
    tool.ddgs = MagicMock()
    tool.ddgs.text.return_value = iter([{}])
    results = tool.search("x")
    assert results[0]["title"] == "No title"
    assert results[0]["body"] == "No description"


def test_search_error_path_returns_error_dict():
    tool = WebSearchTool()
    tool.ddgs = MagicMock()
    tool.ddgs.text.side_effect = RuntimeError("boom")
    results = tool.search("q")
    assert len(results) == 1
    assert "error" in results[0]
    assert "boom" in results[0]["error"]


def test_logger_callback_invoked_on_search():
    logs = []
    tool = WebSearchTool(logger_callback=logs.append)
    tool.ddgs = MagicMock()
    tool.ddgs.text.return_value = iter(_fake_ddgs_results())
    tool.search("abc")
    joined = "\n".join(logs)
    assert "web_search" in joined
    assert "2 hits" in joined


def test_logger_callback_invoked_on_error():
    logs = []
    tool = WebSearchTool(logger_callback=logs.append)
    tool.ddgs = MagicMock()
    tool.ddgs.text.side_effect = Exception("net")
    tool.search("q")
    assert any("error" in m for m in logs)


def test_search_with_context():
    tool = WebSearchTool()
    tool.ddgs = MagicMock()
    tool.ddgs.text.return_value = iter(_fake_ddgs_results())
    out = tool.search_with_context("q", context="some ctx", max_results=2)
    assert out["query"] == "q"
    assert out["context"] == "some ctx"
    assert out["count"] == 2
    assert len(out["results"]) == 2
