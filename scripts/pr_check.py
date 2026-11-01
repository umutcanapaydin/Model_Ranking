#!/usr/bin/env python3
"""Two things `/pre-merge` asks of a pull request, read from the branch and the PR rather than recalled (v7.3).

    python3 scripts/pr_check.py findings [--range A..B] [--pr N]           (make findings-check)
    python3 scripts/pr_check.py closing-keywords [--range A..B] [--pr N]   (make closing-keywords)

**findings** (A26; the owner's ruling of 2026-10-28: a fix's and an enhancement's finding ids are accounted for
the way wave-check accounts for a wave's). The verdicts the range adds or changes under `docs/reviews/` --
`fix-issue-*.md` and `enhancement-*.md`, read as the range's end holds them -- must each be a PASS or MINOR that
declares `**Independent:** yes`, and every finding id in their BLOCKING, MINOR, K.9 and queued-risk sections
(`**B1**`, `**M1**`, `**K1**`, `**R1**`) must be a row of the PR body's findings table, keyed by the verdict's
kind: `| security M1 | fixed <sha> |`, `#<n>` or `refused — <why>` -- wave-check's grammar, and `<sha>` must be a
commit here; a finding bullet with no id fails. A verdict whose `**Date:**` is on or before `.gp/installed`'s
`installed_on` is history for its finding ids only: they are not accounted for, one NOTE line -- a v7.2.2 PR asked
for no findings table (P5 review, B2). Its `## Verdict` and its `**Independent:** yes` are graded on every date:
v7.2.2's reviewer profiles wrote both (the P7 delta security review, M2). The install day itself is history here
(P5 re-review M5); wave-check's history for an unversioned close ends the day before. The two differ because they
skip different things: wave-check's history skips every rule written since, and a close written on the install
day carries the template's process_version, so the ambiguous day fails closed there; here history skips only the
table no v7.2.2 PR body held, so the ambiguous day stays lenient. With no readable `installed_on`, nothing is
history and a finding with no id is a NOTE. Not read here: a wave's verdicts (`make wave-check` accounts for their
ids), a release's (the deploy gate reads its verdict line and reviewed head), an integration's (no gate reads its
ids).

**closing-keywords** (A29; Project-J #255: commit subjects such as `fix: #194's ...` closed two open issues on
merge). GitHub closes the issue a keyword names in a commit message when the commit reaches the default
branch, and lists no such link on the pull request -- its `closingIssuesReferences` hold the body's only -- so
`/pre-merge` §2 cannot see it. Every keyword in the range's commit messages, subject or body (close, closes,
closed, fix, fixes, fixed, resolve, resolves, resolved; any case; a colon or not; `#12`, `owner/repo#12` or the
issue's URL) must name an issue the PR itself closes.

The range is this branch since it left the default branch (`make review-need`'s), or --range (inside a run:
`$(git merge-base integration/run-<name> HEAD)..HEAD`, `/pre-merge` §5); the PR is this branch's, or --pr. gh is
asked only when there is something to compare: a range with no finding id and no keyword passes offline. When
there is, a PR that gh cannot read is CANNOT RUN -- the comparison is never skipped.

Exit: 0 pass · 1 a finding · 2 cannot run (usage, no range, the PR unreadable).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_gate import INDEPENDENT, VERDICT  # noqa: E402
from review_need import default_range  # noqa: E402
from wave_check import DISPOSITION, deferrable_findings, findings_table  # noqa: E402

#: The verdicts `findings` reads: a fix's and an enhancement's (the owner's ruling). A wave's are wave-check's.
VERDICT_FILE = re.compile(r"^docs/reviews/(?:fix-issue|enhancement)-[^/]+\.md$")
#: `installed_on:` dates this installation (write_install_marker.py; an upgrade rewrites it): wave-check's marker.
INSTALL_MARKER = Path(".gp/installed")
DATED = re.compile(r"^\*\*Date:\*\*\s*`?(\d{4}-\d{2}-\d{2})", re.M)
#: The sections a finding id sits in: BLOCKING as well as the three a wave may leave unfixed.
SECTIONS = re.compile(r"BLOCKING|MINOR|K\.9|Risks queued", re.I)
#: GitHub's closing keywords, an optional colon, then an issue: `#12`, `owner/repo#12` or the issue's URL.
KEYWORD = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*:?\s*(?:https?://[^\s/]+/(?P<urlrepo>[\w.-]+/[\w.-]+)"
                     r"/issues/(?P<urln>\d+)|(?P<repo>[\w.-]+/[\w.-]+)?#(?P<n>\d+))", re.I)
REPO_OF = re.compile(r"^https?://[^/\s]+/([\w.-]+/[\w.-]+)/(?:pull|issues)/\d+")
#: A read-only check takes no lock from the session's own git; gh never waits for an answer nobody gives.
ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GH_PROMPT_DISABLED": "1"}
HOW_KEYWORD = ("  a keyword in a commit message closes its issue when the commit reaches the default branch, and "
               "GitHub shows no link for it. An issue this PR resolves goes in the body's `Closes` lines (/pre-merge "
               "§2); any other: re-cut the branch without that message -- a pushed commit is never rewritten")


def shown(rng: str) -> str:
    """The range as the output prints it: a full sha cut to 12 characters, still unambiguous to git."""
    return re.sub(r"\b([0-9a-f]{12})[0-9a-f]{28}\b", r"\1", rng)


class CannotRun(Exception):
    """The question has no answer here: a range git cannot read, or a PR gh cannot."""


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if r.returncode:
        raise CannotRun(f"git {' '.join(args)}: {(r.stderr.strip().splitlines() or ['failed'])[0]}")
    return r.stdout


def resolve(rng: str | None) -> tuple[str, str]:
    """(the range, its end): --range when given, else the branch since it left the default branch. A side that is
    empty or names no commit is not a range: `..HEAD` would read nothing and pass anything."""
    try:
        rng = rng or default_range()
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        raise CannotRun(str(exc)) from exc
    sep = "..." if "..." in rng else ".."
    sides = rng.split(sep, 1) if sep in rng else ["", ""]
    for side in sides:
        if not side.strip() or subprocess.run(["git", "rev-parse", "-q", "--verify", f"{side}^{{commit}}"],
                                              capture_output=True, env=ENV).returncode:
            raise CannotRun(f"`{rng}` is not a range of two commits")
    return rng, sides[1]


def pr_view(pr: str | None, fields: str) -> dict:
    cmd = ["gh", "pr", "view", *([pr] if pr else []), "--json", fields]
    if shutil.which("gh") is None:
        raise CannotRun("gh not installed: the PR's body and closing issues are read through it")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:       # the class only: an OS message reads as a crash
        raise CannotRun(f"gh cannot run ({exc.__class__.__name__})") from exc
    if r.returncode:
        raise CannotRun(f"`{' '.join(cmd)}` failed: {(r.stderr.strip().splitlines() or ['no output'])[0]}")
    try:
        data = json.loads(r.stdout)
    except ValueError as exc:
        raise CannotRun(f"`{' '.join(cmd)}` did not print JSON") from exc
    if not isinstance(data, dict):
        raise CannotRun(f"`{' '.join(cmd)}` did not print a JSON object")
    return data


def installed_on() -> str | None:
    """`.gp/installed`'s `installed_on`, or None when there is no marker or no readable date."""
    try:
        m = re.search(r"^installed_on:\s*(\d{4}-\d{2}-\d{2})\s*$",
                      INSTALL_MARKER.read_text(encoding="utf-8", errors="replace"), re.M)
    except OSError:
        return None
    return m.group(1) if m else None


