#!/usr/bin/env python3
"""The gate stamp spares a second gate run only on the tree the gate passed on.

WHY (v7.2, the owner's ruling of 2026-10-17). `make gate` writes the commit it passed on
(`scripts/gate_stamp.py write`); the pre-push hook and `/pre-merge` accept it instead of running the
gate again. A stamp that outlives its tree would be a gate that never ran, so both polarities: the
stamp is accepted on exactly that commit with a clean tree, and refused after an edit, after a new
commit, for a push carrying another commit, and when there is none; a dirty tree is never stamped.
The pre-push hook is run for real: with a stamp it does not call `make`, without one it does.

Exit: 0 every case behaves - 1 one does not - 2 git or bash not available.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, runnable_bash, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway repository the stamp is read in")):
        print(f"test-gate-stamp NOT-EVALUABLE: {no_git}")
        return 2
    bash, why = runnable_bash("run the pre-push hook")
    if not bash:
        print(f"test-gate-stamp NOT-EVALUABLE: {why}")
        return 2
    bad: list[str] = []
    count = 0
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / "repo"
        (repo / "scripts").mkdir(parents=True)
        (repo / ".githooks").mkdir()
        shutil.copy(ROOT / "scripts" / "gate_stamp.py", repo / "scripts" / "gate_stamp.py")
        shutil.copy(ROOT / ".githooks" / "pre-push", repo / ".githooks" / "pre-push")
        (repo / "a.txt").write_text("one\n", encoding="utf-8")
        fake = pathlib.Path(tmp) / "bin"
        fake.mkdir()
        (fake / "make").write_text("#!/bin/sh\necho \"fake-make: $*\"\nexit 7\n", encoding="utf-8")
        (fake / "make").chmod(0o755)
        env = scrubbed_env()

        def git(*args: str) -> str:
            return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=repo,
                                  capture_output=True, encoding="utf-8", env=env, check=True).stdout.strip()

        def stamp(*args: str, extra: dict | None = None) -> tuple[int, str]:
            # `make gate` runs it with MAKELEVEL set; a case that drops it passes {"MAKELEVEL": ""}
            r = subprocess.run([sys.executable, "scripts/gate_stamp.py", *args], cwd=repo,
                               capture_output=True, encoding="utf-8", env={**env, "MAKELEVEL": "1", **(extra or {})})
            return r.returncode, r.stdout + r.stderr

        def prepush(sha: str, *more: str) -> tuple[int, str]:
            lines = "".join(f"refs/heads/b{k} {s} refs/heads/b{k} {'0' * 40}\n" for k, s in enumerate((sha, *more)))
            r = subprocess.run([bash, ".githooks/pre-push", "origin", "url"], cwd=repo, input=lines,
                               capture_output=True, encoding="utf-8",
                               env={**env, "PATH": os.pathsep.join((str(fake), env.get("PATH", "")))})
            return r.returncode, r.stdout + r.stderr

        def case(name: str, got: tuple[int, str], rc: int, text: str) -> None:
            nonlocal count
            count += 1
            if got[0] != rc or text not in got[1]:
                bad.append(f"  {name}: exit {got[0]} (want {rc}), `{text}` {'missing' if text not in got[1] else ''}\n"
                           + "\n".join(f"    {ln}" for ln in got[1].splitlines()[-6:]))

        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "one")
        head = git("rev-parse", "HEAD")
        case("no stamp: no PASS", stamp("check"), 1, "no stamp")
        case("no stamp: pre-push runs the gate (and refuses on its failure)", prepush(head), 1, "fake-make: gate")
        case("write on a clean tree", stamp("write", "Makefile"), 0, "gate stamp: " + head[:12])
        case("the stamped commit, clean: PASS", stamp("check", head), 0, "gate stamp PASS")
        case("the stamped commit: pre-push does not run the gate", prepush(head), 0, "not run again")
        case("a push carrying another commit: no PASS", stamp("check", head, "f" * 40), 1, "not HEAD")
        case("a push of two refs, one of them another commit: pre-push runs the gate",
             prepush("f" * 40, head), 1, "fake-make: gate")
        case("make told to ignore errors (MAKEFLAGS=i): nothing is stamped",
             stamp("write", "Makefile", extra={"MAKEFLAGS": "i"}), 0, "change what the legs run")
        case("a variable set on make's command line (MAKEFLAGS carries PY=...): nothing is stamped",
             stamp("write", "Makefile", extra={"MAKEFLAGS": " -- PY=/usr/bin/true"}), 0, "change what the legs run")
        case("after that refusal: no PASS", stamp("check"), 1, "no stamp")
        stamp("write", "Makefile")
        git("config", "status.showUntrackedFiles", "no")
        (repo / "hidden.txt").write_text("x\n", encoding="utf-8")
        case("an untracked file git status was told to hide: no PASS", stamp("check"), 1, "uncommitted")
        (repo / "hidden.txt").unlink()
        case("a makefile beside this repository's (`make -f Makefile -f -`): nothing is stamped",
             stamp("write", "Makefile", "/tmp/Gmla0hrE"), 0, "change what the legs run")
        case("make -j (the jobserver flags carry `=`): stamped as usual",
             stamp("write", "Makefile", extra={"MAKEFLAGS": " --jobserver-fds=3,4 -j"}), 0, "gate stamp: ")
        (repo / "a.txt").write_text("two\n", encoding="utf-8")
        case("an edit after the stamp: no PASS", stamp("check"), 1, "uncommitted")
        case("an edit after the stamp: pre-push runs the gate", prepush(head), 1, "fake-make: gate")
        case("write on a dirty tree: no stamp", stamp("write", "Makefile"), 0, "uncommitted changes")
        case("...and the refusal names the file that keeps the tree dirty (v7.2.1)", stamp("write", "Makefile"), 0,
             "(a.txt)")
        count += 1
        if list(pathlib.Path(git("rev-parse", "--absolute-git-dir")).glob("devflow-gate-ok-*")):
            bad.append("  write on a dirty tree left a stamp behind")
        git("commit", "-q", "-am", "two")
        case("a new commit after the stamp: no PASS", stamp("check"), 1, "no stamp")
        stamp("write", "Makefile")
        git("commit", "-q", "--allow-empty", "-m", "three")
        case("HEAD moved past the stamp: no PASS", stamp("check"), 1, "no stamp for HEAD")
        stamp("write", "Makefile")
        case("the script run by hand, not by make (no MAKELEVEL): nothing is stamped, the old stamp goes",
             stamp("write", "Makefile", extra={"MAKELEVEL": ""}), 0, "not run by a plain")
        case("after that: no PASS", stamp("check"), 1, "no stamp for HEAD")
        case("make 3.81 under -j with -i (`--jobserver-fds=3,4 -j -i`): nothing is stamped",
             stamp("write", "Makefile", extra={"MAKEFLAGS": " --jobserver-fds=3,4 -j -i"}), 0, "change what the legs run")
        # A package below the repository's top (a monorepo, the distribution itself): make runs there.
        sub = repo / "pkg"
        sub.mkdir()
        (sub / "Makefile").write_text("x:\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "pkg")
        r = subprocess.run([sys.executable, str(repo / "scripts" / "gate_stamp.py"), "write", "Makefile"], cwd=sub,
                           capture_output=True, encoding="utf-8", env={**env, "MAKELEVEL": "1"})
        case("make run in a package below the top, reading its own Makefile: stamped", (r.returncode, r.stdout),
             0, "gate stamp: ")
        # A writing agent's own worktree (AGENTS.md §4, K.4) sits under `.claude/worktrees/`. Unless the
        # shipped .gitignore covers it, git lists it untracked and no stamp is written beside it (v7.3.1).
        shutil.copy(ROOT / ".gitignore", repo / ".gitignore")
        git("add", ".gitignore")
        git("commit", "-q", "-m", "ignore")
        git("worktree", "add", "-q", "-b", "agent-x", str(repo / ".claude" / "worktrees" / "agent-x"))
        stamp("write", "Makefile")
        case("an agent's worktree under .claude/worktrees/, with the shipped .gitignore: PASS", stamp("check"),
             0, "gate stamp PASS")

    if bad:
        print("test-gate-stamp FAIL (scripts/gate_stamp.py and .githooks/pre-push in a throwaway repository):")
        print("\n".join(bad))
        return 1
    print(f"test-gate-stamp PASS: {count} cases -- the stamp spares a second gate run only on the commit and "
          "tree the gate passed on; the pre-push hook runs the gate otherwise")
    return 0


if __name__ == "__main__":
    sys.exit(main())
