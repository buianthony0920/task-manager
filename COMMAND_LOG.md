# COMMAND_LOG.md: Week 6 Task 1 (Slash Command Library)

"Stayed in scope" = Claude only touched the files the command allows (checked with `git status` / `git diff`).

| # | Command invoked | $ARGUMENTS used | Stayed in scope? (Yes/No) | What worked / what I changed |
|---|---|---|---|---|
| 1 | `/audit-errors` | `services/tasks.py` | Yes | All 6 functions were already correct, so it skipped every one (idempotency held, `git status` clean, pytest 60 passed, ruff clean); it also found two gaps (`create_task` doesn't call `get_user`; `max(TASKS.keys())` raises `ValueError` if `TASKS` is empty) and only reported them. The command never said what to do with out-of-scope findings, so I added a constraint: list them under "Out of scope" and don't fix them. |
| 2 | `/scaffold-endpoint` | `tags POST` | Yes | It touched only the 4 allowed files (`routes/api.py`, `services/tags.py`, `schemas/tags.py` + `__init__.py`, `tests/test_tags.py`); the handler is 3 lines with no logic; the happy-path test asserts 201 + `name == "urgent"`; pytest 61 passed, ruff clean; it flagged trimming/duplicate names instead of guessing. But `REQUIRED_FIELDS` in `schemas/tags.py` is never used, because the handler passes single values and the service validates, so I removed `REQUIRED_FIELDS` from the command's schema spec (now just a `TypedDict` used as the return type). |
| 3 | `/add-field` | `tasks due_date "ISO date YYYY-MM-DD or None" None` | Yes | It touched only `services/tasks.py`, `routes/api.py`, `tests/test_tasks.py`; it ran pytest after each file (61 → 61 → 75 passed), ruff clean; `due_date=None` went last on `create_task`/`update_task`, sample rows only gained the key, and `_validate_due_date` rejects `2026-02-30`, `20260101`, numbers and `True`. It only noticed *after* finishing that a PATCH can't clear a due date (null and "left out" look the same), so I added a constraint: when DEFAULT is `None`, ask how update should treat missing/null **before** editing. |

Suggested follow-up runs (add a row each):
- `/audit-errors services/tasks.py` **a second time**: should produce no diff (idempotency constraint).
- `/audit-errors` with no argument: should stop and ask instead of picking a file.
- `/scaffold-endpoint tags` (one argument): should stop and ask for METHOD.
