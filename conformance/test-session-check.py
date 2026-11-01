#!/usr/bin/env python3
"""`make session-check` fails closed when git cannot answer, and its lines say what was checked.

WHY (DevFlow #16, S5, K1, D7). `scripts/session_check.py` returned 0 when `git rev-parse` failed --
a fail-open in the one place a session with no repository guards is certain. Its PASS line claimed
"pre-push runs make gate" having checked only `core.hooksPath`, and two projects read that as proof
(one had the hook off). The session that installs or upgrades the hook can never pass the check,
and two projects answered that with skip rows, one of them into the three-skips lock; the failure
line now says to start a new session instead, and says what a session started outside the
repository root is missing (no profile, skill or hook is registered in it).

v7.3 (#49): an agent work tree whose `core.hooksPath` names the main work tree's `.githooks` by its absolute
path failed every check in it (Project-K: 21 false post-edit blocks and a night run that could not push),
and a session started in one repository of a product could never push its sibling. The main work tree's
hooks under the same common dir now pass, and so does the marker of a sibling the brief's `Sibling
repositories:` line declares; a foreign hooks path and an undeclared sibling still fail.

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
CASES = [0]


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
        CASES[0] += 1
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

    # Issue #43: git prints --git-common-dir relative to the CURRENT directory (`../.git` from a
    # subdirectory), and the SessionStart hook resolves it from there. Resolved against the toplevel,
    # it lands one level above the repository -- found only when a `.git` sits there, as it did.
    with tempfile.TemporaryDirectory() as tmp:
        outer = pathlib.Path(tmp)
        (outer / ".git").mkdir()
        d = outer / "repo"
        d.mkdir()
        git(d, "init", "-q")
        (d / ".githooks").mkdir()
        (d / "pkg").mkdir()
        (d / ".git" / "devflow-sessions").mkdir()
        (d / ".git" / "devflow-sessions" / SID).write_text("", encoding="utf-8")
        git(d, "config", "core.hooksPath", ".githooks")
        case("started in a subdirectory, a .git above the repository: the marker is read from this "
             "repository (#43)", run(d / "pkg"), 0, "session-check PASS")

    # v7.3 A15 (#49): an agent work tree whose shared config names the main work tree's `.githooks` by its
    # absolute path passes; a foreign repository's `.githooks` still fails. A session started in a sibling
    # repository the brief declares has its marker there, and only a declared one counts.
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp).resolve()
        main_wt, foreign = base / "main", base / "foreign"
        for r in (main_wt, foreign):
            (r / ".githooks").mkdir(parents=True)
            (r / ".githooks" / "pre-push").write_text("#!/bin/sh\n", encoding="utf-8")
            git(r, "init", "-q")
            git(r, "add", "-A")
            git(r, "-c", "user.name=f", "-c", "user.email=f@x", "commit", "-qm", "base")
        (main_wt / ".git" / "devflow-sessions").mkdir()
        (main_wt / ".git" / "devflow-sessions" / SID).write_text("", encoding="utf-8")
        git(main_wt, "worktree", "add", "-q", str(base / "agent-wt"), "-b", "work")
        git(main_wt, "config", "core.hooksPath", str(main_wt / ".githooks"))
        case("an agent work tree, core.hooksPath the main work tree's .githooks by absolute path: PASS (#49)",
             run(base / "agent-wt"), 0, "session-check PASS", "the main work tree's .githooks")
        case("the main work tree itself, the same absolute path: PASS, the line unchanged", run(main_wt), 0,
             "session-check PASS", "resolves to this clone's .githooks")
        git(main_wt, "config", "core.hooksPath", str(foreign / ".githooks"))
        case("an agent work tree, core.hooksPath another repository's .githooks: FAIL", run(base / "agent-wt"), 1,
             "not this clone's `.githooks`", "make hooks")

    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp).resolve()
        app, backend = base / "app", base / "backend"
        for r in (app, backend):
            (r / ".githooks").mkdir(parents=True)
            git(r, "init", "-q")
            git(r, "config", "core.hooksPath", ".githooks")
        (app / ".git" / "devflow-sessions").mkdir()
        (app / ".git" / "devflow-sessions" / SID).write_text("", encoding="utf-8")
        case("a session started in a sibling the brief does not declare: FAIL", run(backend), 1,
             "no SessionStart marker", "Sibling repositories:")
        (backend / "docs").mkdir()
        brief = backend / "docs" / "project-brief.md"
        brief.write_text("- **Sibling repositories:** `<none | comma-separated paths>`\n", encoding="utf-8")
        case("the brief's line still a placeholder: FAIL", run(backend), 1, "no SessionStart marker")
        brief.write_text("- **Sibling repositories:** `../app`\n", encoding="utf-8")
        case("a session started in the declared sibling `../app`: PASS, and the line names it (#49)", run(backend), 0,
             "session-check PASS", "declared sibling", "app")
        (app / ".git" / "devflow-sessions" / SID).unlink()
        case("the declared sibling holds no marker for this session either: FAIL", run(backend), 1,
             "no SessionStart marker")
        brief.write_text("- **Sibling repositories:** `../missing`\n", encoding="utf-8")
        case("a declared sibling that is not a repository: FAIL, closed", run(backend), 1, "no SessionStart marker")

    if bad:
        print("test-session-check FAIL (scripts/session_check.py in throwaway directories):")
        print("\n".join(bad))
        return 1
    print(f"test-session-check PASS: {CASES[0]} cases of scripts/session_check.py -- fail closed, both causes "
          "named, the PASS line says what it checked, a work tree's main hooks and a declared sibling's marker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
