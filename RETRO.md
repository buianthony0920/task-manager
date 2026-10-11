# RETRO.md — Plan Mode and Subagent Decomposition (PA5 Task 3A)

**1 — Plan Mode value.** To be honest, none of my amendments saved me from a revert that was
already happening. The one that mattered most was session 10 in `PLAN_LOG.md`. The first plan
for `test_patch_task_route_updates_priority` only checked what the PATCH sent back. I rejected it
and had it do a follow-up `GET /api/tasks/1` to make sure `priority` was actually `2`. Without
that, the test would pass even if `update_task` returned the new value and never saved it to
`TASKS`. That's the kind of bug you ship behind a green test and then have to revert later. The
funny part is that reading the plans I *didn't* change caught more. In session 3 the plan skipped
`request.args.get(..., type=int)` because Flask would quietly turn `?priority=abc` into "just
return everything". In session 6 it noticed `create_task` already rejects `None`, so the fix only
had to touch `routes/api.py`. And my session 8 amendment, where I added a CLAUDE.md line telling
it to paste `pytest -q` results into `DECOMPOSITION.md`, actually caused a problem later. More on
that in paragraph 3.

**2 — Plan Mode limits.** Session 3 is where the code didn't match the plan I approved. The plan
said "if it's a string of digits, convert it with `int()`". The code in `list_tasks`
(`services/tasks.py`) also added an `isascii()` check that wasn't in the plan anywhere. It turns
out `"²".isdigit()` is `True` but `int("²")` crashes, so it was a good catch, but I didn't approve
it. I only found it by comparing the diff to the plan line by line. Session 7 was a smaller
version of the same thing: the plan said only import lines would change, but `ruff --fix` also
reformatted the import in `tests/test_tasks.py` into a multi-line block. My takeaway is that Plan
Mode only covers what the plan actually spells out. Anything below that level of detail is still
up to Claude, and you only find out by reading the diff afterwards. Also, both of my amended
plans (8 and 10) matched exactly, and every mismatch came from a plan I approved without pushing
back. So the plan is really only as good as how carefully I read it.

**3 — Subagent value.** The most important boundary turned out to be "only touch these files",
and SA-4 proved it. Remember the CLAUDE.md line from session 8 telling every session to paste
its `pytest -q` result into `DECOMPOSITION.md`? SA-1 (told "in `services/users.py` only") and
SA-3 (told "in `routes/api.py` only") both noticed it conflicted with their instructions and
didn't do it. SA-4's constraint was a "don't touch" list instead ("Do not modify any file in
`services/`, `routes/`, `utils/`, or `tests/test_tasks.py`"). `DECOMPOSITION.md` wasn't on that
list, so SA-4 edited it anyway. The services/routes split between SA-2 and SA-3 held up too: the
PATCH route just passes `data.get("notification_pref")` through, even when it's `None`, and
`set_notification_pref` in `services/users.py` handles the 422. Running `pytest -q` after every
subagent (46 → 46 → 46 → 60) meant that if something broke, I'd know exactly which layer did it.
If I'd done the whole feature in one session, there would have been no per-step boundary to push
back against the CLAUDE.md rule. Going by what SA-4 did, I'm pretty sure the CLAUDE.md rule
would have won. I'd have ended up with data, service, route, test and log changes in one big diff
and one test run at the end.

**4 — Gap analysis.** The rule from Task 2 I'd most want enforced automatically is "a subagent
can only modify the files in its Output field". It's the one that actually broke (SA-4 editing
`DECOMPOSITION.md`), and SA-1 and SA-3 only followed it because they made a good call. **Hook:** a
`PreToolUse` hook on `Edit`/`Write` that reads the current subagent's allowed files from
`.claude/active_subagent.json` (like `["tests/test_users.py"]`) and blocks any edit to another
file with exit code 2 and a message like "file outside SA-4's Output field". That would have
stopped SA-4 before it touched `DECOMPOSITION.md`.
