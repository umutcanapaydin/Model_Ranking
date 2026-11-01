#!/usr/bin/env python3
"""`make prune-merged`: delete the local branches whose pull requests merged and whose branch GitHub deleted (#50).

`/post-merge` used to delete a merged branch on origin and here. The remote delete was refused five times by the
auto-mode classifier in one field project, and the guard refuses a branch delete over a variable, so two owners
deleted branches by hand. GitHub now deletes a merged pull request's branch (`delete_branch_on_merge`, the owner's
row in `docs/owner-actions.md`); this deletes the local copies, and nothing else. It never pushes.

After `git fetch --prune origin`, a local branch is deleted only when all three hold:
  * its upstream is on origin and is gone;
  * its tip is on the default branch (origin/HEAD, else origin/main, else origin/master): its work is merged;
  * `git branch -d` agrees -- git's own check, against HEAD once the upstream is gone, which also refuses a
    branch a worktree has checked out. Run from the default branch, pulled (`/post-merge` §2 does).
Any other branch stays, and one whose upstream is gone says why.

`--pr N` (`make prune-merged PR=<n>`, `/post-merge` §2) first deletes that PR's own branch, with `git branch -D`:
squash-merged, or still on origin while the owner's delete-branch-on-merge row is off -- the branch `make doctor`
names until it is gone. Only when gh shows the PR MERGED and the local tip is the PR's `headRefOid`: a commit made
after the merge keeps the branch (P5 review, M2), and a PR gh cannot read deletes nothing.

Exit: 0 done, each deleted or kept branch named · 2 cannot run (usage, no origin, the fetch failed, no default
branch, the PR unreadable or not MERGED): nothing was deleted.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

DEFAULTS = ("origin/HEAD", "origin/main", "origin/master")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def first_line(r: subprocess.CompletedProcess) -> str:
    return ((r.stderr or r.stdout).strip().splitlines() or [f"exit {r.returncode}"])[0]


def merged_pr(n: str) -> tuple[str, str] | str:
    """(headRefName, headRefOid) of PR n when gh shows it MERGED, else why not."""
    if shutil.which("gh") is None:
        return "gh not installed"
    try:
        r = subprocess.run(["gh", "pr", "view", n, "--json", "state,headRefName,headRefOid"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60,
                           env={**os.environ, "GH_PROMPT_DISABLED": "1"})
        data = json.loads(r.stdout) if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, ValueError) as exc:   # the class only: an OS message reads as a crash
        return f"gh cannot read PR #{n} ({exc.__class__.__name__})"
    if not isinstance(data, dict):
        return f"`gh pr view {n}` failed: {first_line(r)}"
    name, oid = data.get("headRefName"), data.get("headRefOid")
    if data.get("state") != "MERGED":
        return f"PR #{n} is {data.get('state')}, not MERGED"
    if not (isinstance(name, str) and name and isinstance(oid, str) and re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", oid)):
        return f"`gh pr view {n}` names no head branch and commit"
    return name, oid


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):    # a console that cannot encode a character prints `?`
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    if len(argv) == 1 and argv[0].startswith("--pr="):
        argv = ["--pr", argv[0][5:]]
    if argv and not (len(argv) == 2 and argv[0] == "--pr" and argv[1].isdigit()):
        print("usage: prune_merged.py [--pr N] -- merged local branches whose upstream is gone; N's own branch by its head")
        return 2

    def cannot(why: str) -> int:
        print(f"prune-merged CANNOT RUN: {why} -- nothing was deleted")
        return 2

    try:
        if git("rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
            return cannot("not inside a git work tree")
        if "origin" not in git("remote").stdout.split():
            return cannot("no `origin` remote")
        fetched = git("fetch", "--prune", "--quiet", "origin")
        if fetched.returncode:
            return cannot(f"`git fetch --prune origin` failed: {first_line(fetched)}")
        default = next((ref for ref in DEFAULTS
                        if git("rev-parse", "-q", "--verify", f"{ref}^{{commit}}").returncode == 0), None)
        if default is None:
            return cannot("no default branch to compare with (origin/HEAD, origin/main, origin/master); "
                          "`git remote set-head origin --auto` names it")
        if default == "origin/HEAD":
            default = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD").stdout.strip() or default
        current = git("branch", "--show-current").stdout.strip()
        deleted = kept = untouched = 0
        listed = git("for-each-ref", "--format=%(refname:short)%00%(upstream)", "refs/heads")
        remote = git("for-each-ref", "--format=%(refname)", "refs/remotes/origin")
        if listed.returncode or remote.returncode:
            return cannot(f"`git for-each-ref` failed: {first_line(listed if listed.returncode else remote)}")
        head = merged_pr(argv[1]) if argv else None
        if isinstance(head, str):
            return cannot(head)
        if head:
            name, oid = head
            tip = git("rev-parse", "-q", "--verify", f"refs/heads/{name}^{{commit}}").stdout.strip()
            if not tip:
                print(f"prune-merged: PR #{argv[1]}'s branch {name} is not here")
            elif tip != oid or name == current:
                print(f"prune-merged: kept {name} -- " + (f"its tip {tip[:7]} is not the PR's head {oid[:7]}: a commit "
                      "after the merge, or not pulled" if tip != oid else "it is checked out here; switch first"))
                kept += 1
            else:
                removed = git("branch", "-D", name)
                print(f"prune-merged: kept {name} -- git branch -D refused: {first_line(removed)}" if removed.returncode
                      else f"prune-merged: deleted {name} (was {tip[:7]}, PR #{argv[1]}'s head)")
                kept, deleted = (kept + 1, deleted) if removed.returncode else (kept, deleted + 1)
    except OSError as exc:                                      # the class only: an OS message reads as a crash
        return cannot(f"git cannot run ({exc.__class__.__name__})")
    on_origin = set(remote.stdout.split())
    for row in listed.stdout.splitlines():
        name, upstream = (row.split("\0") + [""])[:2]
        if head and name == head[0]:
            continue
        if not upstream.startswith("refs/remotes/origin/") or upstream in on_origin:
            untouched += 1
            continue
        if name == current:
            print(f"prune-merged: kept {name} -- it is checked out here; switch to the default branch first")
            kept += 1
            continue
        on_default = git("merge-base", "--is-ancestor", name, default).returncode
        if on_default != 0:
            why = "its tip is not on" if on_default == 1 else "cannot tell whether its tip is on"
            print(f"prune-merged: kept {name} -- upstream gone, {why} {default}: squash-merged or never merged "
                  "(/post-merge §2)")
            kept += 1
            continue
        tip = git("rev-parse", "--short", name).stdout.strip()
        removed = git("branch", "-d", name)
        if removed.returncode:
            print(f"prune-merged: kept {name} -- git branch -d refused: {first_line(removed)}")
            kept += 1
            continue
        print(f"prune-merged: deleted {name} (was {tip}, on {default})")
        deleted += 1
    print(f"prune-merged: {deleted} deleted, {kept} kept, {untouched} untouched (upstream on origin, or none) -- "
          "local branches only, nothing pushed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
