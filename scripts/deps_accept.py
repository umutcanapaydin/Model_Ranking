#!/usr/bin/env python3
"""`.deps-accept`: the advisories `make deps` accepts, each until its expiry -- the owner's file.

WHY (v7.3 A20; the owner's ruling of 2026-10-28). `make deps` had no sanctioned waiver: an advisory with no
fixed release could only turn the gate red for good, or be worked around. Each line of `.deps-accept` is

    <advisory id> #<issue> <expires YYYY-MM-DD> <reason>

and pip-audit is told `--ignore-vuln <id>` for each. A line is what git shows as one: a line holding a control,
separator or format character is red, comment or not. An entry past its expiry, with an expiry more than 90
days out, a field missing or malformed, or an id twice, turns the leg red -- before its twelve-hour memory is
asked. The agent never adds an entry (AGENTS.md §3: an agent never waives a scanner finding); the owner's
merge is the review, and a change to this file routes to no security review (the owner's trim).

    python3 scripts/deps_accept.py    # prints the pip-audit flags; a bad entry: FAIL lines on stderr, exit 1
Exit: 0 every entry whole and current (or no file: nothing accepted) · 1 an entry that is not.
"""
from __future__ import annotations

import datetime
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILE = ROOT / ".deps-accept"
MAX_DAYS = 90
#: An advisory id as pip-audit names one (PYSEC-2021-66, GHSA-xxxx-xxxx-xxxx, CVE-2024-1234): nothing a shell reads.
ID = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+")
#: Not plain text: a control character (tab aside), a line or paragraph separator, a format mark (BOM, bidi,
#: zero width). Python breaks lines on several that git does not, so an entry once hid in what a diff shows as
#: a comment (the security review's M1).
HIDDEN = {"Cc", "Cf", "Zl", "Zp"}


def entries(text: str, today: datetime.date) -> tuple[list[str], list[str]]:
    """(the ids accepted, the problems): a problem line accepts nothing."""
    ids: list[str] = []
    problems: list[str] = []
    for n, raw in enumerate(text.split("\n"), 1):           # a line is what git shows as one
        line = raw[:-1] if raw.endswith("\r") else raw
        odd = next((c for c in line if c != "\t" and unicodedata.category(c) in HIDDEN), None)
        if odd is not None:
            problems.append(f"line {n} holds U+{ord(odd):04X}, a character a diff does not show -- comment or not")
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split(None, 3)
        if len(parts) < 4 or not ID.fullmatch(parts[0]) or not re.fullmatch(r"#\d+", parts[1]):
            problems.append(f"line {n} is not `<advisory id> #<issue> <expires YYYY-MM-DD> <reason>`")
            continue
        try:
            # The shape first: fromisoformat also reads `20261130` and week dates, which nobody reviews as dates.
            expires = datetime.date.fromisoformat(parts[2]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[2]) else None
        except ValueError:
            expires = None
        if expires is None:
            problems.append(f"line {n}: `{parts[2]}` is not a date (YYYY-MM-DD)")
            continue
        if expires < today:
            problems.append(f"line {n}: {parts[0]} expired on {expires} -- fix it, or the owner renews it")
        elif (expires - today).days > MAX_DAYS:
            problems.append(f"line {n}: {parts[0]} expires {expires}, more than {MAX_DAYS} days out")
        elif parts[0] in ids:
            problems.append(f"line {n}: {parts[0]} is accepted twice")
        else:
            ids.append(parts[0])
    return ids, problems


def main() -> int:
    try:
        # Bytes, then decoded: read_text would turn a lone CR into a newline before the line check (re-review M3).
        # utf-8-sig: a Windows editor's BOM is no entry.
        text = FILE.read_bytes().decode("utf-8-sig") if FILE.is_file() else ""
    except (OSError, UnicodeDecodeError) as exc:
        print(f"FAIL [deps-accept]: {FILE.name} cannot be read ({exc}) -- nothing it holds can be accepted",
              file=sys.stderr)
        return 1
    ids, problems = entries(text, datetime.date.today())
    for p in problems:
        print(f"FAIL [deps-accept]: {FILE.name} {p}", file=sys.stderr)
    if problems:
        return 1
    if ids:
        print(" ".join(f"--ignore-vuln {i}" for i in ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
