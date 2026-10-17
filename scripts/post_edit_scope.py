#!/usr/bin/env python3
"""Where the post-edit hook runs `make check-fast`, and how much of it: `<directory>|<check-fast args>`.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit E-34 and B-I12). Two things the field hit:
  * the hook ran in `$CLAUDE_PROJECT_DIR` while the agent edited a file in a worktree
    (`.claude/worktrees/x`), so it graded a tree nobody had changed -- two projects wrote their own
    script to run it where the edited file lives;
  * after a Markdown edit -- a verdict, a checklist, the process log -- it ran lint, the type checker
    and the whole test suite, none of which a document can change, and stayed red while a record was
    half written.

So: the directory is the work tree that holds the edited file (when it carries this kit's
`Makefile`), and an edit to a document -- `*.md`, or anything under `docs/` or `.agents/` -- runs only
the records leg (`--only-records`). Anything this cannot read prints `|`: the hook then runs the full
`check-fast` where it always did. The pre-push gate and CI run every leg regardless.

Reads the hook's JSON payload on stdin. Exit 0 always: the hook decides, this only advises.
"""
import json
import pathlib
import subprocess
import sys


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        raw = str((payload.get("tool_input") or {}).get("file_path") or "")
    except (ValueError, AttributeError):
        raw = ""
    if not raw:
        print("|")
        return 0
    path = pathlib.Path(raw)
    here = path.parent
    while not here.is_dir() and here != here.parent:
        here = here.parent
    r = subprocess.run(["git", "-C", str(here), "rev-parse", "--show-toplevel"], capture_output=True,
                       encoding="utf-8", errors="replace")
    top = pathlib.Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    directory = str(top) if top and (top / "Makefile").is_file() and (top / "scripts" / "check_fast.py").is_file() \
        else ""
    try:
        rel = path.resolve().relative_to(top.resolve()).parts if top else path.parts
    except ValueError:
        rel = path.parts
    document = path.suffix.lower() == ".md" or (rel[:1] in (("docs",), (".agents",)))
    print(f"{directory}|{'--only-records' if document else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
