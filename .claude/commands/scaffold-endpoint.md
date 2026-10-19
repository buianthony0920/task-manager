# Use to add one new HTTP endpoint for a resource (e.g. `/scaffold-endpoint tags POST`); not for changing an existing endpoint.

Scaffold a new API endpoint. Arguments: `$ARGUMENTS`

`$ARGUMENTS` holds two space-separated values: the first is RESOURCE (plural, lowercase, e.g.
`tags`) and the second is METHOD (one of GET, POST, PATCH, DELETE). Before writing any code,
echo back "RESOURCE=<value> METHOD=<value>". If either value is missing or METHOD is not one of
those four, stop and ask. Do not guess.

## Goal
`METHOD /api/RESOURCE` (or `/api/RESOURCE/<int:id>` for GET-one, PATCH and DELETE) works
end to end. These files must be created or updated, and no others:
1. **Route file:** `routes/api.py`. Add one thin handler for the new endpoint.
2. **Service file:** `services/RESOURCE.py`. Create it if missing; add the one service function
   the handler calls, plus the in-memory data dict if the file is new.
3. **Schema file:** `schemas/RESOURCE.py`. Create it if missing (and `schemas/__init__.py`).
   It holds the record shape as a `TypedDict`, used as the service function's return type.
   Don't add field lists or validation here: the service does every value check.
   This repo has no schema library, and you must not add one.
4. **Test file:** `tests/test_RESOURCE.py`. Add the happy-path test described under Verification.

## Context
- `routes/tasks.py` is the canonical route pattern. In this repo the task routes live in
  `routes/api.py` (`get_task_route`, `list_tasks_route`, `create_task_route`,
  `update_task_route`); copy their shape. Do not create a separate `routes/tasks.py`.
- A handler does exactly three things: read input (`request.get_json(silent=True) or {}` or the
  URL id), call **one** service function passing raw values through (even `None`), and return
  `jsonify(...)` with a status code (201 for POST, 200 otherwise).
- `services/users.py` is the canonical service pattern: it owns its data dict, does every value
  check, raises `NotFoundError` / `ValidationError` from `utils/errors.py`, and has type hints and
  a Google-style docstring (`Args:`, `Returns:`, `Raises:`).
- `handle_app_error` in `routes/api.py` already converts any `AppError` to JSON. Don't add
  try/except in the handler.

## Constraints
- **No business logic in the route handler.** No `if` checks on values, no validation, no
  defaults beyond `data.get("field")`, no loops, no touching a data dict, no importing a data dict
  (`TASKS`, `USERS`, the new one) into `routes/api.py`. All of that goes in the service.
- Only the four files listed in Goal may change. Do not touch `app.py`, `utils/errors.py`,
  `requirements.txt`, existing tests, or any `.md` file.
- Do not modify existing handlers or service functions, even to "tidy" them.
- Do not add packages (no marshmallow, pydantic, etc.).

## Verification
- Run `.venv\Scripts\python -m pytest -q`. All existing tests plus the new one must pass.
- The new test in `tests/test_RESOURCE.py` uses `app.test_client()` (from `app import app`),
  sends one valid METHOD request to the new endpoint, and asserts the exact happy-path status:
  `201` for POST, `200` for GET / PATCH / DELETE. It also asserts one field of the JSON body.
- Run `.venv\Scripts\ruff check .` and confirm no new findings.
- Report: the files changed, the new route line, the pytest summary line, and the status code
  the test asserted.
