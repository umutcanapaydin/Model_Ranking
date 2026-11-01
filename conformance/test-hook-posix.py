#!/usr/bin/env python3
"""Every hook command in `.claude/settings.json` is POSIX sh: it parses under dash when dash is here, and carries no bashism.

WHY (v7.1). Claude Code hands a command hook to `sh -c` on macOS and Linux. On macOS `/bin/sh` is
bash; on Debian and Ubuntu it is dash, and dash has no `set -o pipefail`, no `PIPESTATUS`, no `[[`.
The v7.0 post-edit hook used two of those, so on every Linux box each Write and Edit ended in
`set: Illegal option -o pipefail` before `make check-fast` ever ran -- and `test-hook-claims.py`
and `test-bash-guard.py` run every hook through `bash -c`, so neither could see it.

DERIVED: the hooks are read from `.claude/settings.json`, every `command` of every event, and the
`statusLine` command (v7.3), which Claude Code hands to a shell the same way. Two assertions on each:
(1) no token from the bashism list below; (2) when `dash` is on PATH, `dash -n` parses it (the hooks
never run here -- `-n` only parses). An empty hook set is a failure.

Exit: 0 clean - 1 findings.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SETTINGS = ROOT / ".claude" / "settings.json"
# Each is a bash-only construct a POSIX sh refuses or reads differently.
BASHISMS = [
    (r"set\s+-o\s+pipefail", "`set -o pipefail`"),
    (r"PIPESTATUS", "`PIPESTATUS`"),
    (r"(^|[\s;(])\[\[", "`[[ ... ]]`"),
    (r"(^|[\s;{])(declare|typeset|local)\s", "`declare` / `local`"),
    (r"(^|[\s;{])function\s+\w+", "`function name`"),
    (r"\$'", "`$'...'` quoting"),
    (r"&>", "`&>` redirection"),
    (r"<<<", "a here-string"),
    (r"\$\{[A-Za-z_][A-Za-z0-9_]*(//|\^|,|:[0-9])", "bash parameter expansion (`:-` and `:=` are POSIX; a substring or case change is not)"),
    (r"(^|[\s;])source\s", "`source` (POSIX is `.`)"),
    (r"\(\(", "`(( ))` arithmetic command"),
]


def hooks() -> list[tuple[str, str]]:
    cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
    out: list[tuple[str, str]] = []
    for event, groups in cfg.get("hooks", {}).items():
        for g in groups:
            for i, h in enumerate(g.get("hooks", [])):
                if h.get("type") == "command" and h.get("command"):
                    out.append((f"{event}[{g.get('matcher', '*')}][{i}]", h["command"]))
    line = cfg.get("statusLine")
    if isinstance(line, dict) and line.get("command"):
        out.append(("statusLine", line["command"]))
    return out


def main() -> int:
    found = hooks()
    if not found:
        print("test-hook-posix FAIL: no command hook in .claude/settings.json -- an empty derived set is a failure")
        return 1
    bad: list[str] = []
    dash = shutil.which("dash")
    for label, cmd in found:
        for pattern, what in BASHISMS:
            if re.search(pattern, cmd):
                bad.append(f"{label}: carries {what}, which /bin/sh on Debian and Ubuntu (dash) does not run")
        if dash:
            r = subprocess.run([dash, "-n", "-c", cmd], capture_output=True, text=True)
            if r.returncode != 0:
                bad.append(f"{label}: does not parse under dash -n: {r.stderr.strip()[:120]}")
    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-hook-posix {'FAIL' if bad else 'PASS'}: {len(found)} command hook(s), {len(bad)} finding(s)"
          f" ({'parsed by dash -n' if dash else 'dash not installed: token scan only'})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
