"""Replay a PreToolUse payload through .claude/settings.json the way Claude Code does.

Usage: python .claude/hooks/replay_hook.py <tool_name> ['<tool_input JSON>']
       (omit the JSON to read it from stdin, which keeps Windows backslashes intact)

Picks every PreToolUse entry whose matcher matches tool_name, runs its command
with the payload on stdin, and prints the exit code and stderr. Exit 2 = blocked.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    tool_name = sys.argv[1]
    tool_input = json.loads(sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read())
    with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as f:
        entries = json.load(f)["hooks"]["PreToolUse"]

    payload = json.dumps({"hook_event_name": "PreToolUse", "cwd": ROOT,
                          "tool_name": tool_name, "tool_input": tool_input})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": ROOT}
    ran = False
    for entry in entries:
        if not re.fullmatch(entry.get("matcher", ".*") or ".*", tool_name):
            continue
        for hook in entry["hooks"]:
            ran = True
            command = hook["command"].replace("$CLAUDE_PROJECT_DIR", ROOT)
            proc = subprocess.run(command, check=False, input=payload, capture_output=True,
                                  text=True, shell=True, env=env)
            verdict = "BLOCKED" if proc.returncode == 2 else "allowed"
            print(f"{tool_name}: exit {proc.returncode} ({verdict}) {proc.stderr.strip()}")
            if proc.returncode == 2:
                return 2
    if not ran:
        print(f"{tool_name}: no matcher matched, hook never ran (allowed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
