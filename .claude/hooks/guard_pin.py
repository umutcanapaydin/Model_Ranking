#!/usr/bin/env python3
"""Pin the Bash guard: write its sha256 into `.claude/settings.json`, or check that the pin is current.

    python3 .claude/hooks/guard_pin.py            # `make guard-pin`: rewrite the pin (the owner's step)
    python3 .claude/hooks/guard_pin.py --check    # exit 1 when the pin is not the file's sha256

The Bash hook in `.claude/settings.json` computes the sha256 of `.claude/hooks/bash_guard.py` before
running it and refuses every Bash call when it differs: a guard an agent edited, or one that is
missing, never runs. The pin is the 64-hex string after `[ "$h" = "` in the hook's command, and its first
twelve characters appear once more in the refusal line; both are rewritten here, nowhere else. A session
open when the pin changes keeps the hooks it started with: restart Claude Code after `make guard-pin`.
Exit 0 written or current · 1 stale (`--check`) · 2 cannot run.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
ROOT = HOOKS.parent.parent
GUARD = HOOKS / "bash_guard.py"
SETTINGS = ROOT / ".claude" / "settings.json"
PIN = re.compile(r'(\[ \\"\$h\\" = \\")([0-9a-f]{64})(\\" \])')
SHORT = re.compile(r"(sha256 )([0-9a-f]{12})(\))")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    if not GUARD.is_file() or not SETTINGS.is_file():
        print(f"guard-pin CANNOT RUN: {GUARD if not GUARD.is_file() else SETTINGS} is missing")
        return 2
    want = sha256(GUARD)
    text = SETTINGS.read_text(encoding="utf-8")
    pins = PIN.findall(text)
    if not pins:
        print("guard-pin CANNOT RUN: .claude/settings.json carries no `[ \"$h\" = \"<sha256>\" ]` pin to rewrite")
        return 2
    have = {p[1] for p in pins}
    if argv == ["--check"]:
        if have == {want}:
            print(f"guard-pin PASS: .claude/settings.json pins bash_guard.py at sha256 {want[:12]}")
            return 0
        print(f"guard-pin FAIL: .claude/settings.json pins {', '.join(sorted(h[:12] for h in have))}; "
              f"bash_guard.py is {want[:12]} -- run `make guard-pin` (the owner's step), then restart Claude Code")
        return 1
    if argv:
        print("usage: guard_pin.py [--check]")
        return 2
    new = PIN.sub(lambda m: m.group(1) + want + m.group(3), text)
    new = SHORT.sub(lambda m: m.group(1) + want[:12] + m.group(3), new)
    if new == text:
        print(f"guard-pin: already pinned at sha256 {want[:12]}")
        return 0
    SETTINGS.write_text(new, encoding="utf-8")
    print(f"guard-pin: .claude/settings.json now pins bash_guard.py at sha256 {want[:12]} "
          "-- restart Claude Code: a session keeps the hooks it started with")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
