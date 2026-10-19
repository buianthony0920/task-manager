# Task Manager

A Flask JSON API for tasks and users. `app.py` loads the routes from `routes/api.py`
under `/api`.

## Commands
- Install (once): `python -m venv .venv` then `.venv\Scripts\pip install -r requirements.txt ruff`
- Run tests: `.venv\Scripts\python -m pytest -v`. Run them before you finish any task. All must pass.
- Quick check: `.venv\Scripts\python -m pytest -q`. Run it after every step and report the
  summary line in your reply. The human records it in the log; don't edit log files yourself.
- Run the user tests: `.venv\Scripts\python -m pytest tests/test_users.py -q`
- Run one file: `.venv\Scripts\python -m pytest tests/test_tasks.py -v`
- Lint: run `.venv\Scripts\ruff check .` before you start and again when you're done.
  Don't add any new findings, and don't fix old ones unless asked.
- Run server: `.venv\Scripts\python app.py`, then open http://127.0.0.1:5000/api/tasks/1
- `/audit-errors <file>`: make one `services/` file raise only `AppError` subclasses; skips
  functions that are already correct. Not for `routes/` or `tests/`.
- `/scaffold-endpoint <resource> <METHOD>`: add one new endpoint (route + service + schema +
  happy-path test), e.g. `/scaffold-endpoint tags POST`. Not for changing an existing endpoint.
- `/add-field <resource> <field> <allowed> <default>`: add one field to an existing resource
  end to end, the way `priority` and `notification_pref` were added. Not for new resources.
- Test the hook: `.venv\Scripts\python .claude\hooks\run_vectors.py` (all cases must say `ok`).

## Architecture
Three layers: routes → services → repositories. Each layer only calls the one below it.
- `routes/api.py`: HTTP only. Read the request, call one service function, return
  `jsonify(...)`. Routes exist for `get_task`, `list_tasks`, `create_task`, `update_task` and `get_user`.
  `process_order` has no route, so its errors never reach the API.
- `services/*.py`: the logic and input checks. Errors are `AppError` subclasses.
  Use `services/users.py` as the example.
- Tasks have `priority`: an int 1 (urgent)–5 (low), default 3. `_validate_priority` in
  `services/tasks.py` is the single check — reuse it; routes pass raw values through
  (`GET /tasks?priority=` passes the query string to `list_tasks`).
- Repositories: there's no `repositories/` folder yet. The data lives in the dicts
  `TASKS` (`services/tasks.py`) and `USERS` (`services/users.py`). Only code in the same
  file may read or change them. To use another file's data, call its function instead
  (e.g. `tasks.py` calls `get_user` and lets its `NotFoundError("User")` pass through).
- `utils/errors.py`: `AppError(message, status_code)` is the base class.
  `NotFoundError(resource)` gives a 404, and `ValidationError(field, reason)` gives a 422.
  `handle_app_error` in `routes/api.py` turns any `AppError` into `{"error": message}`.
- services/ ↔ routes/ boundary: `services/users.py` is the canonical pattern. It owns `USERS`,
  `VALID_NOTIFICATION_PREFS` and every value check (`set_notification_pref` raises the 422), while
  `routes/api.py` only does `request.get_json(silent=True) or {}`, passes raw values (even `None`)
  to one service function, and never imports `USERS` or validates.

## Conventions
- Follow `services/users.py` as the pattern for every service function.
- Add type hints to every parameter and return value: `def get_user(user_id: int) -> dict:`.
- Add a Google-style docstring with `Args:`, `Returns:` and `Raises:`, laid out like
  `get_user` in `services/users.py`.
- Missing record: check first, then raise: `if task_id not in TASKS: raise NotFoundError("Task")`.
  Never let a `KeyError` through, and never raise `Exception`, `ValueError`, etc.
- Bad input: `raise ValidationError("title", "cannot be empty")`, like `create_user` does.
- Import errors at the top of the file: `from utils.errors import NotFoundError, ValidationError`.
- Tests in `tests/test_tasks.py` check for the exact error, e.g. `pytest.raises(NotFoundError)`.
  If you fix a function whose test uses `pytest.raises(Exception)`, make that test
  stricter. Don't add a second test for the same thing.
- Undecided — ask, don't guess: whether completing a task that's already done in
  `process_order` is an error, and whether to trim spaces from titles.

## Hooks
`.claude/hooks/guard_writes.py` runs before every `Write`, `Edit`, `MultiEdit` and `Bash` call
(registered in `.claude/settings.json`) and exits 2 to block it, so these rules hold even if
Claude ignores this file. It blocks (1) writes to the files in `BLOCKED_PATHS`
(`utils/errors.py`, `requirements.txt`, `DECOMPOSITION.md`, `PLAN_LOG.md`) in any letter case,
including Bash redirects, `tee`, `cp`, `sed -i` or `python -c` writes; (2) Bash commands in
`BASH_RULES`: `DROP/TRUNCATE TABLE`, `rm` with `-r` and `-f`, and `git push --force`/`-f`; and
(3) a hardcoded `postgresql://` or `sqlite:///` string in any file in `CONTENT_GUARDED`
(`services/tasks.py`). To protect another file, add its repo-relative path to `BLOCKED_PATHS`
(or to `CONTENT_GUARDED` for a content check); to ban a command, add a
`(name, check, reason)` tuple to `BASH_RULES`. Then add a blocked and an allowed case to
`CASES` in `.claude/hooks/run_vectors.py` and run it until every line says `ok`. Since
`utils/errors.py` is blocked, Claude can't add a new error class itself; ask the human.

## Do not touch
- The sample data in `TASKS` (ids 1–3) and `USERS` (ids 1–2). The tests need task 2 to
  be "Write report" and id 999 to not exist.
- The signatures of `get_task`, `create_task`, `process_order`, `get_user` and
  `create_user`. The routes and tests call the task functions by position.
- Existing tests. Never delete one or make it weaker just to get the tests passing.
- `RETRO.md`, `COMMAND_LOG.md`, `HOOK_LOG.md`: never edit these during a coding task, even to
  record pytest results. Put results in your reply.
- When the task is `services/users.py`, don't touch `routes/api.py` or `tests/`.
- When the task is `routes/api.py`, don't touch `services/users.py`, and don't import `USERS`
  or check `notification_pref` values in the route. (SA-3 near-miss.)
- When the task is `tests/test_users.py`, modify only that file. Not `services/`, `routes/`,
  `tests/test_tasks.py` or any `.md` file. If a test fails because of source code, report it.
