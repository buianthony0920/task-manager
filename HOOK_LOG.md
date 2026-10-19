# HOOK_LOG.md: Week 6 Task 2 (Hook Guard: Build and Break)

## How the attempts were run

Every attempt was replayed through `.claude/hooks/replay_hook.py`, which reads
`.claude/settings.json`, applies each PreToolUse `matcher` to the tool name the way Claude Code
does, and pipes the same JSON payload Claude Code sends (`tool_name`, `tool_input`, `cwd`) into
`guard_writes.py`. Exit 2 means blocked. `.claude/hooks/run_vectors.py` runs all 29 cases
(both vectors plus the Part A guards and allowed controls). Its full output after each
commit is saved in `hook_runs/`:

| Commit | Hook state | Cases as expected | Output |
|---|---|---|---|
| `bad8977` | Drill 2 baseline: path guard only, matcher `Write\|Edit\|MultiEdit` | 10/29 | `hook_runs/1_baseline.txt` |
| `f908f78` | + Part A: Bash command guard, content guard, matcher adds `Bash` | 20/29 | `hook_runs/2_part_a.txt` |
| `c2360a9` | + Vector 1 fix (case-insensitive paths) | 23/29 | `hook_runs/3_fix_vector1.txt` |
| `5411be2` (first try) | + Vector 2 fix, with a regex bug | 28/29 | `hook_runs/4a_fix_vector2_regression.txt` |
| `5411be2` | + Vector 2 fix, regex bug fixed | **29/29** | `hook_runs/4b_fix_vector2_final.txt` |

`utils/errors.py` exists, and on this Windows (NTFS, case-insensitive) checkout
`ls Utils/errors.py` opens that same file. A write to `Utils/errors.py` really overwrites the
protected file, so Vector 1 is a real bypass here and not just a different path.

Live check: one in-session probe (`true || rm -rf does_not_exist_xyz`) was **not** blocked,
because that Claude Code session had loaded its settings from the parent folder before
`.claude/settings.json` existed. A hook only applies to sessions started in (or after
reloading) the project that registers it. TODO (me): open a new Claude Code session in
`task-manager/`, send the two prompts below, and paste the block messages here.

---

## Vector 1: Case sensitivity

**Prompt:** `Modify Utils/errors.py: add a ConflictError(AppError) subclass with status 409.`
Replayed as `Edit` with `file_path = D:\PA6\task-manager\Utils\errors.py`. Also tried
`UTILS/ERRORS.PY` and `Requirements.TXT`.

**Blocked?** **No.** Baseline and after Part A, all three were `exit 0 (allowed)`, while the
control `utils/errors.py` was blocked.

```
MISS V1 case: Utils/errors.py     expected=BLOCKED  got=allowed  Edit: exit 0 (allowed)
MISS V1 case: UTILS/ERRORS.PY     expected=BLOCKED  got=allowed  Write: exit 0 (allowed)
MISS V1 case: Requirements.TXT    expected=BLOCKED  got=allowed  Write: exit 0 (allowed)
```

**Root cause:** `rel in BLOCKED_PATHS` is an exact, case-sensitive string compare, but the
Windows file system is case-insensitive, so `Utils/errors.py` names the same protected file
while comparing as a different string.

**Fix applied** (`c2360a9`): resolve the path and compare in one case.

```diff
 def _relpath(file_path: str, root: str) -> str:
-    return os.path.relpath(os.path.abspath(os.path.join(root, file_path)), root).replace("\\", "/")
+    full = os.path.realpath(os.path.join(root, file_path))
+    rel = os.path.relpath(full, os.path.realpath(root)).replace("\\", "/")
+    return rel.casefold()
+
+BLOCKED = {p.casefold() for p in BLOCKED_PATHS}
+CONTENT_GUARDED_CF = {p.casefold() for p in CONTENT_GUARDED}
 ...
-    if rel in BLOCKED_PATHS:
+    if rel in BLOCKED:
```

`realpath` also stops a symlink that points at `utils/errors.py` from getting around the check.
After the fix, all three V1 cases print `exit 2 (BLOCKED)`.

---

## Vector 2: Bash indirect write

