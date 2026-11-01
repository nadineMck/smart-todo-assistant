"""Business logic shared by the three MCP tool wrappers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import Task, TaskCreateResult, TaskIfMissingResult, TaskListResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASKS_PATH = PROJECT_ROOT / "data" / "tasks.json"
VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"all", "pending", "completed"}


class TodoService:
    """Read and update tasks in a local JSON document."""

    def __init__(self, tasks_path: Path = DEFAULT_TASKS_PATH) -> None:
        self.tasks_path = Path(tasks_path)

    @staticmethod
    def _normalize_title(title: str) -> str:
        if not isinstance(title, str):
            raise ValueError("title must be text.")
        cleaned = re.sub(r"\s+", " ", title).strip()
        if not cleaned:
            raise ValueError("title must not be blank.")
        if len(cleaned) > 200:
            raise ValueError("title must be 200 characters or fewer.")
        return cleaned

    @staticmethod
    def _normalize_priority(priority: str) -> str:
        if not isinstance(priority, str):
            raise ValueError("priority must be low, medium, or high.")
        cleaned = priority.strip().casefold()
        if cleaned not in VALID_PRIORITIES:
            raise ValueError("priority must be low, medium, or high.")
        return cleaned

    @staticmethod
    def _normalize_status(status: str) -> str:
        if not isinstance(status, str):
            raise ValueError("status must be all, pending, or completed.")
        cleaned = status.strip().casefold()
        if cleaned not in VALID_STATUSES:
            raise ValueError("status must be all, pending, or completed.")
        return cleaned

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as stream:
                return json.load(stream)
        except FileNotFoundError as exc:
            raise ValueError(f"Required data file is unavailable: {path.name}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Data file contains invalid JSON: {path.name}") from exc

    def _load_tasks(self) -> list[Task]:
        payload = self._read_json(self.tasks_path)
        if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
            raise ValueError("Tasks file must contain a 'tasks' list.")
        try:
            return [Task.model_validate(item) for item in payload["tasks"]]
        except ValidationError as exc:
            raise ValueError("Tasks file contains an invalid task record.") from exc

    def _save_tasks(self, tasks: list[Task]) -> None:
        self.tasks_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.tasks_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as stream:
            json.dump(
                {"tasks": [task.model_dump() for task in tasks]},
                stream,
                indent=2,
                ensure_ascii=True,
            )
            stream.write("\n")
        temporary_path.replace(self.tasks_path)

    def get_tasks(self, status: str = "all") -> TaskListResult:
        """Return tasks, optionally filtered by their status."""

        normalized_status = self._normalize_status(status)
        tasks = self._load_tasks()
        if normalized_status != "all":
            tasks = [task for task in tasks if task.status == normalized_status]
        return TaskListResult(
            status_filter=normalized_status,
            count=len(tasks),
            tasks=tasks,
        )

    def add_task(self, title: str, priority: str = "medium") -> TaskCreateResult:
        """Append a validated task to persistent storage."""

        normalized_title = self._normalize_title(title)
        normalized_priority = self._normalize_priority(priority)
        tasks = self._load_tasks()
        next_id = max((task.id for task in tasks), default=0) + 1
        task = Task(
            id=next_id,
            title=normalized_title,
            priority=normalized_priority,
            status="pending",
        )
        tasks.append(task)
        self._save_tasks(tasks)
        return TaskCreateResult(
            task=task,
            message=f"Added '{task.title}' as a {task.priority}-priority task.",
        )

    def add_task_if_missing(
        self, title: str, priority: str = "medium"
    ) -> TaskIfMissingResult:
        """Check current tasks and add the requested task only when absent."""

        normalized_title = self._normalize_title(title)
        normalized_priority = self._normalize_priority(priority)

        # The orchestration deliberately coordinates the same Data operation first.
        current = self.get_tasks(status="all")
        title_key = normalized_title.casefold()
        existing = next(
            (task for task in current.tasks if task.title.casefold() == title_key),
            None,
        )
        if existing is not None:
            return TaskIfMissingResult(
                created=False,
                task=existing,
                message=f"Task '{existing.title}' already exists; no duplicate was added.",
            )

        # Only a missing task reaches the same Action operation used by add_task.
        created = self.add_task(normalized_title, normalized_priority)
        return TaskIfMissingResult(
            created=True,
            task=created.task,
            message=created.message,
        )


default_service = TodoService()

