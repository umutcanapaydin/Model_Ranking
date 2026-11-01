#!/usr/bin/env python3
"""`make prune-merged` deletes only local branches whose upstream GitHub deleted and whose work is on the default branch.

WHY (#50, v7.3 A32; Project-J and Project-L). `/post-merge` deleted the merged branch on origin and locally. The
remote delete was refused five times by the auto-mode classifier in one project, the guard refuses a branch
delete over a variable (`$b`, eleven times across three), and two owners ended up deleting branches by hand,
one through a 35-branch owner row. GitHub now deletes a merged pull request's branch (`delete_branch_on_merge`,
the owner's row in `docs/owner-actions.md`), and `make prune-merged` deletes the local copies. It never pushes, and
it never deletes a branch whose work is not on the default branch.

Proved on a throwaway repository whose `origin` is a bare one and whose "GitHub" is a second clone that merges
and deletes head branches there, out of the first clone's sight:
  * deleted: a branch merged with a merge commit whose upstream is gone;
  * kept: a squash-merged branch and one never merged (their tips are not on the default branch), one merged and
    then given a local commit, one checked out in a worktree, and a merged one while HEAD is behind
    origin/main (`git branch -d` refuses: git's own check is the second lock) -- deleted after the pull;
  * kept, and this is the case only the first lock catches: an unmerged branch whose stacked child is HEAD,
    which `git branch -d` alone would delete, its tip being in HEAD;
  * untouched: a merged branch still on origin, and a branch never pushed;
  * nothing deleted, exit 2, when the fetch fails or there is no default branch to compare with.
With PR=<n> (`/post-merge` §2, after step 1 saw the PR MERGED; P5 review, M2 and B1) the PR's own branch goes too,
squash-merged or still on origin, but only while its tip is the PR's head (`headRefOid`): a branch given a commit
after the merge is kept, as is one a worktree holds; a PR gh cannot read, or one not MERGED, deletes nothing.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import QUIET_GIT, missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "prune_merged.py"
ID = ("-c", "user.name=f", "-c", "user.email=f@x")
GH = ('#!/bin/sh\n[ "$1 $2" = "pr view" ] && [ -f "$FAKE_GH_DIR/pr-$3.json" ] && exec cat "$FAKE_GH_DIR/pr-$3.json"\n'
      'echo "no pull requests found" >&2\nexit 1\n')


def main() -> int:
    no_git = missing_tool("git", "build the throwaway repositories prune_merged.py prunes")
    if no_git:
        print(f"test-prune-merged NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        origin, proj, hub = base / "origin.git", base / "proj", base / "hub"

        def git(cwd: pathlib.Path, *args: str, check: bool = True) -> str:
            r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=scrubbed_env())
            if check and r.returncode:
                raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
            return r.stdout.strip()

        def quiet(cwd: pathlib.Path) -> None:
            for key, value in QUIET_GIT:
                git(cwd, "config", key, value)

        def work(name: str, msg: str, start: str = "main") -> None:
            """A branch in the project with one commit, pushed with its upstream set."""
            git(proj, "checkout", "-q", "-b", name, start)
            (proj / f"{name.replace('/', '-')}.txt").write_text(msg + "\n", encoding="utf-8")
            git(proj, "add", "-A")
            git(proj, *ID, "commit", "-q", "-m", msg)
            git(proj, "push", "-q", "-u", "origin", name)
            git(proj, "checkout", "-q", "main")

        def github(name: str, how: str = "merge", delete: bool = True) -> None:
            """What GitHub does on a merge: the head lands on main (a merge commit or a squash), then the head
            branch is deleted on origin. The project does not see it until it fetches."""
            git(hub, "fetch", "-q", "origin")
            git(hub, "checkout", "-q", "-B", "main", "origin/main")
            if how == "merge":
                git(hub, *ID, "merge", "-q", "--no-ff", "-m", f"Merge pull request from {name}", f"origin/{name}")
            else:
                # A squash merge asks for the committer's identity too: CI has none, and scrubbed_env drops
                # GIT_COMMITTER_* (#258), so it is given here as for every commit (the v7.3.1 upgrade's CI, D-241).
                git(hub, *ID, "merge", "-q", "--squash", f"origin/{name}")
                git(hub, *ID, "commit", "-q", "-m", f"{name} (squashed)")
            git(hub, "push", "-q", "origin", "main")
            if delete:
                git(origin, "branch", "-D", name)

        fake = base / "bin"
        fake.mkdir()
        (fake / "gh").write_text(GH, encoding="utf-8")
        (fake / "gh").chmod(0o755)
        env = scrubbed_env({"FAKE_GH_DIR": str(base), "PATH": os.pathsep.join([str(fake), os.environ.get("PATH", "")])})

        def run(*args: str) -> tuple[int, str]:
            r = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=proj, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env=env)
            return r.returncode, r.stdout + r.stderr

        def branches() -> set[str]:
            return set(git(proj, "for-each-ref", "--format=%(refname:short)", "refs/heads").split())

        def expect(name: str, got: tuple[int, str], rc: int, present: set[str], gone: set[str], *want: str) -> None:
            code, out = got
            have = branches()
            why = [w for w in want if w not in out]
            if code != rc or not present <= have or gone & have or why:
                bad.append(f"  {name}: exit {code} (wanted {rc}); should still exist: {sorted(present - have)}; "
                           f"should be gone: {sorted(gone & have)}; missing {why}; output:\n    "
                           + out.strip().replace("\n", "\n    ")[:1500])

        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], capture_output=True, check=True,
                       env=scrubbed_env())
        quiet(origin)
        proj.mkdir()
        git(proj, "init", "-q", "-b", "main")
        quiet(proj)
        (proj / "a.txt").write_text("base\n", encoding="utf-8")
        git(proj, "add", "-A")
        git(proj, *ID, "commit", "-q", "-m", "base")
        git(proj, "remote", "add", "origin", str(origin))
        git(proj, "push", "-q", "-u", "origin", "main")
        git(base, "clone", "-q", str(origin), str(hub))
        quiet(hub)

        work("fix/merged", "merged with a merge commit")
        work("fix/squashed", "merged as a squash")
        work("fix/unmerged", "closed without a merge")
        work("fix/still-on-origin", "merged, branch kept on origin")
        work("fix/merged-then-more", "merged, then a local commit")
        work("fix/in-worktree", "merged, checked out in a worktree")
        work("fix/lower", "a lower branch, never merged")
        work("fix/upper", "stacked on the lower one", start="fix/lower")
        git(proj, "checkout", "-q", "-b", "local/never-pushed")
        git(proj, *ID, "commit", "-q", "--allow-empty", "-m", "never pushed")
        git(proj, "checkout", "-q", "main")
        for name in ("fix/merged", "fix/merged-then-more", "fix/in-worktree"):
            github(name)
        github("fix/squashed", how="squash")
        github("fix/still-on-origin", delete=False)
        git(origin, "branch", "-D", "fix/unmerged")
        git(origin, "branch", "-D", "fix/lower")
        heads = {n: git(proj, "rev-parse", n) for n in ("fix/squashed", "fix/merged-then-more", "fix/still-on-origin",
                                                       "fix/in-worktree", "fix/unmerged")}
        git(proj, "checkout", "-q", "fix/merged-then-more")
        git(proj, *ID, "commit", "-q", "--allow-empty", "-m", "after the merge")
        git(proj, "checkout", "-q", "main")
        git(proj, "worktree", "add", "-q", str(base / "wt"), "fix/in-worktree")
        everything = branches()

        # HEAD (main) is behind origin/main: git's own check refuses the merged branches, and nothing is lost.
        expect("main not pulled yet: git branch -d refuses", run(), 0, everything, set(), "kept fix/merged",
               "git branch -d refused")
        # From a stacked child of an unmerged branch: `git branch -d` alone would delete fix/lower, its tip in HEAD.
        git(proj, "checkout", "-q", "fix/upper")
        expect("HEAD holds an unmerged branch's tip", run(), 0, {"fix/lower"}, set(), "kept fix/lower")
        git(proj, "checkout", "-q", "main")
        git(proj, "pull", "-q", "--ff-only", "origin", "main")
        expect("after the pull", run(), 0,
               everything - {"fix/merged"}, {"fix/merged"},
               "deleted fix/merged", "kept fix/squashed", "kept fix/unmerged", "kept fix/merged-then-more",
               "kept fix/in-worktree", "kept fix/lower", "1 deleted")
        code, out = run()
        if code != 0 or "deleted fix/" in out or "0 deleted" not in out:
            bad.append(f"  a second run deletes nothing more: exit {code}, output: {out.strip()[:600]}")
        if run("--now")[0] != 2:
            bad.append("  an argument is not a usage error (exit 2)")

        # PR=<n>: the PR's own branch, by its head. Fail closed first: nothing is deleted.
        def pr(n: int, name: str, state: str = "MERGED", oid: str | None = None) -> str:
            (base / f"pr-{n}.json").write_text(json.dumps({"state": state, "headRefName": name,
                                                           "headRefOid": oid or heads.get(name, "0" * 40)}), encoding="utf-8")
            return str(n)

        left = everything - {"fix/merged"}
        expect("PR: gh cannot read the PR", run("--pr", "31"), 2, left, set(), "prune-merged CANNOT RUN",
               "nothing was deleted")
        expect("PR: not MERGED", run("--pr", pr(32, "fix/unmerged", state="OPEN")), 2, left, set(), "CANNOT RUN",
               "not MERGED")
        for spelled in (("--pr", "x"), ("--pr",), ("--pr", "34", "--pr", "35")):
            expect(f"PR: usage {spelled}", run(*spelled), 2, left, set(), "usage")
        expect("PR: a commit after the merge is kept", run("--pr", pr(33, "fix/merged-then-more")), 0, left, set(),
               "kept fix/merged-then-more", "not the PR's head")
        expect("PR: squash-merged, tip is the PR's head", run("--pr", pr(34, "fix/squashed")), 0, left - {"fix/squashed"},
               {"fix/squashed"}, "deleted fix/squashed")
        left -= {"fix/squashed"}
        expect("PR: still on origin (row off), tip is the PR's head", run(f"--pr={pr(35, 'fix/still-on-origin')}"), 0,
               left - {"fix/still-on-origin"}, {"fix/still-on-origin"}, "deleted fix/still-on-origin")
        left -= {"fix/still-on-origin"}
        if "refs/heads/fix/still-on-origin" not in git(proj, "ls-remote", "--heads", "origin"):
            bad.append("  PR: the branch on origin was deleted -- prune-merged must never push")
        expect("PR: checked out in a worktree", run("--pr", pr(36, "fix/in-worktree")), 0, left, set(),
               "kept fix/in-worktree")
        expect("PR: its branch is not here", run("--pr", pr(37, "fix/not-here", oid="1" * 40)), 0, left, set(),
               "fix/not-here", "not here")

        # Fail closed: a fetch that fails, or no default branch to compare with, deletes nothing.
        git(proj, "branch", "fix/again", "main")
        git(proj, "config", "branch.fix/again.remote", "origin")
        git(proj, "config", "branch.fix/again.merge", "refs/heads/fix/again")
        git(proj, "remote", "set-url", "origin", str(base / "no-such-origin.git"))
        expect("the fetch fails", run(), 2, {"fix/again"}, set(), "prune-merged CANNOT RUN", "nothing was deleted")
        git(proj, "remote", "set-url", "origin", str(origin))
        git(origin, "branch", "-m", "main", "trunk")
        git(origin, "symbolic-ref", "HEAD", "refs/heads/trunk")
        expect("no default branch on origin", run(), 2, {"fix/again"}, set(), "prune-merged CANNOT RUN")
        git(proj, "remote", "remove", "origin")
        expect("no origin", run(), 2, {"fix/again"}, set(), "prune-merged CANNOT RUN")

    print("\n".join(bad))
    print(f"test-prune-merged {'FAIL' if bad else 'PASS'}: merged and gone deleted; squashed, unmerged, re-committed, "
          "checked out, stacked, still on origin and never pushed kept; fail closed" +
          (f" -- {len(bad)} finding(s)" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
