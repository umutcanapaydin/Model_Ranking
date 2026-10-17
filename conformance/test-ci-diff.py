#!/usr/bin/env python3
"""`make ci-diff` shows the owner what DevFlow's workflows say that this repository's do not.

WHY (v7.2, the owner's ruling of 2026-10-17). In all three field projects `ci.yml` had drifted from the
version installed, because only the owner may edit a workflow and nothing showed the difference. Both
polarities in a throwaway repository: a drifted workflow prints its diff and the one command; an equal
one says there is nothing; a tag not fetched and a tree with no marker say what is missing.

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
        (repo / ".github" / "workflows").mkdir(parents=True)
        shutil.copy(ROOT / "scripts" / "ci_diff.py", repo / "scripts" / "ci_diff.py")

        def git(*args: str) -> None:
            subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=repo, check=True,
                           capture_output=True, env=env)

        def run() -> str:
            return subprocess.run([sys.executable, "scripts/ci_diff.py"], cwd=repo, capture_output=True,
                                  text=True, env=env).stdout

        def case(name: str, out: str, want: str) -> None:
            nonlocal count
            count += 1
            if want not in out:
                bad.append(f"  {name}: `{want}` missing\n" + "\n".join(f"    {ln}" for ln in out.splitlines()[-5:]))

        git("init", "-q")
        case("no install marker: says so", run(), "no `.gp/installed`")
        (repo / ".gp").mkdir()
        # #331: the marker as `scripts/write_install_marker.py` writes it, its comment lines first. A
        # bare `gp_version:` line here let a pattern anchored at the file's start pass, and the real
        # marker made every ci-diff answer "no `.gp/installed`".
        (repo / ".gp" / "installed").write_text(
            "# Written by `make install`. Do not edit by hand.\n# Read this.\ngp_version: v9.9\n", encoding="utf-8")
        (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\non: push\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "devflow v9.9")
        case("the tag not fetched: says how to fetch it", run(), "git fetch devflow --tags")
        git("tag", "v9.9")
        case("the workflows match the tag: nothing for the owner", run(), "nothing for the owner")
        (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\non: [push, pull_request]\n",
                                                               encoding="utf-8")
        git("commit", "-q", "-am", "the project's own change")
        out = run()
        case("a drifted workflow: its diff", out, "pull_request")
        case("a drifted workflow: the owner's one command", out, "git diff HEAD v9.9 -- .github/workflows | git apply -3")

    if bad:
        print("test-ci-diff FAIL (scripts/ci_diff.py in a throwaway repository):")
        print("\n".join(bad))
        return 1
    print(f"test-ci-diff PASS: {count} cases -- the installed tag's workflows against this repository's, with "
          "the owner's one command")
    return 0


if __name__ == "__main__":
    sys.exit(main())
