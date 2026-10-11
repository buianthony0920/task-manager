# Iteration Log

I ran three Claude Code sessions. Each one started fresh in `task-manager/`, so Claude
read `CLAUDE.md` first. Each session had a different goal and changed a different
function in `services/tasks.py`.

Git isn't installed, so after each session I saved a screenshot of Claude's reply and
copies of `services/tasks.py` and `tests/test_tasks.py` in `../session-notes/sessionN/`.
I also ran the tests and the linter myself after each session to check Claude's work.

| Session | Goal | Tests | Lint | Fixes I had to ask for |
|---|---|---|---|---|
| 1 | Check input in `create_task` | 11 pass | nothing new | 0 |
| 2 | Fix the crash in `get_task` | 12 pass | nothing new | 0 |
| 3 | Handle errors in `process_order` | 12 pass | nothing new (6 → 5) | 0 |

---

## Session 1 — 2026-10-04

### Prompt used
```
Add input validation to create_task in services/tasks.py. Run the tests when done.
```

### What Claude did
**Right:**
- An empty title, or one that's only spaces, now raises
  `ValidationError("title", "cannot be empty")`.
- A bad `user_id` (0, -1, `"1"` or `True`) now raises
  `ValidationError("user_id", "must be a positive integer")`.
- Added a docstring in the right format, put the import at the top of the file, and
  didn't change the function signature.
- Added 7 tests that check for `ValidationError`. All 11 tests pass.

**Wrong or missing:**
- You can still create a task for a user that doesn't exist, like user 999. Claude
  pointed this out but didn't fix it.
- Titles keep their extra spaces (`"  Plan  "` is saved as is).

### Observation
The "Bad input" rule was the one that mattered here, and Claude followed it. It used the
exact same error as the example in `CLAUDE.md`. But Claude didn't check whether the user
exists. To do that, `services/tasks.py` would need to call `get_user` from
`services/users.py`, and v1 didn't say if that was allowed. So Claude didn't do it and
asked me instead.

### CLAUDE.md update
Added under `## Architecture`:
```
- Cross-service calls: a service may call another service's public functions
  (e.g. `services/tasks.py` calls `get_user` from `services/users.py` to check a
  user exists, letting its `NotFoundError("User")` propagate). It must never read
  or write another module's dict (`USERS`, `TASKS`) directly.
```
I added this because Claude didn't check that the user exists in session 1, since v1
didn't say if one service could call another.

---

## Session 2 — 2026-10-04

### Prompt used
```
get_task in services/tasks.py crashes with a KeyError when the task doesn't exist. Fix it and add a test.
```

### What Claude did
**Right:**
- Added `if task_id not in TASKS: raise NotFoundError("Task")`.
- Added a docstring and a new test, `test_get_task_not_found`, that checks for
  `NotFoundError`. All 12 tests pass.
- Noticed `process_order` had the same bug but didn't touch it, because I only asked
  about `get_task`.

**Wrong:**
- Kept the old weak test `test_get_task_invalid`, which only checks for any
  `Exception`, and added a second, stronger test for the same case. Now there are two
  tests doing the same thing.

### Observation
The "Missing record" rule was the one that mattered here, and Claude copied its example
exactly. The duplicate test happened because of the "Do not touch" rule, which says
never delete or loosen a test. v1 didn't say if making a test stricter was OK, so Claude
played it safe and added a new test instead. The rule I added after session 1 didn't
come up, because `get_task` has nothing to do with users.

### CLAUDE.md update
Added under `## Do not touch`, after the rule about existing tests:
```
  Tightening is expected: when you fix a function whose test uses
  `pytest.raises(Exception)`, change that test to the specific class
  (e.g. `pytest.raises(NotFoundError)`) instead of adding a duplicate test.
```
I added this because Claude kept a weak test and added a duplicate in session 2.

---

## Session 3 — 2026-10-04

### Prompt used
```
Add error handling to process_order in services/tasks.py. Don't change its signature. Run the tests and lint when done.
```

### What Claude did
**Right:**
- Added a check that raises `NotFoundError("Task")` for a missing task, plus a
  docstring. Didn't change the signature.
- **Made the existing test `test_process_order_invalid` stricter** instead of adding a
  duplicate, and said it did this because `CLAUDE.md` says to. All 12 tests pass.
- Lint went from 6 findings to 5, because the stricter test got rid of a warning.
  Nothing new was added.

**Wrong:**
- Claude said a missing task would return a 404 from the API. That's not true. No API
  route uses `process_order`; `routes/api.py` imports it but never calls it.
- It left the duplicate test from session 2, because the new rule only covers the
  function you're fixing.

### Observation
The rule I added after session 2 worked. In session 2 Claude added a duplicate test, but
this time it fixed the existing test instead.

**This is the honest failure:** `CLAUDE.md` didn't stop the wrong 404 claim. It caused
it. v1 said the routes call all five functions, including `process_order`, which isn't
true. Claude believed the file and didn't check `routes/api.py`.

Two smaller things came up too. The "6 existing findings" line in `CLAUDE.md` was wrong
once a finding got fixed. And nobody has decided what should happen if you complete a
task that's already done, so Claude asked instead of guessing.

### CLAUDE.md update
Changed the lint line under `## Commands`:
```
- Lint: run `.venv\Scripts\ruff check .` before you start and again when you're done.
  Don't add any new findings, and don't fix old ones unless asked.
```
Changed the routes line under `## Architecture`:
```
- `routes/api.py`: HTTP only. Read the request, call one service function, return
  `jsonify(...)`. Only `get_task`, `create_task` and `get_user` have routes.
  `process_order` has no route, so its errors never reach the API.
```
Added under `## Conventions`:
```
- Undecided — ask, don't guess: whether completing a task that's already done in
  `process_order` is an error, and whether to trim spaces from titles.
```
I changed the routes line because Claude wrongly said in session 3 that `process_order`
errors would become a 404. I changed the lint line because the "6 findings" number
stopped being true in session 3. I added the "Undecided" line because Claude ran into
questions nobody had answered in sessions 1 and 3. I also combined some lines that
overlapped, so the file stays under 60 lines (it's 53).

---

## Evidence of improvement
I didn't have to correct Claude in any session, so I can't show fewer corrections: it
was zero every time. The improvement shows up in Claude's behaviour instead. In
session 2, before the new test rule, Claude added a duplicate test. In session 3, after
the rule, Claude fixed the existing test and said `CLAUDE.md` told it to. In all three
sessions Claude used the exact errors, docstring format and test style from
`CLAUDE.md`, and didn't add any new lint findings. The rule from session 1 (services
calling each other) hasn't been tested yet. A fourth session that adds a check for
whether the user exists in `create_task` would test it.
