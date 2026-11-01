"""Unit tests for local task storage and orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from todo_mcp.services import TodoService


@pytest.fixture
def service(tmp_path: Path) -> TodoService:
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text('{"tasks": []}\n', encoding="utf-8")
    return TodoService(tasks_path)


def test_get_tasks_reads_and_filters_without_mutation(service: TodoService) -> None:
    service.add_task("Pending work", "high")
    before = service.tasks_path.read_text(encoding="utf-8")

    result = service.get_tasks("pending")

    assert result.count == 1
    assert result.tasks[0].title == "Pending work"
    assert service.tasks_path.read_text(encoding="utf-8") == before


def test_add_task_normalizes_input_and_persists(service: TodoService) -> None:
    result = service.add_task("  Finish   report  ", " HIGH ")

    assert result.created is True
    assert result.task.id == 1
    assert result.task.title == "Finish report"
    assert result.task.priority == "high"
    stored = json.loads(service.tasks_path.read_text(encoding="utf-8"))
    assert stored["tasks"] == [result.task.model_dump()]


def test_orchestration_adds_once_then_prevents_duplicate(
    service: TodoService,
) -> None:
    first = service.add_task_if_missing("Finish my MCP assignment", "high")
    second = service.add_task_if_missing(" finish MY mcp assignment ", "low")

    assert first.created is True
    assert second.created is False
    assert second.task.id == first.task.id
    assert service.get_tasks().count == 1
    assert service.get_tasks().tasks[0].priority == "high"


@pytest.mark.parametrize(
    ("title", "priority", "message"),
    [
        ("   ", "high", "title must not be blank"),
        ("Valid task", "urgent", "priority must be low, medium, or high"),
    ],
)
def test_add_task_rejects_invalid_input(
    service: TodoService, title: str, priority: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        service.add_task(title, priority)
    assert service.get_tasks().count == 0


def test_invalid_json_fails_predictably(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        TodoService(tasks_path).get_tasks()

