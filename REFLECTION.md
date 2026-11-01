# Design Reflection

The Smart To-Do Assistant deliberately uses a small local domain so the demonstration
focuses on tool design instead of third-party API setup. `get_tasks` is read-only and
therefore clearly represents the Data category. `add_task` validates and persists one
new record, making its side effect easy to inspect. `add_task_if_missing` represents
orchestration because it first performs the read operation, makes a decision from that
result, and invokes the write operation only when needed.

The most important design choice is that duplicate detection is deterministic business
logic rather than an instruction left to the language model. Titles are whitespace-
normalized and compared case-insensitively. Repeating the same natural-language request
therefore returns the existing task and leaves the JSON file unchanged. Typed Pydantic
outputs also give the agent an explicit `created` flag, so it does not need to infer
whether a write occurred. Three tools felt appropriate because each responsibility stays
easy to discover and test while the orchestration behavior is still meaningful. Local
JSON keeps the project easy to run and explain, although it is not intended for multiple
concurrent writers. A production version would use a transactional database, an
idempotency key, and additional tools for completing or deleting tasks. Those additions
are unnecessary for the single-user assignment demo and would obscure the required
three-tool architecture.