def findings(rng: str, end: str, pr: str | None) -> int:
    names = [n for n in git("diff", "--name-only", "--relative", "--diff-filter=d", rng, "--", "docs/reviews/").split("\n")
             if VERDICT_FILE.match(n)]
    if not names:
        print(f"findings-check PASS: {shown(rng)}: no fix or enhancement verdict changed -- nothing to account for")
        return 0
    bad: list[str] = []
    owed: list[tuple[str, str, str]] = []           # (verdict file, kind, id)
    unnamed: list[str] = []
    history: list[str] = []
    since = installed_on()
    for rel in names:
        text = git("show", f"{end}:./{rel}")
        name = Path(rel).name
        v = VERDICT.search(text)
        if not v or "|" in v.group(2):
            bad.append(f"`{name}` carries no `## Verdict` of PASS / MINOR / BLOCKING")
        elif v.group(1) == "BLOCKING":
            bad.append(f"`{name}` is BLOCKING -- the fix goes back to the same reviewer before the hand-over")
        if not INDEPENDENT.search(text):
            bad.append(f"`{name}` does not declare `**Independent:** yes` -- a reviewer that wrote the code is no review")
        dated = DATED.search(text)
        # History skips the finding-id accounting only (P7 delta security M2); the install day is history (M5).
        if since and dated and dated.group(1) <= since:
            history.append(name)
            continue
        ids, nameless = deferrable_findings(text, SECTIONS)
        kind = Path(rel).stem.rsplit("-", 1)[-1].lower()     # `review`, `security`: the key wave-check uses too
        owed += [(name, kind, fid) for fid in dict.fromkeys(ids)]
        if nameless and since:
            bad.append(f"`{name}` has {nameless} finding(s) with no id -- a verdict written since the install "
                       f"({since}) names each (`**M1**`); the reviewer adds them")
        elif nameless:
            unnamed.append(f"{name}: {nameless}")
    kinds: dict[str, set[str]] = {}
    for name, kind, _ in owed:
        kinds.setdefault(kind, set()).add(name)
    for kind, files in sorted(kinds.items()):
        if len(files) > 1:
            bad.append(f"the range holds {len(files)} {kind} verdicts with ids ({', '.join(sorted(files))}): a row "
                       f"`| {kind} M1 |` cannot say which -- grade one change's range (RANGE=, /pre-merge §5)")
    if history:
        print(f"NOTE [findings-check]: {', '.join(history)} dated on or before DevFlow's install here ({since}): history "
              "-- its verdict and independence are graded, its finding ids are not; account for its findings in the "
              "PR body by hand")
    if unnamed:
        print(f"NOTE [findings-check]: finding(s) with no id ({', '.join(unnamed)}) -- not graded; account for each "
              "in the PR body by hand")
    if owed:
        table = findings_table(str(pr_view(pr, "body").get("body") or ""))
        for name, kind, fid in owed:
            d = table.get(f"{kind} {fid.lower()}")
            if d is None:
                bad.append(f"`{name}` finding {fid} has no row in the PR body's findings table "
                           f"(`| {kind} {fid} | fixed <sha> |`, `#<n>` or `refused — <why>`)")
            elif not DISPOSITION.match(d):
                bad.append(f"finding `{kind} {fid}` has disposition `{d[:40]}` -- write fixed `<sha>`, `#<issue>`, "
                           "or `refused — <why the finding is wrong>`")
            else:
                sha = re.match(r"fixed\s+`?([0-9a-fA-F]{7,40})", d, re.I)
                if sha and subprocess.run(["git", "rev-parse", "-q", "--verify", f"{sha.group(1).lower()}^{{commit}}"],
                                          capture_output=True, env=ENV).returncode:
                    bad.append(f"finding `{kind} {fid}` is `fixed {sha.group(1)}`, and that is not a commit here")
    for b in bad:
        print(f"FAIL [findings-check]: {b}")
    if bad:
        return 1
    print(f"findings-check PASS: {shown(rng)}: {len(names)} verdict(s)"
          + (f" ({len(history)} history, ids not graded)" if history else "")
          + f", {len(owed)} finding id(s), each a row of the PR body's findings table")
    return 0


