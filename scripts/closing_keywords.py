#!/usr/bin/env python3
"""Which issues would the commit messages in a range close when they reach the default branch? (#255, D-206)

    python3 scripts/closing_keywords.py --range A..B      (make closing-keywords RANGE=A..B)

GitHub closes an issue that a closing keyword directly precedes in a commit message once that commit is on
the default branch, whatever the pull request's body says. `gh pr view --json closingIssuesReferences` reads
the body and the manual links only, so it cannot see this path: `fix: #194's model names ...` (35a8563)
closed #194 with that field empty, and 26a334a closed #222 the same way, seconds after #251 merged.

The keyword set is GitHub's: close, closes, closed, fix, fixes, fixed, resolve, resolves, resolved, in any
case, as a word of its own, then a colon or whitespace, then the reference: `#N`, `owner/repo#N`, or an
issue URL. One keyword closes the one reference right after it (`Closes #1, #2` closes #1 alone). A
mention with no keyword before it (`for #255`, `see #12`, `the fix for #12`) closes nothing and is not
listed. Every commit in the range is read, merge commits included, subject and body.

Advisory, not a leg of `make check` (D-206 clause 6): `/pre-merge` asks it. What it does not read: the PR
body's own `Closes` lines -- `gh pr view <pr> --json closingIssuesReferences` is the authority for those.

The last line is the answer: `closing-keywords: none`, or the references in the order they first appear,
oldest commit first. Exit 0 when none, 1 when any, 2 when there is nothing to grade: no range given, a
single revision instead of a range (it would read the whole history, which no merge brings in), a range
git cannot read, or a range with no commits. Each of those is an error, never a pass.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

KEYWORD = r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)"
REFERENCE = (r"(?:https?://github\.com/(?P<url_repo>[\w.-]+/[\w.-]+)/issues/(?P<url_n>\d+)"
             r"|(?P<repo>[\w.-]+/[\w.-]+)#(?P<repo_n>\d+)"
             r"|#(?P<n>\d+))\b")
CLOSING = re.compile(KEYWORD + r"(?::\s*|\s+)" + REFERENCE, re.IGNORECASE)


def closed_by(message: str) -> list[str]:
    """Every issue reference a closing keyword directly precedes in `message`, each once, in order."""
    found: list[str] = []
    for m in CLOSING.finditer(message):
        if m.group("url_n"):
            ref = f"{m.group('url_repo')}#{m.group('url_n')}"
        elif m.group("repo_n"):
            ref = f"{m.group('repo')}#{m.group('repo_n')}"
        else:
            ref = f"#{m.group('n')}"
        if ref not in found:
            found.append(ref)
    return found


class RangeError(Exception):
    """The range cannot be graded: nothing given, not a range, unreadable, or empty."""


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    # `git` with literal subcommands; the range is passed as one argument, before `--`, never to a shell.
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8",  # noqa: S603, S607
                              errors="replace", check=False)
    except OSError as exc:
        raise RangeError(f"git did not run ({exc})") from exc


def read_range(rev_range: str | None) -> tuple[str, list[tuple[str, str]]]:
    """(what was read, [(sha, message)] oldest first), or RangeError when there is nothing to grade."""
    if not rev_range:
        raise RangeError("no range given -- make closing-keywords RANGE=A..B")
    if ".." not in rev_range:
        raise RangeError(f"`{rev_range}` is not a range -- a single revision reads the whole history; give A..B")
    ends = _git("rev-parse", rev_range, "--")
    if ends.returncode != 0:
        raise RangeError(f"cannot read the range `{rev_range}`: {ends.stderr.strip() or 'git rev-parse failed'}")
    shas = [s for s in ends.stdout.split() if s != "--"]
    lows = ",".join(s[1:11] for s in shas if s.startswith("^")) or "-"
    highs = ",".join(s[:10] for s in shas if not s.startswith("^")) or "-"
    log = _git("log", "--reverse", "--format=%H%x00%B%x1e", rev_range, "--")
    if log.returncode != 0:
        raise RangeError(f"cannot read the range `{rev_range}`: {log.stderr.strip() or 'git log failed'}")
    commits = []
    for record in log.stdout.split("\x1e"):
        sha, _, message = record.lstrip("\n").partition("\x00")
        if sha:
            commits.append((sha, message))
    if not commits:
        raise RangeError(f"the range `{rev_range}` holds no commits -- an empty range grades nothing")
    return f"range: {rev_range} ({lows}..{highs}), {len(commits)} commits", commits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--range", dest="rev_range", help="the commits to read, A..B")
    args = parser.parse_args(argv)
    try:
        header, commits = read_range(args.rev_range)
    except RangeError as exc:
        print(f"closing-keywords: ERROR -- {exc}", file=sys.stderr)
        return 2
    print(header)
    print("reads every commit message in the range; the PR body's own closing lines are not read here "
          "(gh pr view <pr> --json closingIssuesReferences)")
    found: list[str] = []
    for sha, message in commits:
        subject = (message.strip().splitlines() or [""])[0]
        for ref in closed_by(message):
            print(f"{ref}  closed by {sha[:10]}  {subject[:100]}")
            if ref not in found:
                found.append(ref)
    if found:
        print("A merge that brings these commits to the default branch closes each issue above. One that must "
              "stay open: say so in the PR body, for the human who merges.")
        print(f"closing-keywords: {' '.join(found)}")
        return 1
    print("closing-keywords: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
