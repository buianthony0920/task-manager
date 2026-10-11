# Task Manager

Flask JSON API for tasks and users. `app.py` registers the `api` blueprint from
`routes/api.py` under the `/api` prefix.

## Commands
- Install (once): `python -m venv .venv` then `.venv\Scripts\pip install -r requirements.txt ruff`
- Run tests: `.venv\Scripts\python -m pytest -v` — run before finishing any task; all tests must pass
- Run one file: `.venv\Scripts\python -m pytest tests/test_tasks.py -v`
- Lint: `.venv\Scripts\ruff check <files you changed>`
  - Baseline: 6 existing findings in `app.py`, `routes/api.py`, `tests/test_tasks.py`.
    Do not add new findings; do not "fix" the baseline unless asked.
- Run server: `.venv\Scripts\python app.py` → http://127.0.0.1:5000/api/tasks/1

## Architecture
Layered: routes → services → repositories. Each layer only calls the one below it.
- `routes/api.py` — HTTP only: read the request, call one service function, return
  `jsonify(...)`. No business logic and no direct access to `TASKS`/`USERS`.
- `services/*.py` — business logic and validation; raises `AppError` subclasses.
  Canonical example: `services/users.py`.
- Repository layer — there is no `repositories/` package yet. The data store is the
  module-level dicts `TASKS` (`services/tasks.py`) and `USERS` (`services/users.py`).
  Only functions in the same module read or write them.
- `utils/errors.py` — `AppError(message, status_code)` base;
  `NotFoundError(resource)` → 404, `ValidationError(field, reason)` → 422.
  `handle_app_error` in `routes/api.py` turns any `AppError` into `{"error": message}`.
- `tests/test_tasks.py` — pytest tests that import directly from `services.tasks`.

## Conventions
- Follow `services/users.py` as the pattern for every service function.
- Type hints on every parameter and return value: `def get_user(user_id: int) -> dict:`.
- Google-style docstring with `Args:`, `Returns:`, `Raises:` sections, laid out exactly
  like `get_user` in `services/users.py`.
- Missing record: check first, then raise — `if task_id not in TASKS: raise NotFoundError("Task")`.
  Never let a `KeyError` escape, and never raise `Exception`, `ValueError`, etc.
- Bad input: `raise ValidationError("title", "cannot be empty")`, as in `create_user`.
- Import errors at module top: `from utils.errors import NotFoundError, ValidationError`.
- New service function → add a test in `tests/test_tasks.py` that asserts the specific
  class, e.g. `pytest.raises(NotFoundError)`, not `pytest.raises(Exception)`.

## Do not touch
- Constructors in `utils/errors.py`: `handle_app_error` reads `e.message` and
  `e.status_code`. Add new subclasses instead of changing existing ones.
- Seed records in `TASKS` (ids 1–3) and `USERS` (ids 1–2): tests rely on task 2 being
  "Write report" and on id 999 not existing.
- Signatures of `get_task`, `create_task`, `process_order`, `get_user`, `create_user`:
  `routes/api.py` calls them positionally.
- Existing tests in `tests/test_tasks.py`: never delete or loosen one to get a green run.
- `requirements.txt` pins `flask==3.0.0` and `pytest==8.0.0`; do not add or bump
  dependencies without asking.
