"""Tests for UI formatting and request behavior."""

from __future__ import annotations

import asyncio

from todo_mcp.ui import _format_agent_output, _run_prompt


def test_formats_empty_task_list() -> None:
    assert "empty" in _format_agent_output(
        '{"status_filter":"all","count":0,"tasks":[]}'
    )


def test_formats_created_and_duplicate_results() -> None:
    task = '{"id":1,"title":"Study","priority":"high","status":"pending"}'
    assert "Task added" in _format_agent_output(
        '{"created":true,"task":' + task + ',"message":"ok"}'
    )
    assert "Already on your list" in _format_agent_output(
        '{"created":false,"task":' + task + ',"message":"exists"}'
    )


def test_agent_request_has_hard_timeout(monkeypatch) -> None:
    async def timeout(*args, **kwargs):
        raise asyncio.TimeoutError

    monkeypatch.setattr("todo_mcp.ui.run_once", timeout)
    assert "longer than 60 seconds" in _run_prompt("show tasks")


def test_ui_passes_history_to_shared_agent(monkeypatch) -> None:
    captured = {}

    async def response(prompt, history):
        captured["prompt"] = prompt
        captured["history"] = history
        return "Hi!"

    history = [{"role": "user", "content": "Earlier message"}]
    monkeypatch.setattr("todo_mcp.ui.run_once", response)

    assert _run_prompt("hello", history) == "Hi!"
    assert captured == {"prompt": "hello", "history": history}

