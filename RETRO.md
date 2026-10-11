# RETRO.md — Plan Mode and Subagent Decomposition (PA5 Task 3A)

**1 — Plan Mode value.** Honestly, no amendment of mine headed off a revert that was already on
its way. The amendment that mattered most was session 10 in `PLAN_LOG.md`. The original plan for
`test_patch_task_route_updates_priority` only asserted on the PATCH response body. I rejected it
and added a follow-up `GET /api/tasks/1` asserting `priority == 2`. Without that, the test would
still pass if `update_task` returned the new value without storing it in `TASKS`, so a persistence
bug would ship behind a green test and then need a revert. The more useful catches came from
reading plans I approved without changes. The session 3 plan rejected `request.args.get(...,
type=int)` because Flask would quietly turn `?priority=abc` into "return every task". The session
6 plan found that `create_task` already rejects `None`, so the fix stayed in `routes/api.py` and
didn't duplicate validation. My session 8 amendment, adding a `pytest -q` line to CLAUDE.md that
said to paste results into `DECOMPOSITION.md`, caused a problem rather than preventing one. That
line is what SA-4 later followed out of its boundary (see paragraph 3).

**2 — Plan Mode limits.** Session 3 is the case where the output didn't match the plan I
approved. The plan said "a str that is all digits → `int(priority)`". The code in
`services/tasks.py` `list_tasks` also added an `isascii()` check, because `"²".isdigit()` is True
but `int("²")` raises `ValueError`. The plan never mentioned it, and I only found it by diffing
the code against the plan. Session 7 showed the same thing at smaller scale: the plan said "confirm
only import lines changed", but `ruff --fix` also rewrapped the `tests/test_tasks.py` import into
a multi-line block. Neither was harmful, and one was an improvement, but together they mark the
boundary. Plan Mode makes Claude's intent reviewable at the resolution the plan is written in. It
says nothing about decisions made below that resolution, and "Did output match?" can only be
answered by reading the diff afterwards. All my amended plans (8, 10) matched exactly. Every
divergence happened in a session I approved without pushing back, so the plan is only as precise
as my review of it.

**3 — Subagent value.** The boundary that mattered most was the per-subagent file allow-list,
and SA-4 is the evidence. CLAUDE.md told every session to paste its `pytest -q` line into
`DECOMPOSITION.md`. SA-1 (constraint: "In `services/users.py` only") and SA-3 ("In
`routes/api.py` only") both spotted the conflict and refused. SA-4's constraint was a blacklist
("Do not modify any file in `services/`, `routes/`, `utils/`, or `tests/test_tasks.py`"), so it
edited `DECOMPOSITION.md` anyway. The services/routes boundary between SA-2 and SA-3 also held:
the PATCH route passes `data.get("notification_pref")` raw, including `None`, and
`set_notification_pref` in `services/users.py` owns the 422. Running `pytest -q` after each
subagent (46 → 46 → 46 → 60) meant a red state would have pointed to exactly one layer. In a
single session there would have been no per-step boundary for the agent to weigh against
CLAUDE.md's standing rule. Based on SA-4, the standing rule would have won, and data, service,
route, test and log edits would have landed in one diff with one pytest run at the end, so a
failure couldn't be traced to a layer.

**4 — Gap analysis.** The constraint I most want enforced mechanically is Task 2's "a subagent may
modify only the files in its Output field". It's the one that failed (SA-4 → `DECOMPOSITION.md`)
and the one SA-1 and SA-3 only kept by judgment. **Hook:** a `PreToolUse` hook on `Edit`/`Write`
that reads the active subagent's allowed paths from `.claude/active_subagent.json` (e.g.
`["tests/test_users.py"]`) and exits with code 2 and a "file outside SA-4's Output field" message
for any other path. That would have blocked SA-4's edit to `DECOMPOSITION.md`.
