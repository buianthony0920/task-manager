# COMMAND_LOG.md: Week 6 Task 1 (Slash Command Library)

<!-- TODO (me): run each command in a Claude Code session opened in task-manager/, then fill in
     the row. "Stayed in scope" = Claude only touched the files the command allows.
     If it drifted, edit the command file, re-run, and add a second row for that command.
     Revert any code changes you don't want to keep with `git restore` afterwards. -->

| # | Command invoked | $ARGUMENTS used | Stayed in scope? (Yes/No) | What worked / what I changed |
|---|---|---|---|---|
| 1 | `/audit-errors` | `services/tasks.py` | | |
| 2 | `/scaffold-endpoint` | `tags POST` | | |
| 3 | `/add-field` | `tasks due_date "ISO date YYYY-MM-DD or None" None` | | |

Suggested follow-up runs (add a row each):
- `/audit-errors services/tasks.py` **a second time**: should produce no diff (idempotency constraint).
- `/audit-errors` with no argument: should stop and ask instead of picking a file.
- `/scaffold-endpoint tags` (one argument): should stop and ask for METHOD.
