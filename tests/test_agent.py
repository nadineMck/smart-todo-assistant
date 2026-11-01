"""Small tests for safe agent and conversation helper behavior."""

from todo_mcp.agent import (
    _build_agent_prompt,
    _final_output_text,
    _local_response,
    _safe_provider_error,
)


def test_extracts_structured_text_result() -> None:
    assert _final_output_text("{'type': 'text', 'text': 'done'}") == "done"


def test_redacts_api_key_from_provider_error() -> None:
    key = "secret-key"
    error = RuntimeError(f"request failed?key={key} and body={key}")
    message = _safe_provider_error(error, key)
    assert key not in message
    assert "[REDACTED]" in message


def test_greetings_are_answered_locally() -> None:
    assert "What task" in _local_response("hello")
    assert "Taskflow" in _local_response("who are u")
    assert _local_response("show my tasks") is None


def test_priority_follow_up_uses_last_verified_single_task() -> None:
    history = [
        {
            "role": "assistant",
            "content": (
                "**Already on your list.**\n\n"
                "Finish my MCP assignment · high priority · pending"
            ),
        }
    ]

    assert _local_response("what priority is it?", history) == (
        "'Finish my MCP assignment' is a high-priority task."
    )


def test_recent_conversation_is_included_for_follow_ups() -> None:
    history = [
        {"role": "user", "content": "Add Study calculus as high priority."},
        {"role": "assistant", "content": "Task added: Study calculus."},
    ]

    prompt = _build_agent_prompt("Is it on my list?", history)

    assert "Study calculus" in prompt
    assert "Latest user message: Is it on my list?" in prompt
    assert "latest message is authoritative" in prompt

