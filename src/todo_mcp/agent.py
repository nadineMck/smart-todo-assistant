"""OpenAI Agents SDK host configured to use Gemini through LiteLLM."""

from __future__ import annotations

import ast
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv


PLACEHOLDER_VALUES = {"", "paste_your_gemini_api_key_here", "your-key-here"}
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ChatMessage(TypedDict):
    """One compact conversation turn supplied as context to the model."""

    role: str
    content: str


def _last_single_task(history: list[ChatMessage] | None) -> tuple[str, str, str] | None:
    """Recover the most recently verified single-task result for short follow-ups."""

    for message in reversed(history or []):
        if message.get("role") != "assistant":
            continue
        content = str(message.get("content", ""))
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("task"), dict):
            task = payload["task"]
            if all(key in task for key in ("title", "priority", "status")):
                return str(task["title"]), str(task["priority"]), str(task["status"])

        match = re.search(
            r"(?m)^\**([^\n·]+?)\**\s*·\s*(low|medium|high) priority\s*·\s*"
            r"(pending|completed)\s*$",
            content,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).strip(), match.group(2).casefold(), match.group(3).casefold()
    return None


def _local_response(
    prompt: str, history: list[ChatMessage] | None = None
) -> str | None:
    """Answer simple casual messages without spending a model request."""

    normalized = re.sub(r"\s+", " ", prompt).strip().casefold().rstrip("!?.")
    if normalized in {"hi", "hello", "hey", "hello there", "hey there"}:
        return "Hi! What task would you like to add or review?"
    if normalized in {"how are you", "how are u", "how's it going", "hows it going"}:
        return "I'm ready to help with your tasks. What would you like to remember?"
    if normalized in {"thanks", "thank you", "thx"}:
        return "You're welcome!"
    if normalized in {"who are you", "who are u", "what is your name"}:
        return (
            "I'm Taskflow, a to-do assistant backed by three MCP tools. "
            "I can show tasks, add one, or prevent duplicate additions."
        )
    if normalized in {"help", "what can you do", "what can u do"}:
        return (
            "I can show all tasks, add a task with low, medium, or high priority, "
            "and add a task only when it is not already present."
        )

    recent_task = _last_single_task(history)
    if recent_task and "priority" in normalized:
        title, priority, _ = recent_task
        return f"'{title}' is a {priority}-priority task."
    return None


def _build_agent_prompt(prompt: str, history: list[ChatMessage] | None = None) -> str:
    """Include recent turns so pronouns and short follow-ups retain context."""

    if not history:
        return prompt

    recent = history[-8:]
    transcript: list[str] = []
    for message in recent:
        role = "User" if message.get("role") == "user" else "Assistant"
        content = re.sub(r"\s+", " ", str(message.get("content", ""))).strip()
        if content:
            transcript.append(f"{role}: {content[:1200]}")

    if not transcript:
        return prompt
    return (
        "Use the recent conversation only to understand references and follow-up wording. "
        "Do not repeat or execute an earlier request unless the latest user message asks "
        "for it. The latest message is authoritative.\n\n"
        "Recent conversation:\n"
        + "\n".join(transcript)
        + f"\n\nLatest user message: {prompt}"
    )


def _final_output_text(final_output: object) -> str:
    """Extract plain text from supported first-tool result shapes."""

    if isinstance(final_output, list) and len(final_output) == 1:
        return _final_output_text(final_output[0])
    if isinstance(final_output, dict) and final_output.get("type") == "text":
        return str(final_output.get("text", ""))
    if getattr(final_output, "type", None) == "text":
        return str(getattr(final_output, "text", ""))
    if isinstance(final_output, str):
        try:
            parsed = ast.literal_eval(final_output)
        except (SyntaxError, ValueError):
            return final_output
        if isinstance(parsed, (dict, list)):
            return _final_output_text(parsed)
        return final_output
    return str(final_output)


def _safe_provider_error(exc: Exception, api_key: str) -> str:
    """Return a useful provider error without exposing the API key."""

    message = str(exc).replace(api_key, "[REDACTED]")
    return re.sub(
        r"([?&]key=)[^&\s\"']+",
        r"\1[REDACTED]",
        message,
        flags=re.IGNORECASE,
    )


def _load_configuration() -> tuple[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("GEMINI_API_KEY", "").strip():
        # Convenient during local development beside the original assignment project.
        load_dotenv(PROJECT_ROOT.parent / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv(
        "GEMINI_MODEL", "gemini/gemini-flash-lite-latest"
    ).strip()
    if api_key in PLACEHOLDER_VALUES:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and paste the key."
        )
    if not model_name:
        raise RuntimeError("GEMINI_MODEL must not be blank.")
    return api_key, model_name


async def run_once(
    prompt: str, history: list[ChatMessage] | None = None
) -> str:
    """Run one request through the agent and local MCP server."""

    local_response = _local_response(prompt, history)
    if local_response is not None:
        return local_response

    from agents import Agent, ModelRetrySettings, Runner, set_tracing_disabled
    from agents.extensions.models.litellm_model import LitellmModel
    from agents.mcp import MCPServerStdio
    from agents.model_settings import ModelSettings

    api_key, model_name = _load_configuration()
    set_tracing_disabled(True)
    server_params = {"command": sys.executable, "args": ["-m", "todo_mcp.server"]}

    async with MCPServerStdio(
        name="To-Do MCP Server",
        params=server_params,
        cache_tools_list=True,
        client_session_timeout_seconds=30,
    ) as server:
        agent = Agent(
            name="Smart To-Do Assistant",
            instructions=(
                "Help users inspect and add tasks. Use an MCP tool for every task lookup "
                "or change. Use add_task_if_missing whenever the user says only if missing, "
                "if it is not already there, avoid duplicates, or equivalent wording. Use "
                "add_task only for an explicit unconditional addition. Never claim a task "
                "was created unless the tool result says created=true. The toolkit cannot "
                "update, complete, or delete tasks; clearly explain that limitation instead "
                "of calling an unrelated tool. Call exactly one tool when a supported task "
                "operation is requested."
            ),
            model=LitellmModel(model=model_name, api_key=api_key),
            model_settings=ModelSettings(retry=ModelRetrySettings(max_retries=0)),
            mcp_servers=[server],
            tool_use_behavior="stop_on_first_tool",
        )
        try:
            result = await Runner.run(agent, _build_agent_prompt(prompt, history))
        except Exception as exc:
            safe_message = _safe_provider_error(exc, api_key)
            raise RuntimeError(f"Model provider request failed: {safe_message}") from None
        return _final_output_text(result.final_output)


async def _interactive() -> None:
    print("Smart To-Do Assistant (type 'quit' to exit)")
    history: list[ChatMessage] = []
    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if prompt.casefold() in {"quit", "exit"}:
            break
        if not prompt:
            continue
        try:
            response = await run_once(prompt, history)
        except Exception as exc:
            print(f"\nError: {exc}")
        else:
            print(f"\nAssistant: {response}")
            history.extend(
                [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response},
                ]
            )


def main() -> None:
    """Run a command-line prompt or start interactive mode."""

    if len(sys.argv) > 1:
        try:
            print(asyncio.run(run_once(" ".join(sys.argv[1:]))))
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
    else:
        asyncio.run(_interactive())


if __name__ == "__main__":
    main()

