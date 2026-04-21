"""Tests for the Gradio UI layer."""
import pytest
import gradio as gr

from src.ui import LlamaStackUI, create_ui


def test_create_ui_returns_blocks():
    demo = create_ui()
    assert isinstance(demo, gr.Blocks)


def test_llamastackui_initializes_components():
    ui = LlamaStackUI()
    assert ui.search_tool is not None
    assert ui.execution_tool is not None
    assert ui.file_io_tool is not None
    assert ui.research_agent is not None
    assert ui.code_agent is not None
    assert ui.pipeline_agent is not None


def test_format_research_result_contains_query():
    ui = LlamaStackUI()
    md = ui._format_research_result({
        "query": "what is rust",
        "summary": "a systems language",
        "sources": ["https://rust-lang.org"],
        "findings_count": 1,
    })
    assert "what is rust" in md
    assert "Research Results" in md
    assert "rust-lang.org" in md


def test_format_research_result_handles_missing_fields():
    ui = LlamaStackUI()
    md = ui._format_research_result({})
    assert "N/A" in md


def test_format_code_result_contains_task_and_code():
    ui = LlamaStackUI()
    md = ui._format_code_result({
        "task": "sum a list",
        "language": "python",
        "code": "print(sum([1,2,3]))",
        "success": True,
        "iterations": 1,
        "stdout": "6",
        "stderr": "",
    })
    assert "sum a list" in md
    assert "print(sum" in md
    assert "Code Generation Results" in md
    assert "python" in md


def test_format_code_result_marks_failure():
    ui = LlamaStackUI()
    md = ui._format_code_result({
        "task": "t", "language": "python", "code": "x",
        "success": False, "iterations": 2, "stderr": "boom",
    })
    assert "boom" in md


def test_format_pipeline_result_contains_query():
    ui = LlamaStackUI()
    md = ui._format_pipeline_result({
        "query": "process x",
        "final_output": "done: process x",
        "success": True,
        "search_count": 3,
        "code_length": 42,
        "execution_stdout": "hello",
    })
    assert "process x" in md
    assert "Pipeline Results" in md
    assert "hello" in md


def test_run_research_rejects_empty_query():
    ui = LlamaStackUI()
    events = list(ui.run_research("   "))
    assert events[0][0] == "Please enter a query"


def test_run_code_rejects_empty_task():
    ui = LlamaStackUI()
    events = list(ui.run_code(""))
    assert events[0][0] == "Please enter a task"


def test_run_pipeline_rejects_empty_query():
    ui = LlamaStackUI()
    events = list(ui.run_pipeline(""))
    assert events[0][0] == "Please enter a query"
