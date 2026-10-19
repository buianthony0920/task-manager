# Use to add one new field to an existing resource's records end to end (data, service, route, tests), like `priority` on tasks or `notification_pref` on users; not for new resources (use /scaffold-endpoint) or for renaming/removing a field.

Add a field to an existing resource. Arguments: `$ARGUMENTS`

`$ARGUMENTS` is `<resource> <field> <allowed values> <default>`, for example
`tasks due_date "ISO date string YYYY-MM-DD or None" None` or
`users timezone "one of UTC, EST, PST" UTC`. Echo back RESOURCE, FIELD, ALLOWED and DEFAULT
before editing. If any of the four is missing, stop and ask.

## Goal
Records in `services/RESOURCE.py` carry FIELD with DEFAULT, it can be set on create and updated,
bad values raise a 422, and both behaviours are covered by tests. Files that change:
1. `services/RESOURCE.py`: add FIELD to every sample record, to the create function's record,
   one `_validate_FIELD` helper, and the update path.
2. `routes/api.py`: pass `data.get("FIELD")` through to the service. Nothing else.
3. `tests/test_RESOURCE.py`: new tests only (see Verification).

## Context
- This is how `priority` was added to tasks (`_validate_priority` in `services/tasks.py`, reused
  by `create_task`, `list_tasks` and `update_task`) and how `notification_pref` was added to users
  (`VALID_NOTIFICATION_PREFS` plus `set_notification_pref` in `services/users.py`). Follow them.
- The validator is the single check: every service function that accepts FIELD calls it.
- Routes pass raw values (even `None`) to the service and never validate; `handle_app_error`
  turns the `ValidationError` into a 422.

## Constraints
- New parameters go **last and with a default** (`FIELD=DEFAULT`). The signatures of
  `get_task`, `create_task`, `process_order`, `get_user` and `create_user` are called by position,
  so never reorder or remove existing parameters.
- Keep the existing sample data ids and values (task 2 is "Write report", id 999 must not exist);
  only add the new key with DEFAULT.
- Do not touch `utils/errors.py`, `requirements.txt`, `app.py`, existing tests or any `.md` file.
- Use `ValidationError("FIELD", "<reason>")` for bad values. Never raise `ValueError`.

## Verification
- After each of the three files, run `.venv\Scripts\python -m pytest -q` and report the summary line.
- New tests must cover: the default is present on an existing record; create with a valid value
  stores it; an invalid value raises `ValidationError` in the service and returns 422 through
  `app.test_client()`.
- Run `.venv\Scripts\ruff check .` at the end and confirm no new findings.
