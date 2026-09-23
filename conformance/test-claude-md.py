#!/usr/bin/env python3
"""CLAUDE.md delivers AGENTS.md: the one line `@AGENTS.md`, or a symlink to it.

WHY. Claude Code reads `CLAUDE.md`, not `AGENTS.md`. The file shipped as a symlink, and Git for
Windows checks a symlink out as a plain file holding its target's name (`core.symlinks=false` is
the default there): a 9-byte `CLAUDE.md` reading `AGENTS.md`, and an agent that loads no house rules
at all. The install check still passed, because nothing asked what the file delivers.

What passes, exactly: a regular file whose whole content is `@AGENTS.md` and one newline (`\\n`, or
`\\r\\n` from a Windows checkout), which Claude Code resolves as an import on every OS; or a symlink
whose target is `AGENTS.md`. Either way `AGENTS.md` must exist beside it. Anything else fails.

Exit: 0 delivers AGENTS.md - 1 it does not.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMPORT_LINE = "@AGENTS.md"


def verdict(root: pathlib.Path) -> str | None:
    """None when `root/CLAUDE.md` delivers `root/AGENTS.md`, else the reason it does not."""
    claude, agents = root / "CLAUDE.md", root / "AGENTS.md"
    if not agents.is_file():
        return "AGENTS.md is missing, so CLAUDE.md has nothing to deliver"
    if claude.is_symlink():
        target = os.readlink(claude)
        if pathlib.PurePath(target).as_posix() != "AGENTS.md":
            return (f"CLAUDE.md is a symlink to `{target}`, not to `AGENTS.md` -- the agent reads "
                    "whatever that is instead of the house rules")
        return None
    if not claude.is_file():
        return "CLAUDE.md is missing -- Claude Code loads no house rules"
    data = claude.read_bytes()
    if data in (b"@AGENTS.md\n", b"@AGENTS.md\r\n"):
        return None
    text = data.decode("utf-8", errors="replace")
    if text.strip() == "AGENTS.md":
        return (f"CLAUDE.md is a {len(data)}-byte plain file reading `AGENTS.md` -- a symlink checked "
                "out where symlinks are off (Git for Windows), so Claude Code loads no house rules. "
                f"Replace it with the one line `{IMPORT_LINE}`")
    if text.strip() == IMPORT_LINE:
        return (f"CLAUDE.md holds `{IMPORT_LINE}` but not as that line and one newline "
                f"({len(data)} bytes) -- nothing else may surround it")
    first = text.strip().splitlines()[0][:60] if text.strip() else "(empty)"
    return (f"CLAUDE.md is a {len(data)}-byte file starting `{first}` -- it must be exactly "
            f"`{IMPORT_LINE}` (or a symlink to AGENTS.md), so the house rules live in one place")


def main() -> int:
    why = verdict(ROOT)
    if why:
        print(f"test-claude-md FAIL: {why}")
        return 1
    form = "a symlink to AGENTS.md" if (ROOT / "CLAUDE.md").is_symlink() else f"`{IMPORT_LINE}`"
    print(f"test-claude-md PASS: CLAUDE.md is {form}, and AGENTS.md exists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
