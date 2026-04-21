"""Tests for CodeGenerationAgent."""
import pytest

from demos.code_agent import CodeGenerationAgent, CodeResult, create_code_agent


def test_factory():
    assert isinstance(create_code_agent(), CodeGenerationAgent)


def test_run_without_client_yields_events():
    agent = CodeGenerationAgent()
    events = list(agent.run("write hello world"))
    log_events = [e for e in events if e["type"] == "log"]
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert len(log_events) >= 3


def test_result_has_required_keys():
    agent = CodeGenerationAgent()
    events = list(agent.run("write a function"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    for key in ("task", "language", "code", "success", "iterations"):
        assert key in result


def test_default_language_is_python():
    agent = CodeGenerationAgent()
    events = list(agent.run("hi"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert result["language"] == "python"


def test_task_is_propagated():
    agent = CodeGenerationAgent()
    events = list(agent.run("compute 1+1"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert result["task"] == "compute 1+1"


def test_mock_code_contains_task():
    agent = CodeGenerationAgent()
    events = list(agent.run("sort a list"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert "sort a list" in result["code"]


def test_iterations_is_at_least_one():
    agent = CodeGenerationAgent()
    events = list(agent.run("anything"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert result["iterations"] >= 1


def test_clean_code_strips_markdown():
    agent = CodeGenerationAgent()
    cleaned = agent._clean_code("```python\nprint(1)\n```")
    assert cleaned == "print(1)"


def test_clean_code_without_markdown():
    agent = CodeGenerationAgent()
    cleaned = agent._clean_code("x = 1")
    assert cleaned == "x = 1"
