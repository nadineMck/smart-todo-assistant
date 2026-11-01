"""Polished Streamlit interface for testing the Smart To-Do Assistant."""

from __future__ import annotations

import asyncio
import html
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from todo_mcp.models import Task
from todo_mcp.agent import ChatMessage, run_once
from todo_mcp.services import default_service


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
if not os.getenv("GEMINI_API_KEY", "").strip():
    load_dotenv(PROJECT_ROOT.parent / ".env")


APP_CSS = """
<style>
    :root {
        --night: #17243a;
        --muted: #68738a;
        --paper: rgba(255, 255, 255, .86);
        --line: rgba(42, 58, 91, .12);
        --blue: #526ed3;
        --violet: #8b6bd6;
        --mint: #44a58f;
        --amber: #d58d38;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 8% 8%, rgba(139, 107, 214, .16), transparent 28rem),
            radial-gradient(circle at 92% 15%, rgba(82, 110, 211, .16), transparent 30rem),
            linear-gradient(145deg, #f6f7fc 0%, #eef2f9 100%);
        color: var(--night);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMainBlockContainer"] {
        max-width: 1240px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    h1, h2, h3, p, label, li, [data-testid="stMarkdownContainer"] {
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.3rem 2.6rem;
        margin-bottom: 1.35rem;
        border: 1px solid rgba(255, 255, 255, .75);
        border-radius: 28px;
        background: linear-gradient(125deg, rgba(255,255,255,.94), rgba(246,247,253,.80));
        box-shadow: 0 20px 60px rgba(40, 52, 88, .10);
    }
    .hero::after {
        content: "";
        position: absolute;
        width: 280px;
        height: 280px;
        right: -90px;
        top: -140px;
        border-radius: 50%;
        background: linear-gradient(145deg, rgba(82,110,211,.35), rgba(139,107,214,.08));
    }
    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        padding: .4rem .75rem;
        border-radius: 999px;
        background: rgba(82,110,211,.10);
        color: #435bb6;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .11em;
        text-transform: uppercase;
    }
    .hero h1 {
        position: relative;
        z-index: 1;
        margin: .85rem 0 .45rem;
        color: var(--night);
        font-size: clamp(2.3rem, 6vw, 4.1rem);
        line-height: 1;
        letter-spacing: -.055em;
    }
    .hero p {
        position: relative;
        z-index: 1;
        max-width: 690px;
        margin: 0;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.65;
    }
    .tool-row {
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin-top: 1.15rem;
    }
    .tool-chip {
        padding: .42rem .68rem;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: rgba(255,255,255,.62);
        color: #526077;
        font-size: .75rem;
        font-weight: 700;
    }
    .tool-dot { color: var(--mint); margin-right: .3rem; }

    .section-label {
        margin: .25rem 0 .7rem;
        color: #53627c;
        font-size: .72rem;
        font-weight: 850;
        letter-spacing: .12em;
        text-transform: uppercase;
    }
    .panel-copy { color: var(--muted); font-size: .88rem; margin: -.35rem 0 1rem; }

    [data-testid="stChatMessage"] {
        padding: 1rem 1.05rem;
        margin-bottom: .7rem;
        border: 1px solid var(--line);
        border-radius: 20px;
        background: var(--paper);
        color: var(--night) !important;
        box-shadow: 0 7px 24px rgba(40,52,88,.05);
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: var(--night) !important;
    }
    [data-testid="stChatInput"] {
        border-color: rgba(82,110,211,.25);
        border-radius: 18px;
        background: rgba(255,255,255,.94) !important;
        box-shadow: 0 10px 30px rgba(40,52,88,.09);
    }
    [data-testid="stChatInput"] textarea {
        color: var(--night) !important;
        -webkit-text-fill-color: var(--night) !important;
    }

    .task-card, .empty-card, .metric-card {
        border: 1px solid var(--line);
        border-radius: 18px;
        background: var(--paper);
        box-shadow: 0 8px 26px rgba(40,52,88,.055);
    }
    .task-card { padding: .9rem 1rem; margin-bottom: .65rem; }
    .task-top { display: flex; align-items: center; gap: .65rem; }
    .check-ring {
        display: inline-flex;
        width: 23px;
        height: 23px;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
        border: 2px solid rgba(82,110,211,.35);
        border-radius: 50%;
        color: var(--blue);
        font-size: .7rem;
        font-weight: 900;
    }
    .task-title { color: var(--night); font-size: .92rem; font-weight: 760; }
    .task-meta { margin: .5rem 0 0 2.35rem; color: var(--muted); font-size: .74rem; }
    .priority {
        display: inline-flex;
        padding: .23rem .47rem;
        margin-right: .35rem;
        border-radius: 999px;
        font-weight: 800;
        text-transform: capitalize;
    }
    .priority-high { color: #a24d36; background: rgba(213,102,68,.12); }
    .priority-medium { color: #9b6727; background: rgba(213,141,56,.13); }
    .priority-low { color: #287c69; background: rgba(68,165,143,.13); }
    .empty-card { padding: 2rem 1.2rem; text-align: center; color: var(--muted); }
    .empty-icon { display: block; margin-bottom: .4rem; font-size: 1.7rem; }
    .metric-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: .65rem; margin-bottom: 1rem; }
    .metric-card { padding: .85rem .95rem; }
    .metric-value { color: var(--night); font-size: 1.45rem; font-weight: 850; }
    .metric-label { color: var(--muted); font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; }

    .stButton > button {
        width: 100%;
        border: 1px solid rgba(82,110,211,.18);
        border-radius: 14px;
        background: rgba(255,255,255,.72);
        color: #405271;
        font-weight: 680;
    }
    .stButton > button:hover {
        border-color: rgba(82,110,211,.48);
        color: #405bc2;
        background: white;
    }
    @media (max-width: 700px) {
        .hero { padding: 1.65rem 1.45rem; border-radius: 22px; }
        .hero h1 { font-size: 2.45rem; }
    }
</style>
"""


