#!/usr/bin/env python3
"""The gate stamp: `make gate` records the commit it passed on, so the same tree is not graded again.

WHY (v7.2, the owner's ruling of 2026-10-17). A light fix ran the full gate three times on one tree
-- its own step, the pre-push hook, `/pre-merge` -- and a run's wave five times, about eight minutes
and 14k tokens of output per wave, with nothing changed between them (process audit F-7, D-26).

  write MAKEFILE...  run by `make gate` after every leg passed (it passes `$(MAKEFILE_LIST)`; make
                 sets MAKELEVEL): when the work tree is clean, make read only the `Makefile` (and
                 `stack.mk`) of the directory it runs in, inside this repository, and MAKEFLAGS changes nothing the legs run, write
                 `<git dir>/devflow-gate-ok-<HEAD>` and remove every older stamp; otherwise remove them
                 all (an uncommitted change was graded, and HEAD is not that tree)
  check [SHA..]  PASS when HEAD's stamp exists, the work tree is clean, and every SHA given is HEAD
                 (pre-push passes the commits it is about to push)

The commit is in the file's NAME: a shell pattern expands only to names that exist, and the stamp for
a new HEAD exists only once `make gate` passed on it -- so a glob can at most rewrite an old stamp,
which proves nothing about HEAD. The Bash guard refuses a command naming `devflow-gate` or
`gate_stamp` anywhere but where it is only read (a `grep`, a `cat`, a commit message, a heredoc into
another file pass, v7.3), a pattern for this script handed to an interpreter, and `make` options or
variables that skip or replace legs; the editor guard refuses writing the stamp.

What it does not hold -- the same as the pre-push hook it serves, which the editor tool can rewrite:
it stops mistakes, not an agent set on evading it. A name built at run time, a program that writes
the file, a commit made while the gate runs (the stamp names the HEAD at its end), a work tree git is
told not to see. CI still runs every leg on the server. The stamp lives in the git dir, so a worktree
has its own.

Exit: write -- always 0 (the gate passed; a missing stamp only means the next gate runs in full);
check -- 0 PASS · 1 no PASS · 2 git cannot answer here.
"""
import os
import pathlib
import subprocess
import sys

PREFIX = "devflow-gate-ok-"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, encoding="utf-8", errors="replace")


def state() -> tuple[pathlib.Path, str, bool, pathlib.Path] | None:
    """(git dir, HEAD, whether the work tree is clean, the top of the work tree), or None."""
    gd, head, top = git("rev-parse", "--git-dir"), git("rev-parse", "HEAD"), git("rev-parse", "--show-toplevel")
    # Every untracked file counts, whatever `status.showUntrackedFiles` says: the gate read them.
    status = git("status", "--porcelain", "--untracked-files=all")
    if gd.returncode or head.returncode or status.returncode or top.returncode:
        return None
    global DIRTY
    DIRTY = [ln[3:] for ln in status.stdout.splitlines() if ln.strip()]
    return (pathlib.Path(gd.stdout.strip()), head.stdout.strip(), status.stdout.strip() == "",
            pathlib.Path(top.stdout.strip()).resolve())


#: The paths that keep the tree from being clean, named in the refusal: a staged file nobody noticed made
#: every push of one field project run its gate again, and the message did not say which (Project-J, v7.2).
DIRTY: list[str] = []


def dirty() -> str:
    shown = ", ".join(DIRTY[:5]) + (f" and {len(DIRTY) - 5} more" if len(DIRTY) > 5 else "")
    return f" ({shown})" if shown else ""


def clear(gitdir: pathlib.Path) -> None:
    for old in [*gitdir.glob(PREFIX + "*"), gitdir / PREFIX.rstrip("-")]:   # and the first cut's name
        old.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("write", "check"):
        print("usage: gate_stamp.py write MAKEFILE... | check [SHA ...]")
        return 2
    now = state()
    if now is None:
        print("gate stamp: git cannot read this tree -- no stamp")
        return 0 if argv[0] == "write" else 2
    gitdir, head, clean, top = now
    stamp = gitdir / (PREFIX + head)
    if argv[0] == "write":
        flags = os.environ.get("MAKEFLAGS", "").split()
        # The letters of every short-option word: make 3.81 puts `--jobserver-fds=...` first under -j.
        letters = "".join(f.lstrip("-") for k, f in enumerate(flags) if not f.startswith("--") and "=" not in f
                          and (f.startswith("-") or k == 0))
        makefiles = argv[1:]
        # The recipe runs where make reads its Makefile -- the top, or the package below it.
        here = pathlib.Path.cwd().resolve()
        allowed = {here / "Makefile", here / "stack.mk"} if here == top or top in here.parents else set()
        foreign = [m for m in makefiles if pathlib.Path(m).resolve() not in allowed]
        # Not from inside make (a script run by hand), `make -i`, `-t`, `-n`, `-q`, `-e`, a variable set
        # on the command line (`make gate PY=/usr/bin/true`, carried in MAKEFLAGS as a word with no
        # leading dash), or a makefile beside this repository's two (`make -f Makefile -f - gate`): the
        # legs may not have run as written, so nothing is stamped.
        if (not os.environ.get("MAKELEVEL") or set(letters) & set("itnqe")
                or any("=" in f and not f.startswith("-") for f in flags) or not makefiles or foreign):
            clear(gitdir)
            print("gate stamp: none -- not run by a plain `make gate`: make ran with options, variables or a "
                  "makefile beside this repository's that change what the legs run "
                  f"(MAKEFLAGS={os.environ.get('MAKEFLAGS', '')!r}); run plain `make gate`")
            return 0
        if not clean:
            clear(gitdir)
            print(f"gate stamp: none -- the work tree has uncommitted changes{dirty()}, so the gate graded a tree "
                  "no commit holds; commit first, then `make gate` -- the order that lets the push skip it")
            return 0
        clear(gitdir)
        stamp.write_text(head + "\n", encoding="utf-8")
        print(f"gate stamp: {head[:12]} -- pre-push and /pre-merge accept it while HEAD and the tree stay so")
        return 0
    have = stamp.read_text(encoding="utf-8").strip() if stamp.is_file() else ""
    others = [s for s in argv[1:] if s != head]
    if have == head and clean and not others:
        print(f"gate stamp PASS: `make gate` passed on {head[:12]}, and the tree is that commit")
        return 0
    why = ("no stamp for HEAD" if not have else
           f"HEAD's stamp names {have[:12]}" if have != head else
           f"the work tree has uncommitted changes{dirty()}" if not clean else
           f"{len(others)} commit(s) being pushed are not HEAD")
    print(f"gate stamp: no PASS -- {why}; run `make gate`")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
