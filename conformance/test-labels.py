#!/usr/bin/env python3
"""`make labels` never creates a file path as a label: one in the vocabulary table is refused, a project's own labels are not.

WHY (#84). scripts/create_labels.py derives the vocabulary from every backticked span in the Labels cells of
.agents/rules/issues.md. A citation of `.agents/rules/ci-traps.md` added to the Gate row's cell made every
`make labels` create a label of that name, and the vocabulary is meant to be closed. Three cases: the vocabulary
derived from this tree's issues.md is non-empty and holds no file path; a fixture whose Labels cell cites a file
path makes create_labels refuse with exit 2, naming that span alone, before it reaches `gh`; and the labels a
project may add (`priority/high`, `v1.2`) are not refused (review M2).

Exit: 0 all hold - 1 one does not.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "create_labels.py"


def main() -> int:
    bad: list[str] = []
    sys.path.insert(0, str(SCRIPT.parent))
    import create_labels  # noqa: PLC0415
    names = [n for _, n in create_labels.vocabulary()]
    paths = [n for n in names if not getattr(create_labels, "PATH", None) or create_labels.PATH.search(n)]
    if not names or paths:
        bad.append(f"the vocabulary derived from .agents/rules/issues.md is {'empty' if not names else 'holds a file path'}: {paths}")

    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        (base / "scripts").mkdir()
        (base / ".agents" / "rules").mkdir(parents=True)
        (base / "bin").mkdir()                                       # on PATH, empty: no gh to reach
        shutil.copy(SCRIPT, base / "scripts" / SCRIPT.name)
        def labels(cell: str) -> subprocess.CompletedProcess:
            (base / ".agents" / "rules" / "issues.md").write_text(
                f"| Group | Labels |\n|---|---|\n| **Type** | `bug` · `enhancement` |\n| **Gate** | {cell} |\n",
                encoding="utf-8")
            return subprocess.run([sys.executable, "-I", str(base / "scripts" / SCRIPT.name)], capture_output=True,
                                  text=True, env=dict(os.environ, PATH=str(base / "bin")), timeout=60)

        r = labels("`agent:triage` · `priority/high` · `v1.2` (its traps: `.agents/rules/ci-traps.md`)")
        if r.returncode != 2 or "a file path, not a label" not in r.stdout or ".agents/rules/ci-traps.md" not in r.stdout \
                or "priority/high" in r.stdout or "v1.2" in r.stdout:
            bad.append(f"a file path in a Labels cell: wanted a refusal (exit 2) naming it alone, got exit {r.returncode}: "
                       f"{r.stdout.strip()[-200:]!r}")
        r = labels("`agent:triage` · `priority/high` · `v1.2`")             # a project's own labels: no gh, so listed
        if r.returncode != 2 or "gh not installed" not in r.stdout or "priority/high" not in r.stdout \
                or "v1.2" not in r.stdout:
            bad.append(f"labels a project adds (`priority/high`, `v1.2`): wanted them listed for creation, got exit "
                       f"{r.returncode}: {r.stdout.strip()[-200:]!r}")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-labels FAIL: {len(bad)} finding(s)" if bad else
          f"test-labels PASS: {len(names)} labels, no file path; a file path in a Labels cell is refused, priority/high and v1.2 are not")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