def repo_of(url: object) -> str:
    m = REPO_OF.match(url) if isinstance(url, str) else None
    return m.group(1).lower() if m else ""


def closing_keywords(rng: str, pr: str | None) -> int:
    log = git("log", "--reverse", "--format=%H%x1f%B%x1e", rng)
    commits = [c.split("\x1f", 1) for c in log.split("\x1e") if "\x1f" in c]
    found: list[tuple[str, str, str, int]] = []      # (sha, the words, the repository or "" for this one, issue)
    for sha, message in commits:
        for m in KEYWORD.finditer(message):
            repo = (m.group("urlrepo") or m.group("repo") or "").lower()
            ref = (sha.strip(), " ".join(m.group(0).split()), repo, int(m.group("urln") or m.group("n")))
            if ref not in found:
                found.append(ref)
    if not found:
        print(f"closing-keywords PASS: {shown(rng)}: {len(commits)} commit(s), no closing keyword")
        return 0
    try:
        data = pr_view(pr, "number,url,closingIssuesReferences")
    except CannotRun as exc:
        named = ", ".join(f"{repo}#{n}" for _, _, repo, n in found)
        raise CannotRun(f"{shown(rng)} holds {len(found)} closing keyword(s) ({named}), and the PR's own closing issues "
                        f"cannot be read: {exc}") from exc
    here = repo_of(data.get("url"))
    closes = {(repo_of(i.get("url")) or here, i["number"]) for i in data.get("closingIssuesReferences") or []
              if isinstance(i, dict) and isinstance(i.get("number"), int)}
    number = data.get("number", "?")
    bad = [(sha, words, repo, n) for sha, words, repo, n in found if ((repo or here), n) not in closes]
    for sha, words, repo, n in bad:
        label = f"#{n}" if not repo or repo == here else f"{repo}#{n}"
        print(f"FAIL [closing-keywords]: {sha[:7]} `{words}` closes {label} on the merge, and PR #{number} "
              "does not close it")
    if bad:
        print(HOW_KEYWORD)
        return 1
    print(f"closing-keywords PASS: {shown(rng)}: {len(found)} closing keyword(s), each for an issue PR #{number} closes")
    return 0


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):    # a console that cannot encode a character prints `?`
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    usage = "usage: pr_check.py findings|closing-keywords [--range A..B] [--pr N]"
    if not argv or argv[0] not in ("findings", "closing-keywords"):
        print(usage)
        return 2
    opts: dict[str, str] = {}
    rest = argv[1:]
    while rest:
        word = rest.pop(0)
        key, eq, value = word.partition("=")
        if key not in ("--range", "--pr") or key in opts:
            print(usage)
            return 2
        if not eq:
            if not rest:
                print(usage)
                return 2
            value = rest.pop(0)
        opts[key] = value
    pr = opts.get("--pr")
    if pr is not None and not re.fullmatch(r"\d+", pr):
        print(usage + " -- N is the pull request's number")
        return 2
    name = "findings-check" if argv[0] == "findings" else "closing-keywords"
    try:
        rng, end = resolve(opts.get("--range"))
        return findings(rng, end, pr) if argv[0] == "findings" else closing_keywords(rng, pr)
    except CannotRun as exc:
        print(f"{name} CANNOT RUN: {exc} -- nothing was graded")
        return 2
    except OSError as exc:                                      # git cannot start; the class only, as above
        print(f"{name} CANNOT RUN: git cannot run ({exc.__class__.__name__}) -- nothing was graded")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
