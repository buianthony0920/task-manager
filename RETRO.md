# RETRO.md: Enforce, Automate, and Reflect (Week 6 Task 3A)

(The Week 5 retrospective moved to `RETRO_W5.md`.)

**1: Slash command value.** `/scaffold-endpoint` saved the most prompt-writing (COMMAND_LOG.md
row 2, `tags POST`). From two words it echoed `RESOURCE=tags METHOD=POST`, created exactly the
four allowed files, wrote a three-line `create_tag_route` with no logic, and added a test
asserting `201` and `name == "urgent"` (61 passed, ruff clean). Typed by hand, the same request needs about 40 lines: which four files to touch
(`routes/api.py`, `services/<resource>.py`, `schemas/<resource>.py`, `tests/test_<resource>.py`),
that the route copies the shape of the task routes and only does
`request.get_json(silent=True) or {}` → one service call → `jsonify`, that `TASKS`/`USERS`
must not be imported into the route, that no schema library may be added, and that the test has
to assert `201` for POST and `200` otherwise. I would forget at least one of those every time.
The "no `if` checks in the handler" line is the one that slipped in Week 5 (SA-3 near-miss in
CLAUDE.md). With the command it's `/scaffold-endpoint tags POST`, and the constraints are the
same every run, so a drift shows up as a fix to the command file and not as a new prompt I
have to remember next time. That's what happened in row 2: the one flaw, an unused
`REQUIRED_FIELDS` in `schemas/tags.py`, came from my command's spec, so I fixed
`scaffold-endpoint.md` once instead of remembering to leave it out of every future prompt.

**2: Hook reliability.** Both vectors got past the hook before I fixed it. Vector 1 was a
straight bypass: `Utils/errors.py`, `UTILS/ERRORS.PY` and `Requirements.TXT` all came back
`exit 0 (allowed)` in `hook_runs/1_baseline.txt`, even though on this NTFS checkout
`ls Utils/errors.py` opens the real protected file. The hook compared strings
case-sensitively while the file system matches names without caring about case. Vector 2 went
in two steps. On the baseline the result was `no matcher matched, hook never ran`. After Part A
added `Bash` to the matcher (`hook_runs/2_part_a.txt`), the hook *did* run and blocked
`rm -rf` and `DROP TABLE` on the same run, but all six indirect writes (heredoc, `>>`, `tee`,
`python -c`, `sed -i`, `cp`) were still allowed, because the path guard only reads
`tool_input.file_path` and a Bash call doesn't have one. So "the rule is in settings.json"
turned out to mean three separate things: the matcher has to include the tool, the hook has to
read the right field for that tool, and the comparison has to match how the OS resolves names.
Each one failed on its own. I also learned that the fix needs the same testing as the gap: my
first Vector 2 regex blocked `cat utils/errors.py` because `\bpy\b` matched inside `errors.py`
(`hook_runs/4a_fix_vector2_regression.txt`, 28/29). I only caught it because
`run_vectors.py` has allowed cases next to the blocked ones. And the live probe in my
session (`true || rm -rf does_not_exist_xyz`) ran because that session was started before
`settings.json` existed. A registered hook does nothing in a session that never loaded it.

**3: Advisory vs. deterministic.** I left "The sample data in `TASKS` (ids 1–3) and `USERS`
(ids 1–2)… task 2 must be 'Write report'" advisory in CLAUDE.md's Do-not-touch section. The
path guard can't hold it, because `services/tasks.py` has to stay writable (it's the
`CONTENT_GUARDED` file, and `/add-field` is *supposed* to add a key to every sample row). A
content regex can't tell "added `due_date: None` to row 2" apart from "renamed row 2's title".
The rule is about meaning, not about a path or a string. COMMAND_LOG.md row 3 shows the
advisory rule holding: `/add-field tasks due_date ...` edited all three sample rows and only
appended `"due_date": None`, with ids and titles untouched. I'll graduate it when an `Edit` whose
`old_string` overlaps the `TASKS = {...}` literal changes an existing `"id"` or `"title"` value
in even one logged run (COMMAND_LOG.md or a failure in `test_get_task_valid`, which asserts
task 2 is "Write report"). At that point the check is worth writing: parse the `TASKS` dict before and after with
`ast.literal_eval` inside the hook and block if any of ids 1–3 lost or changed an existing key's
value. Adding new keys stays allowed.

**4: Limits of hooks.** The rule I wanted to enforce was "Existing tests: never delete one or
make it weaker. All 60 must still pass before you finish." PreToolUse was the wrong event and
the wrong kind of check. It sees one tool call *before* it runs, so it can't know whether the
suite still passes after the edit. It also can't tell weakening `pytest.raises(NotFoundError)`
to `pytest.raises(Exception)` (forbidden) apart from the opposite change, which CLAUDE.md
actually asks for. And `tests/` can't go in `BLOCKED_PATHS`, because `/scaffold-endpoint` and
`/add-field` have to write new test files there. The right mechanism is a check after the work
is done: a `Stop` hook that runs `pytest -q --collect-only` and `pytest -q`, and returns exit 2
(so Claude has to keep working) if the collected count is below the recorded baseline (60) or
anything fails. CI on push would be the backstop. The same idea covers the gap HOOK_LOG.md lists
for Vector 2: `p=utils; cat > $p/errors.py` gets past my regex. The guarantee that can't be
talked around is outside Claude Code: set `utils/errors.py` read-only at the OS level, or run
Claude in a sandbox where that path isn't writable, and keep the hook as the early warning
that explains *why* the write was refused.
