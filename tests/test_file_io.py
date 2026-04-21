"""Tests for FileIOTool."""
import pytest

from src.tools.file_io import FileIOTool, create_file_io_tool


@pytest.fixture
def fio(tmp_path):
    return FileIOTool(workspace_dir=str(tmp_path))


def test_factory(tmp_path):
    t = create_file_io_tool(workspace_dir=str(tmp_path))
    assert isinstance(t, FileIOTool)


def test_write_then_read_round_trip(fio):
    w = fio.write_file("hello.txt", "hi there")
    assert w["success"] is True
    r = fio.read_file("hello.txt")
    assert r["success"] is True
    assert r["content"] == "hi there"
    assert r["size"] == len("hi there")


def test_read_missing_file_returns_error(fio):
    r = fio.read_file("nope.txt")
    assert r["success"] is False
    assert "not found" in r["error"].lower()


def test_list_files(fio):
    fio.write_file("a.txt", "a")
    fio.write_file("b.txt", "bb")
    listing = fio.list_files(".")
    assert listing["success"] is True
    names = {f["name"] for f in listing["files"]}
    assert {"a.txt", "b.txt"} <= names
    assert listing["count"] >= 2


def test_list_nonexistent_directory(fio):
    r = fio.list_files("not_here")
    assert r["success"] is False


def test_delete_file(fio):
    fio.write_file("x.txt", "content")
    out = fio.delete_file("x.txt")
    assert out["success"] is True
    # Re-read should fail
    r = fio.read_file("x.txt")
    assert r["success"] is False


def test_delete_missing_file(fio):
    out = fio.delete_file("ghost.txt")
    assert out["success"] is False


def test_path_outside_workspace_forced_inside(fio, tmp_path):
    # Absolute path outside workspace should be redirected to workspace/basename
    out = fio.write_file("/etc/evilfile.txt", "pwn")
    assert out["success"] is True
    # Ensure nothing was written to /etc
    import os
    assert not os.path.exists("/etc/evilfile.txt")
    # And the file actually exists inside workspace
    inside = tmp_path / "evilfile.txt"
    assert inside.exists()


def test_logger_callback_invoked(tmp_path):
    logs = []
    t = FileIOTool(logger_callback=logs.append, workspace_dir=str(tmp_path))
    t.write_file("a.txt", "abc")
    t.read_file("a.txt")
    assert any("write_file" in m for m in logs)
    assert any("read_file" in m for m in logs)


def test_nested_directory_creation(fio):
    out = fio.write_file("sub/dir/file.txt", "nested")
    assert out["success"] is True
    r = fio.read_file("sub/dir/file.txt")
    assert r["success"] is True
    assert r["content"] == "nested"
