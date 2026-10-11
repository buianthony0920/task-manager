# DECOMPOSITION.md — Notification Preference Pipeline (PA5 Task 2)

Written before opening Claude Code for Task 2. Each subagent runs in a **fresh session**
(`/clear` or relaunch) and is given the exact prompt in its "Prompt" block below.

## Starting state

- Baseline before SA-1: `pytest -q` → `46 passed` (after Task 1; was `12 passed` before Task 1)
- Baseline `ruff check .` → `All checks passed!` (0 findings; the 5 pre-existing ones were fixed in
  Task 1 session 7). Must stay at 0.

## Design decisions fixed up front

- **"User model / nullable column"**: this codebase has no ORM. The "model" is the `USERS`
  dict in `services/users.py`, and the "column" is a `notification_pref` key on each record.
- **Allowed values**: `"email"`, `"sms"`, `"none"`. Default is `"none"`. `None`/missing is
  treated as `"none"` when read (nullable for older records).
- **"Existing user list endpoint"**: there is no `GET /api/users` route today, only
  `GET /api/users/<id>`. SA-2 adds `list_users()` and SA-3 adds the route so both the list and
  the detail responses include `notification_pref`.
- Errors: invalid value → `ValidationError("notification_pref", "must be one of email, sms, none")`
  (422). Unknown user → `NotFoundError("User")` (404).

## Subagent table

| Subagent # | Input (context files) | Task | Output (files created/modified) | Constraint (must NOT touch) | Hand-off |
|---|---|---|---|---|---|
| **SA-1: Data layer** | `CLAUDE.md`, `services/users.py`, `utils/errors.py` | Add the `notification_pref` field to every user record and a `VALID_NOTIFICATION_PREFS` constant. | `services/users.py` (`USERS` records, `create_user` body, new constant only) | Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, `tests/`. Do not add new functions to `services/users.py`. Do not change ids, names, emails in `USERS` or the `create_user` signature. | `VALID_NOTIFICATION_PREFS = ("email", "sms", "none")` in `services/users.py`; every record in `USERS` has `"notification_pref": "none"`. |
| **SA-2: Service layer** | `CLAUDE.md`, `services/users.py`, `utils/errors.py` | Add `get_notification_pref`, `set_notification_pref`, `list_users` service functions. | `services/users.py` (new functions only) | Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, `tests/`. Do not edit the `USERS` dict, `VALID_NOTIFICATION_PREFS`, `get_user`, or `create_user`. | Signatures: `get_notification_pref(user_id: int) -> dict`, `set_notification_pref(user_id: int, pref: str) -> dict`, `list_users() -> list[dict]`. Both pref functions return `{"user_id": int, "notification_pref": str}`. |
| **SA-3: API layer** | `CLAUDE.md`, `routes/api.py`, `services/users.py` (read only) | Add `GET /users`, `GET /users/<id>/notifications`, `PATCH /users/<id>/notifications` routes. | `routes/api.py` | Do not touch anything in `services/`, `utils/errors.py`, `tests/`. Routes must not read `USERS` directly or validate input; they call exactly one service function each. | Route paths + JSON shapes: PATCH body `{"notification_pref": "<value>"}`; responses are the service return values via `jsonify`; 422/404 come from `handle_app_error`. |
| **SA-4: Tests** | `CLAUDE.md`, `services/users.py`, `routes/api.py`, `tests/test_tasks.py` (style reference) | Write tests for the service functions and all three routes. | `tests/test_users.py` (new) | Do not touch `services/`, `routes/`, `utils/`, `tests/test_tasks.py`. If a test fails, report it — do not edit source to make it pass. | Final `pytest -q` output; list of any failing tests that reveal a source bug. |

---

## SA-1: Data layer

**Prompt (paste exactly):**

> Read CLAUDE.md first. In `services/users.py` only: add a module-level constant
> `VALID_NOTIFICATION_PREFS = ("email", "sms", "none")` below the imports, add
> `"notification_pref": "none"` to each existing record in `USERS` (do not change any id, name,
> or email), and make `create_user` store `"notification_pref": "none"` on new records. Do not
> add any new functions. Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`,
> or anything in `tests/`. When done, run `.venv\Scripts\python -m pytest -q` and
> `.venv\Scripts\ruff check .` and show me both outputs.

**Output files:** `services/users.py`
**pytest -q result:** `46 passed in 0.34s`
**ruff findings count:** 0 (`All checks passed!`)
**Fixes made in session (if any):** none — green on first run.
**Constraint followed?** Yes. `git status` showed only `M services/users.py`. Diff: added
`VALID_NOTIFICATION_PREFS` below the import, `"notification_pref": "none"` on users 1–2 (ids/names/
emails unchanged), and `create_user` stores `"notification_pref": "none"`; no new functions,
signature unchanged. Side note: `create_user`'s dict literal was reformatted onto multiple lines
(style only, not asked for).
**Near-violation:** CLAUDE.md's `## Commands` (added in Task 1 session 8) says to paste the
`pytest -q` summary into DECOMPOSITION.md after every step. SA-1 noticed this conflicted with
"`services/users.py` only" and chose the prompt's constraint — it did not edit DECOMPOSITION.md
and asked me instead. The two instructions pulled in opposite directions.

