"""PreToolUse hook: block writes to protected files in task-manager.

Claude Code sends the pending tool call as JSON on stdin. Exit 0 lets it run;
exit 2 blocks it and shows stderr to Claude as the reason.
"""
import json
import os
import sys

# Paths relative to the repo root, with forward slashes.
BLOCKED_PATHS = [
    "utils/errors.py",     # handle_app_error reads e.message / e.status_code
    "requirements.txt",    # flask==3.0.0, pytest==8.0.0 are pinned
    "DECOMPOSITION.md",    # human-written logs
    "PLAN_LOG.md",
]


def main() -> int:
    event = json.load(sys.stdin)
    file_path = event.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0

    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    rel = os.path.relpath(file_path, root).replace("\\", "/")

    if rel in BLOCKED_PATHS:
        print(f"Blocked: {rel} is protected by .claude/hooks/guard_writes.py.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
