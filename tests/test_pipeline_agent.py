"""Tests for PipelineAgent."""
import pytest

from demos.pipeline_agent import PipelineAgent, PipelineResult, create_pipeline_agent


def test_factory():
    assert isinstance(create_pipeline_agent(), PipelineAgent)


def test_run_yields_events_and_one_result():
    agent = PipelineAgent()
    events = list(agent.run("process weather data"))
    log_events = [e for e in events if e["type"] == "log"]
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert len(log_events) >= 5


def test_result_has_required_keys():
    agent = PipelineAgent()
    events = list(agent.run("demo task"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    for key in ("final_output", "search_count", "code_length"):
        assert key in result


def test_query_propagated():
    agent = PipelineAgent()
    events = list(agent.run("weather nyc"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert result["query"] == "weather nyc"


def test_final_output_mentions_query():
    agent = PipelineAgent()
    events = list(agent.run("analyze sales"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert "analyze sales" in result["final_output"]


def test_code_length_positive():
    agent = PipelineAgent()
    events = list(agent.run("anything"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert result["code_length"] > 0


def test_get_logs_contains_phase_markers():
    agent = PipelineAgent()
    list(agent.run("xyz"))
    logs = agent.get_logs()
    joined = "\n".join(logs)
    assert "phase 1" in joined
    assert "phase 2" in joined
    assert "phase 3" in joined


def test_clean_code_helper():
    agent = PipelineAgent()
    assert agent._clean_code("```\nprint(1)\n```") == "print(1)"
