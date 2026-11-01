#!/usr/bin/env python3
"""`make ci-diff`: what DevFlow changed in its workflows between the version this tree came from and the one it
runs -- one command for the owner.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit E-19). An agent never edits
`.github/workflows/**`, so every workflow change waits for the owner -- and in all three field projects
`ci.yml` had drifted, its fixes sitting as diffs in issues for days.

v7.2.1 (field, Project-J, -K and -L): v7.2 printed `HEAD` against the installed tag, so a project's own
workflow changes came out as reverts, and the paste-ready command would have deleted a backend's whole Go
job. Now it prints DevFlow's own change, old tag to new tag, and says when this tree already carries it.
The versions are the brief's `process_version:` and the last different one in its committed history
(`deploy_gate.devflow_history`, the deploy gate's own reading): the newest earlier version whose change
this tree does not carry yet, so a step the owner skipped two upgrades back still shows, and one already
applied is not printed again. `FROM=` and
`TO=` override them.

    python3 scripts/ci_diff.py [--from <tag>] [--to <tag>]

Advisory: exit 0 with the diff or with what is missing; exit 2 only when git cannot run here.
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def git(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace",
                          input=stdin)


def has_tag(tag: str) -> bool:
    return git("rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}").returncode == 0


def carried(diff: str) -> bool:
    """Whether this tree already holds a diff's change (it applies in reverse)."""
    return not diff.strip() or git("apply", "--reverse", "--check", stdin=diff).returncode == 0


def arg(argv: list[str], flag: str) -> str | None:
    if flag not in argv:
        return None
    i = argv.index(flag)
    return argv[i + 1] if i + 1 < len(argv) and argv[i + 1] else ""


def main(argv: list[str]) -> int:
    if shutil.which("git") is None:
        print("ci-diff CANNOT RUN: git is not installed")
        return 2
    from deploy_gate import devflow_history  # noqa: PLC0415
    history = devflow_history(ROOT)
    given_from, given_to = arg(argv, "--from"), arg(argv, "--to")
    if "" in (given_from, given_to):
        print("ci-diff: --from and --to each take a tag (make ci-diff FROM=<tag> TO=<tag>)")
        return 2
    current = given_to or (history[0] if history else None)
    if not current:
        print("ci-diff: the brief declares no `process_version:` and there is no `.gp/installed` -- nothing to compare")
        return 0
    # Every earlier version in the brief's history, newest first, unless FROM= names one: a workflow step the
    # owner skipped two upgrades ago must not vanish because the last step changed no workflow (v7.2.1, review).
    earlier = [given_from] if given_from else [v for v in history if v != current]
    if not earlier:
        print(f"ci-diff: no earlier DevFlow version in the brief's history -- this tree installed `{current}` "
              "directly; name the old one with `make ci-diff FROM=<tag>`")
        return 0
    # A version older than DevFlow's tags (a General Pipeline package) is skipped, not a reason to stop.
    tagged = [v for v in earlier if has_tag(v)]
    if not has_tag(current) or not tagged:
        missing = [t for t in (current, *earlier) if not has_tag(t)]
        print(f"ci-diff: no DevFlow tag {', '.join(f'`{t}`' for t in missing)} in this clone -- `git fetch "
              "devflow --tags` (INSTALL.md) and run this again; a version older than DevFlow's tags (a General "
              "Pipeline package) never has one: name a tagged version with `make ci-diff FROM=<tag>`")
        return 0
    earlier = tagged
    # The newest version whose change since it this tree does not carry yet: an older step the owner already
    # applied is not printed again (v7.2.1, review). Once that is applied, the next run finds an older one.
    previous = next((v for v in earlier if not carried(git("diff", v, current, "--", ".github/workflows").stdout)),
                    None)
    if previous is None:
        print(f"ci-diff: this tree carries DevFlow's workflows from `{earlier[-1]}` to `{current}` -- nothing for "
              "the owner")
        return 0
    diff = git("diff", previous, current, "--", ".github/workflows")
    print(diff.stdout, end="")
    print(f"\nci-diff: DevFlow's workflow change from `{previous}` to `{current}` (above), which this tree does not "
          f"carry yet. The owner applies it with:\n  git diff {previous} {current} -- .github/workflows | git apply -3\n"
          "It changes only what DevFlow changed; where a hunk conflicts with the project's own CI, keep the "
          "project's and take DevFlow's by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
