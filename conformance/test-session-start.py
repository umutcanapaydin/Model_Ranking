#!/usr/bin/env python3
"""After a compaction the SessionStart message names the branch and the issue; at startup it is v7.2's message, byte for byte.

WHY (v7.3, A25; the owner's ruling of 2026-10-28). The SessionStart output is loaded into every session, so
every byte of it is paid on every turn: the addition is made after a compaction only, when the agent has lost
what it was working on. It names the open run file (the message already did), the branch, and the issue: from
`issue-<n>` in the branch, from the running row of the open run for that branch, or from the container issue
of a heavy wave's plan section (`## Wave <W>`, not the wave before it). A branch with no issue gets the branch
alone; a tree without `scripts/doctor.py` (an older install) gets the message unchanged; a payload that is not
JSON still gets the message, and the session marker the hook writes for `make session-check` is still written.

Each case runs the SessionStart hook from .claude/settings.json through `sh -c`, as Claude Code does, in a
throwaway repository.

Exit: 0 every case behaves - 1 one does not - 2 git or sh not installed.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
STARTUP = ("DevFlow: working mode light. Before any change, run /start-session: it reads docs/owner-actions.md, "
           "the process log, the open PRs, and anything merged but not cleaned up.")


def git(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=scrubbed_env())


def main() -> int:
    gone = missing_tool("git", "build the repository the hook reads") or missing_tool("sh", "run the hook")
    if gone:
        print(f"test-session-start NOT-EVALUABLE: {gone}")
        return 2
    hooks = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]["SessionStart"]
    command = hooks[0]["hooks"][0]["command"]
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        proj = pathlib.Path(tmp)
        (proj / "docs" / "plans").mkdir(parents=True)
        (proj / "scripts").mkdir()
        for f in ("doctor.py", "brief_fields.py"):
            if (ROOT / "scripts" / f).is_file():           # absent, the compaction cases fail by their lines
                shutil.copy(ROOT / "scripts" / f, proj / "scripts" / f)
        (proj / "docs" / "project-brief.md").write_text("- **Working mode:** `light`\n", encoding="utf-8")
        git(proj, "init", "-q", "-b", "main")
        git(proj, "add", "-A")
        git(proj, "-c", "user.name=f", "-c", "user.email=f@x", "commit", "-qm", "base")

        def hook(source: str | None, payload: str | None = None, sid: str = "abcd1234-probe") -> str:
            body = payload if payload is not None else json.dumps({"session_id": sid, "source": source})
            r = subprocess.run(["sh", "-c", command], input=body, capture_output=True, text=True, cwd=proj,
                               env=scrubbed_env({"CLAUDE_PROJECT_DIR": str(proj)}))
            return r.stdout if r.returncode == 0 else f"<exit {r.returncode}> {r.stdout}{r.stderr}"

        def expect(name: str, got: str, want: str) -> None:
            if got != want + "\n":
                bad.append(f"  {name}:\n    wanted {want!r}\n    got    {got!r}")

        expect("startup: the v7.2 message, byte for byte", hook("startup"), STARTUP)
        if not (proj / ".git" / "devflow-sessions" / "abcd1234-probe").is_file():
            bad.append("  the session marker make session-check reads was not written")
        expect("resume: unchanged", hook("resume"), STARTUP)
        expect("compact on main: the branch alone", hook("compact"), STARTUP + " After the compaction: branch main.")
        git(proj, "switch", "-q", "-c", "fix/issue-12-thing")
        expect("compact on a fix branch: its issue", hook("compact"),
               STARTUP + " After the compaction: branch fix/issue-12-thing, issue #12.")
        expect("a payload that is not JSON: the message, unchanged", hook(None, payload="{not json"), STARTUP)

        git(proj, "switch", "-q", "-c", "enhancement/owner-view")
        run = proj / "docs" / "plans" / "run-demo.md"
        run.write_text("Mode: light\nStarted: 2026-10-28\nEnded: open\n\n## Waves\n\n| Wave | Branch | PR | Close record "
                       "| Status |\n|---|---|---|---|---|\n| issue-60 | enhancement/other | none | none | running |\n"
                       "| issue-61 | enhancement/owner-view | none | none | running |\n", encoding="utf-8")
        expect("compact in a run: the run file, and the issue of the running row for this branch", hook("compact"),
               STARTUP + " A run is open (docs/plans/run-demo.md): /start-session resumes it. After the compaction: "
               "branch enhancement/owner-view, issue #61.")
        run.unlink()

        git(proj, "switch", "-q", "-c", "wave/m2-w3")
        (proj / "docs" / "plans" / "m2-plan.md").write_text(
            "# M2\n\n## Wave 2\n\n- Container issue: #33; children: #40\n\n## Wave 3\n\n- Risk tier: LOW\n"
            "- Container issue: #34; children: #41, #42\n\n## K.8 contracts\n\nnone\n", encoding="utf-8")
        expect("compact on a heavy wave: its plan section's container issue", hook("compact"),
               STARTUP + " After the compaction: branch wave/m2-w3, issue #34.")

        (proj / "scripts" / "doctor.py").unlink(missing_ok=True)
        expect("compact in a tree without scripts/doctor.py: unchanged", hook("compact"), STARTUP)

    print("\n".join(bad))
    print(f"test-session-start {'FAIL' if bad else 'PASS'}: startup unchanged; after a compaction the branch and the "
          "issue" + (f" -- {len(bad)} finding(s)" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