def _run_prompt(prompt: str, history: list[ChatMessage] | None = None) -> str:
    """Run one live agent request with a hard timeout."""

    try:
        return asyncio.run(
            asyncio.wait_for(run_once(prompt, history), timeout=60)
        )
    except TimeoutError:
        return "The request took longer than 60 seconds and was stopped. Please try again."
    except Exception as exc:
        return str(exc)


def _decode_output(raw_output: str) -> Any:
    """Decode the structured first-tool result returned by the agent."""

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        return raw_output


def _format_agent_output(raw_output: str) -> str:
    """Turn structured tool results into concise, readable chat responses."""

    payload = _decode_output(raw_output)
    if not isinstance(payload, dict):
        return str(payload)

    if "tasks" in payload:
        tasks = payload.get("tasks", [])
        if not tasks:
            return "Your task list is empty. Add something you want to remember."
        lines = [f"You have **{len(tasks)} task{'s' if len(tasks) != 1 else ''}:**"]
        for task in tasks:
            lines.append(
                f"- **{task['title']}** — {task['priority']} priority · {task['status']}"
            )
        return "\n".join(lines)

    if "task" in payload:
        task = payload["task"]
        created = payload.get("created", False)
        heading = "Task added" if created else "Already on your list"
        return (
            f"**{heading}.**\n\n"
            f"{task['title']} · {task['priority']} priority · {task['status']}"
        )
    return str(payload.get("message", raw_output))


def _task_card(task: Task) -> str:
    title = html.escape(task.title)
    priority = html.escape(task.priority)
    status = html.escape(task.status)
    return f"""
    <div class="task-card">
        <div class="task-top">
            <span class="check-ring">✓</span>
            <span class="task-title">{title}</span>
        </div>
        <div class="task-meta">
            <span class="priority priority-{priority}">{priority}</span>
            #{task.id} · {status}
        </div>
    </div>
    """


def _initialize_chat() -> None:
    if "todo_messages" not in st.session_state:
        st.session_state.todo_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! Tell me what you need to remember. I can show tasks, add one, "
                    "or add it only when it is not already there."
                ),
            }
        ]


def main() -> None:
    st.set_page_config(
        page_title="Taskflow · MCP To-Do Assistant",
        page_icon="✓",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)
    _initialize_chat()

    st.markdown(
        """
        <section class="hero">
            <span class="eyebrow">✓ Agent Tools Playground</span>
            <h1>Turn intent into action.</h1>
            <p>Test a natural-language to-do agent backed by exactly three MCP tools.
            Ask normally; the agent chooses the right read, write, or orchestration path.</p>
            <div class="tool-row">
                <span class="tool-chip"><span class="tool-dot">●</span>Data · get_tasks</span>
                <span class="tool-chip"><span class="tool-dot">●</span>Action · add_task</span>
                <span class="tool-chip"><span class="tool-dot">●</span>Orchestration · add_task_if_missing</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    chat_column, tasks_column = st.columns([1.55, 1], gap="large")
    prompt: str | None = None

    with chat_column:
        st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="panel-copy">Try the orchestration prompt twice to see duplicate prevention.</p>',
            unsafe_allow_html=True,
        )
        quick_columns = st.columns(3)
        quick_prompts = [
            ("Show tasks", "Show me all of my tasks."),
            ("Add a task", "Add Review lecture notes as a medium-priority task."),
            (
                "Avoid duplicates",
                "Add Finish my MCP assignment as high priority, but only if it is not already there.",
            ),
        ]
        for column, (label, value) in zip(quick_columns, quick_prompts):
            with column:
                if st.button(label, use_container_width=True):
                    prompt = value

        for message in st.session_state.todo_messages:
            avatar = "✅" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

        typed_prompt = st.chat_input("What do you need to remember?")
        if typed_prompt:
            prompt = typed_prompt

        if prompt:
            history = list(st.session_state.todo_messages)
            st.session_state.todo_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="✅"):
                with st.spinner("Choosing the right MCP tool…"):
                    response = _format_agent_output(_run_prompt(prompt, history))
                st.markdown(response)
            st.session_state.todo_messages.append(
                {"role": "assistant", "content": response}
            )

    with tasks_column:
        st.markdown('<div class="section-label">Live task state</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="panel-copy">This panel reads the same local JSON used by the MCP server.</p>',
            unsafe_allow_html=True,
        )
        try:
            task_result = default_service.get_tasks("all")
            tasks = task_result.tasks
            high_priority = sum(task.priority == "high" for task in tasks)
            st.markdown(
                f"""
                <div class="metric-row">
                    <div class="metric-card">
                        <div class="metric-value">{len(tasks)}</div>
                        <div class="metric-label">Total tasks</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{high_priority}</div>
                        <div class="metric-label">High priority</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if tasks:
                for task in reversed(tasks):
                    st.markdown(_task_card(task), unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="empty-card"><span class="empty-icon">◎</span>'
                    "No tasks yet.<br>Use the chat to add your first one.</div>",
                    unsafe_allow_html=True,
                )
        except (ValueError, OSError) as exc:
            st.error(str(exc))


def launch() -> None:
    """Launch Streamlit on a port separate from the recipe interface."""

    port = os.getenv("TODO_UI_PORT", "8502")
    ui_path = Path(__file__).resolve()
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(ui_path),
                "--server.port",
                port,
                "--server.headless",
                "true",
            ]
        )
    )


if __name__ == "__main__":
    main()

