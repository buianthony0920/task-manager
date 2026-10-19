"""PreToolUse hook: block writes to protected files and dangerous shell commands.

Claude Code sends the pending tool call as JSON on stdin. Exit 0 lets it run;
exit 2 blocks it and shows stderr to Claude as the reason.

Three guards:
  1. Path guard    (Write/Edit/MultiEdit): BLOCKED_PATHS may not be written.
  2. Bash guard    (Bash): BASH_RULES commands are refused.
  3. Content guard (Write/Edit/MultiEdit): files in CONTENT_GUARDED may not
     contain a hardcoded database connection string.
"""
import json
import os
import re
import shlex
import sys

# Paths relative to the repo root, with forward slashes.
# Week 7 (MCP): MCP tools are named mcp__<server>__<tool> and also fire PreToolUse.
# Every path below should ALSO apply to MCP tools that write files (e.g. a filesystem
# server's write_file/edit_file) because each one guards the file itself, not one tool.
# requirements.txt and the two logs matter most there; utils/errors.py too.
BLOCKED_PATHS = [
    "utils/errors.py",     # handle_app_error reads e.message / e.status_code   [MCP: yes]
    "requirements.txt",    # flask==3.0.0, pytest==8.0.0 are pinned             [MCP: yes]
    "DECOMPOSITION.md",    # human-written logs                                 [MCP: yes]
    "PLAN_LOG.md",         #                                                    [MCP: yes]
]

# Files Claude may write, but never with a hardcoded DB connection string.
CONTENT_GUARDED = ["services/tasks.py"]
DB_URL = re.compile(r"\b(?:postgres(?:ql)?(?:\+\w+)?://|sqlite:///)", re.IGNORECASE)


def _segments(command: str) -> list[list[str]]:
    """Split a shell command on ; && || | and newlines, then into tokens."""
    out = []
    for part in re.split(r"&&|\|\||[;|\n]", command):
        try:
            tokens = shlex.split(part)
        except ValueError:          # unbalanced quotes: fall back to whitespace
            tokens = part.split()
        if tokens:
            out.append(tokens)
    return out


def _short_flags(tokens: list[str]) -> str:
    return "".join(t[1:] for t in tokens if t.startswith("-") and not t.startswith("--"))


def _is_rm_rf(tokens: list[str]) -> bool:
    if os.path.basename(tokens[0]) != "rm":
        return False
    flags = _short_flags(tokens[1:])
    recursive = "r" in flags or "R" in flags or "--recursive" in tokens
    force = "f" in flags or "--force" in tokens
    return recursive and force


def _is_force_push(tokens: list[str]) -> bool:
    if os.path.basename(tokens[0]) != "git" or "push" not in tokens:
        return False
    return "--force" in tokens or "f" in _short_flags(tokens[tokens.index("push") + 1:])


# (name, check, reason). A check takes the raw command and its token segments.
BASH_RULES = [
    ("sql-destructive",
     lambda cmd, segs: re.search(r"\b(?:DROP|TRUNCATE)\s+TABLE\b", cmd, re.IGNORECASE),
     "DROP TABLE / TRUNCATE TABLE destroys data. Ask the human to run it."),
    ("rm-rf",
     lambda cmd, segs: any(_is_rm_rf(t) for t in segs),
     "rm with both -r and -f is not allowed. Delete specific files instead."),
    ("git-force-push",
     lambda cmd, segs: any(_is_force_push(t) for t in segs),
     "git push --force / -f rewrites shared history on origin. Use --force-with-lease "
     "only if the human asks."),
]


def _relpath(file_path: str, root: str) -> str:
    return os.path.relpath(os.path.abspath(os.path.join(root, file_path)), root).replace("\\", "/")


def _new_content(tool_input: dict) -> str:
    parts = [tool_input.get("content", ""), tool_input.get("new_string", "")]
    parts += [e.get("new_string", "") for e in tool_input.get("edits", [])]
    return "\n".join(p for p in parts if p)


def block(reason: str) -> int:
    print(f"Blocked by .claude/hooks/guard_writes.py: {reason}", file=sys.stderr)
    return 2


def main() -> int:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()

    if tool == "Bash":
        command = tool_input.get("command", "")
        segs = _segments(command)
        for name, check, reason in BASH_RULES:
            if check(command, segs):
                return block(f"[{name}] {reason}")
        return 0

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0
    rel = _relpath(file_path, root)

    if rel in BLOCKED_PATHS:
        return block(f"{rel} is a protected file.")

    if rel in CONTENT_GUARDED and DB_URL.search(_new_content(tool_input)):
        return block(f"{rel} would contain a hardcoded database connection string "
                     "(postgresql:// or sqlite:///). Connection strings must come from "
                     "environment variables, e.g. os.environ['DATABASE_URL'].")
    return 0


if __name__ == "__main__":
    sys.exit(main())
