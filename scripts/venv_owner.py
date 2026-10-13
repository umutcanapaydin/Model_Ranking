#!/usr/bin/env python3
"""Refuse a venv another tree owns, before `make install` writes into it (#264).

An agent's worktree once had `.venv` as a symlink to the main clone's. `make install` there ran
`pip install -e .` through the link and rewrote the main venv's editable path to the worktree; when
the worktree was deleted, the main clone's venv imported nothing from `app`. Two signs name a venv
another tree owns:

- the venv path is a symbolic link;
- the project's editable install (`direct_url.json`) names another tree.

Runs with the system Python, before the venv's own packages exist. Exit: 0 owned · 1 refused.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

DIST = "model_ranking"


def _editable_tree(venv: Path) -> Path | None:
    for record in sorted(venv.glob(f"[Ll]ib/*/site-packages/{DIST}-*.dist-info/direct_url.json")) + sorted(
        venv.glob(f"Lib/site-packages/{DIST}-*.dist-info/direct_url.json")
    ):
        try:
            url = json.loads(record.read_text(encoding="utf-8")).get("url", "")
        except (OSError, ValueError, AttributeError):
            continue
        parsed = urlparse(url) if isinstance(url, str) else None
        if parsed is not None and parsed.scheme == "file":
            return Path(unquote(parsed.path))
    return None


def problems(tree: Path, venv: Path) -> list[str]:
    """Why ``venv`` is not this ``tree``'s own, or nothing."""
    if venv.is_symlink():
        return [f"{venv} is a link to {venv.resolve()}; a worktree builds its own venv (#264)"]
    installed = _editable_tree(venv)
    if installed is not None and installed.resolve() != tree.resolve():
        return [f"{venv} holds an editable install of {installed.resolve()}, not of {tree.resolve()}; "
                "its tests would import that tree's code (#264)"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="venv_owner")
    parser.add_argument("venv")
    parser.add_argument("--tree", default=".")
    args = parser.parse_args(argv)
    found = problems(Path(args.tree), Path(args.venv))
    for problem in found:
        print(f"make install refused: {problem}. Remove it and run `make install` again.", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
