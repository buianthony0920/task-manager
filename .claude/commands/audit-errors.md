# Use to bring one services/ file's error handling in line with utils/errors.py; not for routes/, tests/, or adding new behaviour.

Audit and fix error handling in `$ARGUMENTS`.

## Goal
Every public function in `$ARGUMENTS` signals failures only with `AppError` subclasses from
`utils/errors.py`: `NotFoundError(resource)` for a missing record (404) and
`ValidationError(field, reason)` for bad input (422). When you finish, no function in the file
raises `Exception`, `ValueError`, `KeyError` or `TypeError`, and no dict lookup can leak a
`KeyError`.

If `$ARGUMENTS` is empty, stop and ask which file to audit. Do not pick one yourself.

## Context
- `utils/errors.py` defines `AppError(message, status_code)`, `NotFoundError` and `ValidationError`.
- `services/users.py` is the canonical pattern: check first, then raise, e.g.
  `if user_id not in USERS: raise NotFoundError("User")`.
- `handle_app_error` in `routes/api.py` turns any `AppError` into `{"error": message}` with its
  status code, so a correct raise in the service is all the route needs.
- `tests/test_tasks.py` and `tests/test_users.py` assert exact error types with
  `pytest.raises(NotFoundError)` / `pytest.raises(ValidationError)`.

## Steps
1. List every function in `$ARGUMENTS` with one line each: already correct, or what is wrong.
   Show me this list before editing anything.
2. Fix the functions marked wrong, one function at a time, in file order.

## Constraints
- **Idempotency:** if a function already raises the right `AppError` subclass for each failure
  and cannot leak a `KeyError`, mark it "already correct — skipped" and do not rewrite it. Do not
  reformat, rename, re-document or reorder it. Running this command twice on the same file must
  produce no diff the second time.
- **Scope lock:** edit only `$ARGUMENTS`. Do not touch `utils/errors.py` (its constructors are
  read by `handle_app_error`), `routes/api.py`, `requirements.txt`, or any `.md` file.
- If a test in `tests/` uses `pytest.raises(Exception)` for a function you fixed, you may make
  that one assertion stricter. Never delete a test or loosen an assertion.
- Do not change a function's signature or the sample data in `TASKS` / `USERS`.
- Do not add new error classes. If none of the existing ones fits, stop and ask.

## Verification
- After every function you change, run `.venv\Scripts\python -m pytest -q` and report the
  summary line before moving to the next function. If it fails, fix that function before going on.
- At the end, run `.venv\Scripts\ruff check .` and confirm no new findings.
- Finish with a table: function | before | after | skipped? (yes/no).
