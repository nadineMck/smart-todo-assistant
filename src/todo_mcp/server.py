"""FastMCP server exposing exactly three assignment tools."""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .models import TaskCreateResult, TaskIfMissingResult, TaskListResult
from .services import default_service


mcp = FastMCP(
    name="Smart To-Do Assistant",
    instructions=(
        "Use get_tasks for read-only retrieval, add_task for an explicit unconditional "
        "addition, and add_task_if_missing when the user requests duplicate prevention."
    ),
)


@mcp.tool
def get_tasks(status: str = "all") -> TaskListResult:
    """Retrieve saved tasks without changing them.

    Args:
        status: Filter by all, pending, or completed tasks.
    """

    try:
        return default_service.get_tasks(status)
    except (ValueError, OSError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool
def add_task(title: str, priority: str = "medium") -> TaskCreateResult:
    """Add a new pending task to the local JSON file.

    Args:
        title: Short description of the work to remember.
        priority: One of low, medium, or high.
    """

    try:
        return default_service.add_task(title, priority)
    except (ValueError, OSError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool
def add_task_if_missing(
    title: str, priority: str = "medium"
) -> TaskIfMissingResult:
    """Check all tasks, then add the requested task only when it is absent.

    This orchestration tool coordinates the same read and write operations exposed by
    get_tasks and add_task.

    Args:
        title: Short description of the work to remember.
        priority: One of low, medium, or high.
    """

    try:
        return default_service.add_task_if_missing(title, priority)
    except (ValueError, OSError) as exc:
        raise ToolError(str(exc)) from exc


def main() -> None:
    """Run the MCP server over standard input/output."""

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

