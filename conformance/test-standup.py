#!/usr/bin/env python3
"""`make standup` opens with what needs the owner: every open row of docs/owner-actions.md and an open run's stops, never a done row.

WHY (v7.3, A23; ruflo take-away 7, the owner's ruling of 2026-10-28). `/start-session` read the whole of
docs/owner-actions.md for its open rows, and every byte of it stayed in the session's context; standup now
prints those rows, first. A row is open when its last cell, Status, is not `done` in any case -- read from the
end, since a command cell may hold a `|`. An open run's Stops rows are the questions the owner decides; an
ended run's are not. Nothing open says `(nothing)`. The test writes its own owner-actions file: it runs in every
project, and a project's own open rows are its normal state, never a failure (v7.3 review, B1).

Each case runs scripts/standup.sh in a throwaway repository.

Exit: 0 every case behaves - 1 one does not - 2 bash or git not installed.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEADER = "----- Needs the owner -----"
STOPS = ("\n## Waves\n\n| Wave | Branch | PR | Close record | Status |\n|---|---|---|---|---|\n"
         "| issue-61 | enhancement/x | none | none | stopped |\n\n## Stops\n\n"
         "| When | Wave | Class | What the owner decides | Continued on |\n|---|---|---|---|---|\n"
         "| 2026-10-29 | issue-61 | control-change | {q} | nothing |\n\n## For the owner\n")


def section(out: str) -> list[str]:
    """The lines of the first section after the header block."""
    lines = out.splitlines()
    first = next((i for i, ln in enumerate(lines) if ln.startswith("----- ")), None)
    if first is None or lines[first] != HEADER:
        return [f"<first section is {lines[first] if first is not None else 'missing'}>"]
    end = next((i for i in range(first + 1, len(lines)) if lines[i].startswith("----- ")), len(lines))
    return [ln for ln in lines[first + 1:end] if ln.strip()]


def main() -> int:
    gone = missing_tool("bash", "run standup.sh") or missing_tool("git", "build the repository standup reads")
    if gone:
        print(f"test-standup NOT-EVALUABLE: {gone}")
        return 2
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        proj = pathlib.Path(tmp)
        (proj / "scripts").mkdir()
        (proj / "docs" / "plans").mkdir(parents=True)
        (proj / ".claude" / "skills").mkdir(parents=True)      # an installation's: standup counts them
        shutil.copy(ROOT / "scripts" / "standup.sh", proj / "scripts" / "standup.sh")
        (proj / "docs" / "owner-actions.md").write_text(       # the fixture's own, never the project's
            "# Owner actions\n\n| Date | What | Why | The command | Status |\n|---|---|---|---|---|\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=proj, capture_output=True, env=scrubbed_env(), check=True)

        def standup() -> list[str]:
            r = subprocess.run(["bash", "scripts/standup.sh"], cwd=proj, capture_output=True, text=True,
                               env=scrubbed_env())
            return section(r.stdout) if r.returncode == 0 else [f"<exit {r.returncode}> {r.stderr[-300:]}"]

        got = standup()
        if got != ["(nothing)"]:
            bad.append(f"  nothing open: wanted `(nothing)`, got {got}")
        rows = ["| 2026-10-28 | Merge the integration PR | the run ended | `gh pr merge 67 --merge` | open |",
                "| 2026-10-27 | Re-pin the guard | the guard changed | `make guard-pin` | done |",
                "| 2026-10-27 | Enable alerts | Dependabot | `gh api -X PUT x` | DONE |",
                "| 2026-10-28 | Apply the bundle | a workflow | `make owner-bundle | sh` | waiting |"]
        with (proj / "docs" / "owner-actions.md").open("a", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
        (proj / "docs" / "plans" / "run-open.md").write_text(
            "Mode: light\nStarted: 2026-10-28\nEnded: open\n" + STOPS.format(q="whether the workflow diff lands"),
            encoding="utf-8")
        (proj / "docs" / "plans" / "run-old.md").write_text(
            "Mode: light\nStarted: 2026-10-01\nEnded: 2026-10-02 — owner stopped\n" + STOPS.format(q="an old question"),
            encoding="utf-8")
        got = standup()
        want = [rows[0], rows[3], "docs/plans/run-open.md: stop | 2026-10-29 | issue-61 | control-change | "
                "whether the workflow diff lands | nothing |"]
        if got != want:
            bad.append("  open rows and an open run's stops, first, and never a done row or an ended run's stop:\n"
                       + "\n".join(f"    wanted {w}" for w in want) + "\n" + "\n".join(f"    got    {g}" for g in got))

    print("\n".join(bad))
    print(f"test-standup {'FAIL' if bad else 'PASS'}: what needs the owner opens the standup"
          + (f" -- {len(bad)} finding(s)" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
