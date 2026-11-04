#!/usr/bin/env python3
"""The sources silent for 7 or more nights, for the owner (#552, D-243, D-240 clause 3).

Reads the refresh record (`advisor.db.refresh.json`), whose `silent` the refresh cycle writes: every
source whose last arrival (D-156) is 7 or more days before the cycle, with that arrival. The rule lives in
`app.workflows.refresh.silent_sources`; this script decides nothing, it only says what the record holds.

    scripts/silent_sources.py <record>           one line per silent source: `<source> last arrived <iso>`
    scripts/silent_sources.py --issue <record>   the one issue the nightly opens or comments on, as one line
                                                 of JSON, `{"title": ..., "body": ...}`; nothing when no
                                                 source is silent

Exit 0 when the record was read (silent sources or none); 2 when it cannot be read, or holds no `silent`
of the expected shape: a record nobody can read is never taken for a night with no silent source.
Standard library only, and no network: the workflow posts the issue with `gh`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#: The issue's title; the workflow finds the open one by it.
TITLE = "Sources silent for 7 or more nights"
#: A line GitHub does not render, so the issue says which notice it is.
MARKER = "<!-- silent-sources -->"


def read_silent(path: Path) -> dict[str, str]:
    """The record's `silent`, or ValueError naming why it cannot be read."""
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ValueError(f"{path}: cannot be read as JSON ({exc.__class__.__name__})") from None
    silent = record.get("silent") if isinstance(record, dict) else None
    if not isinstance(silent, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in silent.items()):
        raise ValueError(f"{path}: holds no `silent` map of source to last arrival (D-243)")
    return dict(sorted(silent.items()))


def _quoted(text: str) -> str:
    """Inline code, so a name renders as written and mentions nobody."""
    return "`" + text.replace("`", "'") + "`"


def issue(silent: dict[str, str]) -> dict[str, str]:
    lines = [
        MARKER,
        "These sources have sent no new data for 7 or more nights (D-240 clause 3, D-243). Their last good",
        "rows still serve, for up to 30 days from their last arrival (D-156). The decision about each source",
        "is the owner's.",
        "",
        "| source | last arrived |",
        "|---|---|",
        *(f"| {_quoted(name)} | {_quoted(stamp)} |" for name, stamp in silent.items()),
    ]
    return {"title": TITLE, "body": "\n".join(lines) + "\n"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--issue", action="store_true", help="print the issue as one line of JSON")
    parser.add_argument("record", type=Path, help="the refresh record, advisor.db.refresh.json")
    args = parser.parse_args(argv)
    try:
        silent = read_silent(args.record)
    except ValueError as exc:
        print(f"silent sources: {exc}", file=sys.stderr)
        return 2
    if not silent:
        return 0
    if args.issue:
        print(json.dumps(issue(silent)))
    else:
        for name, stamp in silent.items():
            print(f"{name} last arrived {stamp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
