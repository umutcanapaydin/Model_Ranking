#!/usr/bin/env python3
"""The owner's setup answers, read from `docs/project-brief.md` -- the one place they live.

`/setup-project` writes the brief; these fields are the ones a script acts on, so they are read
here and nowhere else:

  Working mode:                    light | heavy   (unset or unreadable: heavy -- more checks, not fewer)
  Deploy commands:                 none | a comma-separated list the deploy gate guards
  Paths that make a change HIGH:   none | comma-separated globs (a change touching one needs security)
  QA verification:                 off | on        (unset: off -- a bug closes when its fix merges)

    python3 scripts/brief_fields.py mode          # prints light or heavy
    python3 scripts/brief_fields.py get "<field>" # prints the raw answer, or nothing
Exit 0, always: an absent brief is an answer (the defaults), not an error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BRIEF = Path("docs/project-brief.md")
_PLACEHOLDER = re.compile(r"^<[^>]*>$")


def field(name: str, root: Path | str = ".") -> str | None:
    """The answer on the first line naming `name:`, stripped of Markdown; None if absent or a placeholder."""
    p = Path(root) / BRIEF
    if not p.is_file():
        return None
    want = name.lower() + ":"
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        low = line.lower()
        at = low.find(want)
        if at < 0:
            continue
        rest = line[at + len(want):]
        # The answer is in code spans when there are any -- the template writes every field that
        # way, one span (`a, b`) or one per item (`a`, `b`); all of them, joined, since reading only
        # the first left a second deploy command unguarded. Else the text before a *(explanation)*,
        # which may run onto later lines. A code span is taken as written: a glob's `**` is kept.
        before = re.split(r"\s\*\(", rest, maxsplit=1)[0]
        spans = re.findall(r"`([^`]*)`", before)
        rest = ", ".join(s.strip() for s in spans) if spans else before.strip().strip("*_ ").strip()
        if not rest or _PLACEHOLDER.match(rest):
            return None
        return rest
    return None


def listing(name: str, root: Path | str = ".") -> list[str]:
    """A comma-separated answer as a list; `none` or absent is the empty list."""
    raw = field(name, root)
    if not raw or raw.strip().lower() in ("none", "no", "-", "—"):
        return []
    return [x.strip().strip("`").strip() for x in raw.split(",") if x.strip().strip("`").strip()]


def mode(root: Path | str = ".") -> str:
    raw = (field("Working mode", root) or "").lower()
    return "light" if raw.startswith("light") else "heavy"


def qa_on(root: Path | str = ".") -> bool:
    return (field("QA verification", root) or "").lower().startswith("on")


def main(argv: list[str]) -> int:
    if argv[:1] == ["mode"]:
        print(mode())
    elif argv[:1] == ["get"] and len(argv) == 2:
        print(field(argv[1]) or "")
    else:
        print("usage: brief_fields.py mode | get \"<field>\"")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
