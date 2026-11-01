#!/usr/bin/env python3
"""`make ci-diff` shows the owner DevFlow's own workflow change, old version to new -- never the project's.

WHY (v7.2, the owner's ruling of 2026-10-17; v7.2.1, field). In all three field projects `ci.yml` had
drifted, because only the owner may edit a workflow and nothing showed the difference. v7.2 printed `HEAD`
against the installed tag, so a project's own CI came out as reverts and the paste-ready command would have
deleted a backend's Go job. Both polarities in a throwaway repository: DevFlow's change between the brief's
two versions is printed with its one command; a project's own workflow job is not touched by it; a tree
that already carries the change, a first install, a missing tag and `FROM=` each say what they are.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEF = "---\nprocess_version: {v}\n---\n- **Working mode:** `light`\n"


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway repository ci-diff reads")):
        print(f"test-ci-diff NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    count = 0
    env = scrubbed_env()
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)
        (repo / "scripts").mkdir()
        (repo / "docs").mkdir()
        (repo / ".github" / "workflows").mkdir(parents=True)
        for name in ("ci_diff.py", "deploy_gate.py", "brief_fields.py"):
            shutil.copy(ROOT / "scripts" / name, repo / "scripts" / name)

        def write(rel: str, text: str) -> None:
            (repo / rel).write_text(text, encoding="utf-8")

        def git(*args: str) -> None:
            subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=repo, check=True,
                           capture_output=True, env=env)

        def run(*args: str) -> str:
            r = subprocess.run([sys.executable, "scripts/ci_diff.py", *args], cwd=repo, capture_output=True,
                               text=True, env=env)
            return r.stdout + r.stderr

        def case(name: str, out: str, want: str, absent: str = "") -> None:
            nonlocal count
            count += 1
            if want not in out or (absent and absent in out):
                bad.append(f"  {name}: `{want}` missing" + (f" or `{absent}` present" if absent else "") + "\n"
                           + "\n".join(f"    {ln}" for ln in out.splitlines()[-6:]))

        git("init", "-q")
        case("no brief version and no marker: says so", run(), "declares no `process_version:`")
        # #331: the marker as `scripts/write_install_marker.py` writes it, its comment lines first, is read when
        # the brief declares no version: a pattern anchored at the file's start read none.
        (repo / ".gp").mkdir()
        write(".gp/installed", "# Written by `make install`. Do not edit by hand.\n# Read this.\ngp_version: v9.9\n")
        case("a marker with its comment lines is read", run(), "installed `v9.9` directly")
        (repo / ".gp" / "installed").unlink()
        write("docs/project-brief.md", BRIEF.format(v="v9.9"))
        write(".github/workflows/ci.yml", "name: CI\njobs:\n  test:\n    steps: [falsify]\n  a: 1\n  b: 2\n  c: 3\n  d: 4\n  e: 5\n")
        git("add", "-A")
        git("commit", "-q", "-m", "devflow v9.9")
        git("tag", "v9.9")
        case("a first install: names the way to give the old version", run(), "make ci-diff FROM=<tag>")
        # The project adds its own job; DevFlow v9.10 drops a step. The project upgrades, CI untouched.
        write(".github/workflows/ci.yml", "name: CI\njobs:\n  test:\n    steps: [falsify]\n  a: 1\n  b: 2\n  c: 3\n  d: 4\n  e: 5\n  go:\n    steps: [go-test]\n")
        git("commit", "-q", "-am", "the project's own Go job")
        git("switch", "-q", "-c", "devflow", "v9.9")
        write(".github/workflows/ci.yml", "name: CI\njobs:\n  test:\n    steps: []\n  a: 1\n  b: 2\n  c: 3\n  d: 4\n  e: 5\n")
        git("commit", "-q", "-am", "DevFlow v9.10")
        git("tag", "v9.10")
        git("switch", "-q", "-")
        write("docs/project-brief.md", BRIEF.format(v="v9.10"))
        git("commit", "-q", "-am", "upgrade to v9.10")
        out = run()
        case("an upgrade: DevFlow's change old tag to new", out, "git diff v9.9 v9.10 -- .github/workflows | git apply -3")
        case("...and never the project's own job as a revert", out, "-    steps: [falsify]", absent="go-test")
        git("tag", "v9.11", "v9.10")
        case("FROM= and TO= override the brief", run("--from", "v9.10", "--to", "v9.11"), "carries DevFlow's workflows")
        # v7.2.1, the review: the brief moves on to a version that changed no workflow; the step still owed
        # from v9.9 must still show.
        git("tag", "v9.12", "v9.10")
        write("docs/project-brief.md", BRIEF.format(v="v9.12"))
        git("commit", "-q", "-am", "upgrade to v9.12, workflows unchanged since v9.10")
        case("a skipped step from two upgrades back still shows", run(), "git diff v9.9 v9.12 -- .github/workflows")
        diff = subprocess.run(["git", "diff", "v9.9", "v9.10", "--", ".github/workflows"], cwd=repo,
                              capture_output=True, text=True, env=env).stdout
        subprocess.run(["git", "apply", "-3"], cwd=repo, input=diff, text=True, capture_output=True, env=env)
        out = run()
        case("the owner applied it: nothing more", out, "carries DevFlow's workflows from `v9.9`")
        case("...and the project's own job survived the owner's command",
             (repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"), "go-test")
        # The owner applied the old step; DevFlow changes another one: only the new step is printed.
        git("commit", "-q", "-am", "the owner applied DevFlow's workflow change")
        git("switch", "-q", "devflow")
        wf = repo / ".github" / "workflows" / "ci.yml"
        wf.write_text(wf.read_text(encoding="utf-8").replace("  e: 5\n", "  e: 6\n"), encoding="utf-8")
        git("commit", "-q", "-am", "DevFlow v9.13")
        git("tag", "v9.13")
        git("switch", "-q", "-")
        write("docs/project-brief.md", BRIEF.format(v="v9.13"))
        git("commit", "-q", "-am", "upgrade to v9.13")
        out = run()
        case("an applied old step is not printed again: the newest uncarried one", out,
             "git diff v9.12 v9.13 -- .github/workflows", absent="v9.9 v9.13")
        case("a tag not fetched: says how to fetch it", run("--from", "v1.0"), "git fetch devflow --tags")
        case("--from with no tag: says what it takes", run("--from"), "each take a tag")

    if bad:
        print("test-ci-diff FAIL (scripts/ci_diff.py in a throwaway repository):")
        print("\n".join(bad))
        return 1
    print(f"test-ci-diff PASS: {count} cases -- DevFlow's own workflow change between the brief's two versions, "
          "with the owner's one command; the project's own CI untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