---

## SA-2: Service layer

**Prompt (paste exactly):**

> Read CLAUDE.md first. In `services/users.py`, add three new functions following the pattern of
> `get_user` (type hints, Google-style docstring with Args/Returns/Raises):
> 1. `list_users() -> list[dict]` — return all user records as a list.
> 2. `get_notification_pref(user_id: int) -> dict` — return
>    `{"user_id": user_id, "notification_pref": <value>}`; treat a missing or `None` value as
>    `"none"`; raise `NotFoundError("User")` if the user does not exist.
> 3. `set_notification_pref(user_id: int, pref: str) -> dict` — raise `NotFoundError("User")` if
>    the user does not exist; raise `ValidationError("notification_pref", "must be one of email,
>    sms, none")` if `pref` is not in `VALID_NOTIFICATION_PREFS`; otherwise store it and return the
>    same shape as `get_notification_pref`.
> Do not edit the `USERS` dict, `VALID_NOTIFICATION_PREFS`, `get_user`, or `create_user`. Do not
> touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, or anything in `tests/`. When
> done, run `.venv\Scripts\python -m pytest -q` and `.venv\Scripts\ruff check .` and show me both
> outputs.

**Output files:** `services/users.py`
**pytest -q result:** `46 passed in 0.30s`
**ruff findings count:** 0 (`All checks passed!`)
**Fixes made in session (if any):** none — green on first run.
**Constraint followed?** Yes. `git status` showed only `M services/users.py`, and the diff is
purely additive (three functions appended after `create_user`); `USERS`,
`VALID_NOTIFICATION_PREFS`, `get_user`, `create_user` untouched. SA-2 also hand-checked each
function (404 for a missing user, 422 for `"fax"` and `None`) but added no tests because `tests/`
was off-limits. Hand-off check: signatures match the table exactly; `set_notification_pref`
returns `get_notification_pref(user_id)`, so both return `{"user_id", "notification_pref"}`.
**Observation:** `list_users()` returns raw records, so unlike `get_notification_pref` it does not
normalize a missing/`None` pref to `"none"`. Harmless today (SA-1 gave every record the key) but
the two read paths are inconsistent.

---

## SA-3: API layer

**Prompt (paste exactly):**

> Read CLAUDE.md first. In `routes/api.py` only, add three routes. Each route reads the request,
> calls exactly one function from `services/users.py`, and returns `jsonify(...)`:
> 1. `GET /users` → `list_users()`
> 2. `GET /users/<int:user_id>/notifications` → `get_notification_pref(user_id)`
> 3. `PATCH /users/<int:user_id>/notifications` → read `notification_pref` from the JSON body and
>    call `set_notification_pref(user_id, value)`. If the key is missing, pass `None` so the
>    service raises the ValidationError — do not validate in the route.
> Do not read `USERS` directly. Do not modify anything in `services/`, `utils/errors.py`, or
> `tests/`. When done, run `.venv\Scripts\python -m pytest -q` and `.venv\Scripts\ruff check .`
> and show me both outputs.

**Output files:** `routes/api.py`
**pytest -q result:** _paste here_
**ruff findings count:** _paste here_
**Fixes made in session (if any):** _none / describe_
**Constraint followed?** _Yes / No — what it touched_

---

## SA-4: Tests

**Prompt (paste exactly):**

> Read CLAUDE.md first. Create `tests/test_users.py`, matching the style of
> `tests/test_tasks.py`. Cover: `get_notification_pref` default is `"none"`;
> `set_notification_pref` accepts `"email"` and `"sms"`; it raises `ValidationError` for an
> invalid value like `"fax"` and for `None`; both functions raise `NotFoundError` for user 999;
> `list_users` and `get_user` include `notification_pref`. Also add route tests using
> `app.test_client()` from `app.py`: `GET /api/users`, `GET /api/users/1/notifications`,
> `PATCH /api/users/1/notifications` with a valid value (200) and an invalid value (422), and
> a PATCH on user 999 (404). Tests that change a user's preference must reset it afterwards so
> test order does not matter. Do not modify any file in `services/`, `routes/`, `utils/`, or
> `tests/test_tasks.py`. If a test fails because of a source bug, stop and report it instead of
> editing source. When done, run `.venv\Scripts\python -m pytest -q` and
> `.venv\Scripts\ruff check .` and show me both outputs.

**Output files:** `tests/test_users.py`
**pytest -q result:** _paste here_
**ruff findings count:** _paste here_
**Fixes made in session (if any):** _none / describe_
**Constraint followed?** _Yes / No — what it touched_

---

## Divergence

_Fill in after all four subagents have run. Cite subagent numbers and file names._

**1. Did Claude follow the constraint field for every subagent?**
_…_

**2. Did any subagent's output break the next subagent's assumption? How did you recover?**
_…_

**3. Would you write the decomposition differently a second time? What would you change?**
_…_
