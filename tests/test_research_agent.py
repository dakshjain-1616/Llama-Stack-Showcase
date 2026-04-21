"""Tests for ResearchAgent."""
import pytest

from demos.research_agent import ResearchAgent, ResearchResult, create_research_agent


def test_factory():
    assert isinstance(create_research_agent(), ResearchAgent)


def test_run_without_client_or_search_yields_events():
    agent = ResearchAgent()
    events = list(agent.run("what is python"))
    # Must yield log events and exactly one result event
    log_events = [e for e in events if e["type"] == "log"]
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 1
    assert len(log_events) >= 3


def test_mock_fallback_produces_two_results():
    agent = ResearchAgent()
    events = list(agent.run("quantum computing"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert result["findings_count"] == 2


def test_result_has_required_keys():
    agent = ResearchAgent()
    events = list(agent.run("test query"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    for key in ("query", "summary", "sources", "findings_count"):
        assert key in result


def test_result_query_matches_input():
    agent = ResearchAgent()
    events = list(agent.run("astrophysics basics"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert result["query"] == "astrophysics basics"


def test_sources_are_populated_in_mock_mode():
    agent = ResearchAgent()
    events = list(agent.run("anything"))
    result = [e for e in events if e["type"] == "result"][0]["content"]
    assert len(result["sources"]) == 2


def test_get_logs_reflects_run():
    agent = ResearchAgent()
    list(agent.run("hello"))
    logs = agent.get_logs()
    assert any("starting research" in m for m in logs)
    assert any("research complete" in m for m in logs)
