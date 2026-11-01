"""Deterministic demonstration that does not require a model API key."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .services import TodoService


def main() -> None:
    """Demonstrate Data, Action, and Orchestration behavior."""

    with tempfile.TemporaryDirectory() as directory:
        tasks_path = Path(directory) / "tasks.json"
        tasks_path.write_text('{"tasks": []}\n', encoding="utf-8")
        service = TodoService(tasks_path)

        print("1. Data tool behavior: get_tasks")
        print(service.get_tasks().model_dump_json(indent=2))

        print("\n2. Action tool behavior: add_task")
        print(
            service.add_task("Review lecture notes", "medium").model_dump_json(
                indent=2
            )
        )

        print("\n3. Orchestration: check, then add if missing")
        first = service.add_task_if_missing("Finish my MCP assignment", "high")
        print(first.model_dump_json(indent=2))

        print("\n4. Duplicate prevention: run the same request again")
        second = service.add_task_if_missing("finish MY mcp assignment", "low")
        print(second.model_dump_json(indent=2))

        print("\n5. Predictable failure: reject a blank title")
        try:
            service.add_task("   ", "high")
        except ValueError as exc:
            print(f"Clear error: {exc}")

        print("\nFinal JSON state")
        print(json.dumps(json.loads(tasks_path.read_text()), indent=2))


if __name__ == "__main__":
    main()

