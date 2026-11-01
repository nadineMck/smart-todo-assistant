# 5-7 Minute Screencast Script

## Before recording

1. Ensure `data/tasks.json` contains `{"tasks": []}`.
2. Start the interface with `uv run todo-ui` and open `http://localhost:8502`.
3. Keep the project folder, `server.py`, `services.py`, and a terminal ready.
4. Never show `.env` or the API key on screen.

## 0:00-0:40 - Introduction

“This is my EECE 503P/798S Agent Tools project, the Smart To-Do Assistant. It uses
FastMCP for the server and the OpenAI Agents SDK as the host/client. The model provider
is Gemini through the SDK's LiteLLM adapter. Data is stored locally in JSON, so the
project requires no external task service.”

Show the project folder and the architecture section in `README.md`.

## 0:40-1:30 - Exactly three tools

Show `src/todo_mcp/server.py` and identify:

- Data: `get_tasks`, which reads tasks without changing state.
- Action: `add_task`, which validates and persists one task.
- Orchestration: `add_task_if_missing`, which reads first and writes only if absent.

Point out the descriptions, typed arguments, typed Pydantic results, and `ToolError`
handling. Emphasize that the UI does not add more MCP tools.

## 1:30-2:15 - Orchestration design

Show `TodoService.add_task_if_missing` in `services.py`.

“The orchestration logic calls the same read operation used by the Data tool, normalizes
the title for a case-insensitive duplicate check, and calls the same write operation used
by the Action tool only when the task is missing. The model does not decide whether two
titles are duplicates; deterministic code does.”

## 2:15-2:45 - Tests

Run:

```bash
uv run pytest
```

Show that all tests pass. Mention that `test_mcp_contract.py` proves the server exposes
exactly the three required names. Other tests cover persistence, filtering, duplicate
prevention, invalid priority, blank titles, malformed JSON, conversation context, and
safe API-error redaction.

## 2:45-4:40 - Live full round trip

In the UI, click **Show tasks**. Explain the route: natural language -> Agents SDK host
-> MCP client over stdio -> FastMCP Data tool -> structured result -> UI.

Click **Add a task**. Show the new task card and explain that this is the Action tool's
persistent side effect.

Click **Avoid duplicates** once. If the assignment task is absent, it is created through
the Orchestration tool. Click it again and show **Already on your list**, proving the
second request did not create another record.

Ask: “What priority is the task you just checked?” Show that recent conversational
context resolves the reference without changing task state.

## 4:40-5:25 - Predictable failure

In the terminal run:

```bash
uv run todo-tools-demo
```

Point out the explicit blank-title failure: `title must not be blank.` Explain that the
tool returns a clear error and leaves the task file unchanged instead of silently failing.

## 5:25-6:15 - Challenges and reflection

“The main design challenge was keeping each tool single-purpose while making the
orchestration tool genuinely useful. Duplicate prevention belongs in deterministic
business logic, not only in the model prompt. Another challenge was preserving short
conversation follow-ups without adding more tools. Recent turns are supplied as context,
while greetings are handled locally to avoid unnecessary API calls.”

Discuss the tradeoff: local JSON is ideal for a reproducible single-user demo, while a
production version would use transactional storage and idempotency keys.

## 6:15-6:35 - Conclusion

Show `README.md`, `SUMMARY.md`, and `REFLECTION.md`, then display the repository URL.
Conclude: “The project demonstrates one Data tool, one Action tool, and one Orchestration
tool through the complete agent-to-MCP round trip, with typed outputs, predictable
failures, tests, and duplicate-safe persistence.”


