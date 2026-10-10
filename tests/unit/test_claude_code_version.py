"""The M21 repo review's M10: the Claude Code version the Bash hook's `onFailure` needs is written in
`INSTALL.md` and in gap G-7 (`docs/security-invariants.md`). A later edit to one copy would leave the
other wrong, so the two are held equal here, and each names one version."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = re.compile(r"Claude Code (\d+\.\d+\.\d+)")


def _versions(text: str) -> set[str]:
    return set(VERSION.findall(text))


def test_install_and_g7_name_the_same_claude_code_version() -> None:
    install = _versions((ROOT / "INSTALL.md").read_text(encoding="utf-8"))
    g7 = next(line for line in (ROOT / "docs" / "security-invariants.md").read_text(encoding="utf-8").splitlines()
              if line.startswith("| G-7 |"))
    assert len(install) == 1, f"INSTALL.md names {sorted(install) or 'no'} Claude Code version(s)"
    assert _versions(g7) == install, f"G-7 names {sorted(_versions(g7))}, INSTALL.md {sorted(install)}"


def test_a_version_changed_in_one_copy_is_seen() -> None:
    assert _versions("needs Claude Code 2.1.295") != _versions("needs Claude Code 2.1.296")
