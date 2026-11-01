"""Typed models for the Smart To-Do MCP toolkit."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "medium", "high"]
TaskStatus = Literal["pending", "completed"]


class Task(BaseModel):
    """One persistent task."""

    id: int = Field(gt=0)
    title: str = Field(min_length=1)
    priority: Priority
    status: TaskStatus = "pending"


class TaskListResult(BaseModel):
    """Read-only result returned by the Data tool."""

    status_filter: Literal["all", "pending", "completed"]
    count: int = Field(ge=0)
    tasks: list[Task]


class TaskCreateResult(BaseModel):
    """Result returned after the Action tool creates a task."""

    created: Literal[True] = True
    task: Task
    message: str


class TaskIfMissingResult(BaseModel):
    """Result of the orchestration tool's check-then-add workflow."""

    created: bool
    task: Task
    message: str

