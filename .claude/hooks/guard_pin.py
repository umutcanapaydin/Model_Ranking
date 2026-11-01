#!/usr/bin/env python3
"""Pin the Bash guard: write its sha256 into `.claude/settings.json` and `.codex/hooks.json`, or check that the pin is current.

    python3 .claude/hooks/guard_pin.py            # `make guard-pin`: rewrite the pin (the owner's step)
    python3 .claude/hooks/guard_pin.py --check    # exit 1 when the pin is not the file's sha256

The Bash hook in `.claude/settings.json` computes the sha256 of `.claude/hooks/bash_guard.py` before
running it and refuses every Bash call when it differs: a guard an agent edited, or one that is
missing, never runs. The pin is the 64-hex string after `[ "$h" = "` in the hook's command, and its first
twelve characters appear once more in the refusal line; both are rewritten here, nowhere else. Codex runs
the same command from `.codex/hooks.json` (v7.3), so its pin is rewritten with this one when the file is
there. A session open when the pin changes keeps the hooks it started with: restart Claude Code after
`make guard-pin`; Codex skips the changed hook until it is trusted again in `/hooks`.
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
CODEX = ROOT / ".codex" / "hooks.json"
PIN = re.compile(r'(\[ \\"\$h\\" = \\")([0-9a-f]{64})(\\" \])')
SHORT = re.compile(r"(sha256 )([0-9a-f]{12})(\))")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    if not GUARD.is_file() or not SETTINGS.is_file():
        print(f"guard-pin CANNOT RUN: {GUARD if not GUARD.is_file() else SETTINGS} is missing")
        return 2
    want = sha256(GUARD)
    texts = {f: f.read_text(encoding="utf-8") for f in (SETTINGS, CODEX) if f.is_file()}
    names = " and ".join(str(f.relative_to(ROOT)) for f in texts)
    for f, text in texts.items():
        if not PIN.findall(text):
            print(f"guard-pin CANNOT RUN: {f.relative_to(ROOT)} carries no `[ \"$h\" = \"<sha256>\" ]` pin to rewrite")
            return 2
    have = {p[1] for text in texts.values() for p in PIN.findall(text)}
    if argv == ["--check"]:
        if have == {want}:
            print(f"guard-pin PASS: {names} pin bash_guard.py at sha256 {want[:12]}")
            return 0
        print(f"guard-pin FAIL: {names} pin {', '.join(sorted(h[:12] for h in have))}; "
              f"bash_guard.py is {want[:12]} -- run `make guard-pin` (the owner's step), then restart Claude Code")
        return 1
    if argv:
        print("usage: guard_pin.py [--check]")
        return 2
    changed = []
    for f, text in texts.items():
        new = SHORT.sub(lambda m: m.group(1) + want[:12] + m.group(3),
                        PIN.sub(lambda m: m.group(1) + want + m.group(3), text))
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed.append(f)
    if not changed:
        print(f"guard-pin: already pinned at sha256 {want[:12]}")
        return 0
    print(f"guard-pin: {names} now pin bash_guard.py at sha256 {want[:12]} -- restart Claude Code: a session keeps "
          "the hooks it started with" + ("; Codex skips the changed hook until you trust it again in /hooks"
                                         if CODEX in texts else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
