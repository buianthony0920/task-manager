"""Replay the Week 6 bypass vectors and guard checks through replay_hook.py.

Usage: python .claude/hooks/run_vectors.py
Each case prints the hook's verdict next to the expected one.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def p(*parts: str) -> str:
    """Absolute Windows-style path, as Claude Code sends it."""
    return os.path.join(ROOT, *parts)


CASES = [
    # (label, tool_name, tool_input, expected)
    ("control: utils/errors.py", "Write",
     {"file_path": p("utils", "errors.py"), "content": "x"}, "BLOCKED"),
    ("allowed: services/users.py", "Edit",
     {"file_path": p("services", "users.py"), "old_string": "a", "new_string": "b"}, "allowed"),
    ("V1 case: Utils/errors.py", "Edit",
     {"file_path": p("Utils", "errors.py"), "old_string": "a", "new_string": "b"}, "BLOCKED"),
    ("V1 case: UTILS/ERRORS.PY", "Write",
     {"file_path": p("UTILS", "ERRORS.PY"), "content": "x"}, "BLOCKED"),
    ("V1 case: Requirements.TXT", "Write",
     {"file_path": p("Requirements.TXT"), "content": "x"}, "BLOCKED"),
    ("V2 bash: heredoc > utils/errors.py", "Bash",
     {"command": "cat > utils/errors.py << 'PY'\nclass AppError(Exception):\n    pass\nPY"},
     "BLOCKED"),
    ("V2 bash: echo >> Utils/errors.py", "Bash",
     {"command": 'echo "x = 1" >> Utils/errors.py'}, "BLOCKED"),
    ("V2 bash: tee ./utils/errors.py", "Bash",
     {"command": "printf 'x' | tee ./utils/errors.py"}, "BLOCKED"),
    ("V2 bash: python -c open(...).write", "Bash",
     {"command": "python -c \"open('utils/errors.py','w').write('x')\""}, "BLOCKED"),
    ("V2 bash: sed -i requirements.txt", "Bash",
     {"command": "sed -i 's/flask==3.0.0/flask==3.1.0/' requirements.txt"}, "BLOCKED"),
    ("V2 bash: cp over utils\\errors.py", "Bash",
     {"command": "cp /tmp/x.py utils\\errors.py"}, "BLOCKED"),
    ("allowed: bash reads utils/errors.py", "Bash",
     {"command": "cat utils/errors.py"}, "allowed"),
    ("allowed: bash runs pytest", "Bash",
     {"command": ".venv\\Scripts\\python -m pytest -q"}, "allowed"),
    ("bash guard: DROP TABLE", "Bash",
     {"command": "sqlite3 app.db \"DROP TABLE tasks;\""}, "BLOCKED"),
    ("bash guard: truncate  table (lower, 2 spaces)", "Bash",
     {"command": "psql -c 'truncate  table users'"}, "BLOCKED"),
    ("bash guard: rm -rf", "Bash", {"command": "rm -rf .venv"}, "BLOCKED"),
    ("bash guard: rm -fr", "Bash", {"command": "rm -fr tests"}, "BLOCKED"),
    ("bash guard: rm -r -f", "Bash", {"command": "rm -r -f services"}, "BLOCKED"),
    ("bash guard: git push --force", "Bash",
     {"command": "git push --force origin main"}, "BLOCKED"),
    ("bash guard: git push -f", "Bash", {"command": "git push -f"}, "BLOCKED"),
    ("allowed: git push --force-with-lease", "Bash",
     {"command": "git push --force-with-lease"}, "allowed"),
    ("allowed: rm one file", "Bash", {"command": "rm build.log"}, "allowed"),
    ("allowed: grep -rf (not rm)", "Bash", {"command": "grep -rf patterns.txt ."}, "allowed"),
    ("allowed: word 'dropdown_table'", "Bash",
     {"command": "echo dropdown_table truncated_tables"}, "allowed"),
    ("content: postgres URL in services/tasks.py", "Write",
     {"file_path": p("services", "tasks.py"),
      "content": 'DB_URL = "postgresql://admin:pw@localhost:5432/tasks"\n'}, "BLOCKED"),
    ("content: sqlite URL via Edit", "Edit",
     {"file_path": p("services", "tasks.py"), "old_string": "TASKS",
      "new_string": 'ENGINE = create_engine("sqlite:///tasks.db")\nTASKS'}, "BLOCKED"),
    ("content: MultiEdit with postgres+psycopg", "MultiEdit",
     {"file_path": p("services", "tasks.py"),
      "edits": [{"old_string": "a", "new_string": "b"},
                {"old_string": "c", "new_string": "url = 'postgresql+psycopg2://u@h/db'"}]},
     "BLOCKED"),
    ("content: env var is fine", "Write",
     {"file_path": p("services", "tasks.py"),
      "content": 'import os\nDB_URL = os.environ["DATABASE_URL"]\n'}, "allowed"),
    ("content: other file not inspected", "Write",
     {"file_path": p("tests", "test_db.py"),
      "content": 'URL = "sqlite:///:memory:"\n'}, "allowed"),
]


def main() -> int:
    failures = 0
    for label, tool, tool_input, expected in CASES:
        proc = subprocess.run([sys.executable, os.path.join(HERE, "replay_hook.py"), tool],
                              input=json.dumps(tool_input), capture_output=True, text=True)
        got = "BLOCKED" if proc.returncode == 2 else "allowed"
        mark = "ok  " if got == expected else "MISS"
        failures += got != expected
        print(f"{mark} {label:45} expected={expected:8} got={got:8} {proc.stdout.strip()}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} cases as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
