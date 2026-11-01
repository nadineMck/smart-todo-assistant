# Smart To-Do Assistant MCP Toolkit

Repository: https://github.com/nadineMck/smart-todo-assistant

This is a separate EECE 503P/798S Agent Tools project. The original recipe project in
the parent folder remains unchanged. This project demonstrates exactly three MCP tools
built with FastMCP and used by an OpenAI Agents SDK host. Gemini is connected through
the SDK's LiteLLM adapter.

## Exactly Three Tools

| Category | Tool | Purpose | Changes data? |
|---|---|---|---|
| Data | `get_tasks(status)` | Retrieve all, pending, or completed tasks | No |
| Action | `add_task(title, priority)` | Add a pending task to local JSON | Yes |
| Orchestration | `add_task_if_missing(title, priority)` | Read tasks, then add only when absent | Only when missing |

The orchestration tool performs a genuine check-then-act workflow: it calls the same
service operation as `get_tasks`, performs a case-insensitive duplicate check, and only
then calls the same service operation as `add_task`.

## Architecture

```text
User
  -> OpenAI Agents SDK host (Gemini through LiteLLM)
  -> MCP over stdio
  -> FastMCP server
       |-- get_tasks             -> reads data/tasks.json
       |-- add_task              -> writes data/tasks.json
       `-- add_task_if_missing   -> coordinates read + conditional write
```

## Setup and Test

```bash
cd smart_todo_assistant
uv sync --extra dev
uv run pytest
```

The test suite checks the exact three-tool contract, read-only filtering, persistence,
input validation, malformed data, and duplicate prevention.

## Run Without an API Key

```bash
uv run todo-tools-demo
```

This deterministic demo uses a temporary JSON file, shows every tool category, and runs
the duplicate request twice without changing the project's saved task list.

## Run the Live Agent

Copy `.env.example` to `.env`, paste the Gemini key, and run:

```bash
uv run todo-agent
```

Example one-shot request:

```bash
uv run todo-agent "Add 'Finish my MCP assignment' as high priority, but only if it is not already there."
```

The agent uses exactly one model call to select one MCP tool, and the structured tool
result is authoritative. OpenAI tracing is disabled because Gemini credentials are used.

## Run the Local Web Interface

```bash
uv run todo-ui
```

Open `http://localhost:8502`. The UI offers natural-language chat, three quick test
prompts, and a live read-only view of `data/tasks.json`. It deliberately stays on port
8502 so the original recipe interface can continue running on port 8501. The interface
does not introduce any additional MCP tools; task reads and writes still use the exact
three-tool server described above. Recent chat turns are passed to the agent for short
follow-ups, while greetings and basic help are answered locally without an API call.

## Predictable Failures

- Blank or non-text title
- Title longer than 200 characters
- Priority other than `low`, `medium`, or `high`
- Status filter other than `all`, `pending`, or `completed`
- Missing, malformed, or structurally invalid JSON
- Missing Gemini key for the live agent

Reset `data/tasks.json` to `{"tasks": []}` before recording the demonstration.

