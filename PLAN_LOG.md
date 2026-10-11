# PLAN_LOG.md — Priority Field via Plan Mode (PA5 Task 1)

Feature: optional integer `priority` 1–5 on tasks (1 = urgent, 5 = low, default 3). Accepted on
`POST /tasks` and `PATCH /tasks/{id}`, returned in every task response, and filterable with
`GET /tasks?priority={n}`.

Baseline before session 1: `pytest -q` → `12 passed`; `ruff check .` → 5 findings (pre-existing).

| Session # | Prompt summary (≤15 words) | Did you amend the plan? | What you changed | Did output match amended plan? |
|---|---|---|---|---|
| 1 | | Yes / No | | Yes / Partially / No |
| 2 | | Yes / No | | Yes / Partially / No |
| 3 | | Yes / No | | Yes / Partially / No |
| 4 | | Yes / No | | Yes / Partially / No |

Final `pytest -q`: _paste here_
