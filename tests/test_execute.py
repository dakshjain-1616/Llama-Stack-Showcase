"""Tests for CodeExecutionTool."""
import pytest

from src.tools.execute import CodeExecutionTool, create_execution_tool


def test_default_timeout_is_10():
    t = CodeExecutionTool()
    assert t.timeout == 10


def test_custom_timeout():
    t = CodeExecutionTool(timeout=5)
    assert t.timeout == 5


def test_default_allowed_imports_contains_common_modules():
    t = CodeExecutionTool()
    for m in ["os", "sys", "json", "math", "re"]:
        assert m in t.allowed_imports


def test_factory():
    assert isinstance(create_execution_tool(), CodeExecutionTool)


def test_successful_python_execution_captures_stdout():
    t = CodeExecutionTool()
    result = t.execute("print('hello world')")
    assert result["success"] is True
    assert "hello world" in result["stdout"]
    assert result["returncode"] == 0


def test_execution_captures_stderr_on_failure():
    t = CodeExecutionTool()
    result = t.execute("import sys\nsys.stderr.write('oops\\n')\nsys.exit(2)")
    assert result["success"] is False
    assert "oops" in result["stderr"]
    assert result["returncode"] == 2


def test_execution_non_python_language_rejected():
    t = CodeExecutionTool()
    result = t.execute("console.log('hi')", language="javascript")
    assert result["success"] is False
    assert "not supported" in result["error"]


def test_execution_rejects_dangerous_patterns():
    t = CodeExecutionTool()
    # subprocess is in the dangerous list
    result = t.execute("import subprocess\nprint(1)")
    assert result["success"] is False
    assert "Security violation" in result["error"]


def test_timeout_enforcement():
    t = CodeExecutionTool(timeout=1)
    result = t.execute("while True:\n    pass\n")
    assert result["success"] is False
    # Either raised TimeoutExpired (mapped to error message) or nonzero
    assert result["returncode"] == -1
    # Error text should mention timeout
    err_text = (result.get("error", "") + result.get("stderr", "")).lower()
    assert "timed out" in err_text or "timeout" in err_text


def test_cwd_is_temp_dir():
    # Confirm the subprocess doesn't run in the project directory
    t = CodeExecutionTool()
    code = "import os; print(os.getcwd())"
    result = t.execute(code)
    assert result["success"] is True
    # tempfile usually lives under /tmp on Linux
    assert "/llama-stack-showcase" not in result["stdout"]


def test_logger_callback_invoked():
    logs = []
    t = CodeExecutionTool(logger_callback=logs.append)
    t.execute("print(1)")
    joined = "\n".join(logs)
    assert "execute_code" in joined
    assert "sandbox" in joined or "execution successful" in joined


def test_logger_callback_on_validation_error():
    logs = []
    t = CodeExecutionTool(logger_callback=logs.append)
    t.execute("eval('1+1')")
    assert any("validation" in m.lower() or "security" in m.lower() for m in logs)
