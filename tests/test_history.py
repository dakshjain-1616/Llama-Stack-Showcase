"""Tests for the ConversationHistory class."""
import json
import os
import pytest

from src.history import ConversationHistory


def test_add_and_get_all():
    h = ConversationHistory()
    h.add("research", "what is rust", "a systems language", "log line")
    h.add("code", "sum 1..3", "print(6)", "log line")
    all_entries = h.get_all()
    assert len(all_entries) == 2
    assert all_entries[0]["tab"] == "research"
    assert all_entries[0]["query"] == "what is rust"
    assert all_entries[1]["tab"] == "code"
    assert "timestamp" in all_entries[0]


def test_clear():
    h = ConversationHistory()
    h.add("research", "q", "r", "l")
    assert len(h) == 1
    h.clear()
    assert len(h) == 0
    assert h.get_all() == []


def test_fifo_cap_at_50():
    h = ConversationHistory(max_entries=50)
    for i in range(75):
        h.add("research", f"q{i}", f"r{i}", "log")
    assert len(h) == 50
    # Oldest 25 evicted; first remaining should be q25
    first = h.get_all()[0]
    assert first["query"] == "q25"
    last = h.get_all()[-1]
    assert last["query"] == "q74"


def test_per_tab_partition():
    h = ConversationHistory()
    h.add("research", "r1", "x", "l")
    h.add("code", "c1", "x", "l")
    h.add("pipeline", "p1", "x", "l")
    h.add("research", "r2", "x", "l")
    assert len(h.get_by_tab("research")) == 2
    assert len(h.get_by_tab("code")) == 1
    assert len(h.get_by_tab("pipeline")) == 1
    assert h.get_by_tab("research")[0]["query"] == "r1"
    assert h.get_by_tab("research")[1]["query"] == "r2"


def test_export_json_to_file(tmp_path):
    h = ConversationHistory()
    h.add("research", "q1", "summary1", "logs1", model="m", temperature=0.5)
    h.add("code", "q2", "summary2", "logs2")
    out = tmp_path / "hist.json"
    path = h.export_json(str(out))
    assert path == str(out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert len(data) == 2
    assert data[0]["query"] == "q1"
    assert data[0]["model"] == "m"
    assert data[0]["temperature"] == 0.5


def test_export_json_roundtrip(tmp_path):
    h = ConversationHistory()
    h.add("pipeline", "round", "res", "logs")
    out = tmp_path / "rt.json"
    h.export_json(str(out))
    parsed = json.loads(out.read_text())
    assert parsed[0]["tab"] == "pipeline"
    assert parsed[0]["query"] == "round"
    assert parsed[0]["result_summary"] == "res"
    assert parsed[0]["logs"] == "logs"


def test_empty_history_export_and_display(tmp_path):
    h = ConversationHistory()
    assert h.get_all() == []
    assert h.get_by_tab("research") == []
    out = tmp_path / "empty.json"
    h.export_json(str(out))
    assert json.loads(out.read_text()) == []
    display = h.format_display()
    assert "No history" in display
