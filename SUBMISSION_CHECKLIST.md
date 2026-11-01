# Submission Checklist

## Required files included

- [x] `SUMMARY.md` - 300-400 word reading and existing-server review
- [x] `src/todo_mcp/server.py` - FastMCP server with exactly three tools
- [x] `src/todo_mcp/agent.py` - OpenAI Agents SDK host/client
- [x] `README.md` - setup, configuration, testing, and run instructions
- [x] `tests/` - unit and contract tests, including predictable failures
- [x] `src/todo_mcp/demo.py` - deterministic demonstration and failure case
- [x] `REFLECTION.md` - two-paragraph design reflection
- [x] `SCREENCAST.md` - timed 5-7 minute recording script
- [x] `.env.example` - safe configuration template
- [x] `data/tasks.json` - clean initial state

## Final checks already completed

- [x] Exactly three MCP tools: `get_tasks`, `add_task`, `add_task_if_missing`
- [x] Data, Action, and Orchestration categories are explicitly documented
- [x] Typed arguments and Pydantic outputs
- [x] Predictable validation and data-file errors
- [x] Duplicate prevention is deterministic
- [x] End-to-end Gemini -> Agents SDK -> MCP -> JSON flow tested
- [x] Local UI tested on port 8502
- [x] API key excluded from source package

## Student actions still required

- [x] Create a GitHub repository and push the contents of this folder
- [x] Repository URL: https://github.com/nadineMck/smart-todo-assistant
- [x] Record the 5-7 minute screencast using `SCREENCAST.md`
- [ ] Upload the recording, for example as an unlisted YouTube or Zoom video
- [ ] Paste the video URL below
- [ ] Open both links in a private/incognito window to verify access
- [ ] Submit the links and any required files through the course submission page

## Links to paste before submission

- Repository: `https://github.com/nadineMck/smart-todo-assistant`
- Screencast: `PASTE_VIDEO_URL_HERE`

## Suggested repository commands

Run these from inside `smart_todo_assistant` after creating an empty GitHub repository:

```bash
git init
git add .
git commit -m "Submit Smart To-Do MCP assistant"
git branch -M main
git remote add origin PASTE_GITHUB_REPOSITORY_URL_HERE
git push -u origin main
```

Do not add `.env`, `.venv`, `.pytest_cache`, API keys, or editor-specific files.

