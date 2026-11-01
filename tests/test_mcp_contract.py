"""Contract test proving the server exposes exactly three tools."""

from __future__ import annotations

import asyncio

from fastmcp import Client

from todo_mcp.server import mcp


def test_server_exposes_exactly_three_named_tools() -> None:
    async def list_names() -> list[str]:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            return sorted(tool.name for tool in tools)

    assert asyncio.run(list_names()) == [
        "add_task",
        "add_task_if_missing",
        "get_tasks",
    ]

