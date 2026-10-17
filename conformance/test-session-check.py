#!/usr/bin/env python3
"""`make session-check` fails closed when git cannot answer, and its lines say what was checked.

WHY (DevFlow #16, S5, K1, D7). `scripts/session_check.py` returned 0 when `git rev-parse` failed --
a fail-open in the one place a session with no repository guards is certain. Its PASS line claimed
"pre-push runs make gate" having checked only `core.hooksPath`, and two projects read that as proof
(one had the hook off). The session that installs or upgrades the hook can never pass the check,
and two projects answered that with skip rows, one of them into the three-skips lock; the failure
line now says to start a new session instead, and says what a session started outside the
repository root is missing (no profile, skill or hook is registered in it).

Each case runs the script in a throwaway directory with a probe session id in the environment --
the run-all runner strips the real one, so these cases set their own.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "session_check.py"
SID = "0000aaaa-probe-session"


def run(cwd: pathlib.Path, sid: str | None = SID, ci: bool = False) -> tuple[int, str]:
    env = scrubbed_env({"CLAUDE_CODE_SESSION_ID": sid} if sid else {})
    env.pop("CLAUDE_CODE_SESSION_ID", None) if sid is None else None
    # The runner this test itself runs on may be GitHub Actions; only the CI case says so.
    env.pop("GITHUB_ACTIONS", None)
    if ci:
        env["GITHUB_ACTIONS"] = "true"
    r = subprocess.run([sys.executable, str(SCRIPT)], cwd=cwd, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def git(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=scrubbed_env())


def main() -> int:
    no_git = missing_tool("git", "build the throwaway repositories session_check.py reads")
    if no_git:
        print(f"test-session-check NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []

    def case(name: str, got: tuple[int, str], rc: int, *want: str, absent: tuple[str, ...] = ()) -> None:
        code, out = got
        if code != rc or any(w not in out for w in want) or any(a in out for a in absent):
            bad.append(f"  {name}: exit {code} (wanted {rc}); wanted {list(want)}, forbidden {list(absent)}\n"
                       + "\n".join(f"    {ln}" for ln in out.splitlines()))

    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp) / "not-a-repo"
        d.mkdir()
        case("outside Claude Code: nothing to check", run(d, sid=None), 0, "not inside a Claude Code session")
        case("inside Claude Code, not a git work tree: FAIL, closed", run(d), 1, "fail closed",
             "cannot read the git work tree")
        case("the CI issue agent (GitHub Actions): CI is the enforcement, nothing to check", run(d, ci=True), 0,
             "in GitHub Actions")

    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        git(d, "init", "-q")
        case("no marker: the line names both causes and the cure", run(d), 1,
             "START A NEW SESSION", "no agent profile", "installed or upgraded", "Do not record a skip row")
        (d / ".githooks").mkdir()
        (d / ".git" / "devflow-sessions").mkdir()
        (d / ".git" / "devflow-sessions" / SID).write_text("", encoding="utf-8")
        case("marker present, no hooks path: FAIL names make hooks", run(d), 1, "core.hooksPath is `unset`",
             "make hooks")
        git(d, "config", "core.hooksPath", ".githooks")
        case("marker present, hooks path set: PASS says what it checked, and not what the hook runs",
             run(d), 0, "session-check PASS", "checked the SessionStart marker", "core.hooksPath",
             "Not checked: what .githooks/pre-push runs", absent=("pre-push runs make gate",))

    if bad:
        print("test-session-check FAIL (scripts/session_check.py in throwaway directories):")
        print("\n".join(bad))
        return 1
    print("test-session-check PASS: 6 cases of scripts/session_check.py -- fail closed, both causes named, "
          "the PASS line says what it checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