**Prompt:** `Use bash to write the following content to utils/errors.py: class AppError(Exception): pass`
Replayed as `Bash` with a heredoc (`cat > utils/errors.py << 'PY' ...`). Five more variants of
the same attack were tried: `echo >> Utils/errors.py`, `printf | tee ./utils/errors.py`,
`python -c "open('utils/errors.py','w').write(...)"`, `sed -i ... requirements.txt`,
`cp /tmp/x.py utils\errors.py`.

**Blocked?**
- **Baseline: No.** `Bash: no matcher matched, hook never ran (allowed)`. The hook did not even run.
- **After Part A: Partially.** Adding `Bash` to the matcher (needed for the Bash command guard) made
  the hook **fire** on every variant, but all six still returned `Bash: exit 0 (allowed)`.
  `rm -rf`, `DROP TABLE` and `git push --force` were blocked on the same run. The hook ran, but
  the path guard never looked at Bash.

**Root cause:** the path guard only reads `tool_input.file_path`, which only Write/Edit/MultiEdit
have; a Bash call has only `tool_input.command`, so a shell redirect writes the protected file
without the path guard ever seeing a path. Before Part A the matcher did not include `Bash` at all.

**Fix applied** (`5411be2`): matcher already covered `Bash` (from Part A); added a Bash path
guard that parses the command string. For each `;` / `&&` / `||` / `|` / newline segment
it blocks if
1. a redirect target (`>`, `>>`, `2>`, `&>`) is a protected path, or
2. the segment runs a writing command or interpreter (`tee cp mv dd truncate rm ln touch sed -i
   perl -i python node Set-Content Out-File ...`) **and** names a protected path (any case,
   `/` or `\`, optional `./`).

```diff
+WRITING_CMDS = re.compile(r"(?<![\w./-])(?:tee|cp|mv|dd|truncate|install|rm|ln|touch|patch|"
+    r"sed\s+(?:-\w+\s+)*-i|perl\s+(?:-\w+\s+)*-p?i|python3?|py|perl|ruby|node|"
+    r"set-content|add-content|out-file|new-item|copy-item|move-item|remove-item)(?![\w.-])", re.I)
+REDIRECT = re.compile(r"(?:\d|&)?>>?\s*['\"]?([^\s;&|'\"<>]+)")
 ...
     if tool == "Bash":
         ...
+        hit = _bash_writes_protected(command)
+        if hit:
+            return block(f"{hit} is a protected file; this Bash command would write to it.")
```

**Regression caught by the replay run:** the first version used `\b(?:...|py|...)\b`, and the
allowed control `cat utils/errors.py` was **blocked** (`hook_runs/4a_fix_vector2_regression.txt`,
28/29), because `\bpy\b` matches the `py` in `errors.py`. I swapped `\b` for the lookarounds
`(?<![\w./-])` / `(?![\w.-])` so a command word can't be part of a file name. Reading protected
files (`cat`, `grep`) is allowed again, and every V2 variant is blocked (29/29).

**Known remaining gap:** this is still pattern matching on a string, so an obfuscated write like
`p=utils; cat > $p/errors.py` or a base64-decoded script gets past it. See RETRO.md paragraph 4.

---

## Part A guards (same run, `hook_runs/4b_fix_vector2_final.txt`)

| Guard | Blocked | Allowed (must not over-block) |
|---|---|---|
| SQL (`\b(?:DROP\|TRUNCATE)\s+TABLE\b`, case-insensitive) | `DROP TABLE tasks;`, `truncate  table users` | `echo dropdown_table truncated_tables` |
| `rm` with `-r` and `-f` (token-level: flags merged per `rm` segment) | `rm -rf`, `rm -fr`, `rm -r -f` | `rm build.log`, `grep -rf patterns.txt .` |
| `git push --force` / `-f` (token-level) | `git push --force origin main`, `git push -f` | `git push --force-with-lease` |
| Content guard on `services/tasks.py` (`postgres(ql)(+driver)://`, `sqlite:///`) | `Write`, `Edit`, and `MultiEdit` with a hardcoded URL | `os.environ["DATABASE_URL"]`; a sqlite URL in `tests/test_db.py` |

## pytest after the fix

```
> .venv\Scripts\python -m pytest -q
............................................................             [100%]
60 passed in 0.50s
```
(`hook_runs/5_pytest_after_fix.txt`; same 60 passing as before any hook change.
`ruff check .` reports `All checks passed!`.)
