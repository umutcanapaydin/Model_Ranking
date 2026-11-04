#!/usr/bin/env python3
"""The deploy gate: nothing deploys that no security review and no milestone Tester has seen.

Three ways in, one question -- is the release verdict current for THIS tree?

    python3 scripts/deploy_gate.py --judge          # the Bash guard: program words as JSON on stdin
    python3 scripts/deploy_gate.py "<command>"      # by hand: one command line
    python3 scripts/deploy_gate.py --check [--target <class>]   # `make deploy-check [TARGET=<class>]`

The Bash guard (`.claude/hooks/bash_guard.py`) lexes every Bash tool call into simple commands and hands
this script, with `--judge`, the words of each one in program position: `{"commands": [["fly",
"deploy", "--remote-only"], ...]}` -- only when this file carries the line `JUDGE_PROTOCOL = <n>` (below),
so an older gate is refused rather than asked a question it would answer with exit 0. A command is a deploy when one the brief lists as `Deploy commands:`
or `Deploy targets:` (below)
(`docs/project-brief.md`; `/setup-project` asks for them; none listed, nothing is a deploy) matches it
word for word from the first word: the program by its basename (`/usr/local/bin/fly` is `fly`), the
rest exactly, all case-insensitive, with the invoked command's own options ignored unless the declared
command carries options itself (`fly deploy` matches `fly --verbose deploy` and `fly deploy -a app`;
a team-only `./deploy.sh --stage` matches `./deploy.sh --stage` only; a production declaration matches its
words in any order, below). A commit message, an echo or a heredoc that
mentions the command is not a deploy, because the guard never hands those words over.

A `gh` COMMAND IS READ BY WHAT IT STARTS (#390), not word for word: `gh workflow run <workflow>`, `gh api` on
`.../actions/workflows/<workflow>/dispatches` (its path URL-encoded too), a repository dispatch, and a rerun
(`gh run rerun`, `gh api` on `.../rerun`). Its options are read where they sit, with their values
(`gh workflow run -R a/b x.yml`). An alias, an extension (any word that is not one of gh's own commands) and an
alias definition are judged as a workflow it cannot name. A DEPLOY WORKFLOW is derived, never listed: a workflow
file (under `.github/workflows/`, or a proposal under `scripts/ci/` that the owner installs there), in the tree or at
the protected base (a dispatch with no `--ref` runs the default branch's copy), with a line that runs a declared
deploy command (`flyctl` is `fly`; a backslash continuation is joined); and every workflow a declared
`gh workflow run <file>` names. gh knows it by its file name, its stem and its `name:`. A dispatch whose workflow
cannot be told -- an id, an expansion, a pattern or a brace, a name no workflow read here has, none given, a rerun
of a run this cannot see, an alias -- is a deploy whenever a deploy workflow exists (fail closed), and none when
none does; a workflow file at the base that git cannot read makes every dispatch a deploy. The Bash guard hands
this the words of every simple command, so it needs no rule of its own for `gh`.

THE REPOSITORY IS THE ONE THE COMMAND RUNS IN. The guard resolves it from the call's own directory
(`git rev-parse --show-toplevel`), a worktree included, and runs this script -- always its own
project's copy, never the one in the tree it judges -- with that tree as its directory; the verdicts and
the diff are read from that checkout, never from the main checkout. A repository that is neither the
project nor a worktree of it is `foreign`: its brief is read only to tell a deploy, and every deploy there
is refused. By hand, the repository is the work tree of the current directory.

For a deploy, and for `--check`, two verdicts must be current, each read the same way:
  * the security verdict, `docs/reviews/release-security.md` -- the Security-Reviewer's;
  * the milestone Tester's verdict: in light mode `docs/reviews/release-tester.md`, in heavy mode the
    latest `docs/reviews/m<N>-tester.md` (the Tester runs at every milestone close in both modes).
A verdict is current when it exists, says PASS or MINOR under `## Verdict`, names a `**Reviewed
head:** <sha>`, declares `**Independent:** yes` (the Tester's, as every review verdict does), and NO
CODE differs from that head in the working tree -- committed, uncommitted or untracked: the code about
to ship must be the code that was reviewed. What is code is one function, `change_class` (v7.3, harvest
Q2): a `record` is `docs/` and `*.md` anywhere else; everything under `.claude/`, `.githooks/`, `scripts/`,
`conformance/`, `.github/` and the `Makefile` IS code whatever its extension, because a reviewer
profile, a skill, a hook or a gate changes what ships and what guards it. Once the brief carries a
`Security-invariant tests:` line -- at every protected base and in the tree (model_ranking, #283: a change
cannot opt itself in) --, `test-and-ci` -- a test, or `conformance/` -- ships nothing and re-opens
neither verdict while CI is green on HEAD (one `gh run list --commit` call; no answer is not green), except a
security-invariant test a line names (a glob without `/` also names a file); a brief without the line keeps
v7.2's reading, every test code. A nested checkout (a
worktree under `.claude/worktrees/`, which git lists as `dir/`) is another tree's business. What git cannot see -- a gitignored config file -- no
git-based check can see either; `/going-live` reads the brief's declared runtime config files by hand.

TARGET CLASSES (v7.3, harvest Q1). `Deploy commands:` are production deploys. `Deploy targets:` gives each
command a class, `<class>: <command>`: `production` and `external-test` (real users run the build) owe both
verdicts; `internal` and `staging` (the team runs it) owe the Tester's verdict, the per-change security verdict
`make review-need` asks for over what is not released yet (a `docs/reviews/*-security.md` current for this
tree), and a line in `docs/releases/` marked `unreleased` that names a commit with no code changed since -- the
build going out -- and no release security delta. A class this gate cannot read is production, and so is a
team-only entry that some protected base's brief does not hold too (model_ranking, #283: a change can add a
deploy but cannot lower what one owes). A production or
external-test declaration matches in any word order (`vercel --prod deploy`), and `--opt=value` is two words.
A team-only declaration decides only when it holds every word of each production one the command also
matches, and more; otherwise, a tie included, the stricter class decides, and one such command in a call
decides the call. `--check --target <class>` asks one class.

A delta review closes a stale verdict: the reviewer reads `<reviewed head>..HEAD` and writes the new
head into the same file.

THE BRIEF'S POLICY IS THE BASE'S (AGENTS.md section 5, base-pinned policy; #283). `Working mode:` (which
Tester verdict) and `Deploy commands:` are read from the brief at the protected base -- the merge-base of
HEAD with the default branch, and its tip (`brief_fields.protected_bases`, D-232) -- not from the tree about to ship:
  * a deploy is any command the base's brief OR the tree's declares, so a change can add a deploy command
    but cannot remove one;
  * the Tester verdict is the one the base's mode names; when the tree's brief names the other mode, the
    verdicts of both are required, so a change of mode moves no deploy to the verdict it prefers;
  * a base git cannot read refuses every declared deploy, and `--check` fails: a policy read from nowhere
    is not the change's own. Matching still reads the tree's brief then, so a non-deploy is never refused.

A FILE STARTED WITHOUT ITS NAME REFUSES EVERY DEPLOY (#549, D-239): while a `run:` step of a dispatched deploy
workflow starts a program by a pattern or a name built at run time, gives a shell, `source` or an interpreter such
a file, runs `eval`, `xargs` or `find -exec`, or names a symlink to a tree file, a deploy is refused and `--check`
fails, whatever the verdicts say: the file it starts cannot be put on the surface. The refusal names the workflow,
the line and the shape; write the file's name instead.

`--check` prints one line per verdict (security, tester; for a team-only class, the release note) so the
closure checklist and `/going-live` can paste them, then any note, then `deploy-check PASS` or
`deploy-check FAIL: <why>`.

WHY. Three field projects, four real deploys in two weeks: three were run by the owner outside any
command guard and two of those had no current security verdict; one went through the guard and
passed correctly. The guard's eleven refusals were all on text that mentioned a deploy command. The
owner's deploys needed a question the guard cannot ask from a terminal: `make deploy-check` is that
question. Exit 0 not a deploy, or current · 1 `--check` found a verdict not current · 2 a deploy
refused, or this could not run.
"""
from __future__ import annotations

import fnmatch
import hashlib
import itertools
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote

# No bytecode: a `__pycache__` written beside the gate would itself read as a code change in a tree
# that does not ignore it, and the tree about to ship is what this compares.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import brief_fields  # noqa: E402
from brief_fields import (  # noqa: E402
    Unverified,
    field,
    listing,
    mode,
    protected_bases,
    root_at,
)

#: #526 (D-234): the `GIT_*` variables the caller set, read before this module sets its own below. Git reads its
#: tree, index, objects and configuration from them, so with one set the gate can judge another checkout than the
#: one being deployed (`GIT_WORK_TREE` passed a product change). `main` refuses a deploy, and `--check` fails, while
#: any is set: any `GIT_*`, since git reads more of them than a list of the redirecting ones would keep up with.
#: Every one is then removed from this process's environment, so the gate's own git reads the repository it runs
#: in: pointed at another one, the command form read that brief, found no deploy and passed before it reached the
#: refusal (the fixes-1101 security review's M1). Three named exceptions (D-234) are not refused: none names a
#: tree, an index, an object store or a configuration, and refusing them would fail every agent session and every
#: git hook whatever the verdicts said.
HARMLESS_GIT = {
    # Claude Code sets it in every session, and git in its hooks: the program git opens for a message, which no
    # command this gate runs asks for.
    "GIT_EDITOR": "the editor git opens for a message",
    # git sets it in every hook it runs (measured 2026-11-01): where git finds its own programs, and every command
    # this gate runs is built into git.
    "GIT_EXEC_PATH": "where git finds its own programs",
    # git merge, pull and rebase set it for their hooks (measured 2026-11-01): the label of the reflog line they
    # write, which this gate writes none of.
    "GIT_REFLOG_ACTION": "the label of the reflog line a command writes",
}
CALLER_GIT = tuple(sorted(name for name in os.environ if name.startswith("GIT_") and name not in HARMLESS_GIT))
for _name in [name for name in os.environ if name.startswith("GIT_")]:
    del os.environ[_name]

#: #410 round 1's B1: git honours `refs/replace/` refs everywhere, so one written by the change under evaluation
#: could stand in for the pinned commit or the protected base. Every git this gate starts, directly or through
#: `brief_fields`, ignores them.
os.environ["GIT_NO_REPLACE_OBJECTS"] = "1"
#: v7.3 (doctor's B2): a read-only check takes no optional lock, so it never holds `.git/index.lock` while the
#: session's own `git add` runs. Set here, after the caller's `GIT_*` are removed: a caller that sets it is still
#: refused (D-234), and `make doctor` runs this gate without it.
os.environ["GIT_OPTIONAL_LOCKS"] = "0"

#: The Bash guard calls `--judge` only in a gate that carries this line, at the start of a line, exactly:
#: a gate written before `--judge` existed reads the flag as the command, finds no deploy and exits 0, so
#: under a newer guard every declared deploy passed (a v7.0 gate under the v7.1 guard passed `fly deploy`).
#: Raise the number when the `--judge` payload or its answer changes; the guard reads it as a floor.
#: 2 (v7.1.2): the payload may say `"foreign": true` -- the guard runs only its own project's gate, and in
#: any other repository asks it only whether a word list is one of that brief's deploys, which it refuses.
JUDGE_PROTOCOL = 2
SECURITY = Path("docs/reviews/release-security.md")
RELEASE_TESTER = Path("docs/reviews/release-tester.md")
MILESTONE_TESTER = re.compile(r"^m(\d+)-tester\.md$")
#: Heavy mode, from v7.2 (the owner's ruling of 2026-10-17): the latest milestone security verdict, when
#: it is current for this tree, stands for the release's -- the same code was reviewed once already.
MILESTONE_SECURITY = re.compile(r"^m(\d+)-security\.md$")
#: Code whatever the extension: what guards and gates the tree is part of what ships.
CODE_DIRS = (".claude/", ".githooks/", "scripts/", "conformance/", ".github/")
CODE_FILES = {"Makefile"}
#: The test-path set, ONE definition: `change_class` reads it here, and `make review-need` as git pathspecs for
#: its parser scan (`*` crosses `/`, so each pair covers the top level and any depth).
TEST_PATH = re.compile(r"(^|/)(tests/|test_[^/]*$|[^/]*_test\.[^/]+$|[^/]*Tests/)")
TEST_PATHSPECS = [":(exclude)tests/*", ":(exclude)*/tests/*", ":(exclude)test_*", ":(exclude)*/test_*",
                  ":(exclude)*_test.*", ":(exclude)*Tests/*"]
#: The brief line naming the security-invariant tests, which stay code (harvest Q2).
INVARIANT_TESTS = "Security-invariant tests"
#: The deploy target classes (harvest Q1): real users run the first two, only the team the last two.
CLASSES = ("production", "external-test", "internal", "staging")
TEAM_ONLY = {"internal", "staging"}
RELEASES = Path("docs/releases")
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
#: A verdict's answer and its independence, as every gate reads them (`make owner-bundle`'s apply too).
VERDICT = re.compile(r"^##\s*Verdict\s*\n+\s*\W*(PASS|MINOR|BLOCKING)\b(.*)$", re.M)
INDEPENDENT = re.compile(r"^\s*\*\*Independent:\*\*\s*yes\b", re.M | re.I)
#: An owner-bundle review names the patch it read (`make owner-bundle`); it read no tree, so the per-change
#: security question never counts it (the Security-Reviewer's M5, round 3).
REVIEWED_PATCH = re.compile(r"^\s*\*\*Reviewed patch:\*\*\s*`?([0-9a-f]*)`?", re.M)
#: What the brief's deploy lines could not say clearly, printed after the answer and never before it: the Bash
#: guard reads a refusal that does not start with `BLOCKED:` as the gate itself failing.
NOTES: list[str] = []
#: Words that run the command after them, skipped with their own options to reach the program.
WRAPPERS = {"env", "command", "builtin", "time", "exec", "nohup", "nice", "sudo", "doas", "timeout",
            "gtimeout", "caffeinate", "noglob", "nocorrect", "stdbuf", "setsid", "unbuffer", "chronic", "ionice"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\+?=")
#: #553 M2: each wrapper's options that take the next word as their value, per its own syntax; a wrapper not named
#: here keeps the set every wrapper was read with before.
WRAPPER_VALUED_DEFAULT = frozenset({"-n", "-u", "-g", "-k", "-s", "--signal", "-C", "-t"})
WRAPPER_VALUED: dict[str, frozenset[str]] = {
    "timeout": frozenset({"-k", "--kill-after", "-s", "--signal"}),
    "gtimeout": frozenset({"-k", "--kill-after", "-s", "--signal"}),
    "exec": frozenset({"-a"}),
    "stdbuf": frozenset({"-i", "-o", "-e", "--input", "--output", "--error"}),
    "nice": frozenset({"-n", "--adjustment"}),
    # not `-S`/`--split-string`: its value is the command line itself (the #553 review's B3)
    "env": frozenset({"-u", "--unset", "-C", "--chdir"}),
    # not `-h`: a flag (help) in some sudo versions, a host in others; read as a flag, it swallows nothing
    "sudo": frozenset({"-u", "-g", "-C", "-D", "-p", "-r", "-t", "-U", "-T", "-R"}),
    "doas": frozenset({"-u", "-C"}),
    "ionice": frozenset({"-c", "-n", "-p", "-P", "-u"}),
    "time": frozenset({"-o", "--output", "-f", "--format"}),
    "caffeinate": frozenset({"-t", "-w"}),
}
HOW_TO_CLOSE = ("Run the reviewer on the delta (the Security-Reviewer, .claude/agents/Security-Reviewer.md; "
                "the Tester, .claude/agents/Tester.md) and record its head in the verdict file, then deploy.")


def _git_variables(names: tuple[str, ...]) -> str | None:
    """#526 (D-234): why a caller's `GIT_*` variables refuse a deploy, or None when it set none."""
    if not names:
        return None
    return (f"{', '.join(names)} {'is' if len(names) == 1 else 'are'} set in the environment, and git reads its tree, "
            f"index and configuration from such variables, so the gate could judge another checkout than this one "
            f"(#526); run it from a shell with none set (`unset {' '.join(names)}`)")


def refuse(why: str, how: str = HOW_TO_CLOSE) -> int:
    print(f"BLOCKED: deploy gate -- {why}.{' ' + how if how else ''}", file=sys.stderr)
    return 2


# --- the verdicts --------------------------------------------------------------------------------------

def is_deploy_record(path: str) -> bool:
    """Whether a repository-relative path (POSIX, as `git diff --name-only` prints it) is a RECORD the
    deploy gate ignores, as opposed to CODE that must have been reviewed. A record is anything under
    `docs/` and any `.md` file -- except under `.claude/`, `.githooks/`, `scripts/`, `conformance/`,
    `.github/` or the `Makefile` itself, which are code whatever their extension. `change_class` reads it."""
    if path in CODE_FILES or path.startswith(CODE_DIRS):
        return False
    # `.gp/installed` is the install's measurement (`make install` writes it), not the product. #562 (M16):
    # `.deps-accept` waives a dependency advisory, so it is code here, as `data/accepted-cuts.yaml` is -- v7.3's trim
    # made it a record, and an agent's waiver then reached a deploy with no review.
    return path.startswith("docs/") or path.endswith(".md") or path == ".gp/installed"


def invariant_tests(root: Path | str) -> list[str] | None:
    """The globs on the brief's `Security-invariant tests:` line (`none`: no glob). None when the brief has no
    such line: it predates the change classes, and every test stays code to it."""
    return None if field(INVARIANT_TESTS, root) is None else listing(INVARIANT_TESTS, root)


def policy_invariant_tests(root: Path) -> list[str] | None:
    """model_ranking (#283, base-pinned policy): the security-invariant globs the deploy gate reads -- None (every
    test is code) unless the tree's brief AND every protected base's carry the line, which no change can then add
    for itself; else every glob any of them names, so a change can name one more but cannot drop one."""
    policies, _, _ = _policy(root)
    if policies is None:
        return None
    globs: list[str] = []
    for brief_root in (root, *policies):
        named = invariant_tests(brief_root)
        if named is None:
            return None
        globs += [g for g in named if g not in globs]
    return globs


def invariant_hit(path: str, globs: list[str]) -> bool:
    """Whether a path is one of the brief's security-invariant tests: a glob with a `/` matches the whole path,
    one without matches the file name too, as .gitignore reads it (`test_scope.py` names tests/test_scope.py)."""
    name = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(path, g) or ("/" not in g and fnmatch.fnmatch(name, g)) for g in globs)


def change_class(path: str, invariants: list[str] | None = None) -> str:
    """`record`, `test-and-ci` or `code` -- the ONE classification of a changed path (harvest Q2, the owner's
    ruling of 2026-10-28) that the deploy gate, `closure_check.py` and `make review-need` read. A record is
    `is_deploy_record`'s. Test-and-CI is a test outside the tooling directories, or `conformance/`: the checks
    CI runs that the agent may edit (a workflow is the owner's and stays code). A security-invariant test the
    brief names is code, and so is every test while `invariants` is None (a brief without the line)."""
    if is_deploy_record(path):
        return "record"
    if invariants is None or invariant_hit(path, invariants):
        return "code"
    if path.startswith("conformance/") or (
            TEST_PATH.search(path) and not (path in CODE_FILES or path.startswith(CODE_DIRS))):
        return "test-and-ci"
    return "code"


def latest_milestone(root: Path, pattern: re.Pattern) -> Path | None:
    """The highest-numbered `docs/reviews/m<N>-...` verdict the pattern names, or None."""
    reviews = root / "docs" / "reviews"
    found = [(int(m.group(1)), Path("docs/reviews") / p.name) for p in (reviews.iterdir() if reviews.is_dir() else [])
             if (m := pattern.match(p.name))]
    return max(found)[1] if found else None


_POLICIES: dict[str, tuple[list[Path] | None, str, bool]] = {}


def _policy(root: Path) -> tuple[list[Path] | None, str, bool]:
    """(the policy roots -- the brief at the merge-base, and at the default branch's tip when it differs (#517,
    D-232 clause 1) --, or None when one cannot be read; the line that says which; whether a base's brief failed its
    hash check: #509)."""
    key = str(root)
    if key not in _POLICIES:
        bases = protected_bases(root)
        if not bases:
            _POLICIES[key] = (None, "no merge-base of HEAD with a default branch "
                                    f"({', '.join(brief_fields.DEFAULT_BRANCHES)})", False)
        else:
            # #534: every default-branch ref's merge-base and tip, the first one a merge-base.
            where = (f"the brief at {bases[0][:12]}, the merge-base of HEAD with the default branch"
                     + (f", and at {', '.join(b[:12] for b in bases[1:])}, the default branch refs' merge-bases and "
                        "tips" if len(bases) > 1 else ""))
            try:
                _POLICIES[key] = ([root_at(base, root) for base in bases], where, False)
            except Unverified as error:
                _POLICIES[key] = (None, str(error), True)
            except RuntimeError as error:
                _POLICIES[key] = (None, str(error), False)
    return _POLICIES[key]


def tester_path(root: Path, working_mode: str | None = None) -> tuple[Path | None, str]:
    """(the Tester verdict this tree must carry, its label): `release-tester.md` in light mode, the latest
    `m<N>-tester.md` in heavy mode; None when heavy mode has none yet. The mode is `working_mode`, the
    tree's brief's when none is given."""
    if (working_mode or mode(root)) == "light":
        return RELEASE_TESTER, "tester (light mode)"
    reviews = root / "docs" / "reviews"
    found: list[tuple[int, Path]] = []
    if reviews.is_dir():
        for p in reviews.iterdir():
            m = MILESTONE_TESTER.match(p.name)
            if m:
                found.append((int(m.group(1)), Path("docs/reviews") / p.name))
    if not found:
        return None, "tester (heavy mode)"
    return max(found)[1], "tester (heavy mode)"


def verdict_head(text: str) -> str | None:
    """The sha the verdict reviewed: its `**Reviewed head:**` line."""
    m = re.search(r"^\s*\*\*Reviewed head:\*\*\s*`?([0-9a-f]{7,40})`?", text, re.M)
    return m.group(1) if m else None


def changed_since(root: Path, head: str, ask_ci: bool = True) -> list[str] | None:
    """Every code path (`change_class`) that differs from `head` in the working tree of `root`, or None when git
    cannot compare. Committed, uncommitted and untracked alike. None as well
    when the comparison cannot be trusted (#493, #500: `compare_problem`), so `closure_check` agrees with the gate.

    #505 (D-231 clause 2): by content, never by git's state. Each file the reviewed head's (verified) tree holds is
    hashed here from the working tree; a file it does not hold is new unless a `.gitignore` committed at that head
    ignores it. No index stat data, fsmonitor, attribute filter, `.git/info/exclude` or `core.excludesFile` is read,
    since the change under evaluation can write each of them. A path that leaves or enters is listed by its name,
    so a rename is both its sides (#506). An untracked nested checkout is listed as its folder (`dir/`), a change,
    unless a committed `.gitignore` ignores it: git lists nothing below it, so it hid every file there (the #505
    review's M1)."""
    if compare_problem(root, head):
        return None
    try:
        tree = brief_fields.verified_tree(root, head)
        ignores = {path: oid for path, (mode, oid) in tree.items()
                   if os.path.basename(path) == ".gitignore" and mode in brief_fields.FILES}
        rules = brief_fields.verified_blobs(root, sorted(set(ignores.values())))
        new = _new_files(root, tree, {path: rules[oid] for path, oid in ignores.items()})
    except (OSError, subprocess.SubprocessError, RuntimeError):
        return None
    paths = sorted({p for p, (mode, oid) in tree.items() if _differs(root / p, mode, oid)} | new)
    invariants = policy_invariant_tests(root)
    classes = {p: change_class(p, invariants) for p in paths}
    # Harvest Q2(b): test-and-CI re-opens neither verdict only "when CI is green on the head". Asked once, and
    # only when such a change exists; an offline caller (`closure_check.py` in `make check`) never asks, so
    # there a test stays code. No answer, a run unfinished or not green: not green.
    tests = [p for p, c in classes.items() if c == "test-and-ci"]
    green = bool(tests) and ask_ci and ci_green(root)
    note = ("test-and-CI changes count as code here: CI is not green on HEAD (`gh run list --commit`), so they "
            "re-open the verdicts")
    if tests and not green and ask_ci and note not in NOTES:
        NOTES.append(note)
    code = [p for p, c in classes.items() if c == "code" or (c == "test-and-ci" and not green)]
    return [p for p in code if not shipped_unchanged(root, p)]


_CI: dict[str, bool] = {}


#: Under the Bash guard's 10 s budget, so a slow `gh` reads as not green, not as the budget's refusal (run v73 R2).
GH_TIMEOUT_S = 8


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=30)


#: #563: `origin`'s URL as git stores it -- `https://github.com/<o>/<r>[.git]`, `ssh://git@github.com/<o>/<r>[.git]`
#: or `git@github.com:<o>/<r>[.git]`. Anything else names no repository this gate may ask about.
_GITHUB_URL = re.compile(r"^(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)"
                         r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$")


def _github_repo(url: str) -> str | None:
    """`<owner>/<repo>` of a GitHub `origin` URL, or None."""
    found = _GITHUB_URL.match(url)
    return found.group(1) if found else None


def ci_green(root: Path) -> bool:
    """Whether CI is green on HEAD: one `gh run list --commit <HEAD>` call, remembered for this process. Green
    means at least one run, every run finished, and each a success (a skipped run aside); no `gh`, no answer,
    or anything else is not green.

    #563 (R13): the repository is named, `-R github.com/<owner>/<repo>` read from `origin`'s URL, and `GH_REPO` and
    `GH_HOST` are dropped from `gh`'s environment, so neither they nor `gh repo set-default` can point the question
    at another repository's CI. An origin that names no GitHub repository is not green, and `gh` is not asked."""
    key = str(root)
    if key not in _CI:
        try:
            head = _git(root, "rev-parse", "HEAD").stdout.decode().strip()
            repo = _github_repo(_git(root, "config", "--get", "remote.origin.url").stdout.decode().strip())
            if repo is None:
                _CI[key] = False
                return False
            env = {k: v for k, v in os.environ.items() if k not in ("GH_REPO", "GH_HOST")}
            r = subprocess.run(["gh", "run", "list", "-R", f"github.com/{repo}", "--commit", head,
                                "--json", "status,conclusion", "--limit", "50"],
                               cwd=root, capture_output=True, timeout=GH_TIMEOUT_S, env=env)
            runs = json.loads(r.stdout.decode("utf-8", "replace")) if r.returncode == 0 and head else []
            _CI[key] = (isinstance(runs, list) and bool(runs) and all(
                isinstance(x, dict) and x.get("status") == "completed" and x.get("conclusion") in ("success", "skipped")
                for x in runs) and any(x.get("conclusion") == "success" for x in runs))
        except (OSError, subprocess.SubprocessError, ValueError):
            _CI[key] = False
    return _CI[key]


#: #505: git as the comparison runs it -- no fsmonitor and no untracked cache, so what is listed is what is on disk.
_PLAIN_GIT = ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false"]


def _blob_id(body: bytes, like: str) -> str:
    """The id git would name `body` by, as a blob, in the hash `like` is written in."""
    digest = hashlib.sha256 if len(like) == 64 else hashlib.sha1
    return digest(b"blob %d\0" % len(body) + body).hexdigest()


def _differs(path: Path, mode: bytes, oid: str) -> bool:
    """Whether the working tree's `path` is not the reviewed head's entry (mode as written, id): its bytes, its kind
    (file or link) and its executable bit, read from disk, never from the index. A submodule differs unless the
    checkout there is at the recorded commit."""
    try:
        if mode == b"120000":
            # `os.readlink`, not `Path.readlink`: the link's text as written (`./x` stays `./x`), which git hashes.
            return not path.is_symlink() or _blob_id(os.fsencode(os.readlink(path)), oid) != oid  # noqa: PTH115
        if mode in brief_fields.FILES:
            if path.is_symlink() or not path.is_file():
                return True
            if bool(path.stat().st_mode & 0o100) != (mode == b"100755"):  # the owner's bit, as git reads it
                return True
            return _blob_id(path.read_bytes(), oid) != oid
        if mode == b"160000":
            at = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, encoding="utf-8",
                                timeout=30)
            return at.returncode != 0 or at.stdout.strip() != oid
    except OSError:
        return True
    return True  # a mode git does not write


def _head_excludes(rules: dict[str, bytes]) -> str:
    """The reviewed head's committed `.gitignore` files as one exclude list, each pattern made relative to the top
    of the tree the way git scopes it to its own directory; the deeper files last, since they take precedence."""
    out: list[str] = []
    for path in sorted(rules, key=lambda p: (p.count("/"), p)):
        folder = re.sub(r"([\\*?\[])", r"\\\1", path.rpartition("/")[0])  # a folder's name is literal (R3)
        for raw in rules[path].decode("utf-8", "replace").splitlines():
            line = re.sub(r"(?<!\\) +$", "", raw.rstrip("\r"))
            if not line or line.startswith("#"):
                continue
            negate, body = ("!", line[1:]) if line.startswith("!") else ("", line)
            if folder:
                trailing = "/" if body.endswith("/") else ""
                core = body[:-1] if trailing else body
                body = f"{folder}/{core.lstrip('/')}{trailing}" if "/" in core else f"{folder}/**/{core}{trailing}"
            out.append(negate + body)
    return "\n".join(out) + "\n"


def _new_files(root: Path, tree: dict[str, tuple[bytes, str]], rules: dict[str, bytes]) -> set[str]:
    """#505: the files on disk the reviewed head's tree does not hold and its committed `.gitignore` files do not
    ignore. `--others` reads only the patterns given here; and every index entry the tree does not hold counts too,
    since an entry forged into the index takes a file out of `--others`."""
    with tempfile.NamedTemporaryFile("w", suffix=".exclude", delete=False, encoding="utf-8") as excludes:
        excludes.write(_head_excludes(rules))
    try:
        # `--work-tree`: the listing is of `root`, whatever `core.worktree` names (the #505 review's M2).
        others = subprocess.run([*_PLAIN_GIT, "-C", str(root), f"--work-tree={root}", "ls-files", "-z", "--others",
                                 f"--exclude-from={excludes.name}"], capture_output=True, check=True, timeout=60).stdout
        cached = subprocess.run([*_PLAIN_GIT, "-C", str(root), f"--work-tree={root}", "ls-files", "-z", "--cached"],
                                capture_output=True,
                                check=True, timeout=60).stdout
    finally:
        Path(excludes.name).unlink()
    listed = {os.fsdecode(p) for p in others.split(b"\0") if p}
    staged = {p for p in (os.fsdecode(p) for p in cached.split(b"\0") if p)
              if p not in tree and ((root / p).is_symlink() or (root / p).exists())}
    return {p for p in listed | staged if p not in tree}


def _flagged(root: Path) -> list[str] | None:
    """#500: each index entry git is told not to look at in the working tree -- assume-unchanged (a lower-case tag in
    `git ls-files -v`) or skip-worktree (`S`) --, or None when git cannot list the index."""
    try:
        listed = subprocess.run([*_PLAIN_GIT, "-C", str(root), "ls-files", "-v", "-z"], capture_output=True, check=True,
                                timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    entries = [e.decode("utf-8", "replace") for e in listed.split(b"\0") if e]
    return [e[2:] for e in entries if e[:1].islower() or e[:1] == "S"]


def _subtrees(body: bytes, size: int) -> list[str]:
    """The ids of a tree's own subtrees (a mode whose type bits say tree); a blob, a link or a submodule is none."""
    # The review's M2: `040000` is a tree to git too, so the walk reads the type bits, not the spelling.
    return [oid for mode, _, oid in brief_fields.tree_entries(body, size) if int(mode, 8) & 0o170000 == 0o040000]


def _unhashed(root: Path, head: str) -> str | None:
    """#493: the first object on the reviewed head's side of the comparison -- its commit, or a tree under it -- that
    does not hash to its id, or that git cannot read; None when every one does. Git hashes a loose root tree as it
    parses a commit, and no tree below it, so a forged subtree hid a change from `git diff`. Blobs need no check: the
    diff compares their ids. One `git cat-file --batch` reads them all."""
    try:
        # The name alone, never `^{commit}`: peeling parses the commit, and a forged one then fails to resolve, which
        # read as "not in this clone" while `git diff` used it unhashed (the #493 review's B1).
        commit = subprocess.run(["git", "--no-replace-objects", "-C", str(root), "rev-parse", "--verify", "--quiet",
                                 "--end-of-options", head], capture_output=True, encoding="utf-8",
                                timeout=30).stdout.strip()
        batch = brief_fields.open_batch(root)
    except (OSError, subprocess.SubprocessError):
        return "objects cannot be read by git"
    try:
        if not commit:
            return None  # `changed_since` reports a head this clone does not have
        body = brief_fields.batch_read(batch, commit, "commit")
        m = re.match(rb"tree ([0-9a-f]{40,64})\n", body) if isinstance(body, bytes) else None
        if m is None:
            return body if isinstance(body, str) else f"commit {commit} names no tree"
        todo, seen = [m.group(1).decode()], {m.group(1).decode()}
        while todo:
            oid = todo.pop()
            tree = brief_fields.batch_read(batch, oid, "tree")
            if isinstance(tree, str):
                return tree
            fresh = [child for child in _subtrees(tree, len(oid) // 2) if child not in seen]
            seen.update(fresh)
            todo += fresh
    except (OSError, ValueError):
        return "objects cannot be read by git"
    finally:
        brief_fields.close_batch(batch)
    return None


def compare_problem(root: Path, head: str) -> str | None:
    """#493, #500: why `changed_since(root, head)` cannot be trusted, or None. Both fail closed."""
    flagged = _flagged(root)
    if flagged is None:
        return "git cannot list the index"
    if flagged:
        return (f"the index tells git not to look at {', '.join(flagged[:5])}{' ...' if len(flagged) > 5 else ''} "
                "(assume-unchanged or skip-worktree; `git update-index --no-assume-unchanged --no-skip-worktree <path>`, "
                "or `git sparse-checkout disable`)")
    unhashed = _unhashed(root, head)
    return f"the reviewed head's {unhashed}" if unhashed else None


#: Where DevFlow's own tooling lives. Only a file here can be "DevFlow's, unchanged": the product scaffold
#: the package also ships (`src/`, `tests/`, `pyproject.toml`) is the product's code from the first commit.
DEVFLOW_TOOLING = (".claude/", ".codex/", ".githooks/", "scripts/", "conformance/", ".agents/", ".github/")
# Not `.gitattributes`: a project's LFS filters and export-ignore rules change what deploys (v7.2.1, review).
DEVFLOW_TOOLING_FILES = {"Makefile", ".install-lock", "pipeline-schema.html", ".path-refs-allow", ".placeholder-allow"}

#: Always code, even byte-identical to DevFlow's commit: the guard, its settings and the gate are the safety surface
#: the verdicts stand on, and the product's deploy scripts decide what ships where (#410, D-223 clause 5). v7.3 lets
#: these count as DevFlow's when byte for byte the release's (harvest Q3); model_ranking keeps them code always
#: (D-223 clause 5, kept by D-241 clause 2), `.codex/hooks.json` (v7.3) among them.
SAFETY_SURFACE = {".claude/hooks/bash_guard.py", ".claude/settings.json", ".codex/hooks.json", "scripts/deploy_gate.py",
                  "scripts/brief_fields.py", "scripts/deploy_hosted_engine.sh", "scripts/nightly_hosted.sh"}
SAFETY_SURFACE_DIRS = ("scripts/ci/",)
#: #410 (D-223 clause 5): `<version> <commit>`, the DevFlow commit whose bytes the exemption compares with. Read
#: at the protected bases only (D-233: the merge-base and the default branch's tip, both must hold the bytes): an
#: agent's branch can neither move it nor forge it, and an upgrade the owner merges moves it. `.gp/installed` and the local tags are not read: both are writable by the change under evaluation.
DEVFLOW_PIN = "docs/devflow-pin.txt"
_PINS: dict[str, list[str] | None] = {}


def devflow_pins(root: Path) -> list[str] | None:
    """The DevFlow commit pinned at each protected base of `root` -- the merge-base and the default branch's tip
    (D-233) --, or None when there is no base, or one has no pin or not a commit."""
    key = str(root)
    if key not in _PINS:
        bases = protected_bases(root)
        # #509: verified, as the gate reads every base file whose content it trusts; a forged pin exempts nothing.
        found = [re.fullmatch(r"\s*v\S+\s+([0-9a-f]{40})\s*",
                              (verified_blob(root, base, DEVFLOW_PIN) or b"").decode("utf-8", "replace"))
                 for base in bases]
        _PINS[key] = [m.group(1) for m in found if m] if bases and all(found) else None
    return _PINS[key]


def shipped_unchanged(root: Path, rel: str) -> bool:
    """Whether `rel` is a file DevFlow shipped, byte for byte as the commit pinned at the protected base has it --
    DevFlow's own tooling after an upgrade, which is not this product's code (v7.2, the owner's ruling of
    2026-10-17: every upgrade made both release verdicts stale). False with no pin at the base, for the safety
    surface, and for anything the project changed (#410: never from a local tag or the untracked marker).

    #444: false for a symlink (M2: `lstat`, never the target's bytes), for what the deploy commands start (M3,
    `deploy_surface`), and when the pinned bytes do not hash to the ids git names them by (R2)."""
    if rel in SAFETY_SURFACE or rel.startswith(SAFETY_SURFACE_DIRS) \
            or not (rel in DEVFLOW_TOOLING_FILES or rel.startswith(DEVFLOW_TOOLING)):
        return False
    pins = devflow_pins(root)
    target = root / rel
    if pins is None or target.is_symlink() or not target.is_file():
        return False
    surface = deploy_surface(root)
    if surface is None or rel in surface:
        return False
    # D-233 (the #517 review's M2): the bytes every pin holds -- an older pin at the merge-base alone let a branch cut
    # before an upgrade put the older bytes back unreviewed.
    here = target.read_bytes()
    if rel.startswith(".claude/agents/") and rel.endswith(".md"):
        # v7.2.1: a reviewer profile's frontmatter `model:` line is the project's answer to `/setup-project`
        # question 12, not a change to what the profile reviews.
        return all((pinned_bytes := verified_blob(root, pinned, rel)) is not None
                   and _without_model(pinned_bytes) == _without_model(here) for pinned in pins)
    return all(verified_blob(root, pinned, rel) == here for pinned in pins)


VERSION_LINE = re.compile(r"^process_version:\s*`?([^\s`]+)", re.M)
#: The one line a project writes into a shipped reviewer profile (`/setup-project` question 12).
MODEL_LINE = re.compile(rb"^model:[^\r\n]*\r?\n", re.M)
_HISTORY: dict[str, list[str]] = {}


def _without_model(text: bytes) -> bytes:
    """A reviewer profile without the `model:` line of its FRONTMATTER, and only that one: a `model:` line
    in the body is the profile's instructions (v7.2.1, review)."""
    if not text.startswith(b"---\n"):
        return text
    end = text.find(b"\n---\n", 3)
    if end < 0:
        return text
    return text[:4] + MODEL_LINE.sub(b"", text[4:end + 1], count=1) + text[end + 1:]


def devflow_history(root: Path) -> list[str]:
    """The DevFlow versions this tree has run, newest first: the brief's `process_version:` now, then each
    different one in its committed history (`make ci-diff` reads it). The exemption above never reads it:
    model_ranking compares with the commit pinned at the protected bases (#410, D-233), never a local tag."""
    key = str(root)
    if key in _HISTORY:
        return _HISTORY[key]
    brief = root / "docs" / "project-brief.md"
    m = VERSION_LINE.search(brief.read_text(encoding="utf-8", errors="replace")) if brief.is_file() else None
    if not m:
        marker = root / ".gp" / "installed"
        m = re.search(r"^gp_version:\s*(\S+)", marker.read_text(encoding="utf-8", errors="replace"), re.M) \
            if marker.is_file() else None
    seen = [m.group(1)] if m else []
    try:
        log = _git(root, "log", "--format=%H", "-n", "200", "--", "docs/project-brief.md")
        for sha in log.stdout.decode().split() if log.returncode == 0 else []:
            shown = _git(root, "show", f"{sha}:docs/project-brief.md")
            v = VERSION_LINE.search(shown.stdout.decode("utf-8", "replace")) if shown.returncode == 0 else None
            if v and v.group(1) not in seen:
                seen.append(v.group(1))
    except (OSError, subprocess.SubprocessError):
        pass
    _HISTORY[key] = seen
    return seen


def devflow_versions(root: Path) -> tuple[str | None, str | None]:
    """(the DevFlow version this tree came from, the one it runs), from `devflow_history`."""
    history = devflow_history(root)
    return (history[1] if len(history) > 1 else None, history[0] if history else None)


_SURFACES: dict[str, frozenset[str] | None] = {}

#: #494, #501: programs that run a recipe this gate does not read, so what they start cannot be derived: `make
#: <target>` runs whatever the Makefile's recipe names, `just <recipe>` the justfile's. Named for that reason; a
#: dispatched deploy workflow whose run line starts one exempts nothing either.
UNREAD_RECIPES = {"make", "gmake", "just"}
#: #501 (D-231 clause 1): the external programs a declared command may run whose targets need no deriving here --
#: `fly` builds and ships the image from the tree, all of which is already code to this gate. A NAMED ENUMERATION
#: with the ADR as its reason (AGENTS.md section 3.5): a program that is not here, not a shell in SHELLS with a
#: script, not `gh` dispatching a workflow, and not a script git lists, is one whose targets this cannot read.
KNOWN_PROGRAMS = {"fly", "flyctl"}
SHELLS = {"bash", "sh"}


def _files(root: Path) -> dict[str, set[str]] | None:
    """Every file git sees in `root`'s tree, tracked or untracked-not-ignored, by its lower-cased path (the declared
    words are lower-cased); None when git cannot list them."""
    try:
        listed = subprocess.run([*_PLAIN_GIT, "-C", str(root), "ls-files", "-z", "--cached", "--others",
                                 "--exclude-standard"], capture_output=True, check=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    out: dict[str, set[str]] = {}
    for path in (p.decode("utf-8", "replace") for p in listed.split(b"\0") if p):
        out.setdefault(path.lower(), set()).add(path)
    return out


def _named_files(root: Path, word: str, files: dict[str, set[str]]) -> set[str]:
    """#494 M1: the files a declared word names, however it is spelled -- `./x`, `a/../x`, an absolute path inside
    `root`, any case -- as git spells them."""
    rel = word
    if Path(rel).is_absolute():
        for at in {str(root).lower(), str(root.resolve()).lower()}:
            if rel.startswith(at.rstrip("/") + "/"):
                rel = rel[len(at.rstrip("/")) + 1:]
                break
        else:
            return set()
    rel = os.path.normpath(rel).replace(os.sep, "/")
    return set() if rel.startswith("../") or rel == ".." else files.get(rel, set())


def _path_like(word: str) -> bool:
    """A word the shell may resolve to a file: it has a slash, or starts with `.`, `~` or an expansion."""
    return "/" in word or word.startswith((".", "~", "$", "`"))


def _command_surface(root: Path, words: list[str], files: dict[str, set[str]]) -> set[str] | None:
    """#501 (D-231 clause 1): the files a declared command starts, read only through the programs this knows -- a
    script git lists, a shell in SHELLS given such a script, `gh` dispatching a workflow (its files come from
    `deploy_workflows`), and KNOWN_PROGRAMS --; None for any other program, a shell's option (`bash -c`), or a
    path-like word that names no file git lists (`cd x && ./y`, `$PWD/y`, a directory). The #501 review: None as well
    for a command that is more than one (`a && b`, `a; b`, `a | b`: only the first would be read), for an assignment
    before the program (`BASH_ENV=x bash y` runs `x` too), and for a dispatch whose workflow is not named (an id)."""
    if any(any(mark in word for mark in ";&|`\n") or "$(" in word for word in words):
        return None
    run = _program_position(words)
    if not run or any(ASSIGNMENT.match(word) for word in words[:len(words) - len(run)]):
        return None
    named = [_named_files(root, word, files) for word in run]
    if any(_path_like(word) and not found for word, found in zip(run, named, strict=True)):
        return None
    program = os.path.basename(run[0])
    if named[0]:
        pass  # a script git lists
    elif program in SHELLS:
        if len(run) < 2 or run[1].startswith("-") or not named[1]:
            return None
    elif program == "gh":
        started = gh_dispatch(run)
        if started is None or UNKNOWN in started:
            return None
    elif program not in KNOWN_PROGRAMS:
        return None
    return {path for found in named for path in found}


#: #522 (D-232 clause 2): what in a dispatched deploy workflow's text hides what it starts, so nothing is exempt -- a
#: recipe runner named anywhere (quoted, after `bash -c` or `xargs`, as an expansion's default), a change of
#: directory (what a relative path after it names cannot be read), and a local action or workflow (`uses: ./`).
#: The #522 review's B1: a runner written with its path (`/usr/bin/make`, `./make`) or in another case is one too, and
#: its M1: `working-directory:` and `env -C` change directory as `cd` does.
_UNREAD_IN_WORKFLOW = re.compile(
    r"(?<![\w.-])(?:" + "|".join(sorted(UNREAD_RECIPES | {"cd", "pushd"})) + r")(?![\w/.-])"
    r"|\buses\s*:\s*[\"']?\./|\bworking-directory\s*:|\benv\b[^\n]*\s(?-i:-[A-Za-z]*C|--chdir)",
    re.IGNORECASE)
#: A run of characters a path can be written with: every one in a workflow's text is looked up as a file git lists.
_PATH_WORD = re.compile(r"[A-Za-z0-9_./-]+")
#: A variable or an expression (`$X`, `${X}`, `${{ x }}`): taken out, what follows it is read from the checkout's top.
_EXPANSION = re.compile(r"\$\{\{[^}]*\}\}|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?")


def _runs_unread(text: str) -> bool:
    """#501, #522: whether a dispatched deploy workflow's text hides what it starts (`_UNREAD_IN_WORKFLOW`). Read
    wide on purpose: a word in a comment counts too, which refuses more."""
    return _UNREAD_IN_WORKFLOW.search(text) is not None or any(
        (run := _program_position(words)) and os.path.basename(run[0]).lower() in UNREAD_RECIPES
        for words in _line_commands(text))


#: #541 (D-237): quoting a shell joins back into one word (`./'ship'_it.sh`).
_QUOTING = re.compile(r"[\"'\\]")


def _named_by_name(text: str, files: dict[str, set[str]]) -> set[str]:
    """#541 (D-237): every file git lists whose name, or whose name less its last suffix (a module: `-m scripts.x`,
    `import x`), the text writes with no letter, digit or `_` beside it -- wherever the file lies. A change of the
    directory or the prefix a file is started under (`cd`, `env --chd`, `sudo -D`, a PATH entry or `$GITHUB_PATH`, a
    checkout's `path:`, `os.chdir`) leaves its name to be written, so no list of those ways is needed. The text is
    read as written and with its quotes, backslashes and expansions taken out."""
    low = text.lower()
    sources = {low, _QUOTING.sub("", low), _QUOTING.sub("", _EXPANSION.sub("", low))}
    out: set[str] = set()
    for key, paths in files.items():
        name = key.rsplit("/", 1)[-1]
        for word in {name, Path(name).stem}:
            if word and any(word in source and re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])", source)
                            for source in sources):
                out |= paths
                break
    return out


def _workflow_names(root: Path, text: str, files: dict[str, set[str]]) -> set[str]:
    """#522: every file git lists that a workflow's text names, quoted or not, inside a `-c` string or not; #541
    (D-237): and every one whose name it writes, under any prefix (`_named_by_name`)."""
    # The #522 review's M1: `$GITHUB_WORKSPACE/x`, `${{ github.workspace }}/x` and `$PWD/x` reach here as `/x`, a
    # path from the checkout's top, so each word is looked up as written and without its leading slash.
    bare = _EXPANSION.sub("", text)
    return {path for source in (text, bare) for word in _PATH_WORD.findall(source.lower())
            for spelled in {word, word.lstrip("/")} for path in _named_files(root, spelled, files)} | \
        _named_by_name(text, files)


def _line_commands(text: str) -> list[list[str]]:
    """The commands each line of a workflow file runs: a `run:` value, or a line of its block, with a `\\`
    continuation joined; a line the shell cannot split is read by its words."""
    out: list[list[str]] = []
    for line in re.sub(r"\\\n\s*", " ", text).splitlines():
        line = re.sub(r"^\s*(?:-\s*)?(?:run:\s*)?", "", line)
        try:
            out += split_line(line)
        except ValueError:
            out.append(line.split())
    return out


def deploy_surface(root: Path) -> frozenset[str] | None:
    """#444 M3: what the brief's deploy commands start, derived rather than listed -- each file a declared command
    names, and each workflow file a declared `gh workflow run` dispatches or whose run line is a declared command.
    None -- nothing is exempt (fail closed) -- when the workflows cannot all be read, when git cannot list the tree,
    (#494) when nothing is declared, and (#501) when a declared command is not read through a program this knows
    (`_command_surface`) or a deploy workflow it dispatches runs a recipe this does not read (UNREAD_RECIPES)."""
    key = str(root)
    if key not in _SURFACES:
        decl = declared(root)
        texts, complete = _workflow_texts(root)
        files = _files(root)
        commands = [_command_surface(root, words, files) for words in decl] if files is not None else [None]
        starts = set(deploy_workflows(root, decl, texts)) if complete else set()
        recipe = any(_runs_unread(text) for name in starts for text in texts.get(name, []))
        if not decl or any(c is None for c in commands) or recipe or not complete or files is None:
            _SURFACES[key] = None
        else:
            named = {path for c in commands for path in c or ()}
            named |= {path for name in starts for text in texts.get(name, []) for path in _workflow_names(root, text, files)}
            workflows = {path for d in WORKFLOW_DIRS for name in starts for path in files.get(f"{d}/{name}", set())}
            _SURFACES[key] = frozenset(named | workflows | {f"{d}/{name}" for d in WORKFLOW_DIRS for name in starts})
    return _SURFACES[key]


# --- #549 (D-239): a file a dispatched deploy workflow starts without writing its name ---------------------------

#: D-239 clause 3: the programs that run the file their first operand names -- a shell (SHELLS among them), `source`,
#: `.`, an interpreter --, matched on the program's lower-cased basename. A NAMED ENUMERATION (AGENTS.md section 3.5),
#: kept for this reason: which program reads its operand as a script is the program's own behaviour, which no text
#: this gate reads says. A program not here that starts a file it is given is D-239's residual risk.
STARTER_SHELLS = re.compile(r"(?:ba|rba|da|z|k|mk|pdk|c|tc|a|ya)?sh|fish")
STARTERS = re.compile(r"source|\.|python[0-9.]*|pypy[0-9.]*|node|deno|bun|perl[0-9.]*|ruby[0-9.]*|php[0-9.]*"
                      r"|lua[0-9.]*|pwsh|rscript|tclsh")
#: D-239 clause 2: programs that run names they read at run time; `find` only with one of FIND_RUNS.
RUNTIME_RUNNERS = {"xargs", "parallel"}
FIND_RUNS = {"-exec", "-execdir", "-ok", "-okdir"}
#: The shell's reserved words that may stand before a command (POSIX 2.4), set aside to reach it; and those that
#: open a header whose words are names, not a command (`for f in scripts/*.sh`).
RESERVED = {"!", "{", "}", "if", "then", "else", "elif", "fi", "do", "done", "while", "until"}
HEADERS = {"for", "select", "function"}
#: A starter's options that take the next word as their value (`bash -o pipefail x`, `python -W error x`).
STARTER_VALUED = {"-o", "-O", "+o", "+O", "-W", "-X", "--rcfile", "--init-file"}
#: An interpreter's options whose value is code in its own language, which this does not read (D-239's residual).
STARTER_CODE = {"-c", "-e", "--eval", "-p", "--print"}
#: A pattern the shell expands to names: `*`, `?`, a bracket expression, a brace expansion.
PATTERN = re.compile(r"[*?]|\[[^\]]*\]|\{[^{}]*(?:,|\.\.)[^{}]*\}")
#: A `run:` key, plain or as a step's first key (`- run:`), its name bare or quoted (#553 M3), with its value on the
#: line. Group 1: what stands before the key (its width is the key's column); group 3: the value.
_RUN_KEY = re.compile(r"^(\s*(?:-\s+)?)([\"']?)run\2[ \t]*:[ \t]*(.*?)\s*$")
#: #553 M3: a `run:` key this reader does not split -- inside a flow mapping (`- {name: x, run: ...}`), or an
#: explicit key (`? run`).
_FLOW_RUN = re.compile(r"[{,]\s*[\"']?run[\"']?\s*:")
_EXPLICIT_RUN = re.compile(r"^\s*(?:-\s+)?\?\s*[\"']?run[\"']?\s*$")
#: #553 M2: the variable whose value bash runs as a file when it starts non-interactively. (`ENV` is read by an
#: interactive sh only, and `ENV:` is a common workflow name -- the #553 review's M4.)
_STARTUP_KEY = re.compile(r"(?:^\s*(?:-\s+)?|[{,]\s*)[\"']?BASH_ENV[\"']?\s*:\s*(\"[^\"]*\"|'[^']*'|[^,}#\s]*)")
_STARTUP_WORD = re.compile(r"BASH_ENV=(.*)", re.S)
#: YAML's double-quoted escapes (1.2, 5.7), each one decoded in one pass.
_YAML_ESCAPES = {"0": "\0", "a": "\a", "b": "\b", "t": "\t", "\t": "\t", "n": "\n", "v": "\v", "f": "\f", "r": "\r",
                 "e": "\x1b", " ": " ", '"': '"', "/": "/", "\\": "\\", "N": "\x85", "_": "\xa0", "L": chr(0x2028),
                 "P": chr(0x2029)}
_UNNAMED: dict[str, list[str] | None] = {}
#: #556: what `unnamed_starts` read for each root -- the dispatched deploy workflows and their run commands -- so a
#: PASS names its evidence.
_UNNAMED_READ: dict[str, tuple[list[str], int]] = {}


def _run_values(text: str, new: bool = True) -> list[tuple[int, list[str]]]:
    """D-239 clause 1: each `run:` value of a workflow, as (its first line's number, its lines): the value on the
    key's line, or a block scalar's lines (`|`, `>`), which run while they are blank or indented as the first.
    `new` (#553): a quoted value unquoted, a plain value with its continuation lines, a folded value also line by
    line; without it, as the reader before #553 read them -- `unnamed_starts` reads both, so it never refuses less."""
    lines = text.splitlines()
    out: list[tuple[int, list[str]]] = []
    i = 0
    while i < len(lines):
        m = _RUN_KEY.match(lines[i])
        i += 1
        if not m:
            continue
        value, column = m.group(3), len(m.group(1))
        if not re.fullmatch(r"[|>][-+0-9]*(?:\s+#.*)?", value):
            if not new:
                out.append((i, [value]))
            elif (quoted := _yaml_quoted(value)) is not None:
                out.append((i, [quoted]))
            else:
                start = i
                i, plain = _plain_continued(lines, i, column, value)
                out.append((start, plain))
            continue
        start, block, indent = i + 1, [], 0
        while i < len(lines):
            width = len(lines[i]) - len(lines[i].lstrip())
            if lines[i].strip() and (width <= column if not indent else width < indent):
                break
            if lines[i].strip() and not indent:
                indent = width
            block.append(lines[i][indent:] if lines[i].strip() else "")
            i += 1
        if value.startswith(">"):
            # #553 review M3: a folded value keeps a more-indented or blank-separated line apart; read it both folded
            # and line by line, so neither reading hides a start.
            out += [(start, block)] if new else []
            block = [" ".join(line.strip() for line in block)]
        out.append((start, block))
    return out


def _plain_continued(lines: list[str], i: int, column: int, value: str) -> tuple[int, list[str]]:
    """#553 M3: a plain `run:` value from line `i` on -- it continues on each following line indented past the key's
    `column` (YAML 7.3.3), folded with a space; a blank line between them is a line break. Returns (the next line,
    the value's lines)."""
    groups: list[list[str]] = [[value]]
    while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > column):
        if lines[i].strip() and not lines[i].lstrip().startswith("#"):
            groups[-1].append(lines[i].strip())
        elif not lines[i].strip() and groups[-1]:
            groups.append([])
        i += 1
    return i, [" ".join(group) for group in groups if group]


def _yaml_quoted(value: str) -> str | None:
    """#553 M3: a `run:` value quoted on its own line, as YAML reads it (single: `''` is one quote; double: the
    backslash escapes), or None when the value is not quoted on one line (a quote that runs on is unreadable)."""
    if not value or value[0] not in "\"'":
        return None
    q, out, i = value[0], [], 1
    while i < len(value):
        ch = value[i]
        if q == "'" and ch == "'":
            if value[i + 1:i + 2] == "'":
                out.append("'")
                i += 2
                continue
            break
        if q == '"' and ch == '"':
            break
        if q == '"' and ch == "\\":
            esc = value[i + 1:i + 2]
            width = {"x": 2, "u": 4, "U": 8}.get(esc, 0)
            digits = value[i + 2:i + 2 + width]
            if width and len(digits) == width and all(c in "0123456789abcdefABCDEF" for c in digits):
                out.append(chr(int(digits, 16)))
                i += 2 + width
                continue
            if esc not in _YAML_ESCAPES:
                return None  # an escape YAML refuses: unreadable
            out.append(_YAML_ESCAPES[esc])
            i += 2
            continue
        out.append(ch)
        i += 1
    else:
        return None  # the quote runs past the line
    rest = value[i + 1:]
    # #553 review M4: a comment may follow the closing quote; anything else after it is not one scalar
    return "".join(out) if not rest.strip() or re.fullmatch(r"\s+#.*", rest) else None


def _unreadable_runs(text: str) -> list[int]:
    """#553 M3, D-239 fail closed: the lines of `run:` values this reader cannot place -- inside a flow mapping, an
    explicit key (`? run`), a value with a tag or an anchor (`!!str`, `&a`), or a quote it cannot read on its line."""
    found: list[int] = []
    for n, line in enumerate(text.splitlines(), 1):
        m = _RUN_KEY.match(line)
        value = m.group(3) if m else ""
        unreadable = ((_FLOW_RUN.search(line) is not None and not m) or _EXPLICIT_RUN.match(line) is not None
                      or value[:1] in ("!", "&")
                      or (value[:1] in ("\"", "'") and _yaml_quoted(value) is None))
        if unreadable:
            found.append(n)
    return found


def _startup_values(text: str) -> list[tuple[int, str]]:
    """#553 M2: each `BASH_ENV:` a workflow sets in an `env:` mapping, block or flow, as (line, value)."""
    return [(n, m.group(1).strip("\"'")) for n, line in enumerate(text.splitlines(), 1)
            for m in _STARTUP_KEY.finditer(line)]


def _strip_comment(line: str, quote: str | None) -> tuple[str, str | None]:
    """#553 M1: `line` without its shell comment, as the shell reads one -- a `#` that begins a word outside quotes
    runs to the end of the line --, and the quote still open at its end. `quote` is the one open at its start."""
    out: list[str] = []
    i, depth, tick = 0, 0, False
    while i < len(line):
        ch, two = line[i], line[i:i + 2]
        if ch == "\\" and quote != "'":
            out.append(two)
            i += 2
            continue
        if quote:  # `'`, `"` or `$'`, each closed by its last character
            quote = None if ch == quote[-1] else quote
        elif two in ("$'", "${", "$("):
            # the #553 review's B1: no `#` inside `$'...'`, `${...}`, `$(...)` or `$((...))` ends the line
            quote, depth = ("$'", depth) if two == "$'" else (quote, depth + 1)
            out.append(two)
            i += 2
            continue
        elif ch in "'\"":
            quote = ch
        elif ch in ")}" and depth:
            depth -= 1
        elif ch == "`":
            tick = not tick
        elif ch == "#" and not depth and not tick and (i == 0 or line[i - 1] in " \t;&|()<>"):
            break
        out.append(ch)
        i += 1
    return "".join(out), quote


def _run_tokens(lines: list[str], new: bool = True) -> list[tuple[int, str]]:
    """Each token of a run value with its line (from 0), split as `split_line` splits (`;`, `&&`, `|`, `(`, `)` and
    the redirections stay tokens), a `\\` continuation joined, a here-document's body left out, and each line's end
    a `;`. Read as one text, so a quote across lines is one word; when it cannot be split so, line by line, and a
    line the shell cannot split is read by its words."""
    def lex(text: str, at: int) -> list[tuple[int, str]]:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""  # a comment is read as words, which refuses more
        return [(at + lexer.lineno - 1, token) for token in lexer]

    body: list[str] = []
    delimiters: list[str] = []
    quote: str | None = None
    for line in lines:
        if delimiters:
            body.append("")
            if line.strip() == delimiters[0]:
                delimiters.pop(0)
            continue
        # #553 M1: the comment goes first, as the shell drops it: an apostrophe, a trailing `\` or a `<<` in it
        # no longer hides the lines after it.
        if new:
            line, quote = _strip_comment(line, quote)
        try:  # a here-document's operator as the shell reads it, never `<<` inside quotes; unsplit, its body is read
            words = [word for _, word in lex(line, 0)]
        except ValueError:
            words = []
        delimiters += [after.removeprefix("-") for word, after in itertools.pairwise(words)
                       if word.endswith("<<") and not word.endswith("<<<") and set(word) <= set(";&|()<>")]
        body.append(line[:-1] + " " if line.endswith("\\") else line + " ;")

    try:
        return lex("\n".join(body), 0)
    except ValueError:
        out: list[tuple[int, str]] = []
        for at, line in enumerate(body):
            try:
                out += lex(line, at)
            except ValueError:
                out += [(at, word) for word in line.split()]
        return out


def _in_case(case: list[str], word: str, operator: bool) -> bool:
    """Whether `word` is a `case` subject's or a pattern's, read past: `case` holds, per open `case`, "subject" until
    `in`, "pattern" until `)`, then "body" until `;;`, `;&` or `;;&`."""
    if case and case[-1] == "subject":
        if word == "in":
            case[-1] = "pattern"
        return True
    if case and case[-1] == "pattern":
        if word == "esac":
            case.pop()
        elif operator and ")" in word:
            case[-1] = "body"
        return True
    if operator and case and case[-1] == "body" and word in (";;", ";&", ";;&"):
        case[-1] = "pattern"
    return False


def _redirection(operator: str) -> str:
    """What an operator token redirects: "<" a command's standard input (its target is kept), "skip" another (its
    target is set aside), "" none -- a process substitution (`<(`) is no redirection."""
    if "<(" in operator or ">(" in operator or not ("<" in operator or ">" in operator):
        return ""
    return "<" if operator in ("<", "<>") else "skip"


def _run_commands(lines: list[str], new: bool = True) -> list[tuple[int, list[str], list[str]]]:
    """D-239 clause 1: the simple commands of a run value, each as (its line, from 0; its words; the targets of its
    `<` redirections), with what starts no program set aside: a redirection's target, a `case` subject and its
    patterns. A process substitution (`<(...)`) stays as the word `<(` where it stands."""
    out: list[tuple[int, list[str], list[str]]] = []
    cur: list[str] = []
    stdin: list[str] = []
    case: list[str] = []
    at = 0
    target = ""  # "<" or "skip" after a redirection, until its target is read
    digits = False  # #553 M2: the last word read was all digits, the descriptor of a redirection if one follows
    for line, word in _run_tokens(lines, new):
        operator = all(ch in ";&|()<>" for ch in word)
        if _in_case(case, word, operator):
            continue
        if new and operator and digits and cur and _redirection(word):
            cur.pop()  # `2>&1`, `2>/dev/null`: the shell reads the digits as the descriptor, not as a word
        digits = not operator and not target and (word.isdigit() or re.fullmatch(r"\{[A-Za-z_][A-Za-z0-9_]*\}", word) is not None)
        if operator:
            cur += ["<("] if "<(" in word or ">(" in word else []
            target = _redirection(word)
            if not target or any(ch in word for ch in ";|()") or "&&" in word:
                out += [(at, cur, stdin)] if cur else []
                cur, stdin = [], []
        elif target:
            stdin += [word] if target == "<" else []
            target = ""
        elif not cur and word == "case":
            case.append("subject")
        elif not cur and word == "esac" and case:
            case.pop()
        else:
            at = line if not cur else at
            cur.append(word)
    if cur:
        out.append((at, cur, stdin))
    return out


def _unnamed_word(word: str) -> str | None:
    """D-239 clause 2: why the shell builds this word's file name rather than reading it as written, or None."""
    if word.startswith(("<(", ">(")) or UNREAD.search(word):
        return "a name built at run time"
    return "a pattern" if PATTERN.search(word) else None


def _started(words: list[str]) -> list[str]:
    """The words from the program a simple command starts: past reserved words, assignments and the WRAPPERS;
    none for a header (`for f in ...`)."""
    i = 0
    while True:
        while i < len(words) and words[i] in RESERVED:
            i += 1
        if i < len(words) and words[i] in HEADERS:
            return []
        i = len(words) - len(_program_position(words[i:]))
        if not (i < len(words) and words[i] in RESERVED):
            return words[i:]


def _shapes_in(text: str, new: bool = True, where: _Where | None = None) -> list[tuple[str, str]]:
    """The shapes of every command in a text a command runs in turn (`eval`'s, a shell's `-c` string, #551: a
    Makefile's recipe line)."""
    where = _moved([text], new, where)
    return [found for _, command, into in _run_commands([text], new)
            for found in _unnamed_shapes(command, into, new, where)]


def _unnamed_shapes(words: list[str], stdin: list[str], new: bool = True,
                    where: _Where | None = None) -> list[tuple[str, str]]:
    """D-239 clause 2 and #551 (D-242): each (shape, word) by which this simple command starts a file it does not
    name -- D-239's reading as it was, and D-242's added to it, so D-242 only ever refuses more."""
    return [*_d239_shapes(words, stdin, new, where), *_d242_shapes(words, stdin, new, where)]


def _d239_shapes(words: list[str], stdin: list[str], new: bool = True,
                 where: _Where | None = None) -> list[tuple[str, str]]:
    """D-239 clause 2: each (shape, word) by which this simple command starts a file it does not name."""
    # #553 M2: `BASH_ENV=...` set for a command, or exported, names a file bash runs when it starts; its value is
    # read as a started file's name. (Not `ENV`: only an interactive sh reads it -- the review's M4.)
    startup = [value for word in words if (m := _STARTUP_WORD.fullmatch(word)) for value in [m.group(1)]
               if _unnamed_word(value)]
    if startup:
        return [(f"{_unnamed_word(value)} in the file `BASH_ENV` names", value) for value in startup]
    run = _started(words)
    if not run:
        return []
    if (shape := _unnamed_word(run[0])):
        return [(f"{shape} in the program it runs", run[0])]
    program = os.path.basename(run[0]).lower()
    if program in RUNTIME_RUNNERS or (program == "find" and FIND_RUNS & set(run[1:])):
        return [("a name built at run time: a program that runs names it reads then", run[0])]
    if program == "eval":
        return _shapes_in(" ".join(run[1:]), new, where)
    if STARTER_SHELLS.fullmatch(program) or STARTERS.fullmatch(program):
        return _starter_shapes(program, run, stdin, new, where)
    return []


def _starter_shapes(program: str, run: list[str], stdin: list[str], new: bool = True,
                    where: _Where | None = None) -> list[tuple[str, str]]:
    """D-239 clause 3: the shape of the file a starter is given -- its first operand that is not an option or an
    option's value, the module `-m` names, or with neither its `<` target --; a shell's `-c` string is read in turn,
    and an interpreter's code (`python -c`) is not read."""
    shell = STARTER_SHELLS.fullmatch(program) is not None
    j = 1
    while j < len(run) and run[j].startswith(("-", "+")) and run[j] not in ("-", "+", "--"):
        if shell and re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", run[j]):
            return _shapes_in(run[j + 1], new, where) if j + 1 < len(run) else []
        if not shell and run[j] in STARTER_CODE:
            return []
        if not shell and run[j].startswith("-m"):
            module = run[j][2:] or (run[j + 1] if j + 1 < len(run) else "")
            return [(f"{shape} in the module `{program}` runs", module)] if (shape := _unnamed_word(module)) else []
        # #553 M2: a shell cluster holding `o`/`O` takes the next word (`bash -eo pipefail`, `-oe`), and so does a
        # Python cluster ending in `W`/`X` (`python -uW x`; not perl's `-W`, the review's M2)
        valued = run[j] in STARTER_VALUED or (new and (
            (shell and re.fullmatch(r"[-+][A-Za-z]*[oO][A-Za-z]*", run[j]) is not None)
            or (program.startswith(("python", "pypy")) and re.fullmatch(r"-[A-Za-z]*[WX]", run[j]) is not None)))
        j += 2 if valued else 1
    j += 1 if j < len(run) and run[j] == "--" else 0
    for operand in run[j:j + 1] or stdin:
        if (shape := _unnamed_word(operand)):
            return [(f"{shape} in the file `{program}` runs", operand)]
    return []


# --- #551 (D-242): the unread starts D-239's mitigation named refuse too ------------------------------------------


class _Where(NamedTuple):
    """#551 (D-242 clause 3): where a run text runs, which `make` needs to find its Makefile -- the tree (None: no
    Makefile can be read here), the directory from the checkout's top (None: a `cd` or a `working-directory:` moved
    it, so which Makefile cannot be told), and how many recipes deep the reading is."""
    root: Path | None
    cwd: str | None = "."
    depth: int = 0


#: D-242 clause 1: the shells a step may name that are POSIX shells, written plain. A custom template (`bash -e {0}`)
#: is not one: its program is whatever the template says.
POSIX_SHELLS = {"bash", "sh"}
#: A `shell:` key -- a step's, or a workflow's or a job's `defaults: run:` --, block or flow, and its value.
_SHELL_KEY = re.compile(r"(?:^\s*(?:-\s+)?|[{,]\s*)[\"']?shell[\"']?\s*:\s*(\"[^\"]*\"|'[^']*'|[^,}#]*)")
#: A `runs-on:` key and its value on the line; the lines indented past it continue it (a list of labels).
_RUNS_ON_KEY = re.compile(r"^(\s*(?:-\s+)?)[\"']?runs-on[\"']?\s*:\s*(.*)$")
#: A runner whose steps' default shell is PowerShell (Windows), or one the text cannot tell (an expression).
_UNPOSIX_RUNNER = re.compile(r"windows|\$\{\{", re.IGNORECASE)
#: D-242 clause 3: a step that runs in another directory than the checkout's top, so `make` reads another Makefile.
_WORKING_DIRECTORY = re.compile(r"\bworking-directory\s*:")
#: The programs that change the directory the commands after them run in.
CHDIRS = {"cd", "pushd", "popd"}
#: D-242 clause 4: per interpreter, the letters of an option cluster that hold code in its own language (`perl -lne`),
#: those whose value is the rest of the cluster or the next word, and those that take digits only. A NAMED
#: ENUMERATION (D-239 clause 3's reason: which option holds code is the interpreter's own behaviour).
_CLUSTER_CODE = {"perl": ("eE", "CdDFiIMmx", "0l"), "ruby": ("e", "CEFiIKrTWx", "0")}
_NODE_CODE = {"-e", "--eval", "-p", "--print", "-pe", "-ep"}
#: Options that print and exit, reading no program.
INFO_OPTIONS = {"--version", "--help"}
#: D-242 clause 3: `deno` and `bun` subcommands that start the file or command their operand names (`deno run x`);
#: `deno eval`'s operand is code.
_SUBCOMMANDS = {"deno": {"run", "test", "bench", "serve", "compile", "install"}, "bun": {"run", "x", "exec"}}
#: D-242 clause 3: programs that start the command or the file their operand names, keyed as written (`uv run`),
#: each with (its options that take the next word as their value; its options known to take none). An option in
#: neither may take one, so the word after it is read as the operand AND the word after that too (fail closed).
#: A NAMED ENUMERATION (D-239 clause 3's reason).
RUNNERS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "uv run": (frozenset({
        "--extra", "--no-extra", "--group", "--no-group", "--only-group", "--env-file", "-w", "--with",
        "--with-editable", "--with-requirements", "--package", "--index", "--default-index", "-i", "--index-url",
        "--extra-index-url", "-f", "--find-links", "-P", "--upgrade-package", "--reinstall-package",
        "--index-strategy", "--keyring-provider", "--resolution", "--prerelease", "--fork-strategy", "-C",
        "--config-setting", "--config-settings-package", "--no-build-isolation-package", "--exclude-newer",
        "--exclude-newer-package", "--link-mode", "--no-build-package", "--no-binary-package", "--refresh-package",
        "-p", "--python", "--python-platform", "--cache-dir", "--python-preference", "--allow-insecure-host",
        "--directory", "--project", "--config-file", "--color", "--max-recursion-depth"}),
        frozenset({
            "--all-extras", "--no-dev", "--dev", "--only-dev", "--no-default-groups", "--all-groups", "--no-editable",
            "--exact", "--no-env-file", "--isolated", "--active", "--no-active", "--no-sync", "--locked", "--frozen",
            "-s", "--script", "--gui-script", "--no-project", "--no-index", "-U", "--upgrade", "--reinstall", "--pre",
            "--no-build-isolation", "--compile-bytecode", "--no-sources", "--no-build", "--no-binary", "--refresh",
            "-n", "--no-cache", "--managed-python", "--no-managed-python", "--no-python-downloads", "--offline",
            "--native-tls", "--no-config", "-q", "--quiet", "-v", "--verbose", "--no-progress", "-h", "--help"})),
    "uvx": (frozenset({
        "--from", "-w", "--with", "--with-editable", "--with-requirements", "-p", "--python", "--index",
        "--default-index", "-i", "--index-url", "--extra-index-url", "-f", "--find-links", "-C", "--config-setting",
        "--cache-dir", "--directory", "--project", "--config-file", "--color", "--env-file"}),
        frozenset({
            "--isolated", "-q", "--quiet", "-v", "--verbose", "--offline", "-n", "--no-cache", "--refresh", "-U",
            "--upgrade", "--reinstall", "--no-config", "--no-progress", "--native-tls", "--pre",
            "--no-python-downloads", "--managed-python", "-h", "--help"})),
    "poetry run": (frozenset({"-C", "--directory", "-P", "--project"}),
                   frozenset({"-q", "--quiet", "-v", "-vv", "-vvv", "--verbose", "-n", "--no-interaction", "--ansi",
                              "--no-ansi", "--no-plugins", "--no-cache", "-h", "--help"})),
    "npx": (frozenset({"-p", "--package", "--prefix", "--registry", "--cache", "-w", "--workspace", "--userconfig",
                       "--loglevel"}),
            frozenset({"-y", "--yes", "--no", "-q", "--quiet", "--ignore-existing", "--no-install",
                       "--include-workspace-root", "--workspaces", "--silent"})),
    "deno run": (frozenset({"-c", "--config", "--import-map", "--lock", "--cert", "--location", "--seed"}),
                 frozenset({"-A", "--allow-all", "--allow-net", "--allow-read", "--allow-write", "--allow-env",
                            "--allow-run", "--allow-sys", "--allow-ffi", "--allow-import", "-q", "--quiet",
                            "--no-check", "--check", "--reload", "-r", "--watch", "--unstable", "--no-prompt",
                            "--frozen", "--no-lock", "--no-remote", "--no-npm", "--cached-only"})),
    "bun run": (frozenset({"--cwd", "--env-file", "-c", "--config", "--filter", "-F", "--shell", "-r", "--preload"}),
                frozenset({"--bun", "--silent", "--watch", "--hot", "--smol", "--no-install", "--if-present"})),
}
#: The global options before `uv`'s and `poetry`'s subcommand that take the next word as their value.
_RUNNER_GLOBAL = {"uv": frozenset({"--directory", "--project", "--cache-dir", "--config-file", "--color",
                                   "--python-preference", "--allow-insecure-host"}),
                  "poetry": frozenset({"-C", "--directory", "-P", "--project"})}
#: A runner's option whose value is the module it runs (`uv run -m x`), and one whose value is a shell string.
_RUNNER_MODULE = {"uv run": {"-m", "--module"}}
_RUNNER_CALL = {"npx": {"-c", "--call"}}
#: D-242 clause 3: `make` and its GNU name; its targets' recipes are read as run text in turn.
MAKES = {"make", "gmake"}
#: How deep `make` is followed -- a recipe's own `make`, a prerequisite, an include, a variable --; past it, refused.
_MAKE_DEPTH = 8
#: The names GNU make reads, in its order, when it is given no `-f`.
_MAKEFILE_NAMES = ("GNUmakefile", "makefile", "Makefile")
_MAKE_ASSIGN = re.compile(r"^([^\s:#=]+)\s*(:::=|::=|:=|\?=|\+=|!=|=)\s*(.*)$", re.S)
_ARGUMENT_ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*)(:::=|::=|:=|\?=|\+=|!=|=)(.*)$", re.S)
_BASES: dict[str, list[str]] = {}
#: What one `make` command line, in one directory of one tree, starts (None while it is being read: a `make` that
#: reaches itself again adds nothing to what the outer reading reports), so a recipe that runs `$(MAKE)` many times
#: is read once.
_MAKE_READ: dict[tuple[str, str, tuple[str, ...], bool], list[tuple[str, str]] | None] = {}


def _moved(lines: list[str], new: bool, where: _Where | None) -> _Where | None:
    """`where` with no directory once a command of this run text changes it (`cd`, `pushd`): which Makefile a
    `make` after it reads cannot be told."""
    if where is None or where.cwd is None:
        return where
    for _, words, _ in _run_commands(lines, new):
        run = _started(words)
        if run and os.path.basename(run[0]).lower() in CHDIRS:
            return where._replace(cwd=None)
    return where


def _non_posix_shells(text: str) -> list[tuple[int, str, str]]:
    """D-242 clause 1: each (line, why, value) where a workflow runs a step in a shell that is not a POSIX shell --
    a `shell:` key that is not `bash` or `sh` (a step's, or a workflow's or a job's `defaults: run:`), and a runner
    whose default shell is PowerShell or cannot be told. Read wide on purpose: a `shell:` anywhere counts, which
    refuses more."""
    out: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        for m in _SHELL_KEY.finditer(line):
            value = m.group(1).strip()
            value = value[1:-1].strip() if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'" else value
            if value not in POSIX_SHELLS:
                out.append((n, "a step's shell that is not a POSIX shell (D-242)", value))
        if (key := _RUNS_ON_KEY.match(line)) is not None:
            column, value_lines, k = len(key.group(1)), [key.group(2)], n
            while k < len(lines) and (not lines[k].strip() or len(lines[k]) - len(lines[k].lstrip()) > column):
                value_lines.append(lines[k].strip())
                k += 1
            joined = " ".join(part for part in value_lines if part)
            if _UNPOSIX_RUNNER.search(joined):
                out.append((n, "a runner whose default shell is not a POSIX shell, or cannot be told (D-242)", joined))
    return out


def _d242_shapes(words: list[str], stdin: list[str], new: bool = True,
                 where: _Where | None = None) -> list[tuple[str, str]]:
    """#551 (D-242 clauses 2-4): what D-239 left unread in this simple command -- a starter reading its program from
    standard input, an interpreter given code in its own language, a runner (`uv run`, `npx`, `poetry run`) and
    `make`'s recipes. Only ever added to D-239's findings."""
    run = _started(words)
    if not run or _unnamed_word(run[0]):
        return []  # D-239 refuses the program word itself
    program = os.path.basename(run[0]).lower()
    if program in MAKES:
        return _make_shapes(words, run, new, where)
    if program in ("uv", "uvx", "poetry", "npx"):
        return _runner_shapes(program, run, stdin, new, where)
    if STARTER_SHELLS.fullmatch(program) or STARTERS.fullmatch(program):
        return _input_shapes(program, run, stdin, new, where)
    return []


def _cluster_code(word: str, code: str, valued: str, numeric: str) -> bool:
    """Whether an option cluster (`-lne`) holds a letter whose value is code, before a letter whose value is the
    rest of the cluster (`-Mfoo`); a `numeric` letter's digits are its value (`-l0e`)."""
    k = 1
    while re.match(r"-[A-Za-z0-9]", word) and k < len(word):
        ch, k = word[k], k + 1
        if ch in code or ch in valued:
            return ch in code
        while ch in numeric and k < len(word) and word[k].isdigit():
            k += 1
    return False


def _pwsh_code(word: str) -> bool:
    """`pwsh`'s `-Command`, `-EncodedCommand` and `-CommandWithArgs`, by any prefix it accepts."""
    bare = word.lower().lstrip("-")
    return bare in ("c", "e", "ec", "cwa") or any(
        len(bare) >= least and name.startswith(bare)
        for name, least in (("command", 2), ("encodedcommand", 2), ("commandwithargs", 8)))


#: D-242 clause 4: per interpreter (a test of its name), the test of an option that holds code in its own language.
_CODE_OPTIONS: tuple[tuple[Callable[[str], bool], Callable[[str], bool]], ...] = (
    (lambda p: p.startswith(("python", "pypy")), lambda w: re.fullmatch(r"-[bBdEhiIOPqRsSuvVx]*c.*", w, re.S) is not None),
    (lambda p: p in ("node", "bun", "deno"), lambda w: w in _NODE_CODE),
    (lambda p: p.startswith("php"), lambda w: re.match(r"-[rRBE]", w) is not None),
    (lambda p: p.startswith("lua") or p == "rscript", lambda w: w.startswith("-e")),
    (lambda p: p == "pwsh", _pwsh_code),
    (lambda p: p.startswith("perl"), lambda w: _cluster_code(w, *_CLUSTER_CODE["perl"])),
    (lambda p: p.startswith("ruby"), lambda w: _cluster_code(w, *_CLUSTER_CODE["ruby"])),
)


def _interpreter_code(program: str, word: str) -> bool:
    """D-242 clause 4: whether this option of an interpreter holds code in its own language. Every option D-239
    stops its reading at (STARTER_CODE) is one, so what D-239 does not read past is refused here."""
    if word in STARTER_CODE or word.startswith(("--eval=", "--print=")):
        return True
    return any(applies(program) and holds(word) for applies, holds in _CODE_OPTIONS)


def _from_stdin(program: str, stdin: list[str], operand: str) -> list[tuple[str, str]]:
    """D-242 clause 2: a starter told to read its program from standard input -- refused, unless its `<` names the
    file (then that name is read, as D-239 reads it)."""
    if stdin:
        return [(f"{shape} in the file `{program}` reads on standard input", target)
                for target in stdin if (shape := _unnamed_word(target))]
    return [(f"a program `{program}` reads from standard input, which names no file (D-242)", operand)]


def _input_options(program: str, run: list[str]) -> tuple[int, bool] | list[tuple[str, str]]:
    """A starter's options read as D-239 reads them (its new reading, whose valued options take the most words):
    (where its operand would stand, whether a shell's `-s` tells it to read standard input), or the findings
    that end the reading -- none for `--version` or a shell's `-c` (D-239 reads that string), code for an
    interpreter's code option, none for Python's `-m` (D-239 reads the module)."""
    shell = STARTER_SHELLS.fullmatch(program) is not None
    python = program.startswith(("python", "pypy"))
    j, told = 1, False
    while j < len(run) and run[j].startswith(("-", "+")) and run[j] not in ("-", "+", "--"):
        word = run[j]
        if word in INFO_OPTIONS or (shell and re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", word)) or (
                python and word.startswith("-m")):
            return []
        if not shell and _interpreter_code(program, word):
            return [(f"code in the interpreter's own language, which names no file (D-242): `{program}`'s", word)]
        told = told or (shell and re.fullmatch(r"-[A-Za-z]*s[A-Za-z]*", word) is not None)
        valued = (word in STARTER_VALUED
                  or (shell and re.fullmatch(r"[-+][A-Za-z]*[oO][A-Za-z]*", word) is not None)
                  or (python and re.fullmatch(r"-[A-Za-z]*[WX]", word) is not None)
                  or (not shell and not python and word in ("-I", "-r", "-m", "-M", "--require", "--import")))
        j += 2 if valued else 1
    return j + (1 if j < len(run) and run[j] == "--" else 0), told


def _input_shapes(program: str, run: list[str], stdin: list[str], new: bool,
                  where: _Where | None) -> list[tuple[str, str]]:
    """D-242 clauses 2-4 for a starter: its program read from standard input (no file operand and no `<` naming
    one, `-`, a shell's `-s`), code in an interpreter's own language, and `deno`'s and `bun`'s subcommands."""
    read = _input_options(program, run)
    if isinstance(read, list):
        return read
    j, told = read
    operand = run[j] if j < len(run) else None
    if program in ("source", "."):
        return []  # they read no program from standard input
    if operand is not None and operand in _SUBCOMMANDS.get(program, set()):
        return _runner_operands(f"{program} run", run[j + 1:], stdin, new, where)
    if program == "deno" and operand == "eval":
        return [("code in the interpreter's own language, which names no file (D-242): `deno`'s", "eval")]
    # A starter with no operand and no `<` reads standard input; read only as the shell reads the value (`new`):
    # the reading before #553 drops a plain value's continuation lines (`bash` then `scripts/x.sh`), so an absent
    # operand there is no evidence. A `-` or a `-s` is, in either reading.
    if told or operand == "-" or (operand is None and not stdin and new):
        return _from_stdin(program, stdin, operand or program)
    return []


def _runner_shapes(program: str, run: list[str], stdin: list[str], new: bool,
                   where: _Where | None) -> list[tuple[str, str]]:
    """D-242 clause 3: `uv run` (and `uv tool run`, `uvx`), `poetry run` and `npx` start what their operand names."""
    words = run[1:]
    key = program
    if program in _RUNNER_GLOBAL:
        k = 0
        while k < len(words) and words[k].startswith("-"):
            k += 2 if words[k] in _RUNNER_GLOBAL[program] else 1
        if k >= len(words):
            return []
        if (shape := _unnamed_word(words[k])):
            return [(f"{shape} in the command `{program}` runs", words[k])]
        if program == "uv" and words[k] == "tool" and words[k + 1:k + 2] == ["run"]:
            k, key = k + 1, "uvx"
        elif words[k] != "run":
            return []
        else:
            key = f"{program} run"
        words = words[k + 1:]
    return _runner_operands(key, words, stdin, new, where)


def _runner_operands(key: str, words: list[str], stdin: list[str], new: bool,
                     where: _Where | None) -> list[tuple[str, str]]:
    """The command a runner (RUNNERS) starts, read as a command in turn: past its options, the operand and what
    follows it. After an option this does not know, the next word may be its value, so the word after it is read as
    the operand too (fail closed)."""
    valued, flags = RUNNERS[key]
    out: list[tuple[str, str]] = []
    k, unknown = 0, False
    while k < len(words):
        word = words[k]
        if word == "--":
            out += _runner_command(key, words[k + 1:], stdin, new, where)
            break
        if word.startswith("-") and word != "-":
            name, eq, value = word.partition("=")
            later = words[k + 1] if k + 1 < len(words) else ""
            attached = key in _RUNNER_MODULE and re.fullmatch(r"-m\S+", name) is not None
            if name in _RUNNER_MODULE.get(key, set()) or attached:
                module = value if eq else (name[2:] if attached else later)
                return out + ([(f"{shape} in the module `{key}` runs", module)]
                              if (shape := _unnamed_word(module)) else [])
            if name in _RUNNER_CALL.get(key, set()):
                return out + _shapes_in(value if eq else later, new, where)
            if not eq and name in valued:
                k, unknown = k + 2, False
                continue
            unknown = not eq and name not in flags
            k += 1
            continue
        out += _runner_command(key, words[k:], stdin, new, where)
        if not unknown:
            break
        k, unknown = k + 1, False
    return out


def _runner_command(key: str, rest: list[str], stdin: list[str], new: bool,
                    where: _Where | None) -> list[tuple[str, str]]:
    """The command a runner starts, as a command of its own; `-` is a program read from standard input."""
    if not rest:
        return []
    if rest[0] == "-":
        return _from_stdin(key, stdin, "-")
    return _unnamed_shapes(rest, stdin, new, where)


class _Makefile:
    """D-242 clause 3: what this reader takes from a Makefile -- its variables (each definition's value; None for
    one it cannot read: `+=`, `!=`, `define`, a target's own), its rules (target -> prerequisites, recipe lines),
    its first target, and what it could not read."""

    def __init__(self) -> None:
        self.vars: dict[str, list[str | None]] = {}
        self.rules: dict[str, tuple[list[str], list[str]]] = {}
        self.first: str | None = None
        self.problems: list[tuple[str, str]] = []


def _make_sources(root: Path) -> list[tuple[str, Callable[[str], str | None]]]:
    """Where `make`'s files are read: the tree, and each protected base a dispatch runs (`protected_bases`)."""
    key = str(root)
    if key not in _BASES:
        try:
            _BASES[key] = protected_bases(root)
        except (OSError, RuntimeError, subprocess.SubprocessError):
            _BASES[key] = []

    def inside(rel: str) -> bool:  # a file outside the checkout is not read: it is the runner's, not the tree's
        return not posixpath.isabs(rel) and rel != ".." and not rel.startswith("../")

    def tree(rel: str) -> str | None:
        path = root / rel
        try:
            return path.read_text(encoding="utf-8", errors="replace") if inside(rel) and path.is_file() else None
        except OSError:
            return None

    def at(base: str) -> Callable[[str], str | None]:
        def read(rel: str) -> str | None:
            blob = verified_blob(root, base, rel) if inside(rel) else None
            return None if blob is None else blob.decode("utf-8", "replace")
        return read

    return [("the tree", tree), *((base[:12], at(base)) for base in _BASES[key])]


def _make_split(text: str) -> int:
    """The first `:` of a rule line outside a variable reference (`$(X:a=b): y`), or -1."""
    depth = 0
    for i, ch in enumerate(text):
        if ch in "({" and i and text[i - 1] == "$":
            depth += 1
        elif ch in ")}" and depth:
            depth -= 1
        elif ch == ":" and not depth:
            return i
    return -1


def _make_read(load: Callable[[str], str | None], rel: str, cwd: str, model: _Makefile, depth: int = 0) -> bool:
    """Read the Makefile at `rel` into `model` (an `include` read where it stands); False when it cannot be read."""
    text = load(rel)
    if text is None:
        return False
    current: list[str] | None = None
    define = False
    for raw in re.sub(r"\\\r?\n", " ", text).splitlines():
        if define:
            define = not raw.strip().startswith("endef")
        elif raw.startswith("\t"):
            for target in current or []:
                model.rules[target][1].append(raw[1:])
        elif (line := re.sub(r"(?<!\\)#.*", "", raw).strip()):
            current, define = _make_line(load, line, cwd, model, depth)
    return True


def _make_line(load: Callable[[str], str | None], line: str, cwd: str, model: _Makefile,
               depth: int) -> tuple[list[str] | None, bool]:
    """One Makefile line that is not a recipe line: (the targets a recipe after it belongs to, whether it opens a
    `define`). Both branches of a conditional are read: more is read, never less."""
    first = line.split()[0]
    if first in ("ifeq", "ifneq", "ifdef", "ifndef", "else", "endif", "vpath", "unexport"):
        return None, False
    if first in ("define", "undefine"):
        model.vars.setdefault(line.split()[1] if len(line.split()) > 1 else "", []).append(None)
        return None, first == "define"
    if first in ("include", "-include", "sinclude"):
        _make_include(load, line, first, cwd, model, depth)
        return None, False
    if first in ("export", "override", "private"):
        line = line[len(first):].strip()
        if not line or _MAKE_ASSIGN.match(line) is None:
            return None, False
    if (assign := _MAKE_ASSIGN.match(line)) is not None:
        name, op, value = assign.groups()
        model.vars.setdefault(name, []).append(None if op in ("+=", "!=") else value)
        if name == ".RECIPEPREFIX":
            model.problems.append(("a recipe prefix this reader does not read (D-242)", line))
        return None, False
    return _make_rule(line, model), False


def _make_include(load: Callable[[str], str | None], line: str, first: str, cwd: str, model: _Makefile,
                  depth: int) -> None:
    """An `include` read where it stands; one this cannot name or read is a problem (`-include` may be absent)."""
    for name in _make_expand(line[len(first):], model, {}).split():
        if "$" in name or PATTERN.search(name) or depth >= _MAKE_DEPTH:
            model.problems.append(("an include this reader cannot follow (D-242)", name))
        elif not _make_read(load, posixpath.normpath(posixpath.join(cwd, name)), cwd, model, depth + 1) \
                and first == "include":
            model.problems.append(("an include this reader cannot read (D-242)", name))


def _make_rule(line: str, model: _Makefile) -> list[str] | None:
    """A rule line (`a b: c d`, `a:: c`, `a: c ; recipe`): its targets, or None for a target's own variable
    (`ship: TOOL = x`, whose value is the target's, so the variable is unreadable) or a line this cannot read."""
    at = _make_split(line)
    if at < 0:
        model.problems.append(("a Makefile line this reader cannot read (D-242)", line))
        return None
    rest, semi, inline = line[at + 1:].removeprefix(":").partition(";")
    if "=" in rest:
        assigned = rest.split("=", 1)[0].rstrip(":?+!").split()
        model.vars.setdefault(assigned[-1] if assigned else "", []).append(None)
        return None
    targets = _make_expand(line[:at], model, {}).split()
    prerequisites = [p for p in _make_expand(rest.rsplit(":", 1)[-1], model, {}).split() if p != "|"]
    for target in targets:
        prereqs, recipe = model.rules.setdefault(target, ([], []))
        prereqs += prerequisites
        recipe += [inline] if semi else []
        if model.first is None and (not target.startswith(".") or "/" in target) and "%" not in target:
            model.first = target
    return targets


def _make_expand(text: str, model: _Makefile, assigns: dict[str, str | None], depth: int = 0,
                 auto: dict[str, str] | None = None) -> str:
    """`text` with each `$(NAME)`/`${NAME}` the Makefile (or `make`'s command line) defines once replaced by its
    value, expanded in turn, `$$` as `$`, and `$@`/`$<` as the target and its first prerequisite. What it cannot
    expand -- a variable defined more than once or never, a function, an automatic variable it does not know --
    stays as written, a `$` the shell would expand, so it refuses where D-239 reads it (fail closed)."""
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i] != "$" or i + 1 >= len(text):
            out.append(text[i])
            i += 1
            continue
        mark = text[i + 1]
        if mark == "$":
            out.append("$")
            i += 2
            continue
        if mark not in "({":
            out.append((auto or {}).get(mark, text[i:i + 2]))
            i += 2
            continue
        close, j, level = ")" if mark == "(" else "}", i + 2, 1
        while j < len(text) and level:
            level += 1 if text[j] == mark else -1 if text[j] == close else 0
            j += 1
        if level:
            out.append(text[i:])
            break
        name = text[i + 2:j - 1]
        values = [assigns[name]] if name in assigns else model.vars.get(name, [])
        if name == "MAKE" and not values:
            values = ["make"]
        if (re.fullmatch(r"[A-Za-z0-9_.-]+", name) and depth < _MAKE_DEPTH and len(values) == 1
                and values[0] is not None):
            out.append(_make_expand(values[0], model, assigns, depth + 1, auto))
        else:
            out.append(text[i:j])
        i = j
    return "".join(out)


class _MakeArguments:
    """`make`'s command line: its `-C` directories, its `-f` files, its targets, its variable assignments, and the
    option that gives it Makefile text (`--eval`, `-E`), which this does not read."""

    def __init__(self) -> None:
        self.dirs: list[str] = []
        self.files: list[str] = []
        self.targets: list[str] = []
        self.assigns: dict[str, str | None] = {}
        self.text: str | None = None

    def value(self, letter: str, value: str) -> None:
        """A valued option's value: a directory (`C`), a file (`f`), Makefile text (`E`), or another's."""
        if letter == "C":
            self.dirs.append(value)
        elif letter == "f":
            self.files.append(value)
        elif letter == "E":
            self.text = value


_MAKE_LONG = {"--directory": "C", "--file": "f", "--makefile": "f", "--eval": "E", "--include-dir": "I",
              "--old-file": "o", "--assume-old": "o", "--new-file": "W", "--assume-new": "W", "--what-if": "W"}


def _make_arguments(run: list[str]) -> _MakeArguments:
    """`make`'s command line, read as GNU make reads its options."""
    args = _MakeArguments()
    i = 1
    while i < len(run):
        word, i = run[i], i + 1
        name, eq, value = word.partition("=")
        if word == "--":
            continue
        if name in _MAKE_LONG:
            if not eq:
                value, i = (run[i] if i < len(run) else ""), i + 1
            args.value(_MAKE_LONG[name], value)
        elif word.startswith("--"):
            optional = name in ("--jobs", "--load-average", "--max-load") and not eq
            i += 1 if optional and i < len(run) and re.fullmatch(r"[0-9.]+", run[i]) else 0
        elif word.startswith("-") and len(word) > 1:
            i = _make_short(word, run, i, args)
        elif (assign := _ARGUMENT_ASSIGN.match(word)) is not None:
            args.assigns[assign.group(1)] = None if assign.group(2) in ("+=", "!=") else assign.group(3)
        else:
            args.targets.append(word)
    return args


def _make_short(word: str, run: list[str], i: int, args: _MakeArguments) -> int:
    """A cluster of `make`'s short options (`-sC dir`, `-j4`); returns where the next word is."""
    k = 1
    while k < len(word):
        letter, k = word[k], k + 1
        if letter in "CfIoWE":
            value = word[k:]
            if not value:
                value, i = (run[i] if i < len(run) else ""), i + 1
            args.value(letter, value)
            return i
        if letter == "O":
            return i
        while letter in "jl" and k < len(word) and (word[k].isdigit() or word[k] == "."):
            k += 1
    last = word[-1] in "jl"
    return i + 1 if last and i < len(run) and re.fullmatch(r"[0-9.]+", run[i]) else i


def _make_shapes(words: list[str], run: list[str], new: bool, where: _Where | None) -> list[tuple[str, str]]:
    """D-242 clause 3: what `make` starts, read from the Makefile it reads -- in the tree and at each protected base
    --: its targets' recipes (with none named, `.DEFAULT_GOAL` or the first target) and their prerequisites', each
    recipe line read as run text in turn. A Makefile, an include or a target this cannot read refuses."""
    word = run[0]
    prefix = words[:len(words) - len(run)]
    moved = any(w.startswith("--chd") or re.fullmatch(r"-[A-Za-z]*[CD].*", w) for w in prefix)
    if where is None or where.root is None:
        return [("a `make` whose Makefile this reader is not given (D-242)", word)]
    if where.cwd is None or moved:
        return [("a `make` run in a directory this reader cannot tell, so its Makefile cannot be read (D-242)", word)]
    if where.depth >= _MAKE_DEPTH:
        return [("a `make` nested deeper than this reader follows (D-242)", word)]
    args = _make_arguments(run)
    if args.text is not None:
        return [("a `make` given Makefile text on its command line (D-242)", args.text)]
    out = [(f"{shape} in the {what} `make` reads", value)
           for what, values in (("directory", args.dirs), ("Makefile", args.files), ("target", args.targets))
           for value in values if (shape := _unnamed_word(value))]
    cwd = posixpath.normpath(posixpath.join(where.cwd, *args.dirs))
    if out or posixpath.isabs(cwd) or cwd == ".." or cwd.startswith("../"):
        return out or [("a `make` run outside the checkout, whose Makefile this reader cannot read (D-242)", cwd)]
    key = (str(where.root), cwd, tuple(run[1:]), new)
    if key not in _MAKE_READ:
        _MAKE_READ[key] = None
        models = _make_models(where.root, cwd, args.files)
        inner = _Where(where.root, cwd, where.depth + 1)
        _MAKE_READ[key] = [found for label, model in models
                           for found in _make_model_shapes(label, model, args, new, inner)] if models else [
            ("a Makefile `make` reads that this reader cannot read (D-242)",
             ", ".join(args.files) or posixpath.join(cwd, "Makefile"))]
    return list(_MAKE_READ[key] or [])


def _make_models(root: Path, cwd: str, files: list[str]) -> list[tuple[str, _Makefile]]:
    """Each distinct copy of the Makefile(s) `make` reads in `cwd` -- the `-f` files, or the first of GNU make's
    names --, in the tree and at each protected base, as (where it was read, what was read); a copy that cannot be
    read is left out, and none at all is for the caller to refuse."""
    models: dict[str, tuple[str, _Makefile]] = {}
    for label, load in _make_sources(root):
        names = [posixpath.normpath(posixpath.join(cwd, f)) for f in files] or [
            next(name for name in [*(posixpath.normpath(posixpath.join(cwd, n)) for n in _MAKEFILE_NAMES), ""]
                 if not name or load(name) is not None)]
        model = _Makefile()
        if all(name and _make_read(load, name, cwd, model) for name in names):
            texts = "\0".join(load(name) or "" for name in names)
            models.setdefault(texts, (f"{', '.join(names)} in {label}", model))
    return list(models.values())


def _make_model_shapes(label: str, model: _Makefile, args: _MakeArguments, new: bool,
                       where: _Where) -> list[tuple[str, str]]:
    """What one copy of a Makefile starts for this command line: what it could not read, a SHELL that is not a
    POSIX shell, and each wanted target's recipe and its prerequisites', read as run text in turn."""
    out = [(f"{why}, in {label}", what) for why, what in model.problems]
    shells = [args.assigns["SHELL"]] if "SHELL" in args.assigns else model.vars.get("SHELL", [])
    for value in shells:
        program = "" if value is None else _make_expand(value, model, args.assigns).strip()
        if os.path.basename(program) not in POSIX_SHELLS:
            out.append((f"a Makefile's SHELL that is not a POSIX shell (D-242), in {label}", program or "SHELL"))
    goal = model.vars.get(".DEFAULT_GOAL", [])
    wanted = args.targets or ([_make_expand(goal[0], model, args.assigns)] if len(goal) == 1 and goal[0] is not None
                              else [model.first] if model.first else [])
    out += [] if wanted else [(f"a Makefile with no target to run (D-242), in {label}", "make")]
    out += [(f"a target this reader cannot find in the Makefile (D-242), in {label}", target)
            for target in wanted if target not in model.rules]
    seen: set[str] = set()
    todo = [(target, 0) for target in wanted if target in model.rules]
    while todo:
        target, depth = todo.pop(0)
        if target in seen or target not in model.rules:
            continue  # a prerequisite with no rule is a file
        seen.add(target)
        if depth >= _MAKE_DEPTH:
            out.append((f"a prerequisite deeper than this reader follows (D-242), in {label}", target))
            continue
        prereqs = model.rules[target][0]
        out += _make_recipe_shapes(label, model, args, target, new, where)
        todo += [(p, depth + 1) for p in prereqs]
    return out


def _make_recipe_shapes(label: str, model: _Makefile, args: _MakeArguments, target: str, new: bool,
                        where: _Where) -> list[tuple[str, str]]:
    """A target's recipe lines -- `@`, `-` and `+` taken off before and after expansion, its variables expanded --
    read as run text in turn; a `cd` in any of them leaves the directory of every one unknown."""
    prereqs, recipe = model.rules[target]
    auto = {"@": target, "<": prereqs[0] if prereqs else ""}
    lines = [re.sub(r"^[\s@+-]*", "", _make_expand(re.sub(r"^[\s@+-]*", "", line), model, args.assigns, 0, auto))
             for line in recipe]
    inner = _moved(lines, new, where)
    return [(f"{shape} (in `make {target}`'s recipe, {label})", found)
            for line in lines for shape, found in _shapes_in(line, new, inner)]


def _linked(root: Path, rel: str) -> str | None:
    """D-239 clause 2: the tree path a symlink git lists at `rel` points to, or None (not a link, or one that leaves
    the tree or points nowhere)."""
    link = root / rel
    if not link.is_symlink():
        return None
    try:
        target = link.resolve()
        inside = target.relative_to(root.resolve()).as_posix()
    except (OSError, RuntimeError, ValueError):
        return None
    return inside if target.exists() and inside != rel else None


def unnamed_starts(root: Path) -> list[str] | None:
    """#549 (D-239): each place a dispatched deploy workflow (the tree's copy and each protected base's) starts a file
    without writing its name -- a pattern, a name built at run time, a symlink to a tree file --, as `<workflow> line
    <n>: <shape> `<word>``; None when the workflows cannot all be read or git cannot list the tree (fail closed)."""
    key = str(root)
    if key not in _UNNAMED:
        texts, complete = _workflow_texts(root)
        files = _files(root)
        if not complete or files is None:
            _UNNAMED[key] = None
            return None
        found: list[str] = []
        names, runs = sorted(deploy_workflows(root, declared(root), texts)), 0
        for name in names:
            counted: set[str] = set()
            for text in dict.fromkeys(texts.get(name, [])):   # #556: an identical copy at a base adds no command
                # #570: the tree's copy is read with its line endings normalised and a base's blob is not, so a CRLF
                # workflow's copies differ; each is read for findings, but the evidence line counts a text once.
                count = (normal := text.replace("\r\n", "\n")) not in counted
                counted.add(normal)
                # #553: a run value this reader cannot place refuses (D-239, fail closed), and so does a shell's
                # startup file set under `env:` by a name it does not write.
                found += [f"{name} line {n}: a run value this reader cannot read (a flow mapping, or a quote "
                          "running past its line)" for n in _unreadable_runs(text)]
                found += [f"{name} line {n}: {shape} in the file `BASH_ENV` names `{value}`"
                          for n, value in _startup_values(text) if (shape := _unnamed_word(value))]
                # #553 review B1-B3, R2: the value is read as the reader before #553 read it and as it reads now, and
                # every start either finds is a finding -- a new reading never refuses less than the old one.
                # #551 (D-242 clause 1): a step whose shell is not a POSIX shell, its own or its runner's default.
                found += [f"{name} line {n}: {why} `{value}`" for n, why, value in _non_posix_shells(text)]
                # #551 (D-242 clause 3): `make` reads its Makefile from the checkout's top, unless a step's
                # `working-directory:` or a `cd` in the run value moved it.
                top = _Where(root, None if _WORKING_DIRECTORY.search(text) else ".")
                for new in (True, False):
                    for start, lines in _run_values(text, new):
                        at = _moved(lines, new, top)
                        for line, words, stdin in _run_commands(lines, new):
                            runs += new and count
                            found += [f"{name} line {start + line}: {shape} `{word}`"
                                      for shape, word in _unnamed_shapes(words, stdin, new, at)]
                low = text.lower().splitlines()
                for path in sorted(_workflow_names(root, text, files)):
                    if (target := _linked(root, path)) is not None:
                        where = next((n for n, line in enumerate(low, 1)
                                      if path.lower() in line or path.lower().rsplit("/", 1)[-1] in line), 0)
                        found.append(f"{name} line {where}: a symlink, `{path}`, to `{target}`")
        _UNNAMED[key] = list(dict.fromkeys(found))
        _UNNAMED_READ[key] = (names, runs)
    return _UNNAMED[key]


def verified_blob(root: Path, commit: str, rel: str) -> bytes | None:
    """The bytes of `rel` at `commit`, every object on the way hashed against its id (#444 R2; #511, #509: the one
    verified reader, `brief_fields.verified_file`). None when one does not hash, or the path is not a file there."""
    try:
        return brief_fields.verified_file(root, commit, rel)
    except RuntimeError:
        return None


def current(root: Path, rel: Path, label: str, independent: bool = False) -> tuple[str | None, str]:
    """(why the verdict at `rel` is not current, or None; the one-line summary of what was read).
    With `independent`, the verdict must also declare `**Independent:** yes`."""
    path = root / rel
    if not path.is_file():
        return f"there is no {rel.as_posix()} ({label} verdict)", f"{label}: no {rel.as_posix()}"
    text = path.read_text(encoding="utf-8", errors="replace")
    # Pass only on a verdict that SAYS pass: `**BLOCKING**`, or the template's unfilled
    # `PASS | MINOR | BLOCKING`, once read as "not BLOCKING" and let the deploy through.
    v = re.search(r"^##\s*Verdict\s*\n+\s*\W*(PASS|MINOR|BLOCKING)\b(.*)$", text, re.M)
    if not v or v.group(1) == "BLOCKING" or "|" in v.group(2):
        return f"{rel.as_posix()} has no PASS or MINOR verdict ({label})", f"{label}: {rel.as_posix()} not PASS"
    if independent and not re.search(r"^\s*\*\*Independent:\*\*\s*yes\b", text, re.M | re.I):
        return (f"{rel.as_posix()} does not declare `**Independent:** yes` ({label})",
                f"{label}: {rel.as_posix()} not independent")
    head = verdict_head(text)
    if not head:
        return (f"{rel.as_posix()} names no `**Reviewed head:** <sha>` ({label})",
                f"{label}: {rel.as_posix()} names no head")
    problem = compare_problem(root, head)
    if problem:
        return (f"the comparison with the reviewed head {head[:7]} of {rel.as_posix()} cannot be trusted ({label}): "
                f"{problem}", f"{label}: the comparison with {head[:7]} cannot be trusted")
    code = changed_since(root, head)
    if code is None:
        return (f"git cannot compare the reviewed head {head} of {rel.as_posix()} with the working tree ({label}): "
                "the sha is not in this clone's history -- a squash merge or a deleted branch dropped it "
                "(docs/branch-protection.md asks for merge commits). Run the reviewer on the delta from the "
                "default branch and record a head that is",
                f"{label}: git cannot compare {head[:7]}")
    if code:
        return (f"{len(code)} file(s) changed since the reviewed head {head[:7]} of {rel.as_posix()} ({label}): "
                f"{', '.join(code[:5])}{' ...' if len(code) > 5 else ''}",
                f"{label}: {rel.as_posix()} {v.group(1)} at {head[:7]}, {len(code)} code file(s) changed since")
    return None, f"{label}: {rel.as_posix()} {v.group(1)} at {head[:7]}, no code changed since (working tree included)"


def _redirected(root: Path) -> str | None:
    """The #505 review's M2: why the tree git reads is not the one here -- `core.worktree` names another folder, so
    every listing, and the top level this was given, is of that one --, or None."""
    try:
        named = subprocess.run(["git", "-C", str(root), "config", "--get", "core.worktree"], capture_output=True,
                               encoding="utf-8", errors="replace", timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "git cannot say whether `core.worktree` is set"
    return (f"`core.worktree` is set ({named}), so git reads another tree than the one being deployed; unset it "
            "(`git config --unset core.worktree`)") if named else None


def release_note(root: Path, target: str) -> tuple[str | None, str]:
    """A team-only build's record: a line in `docs/releases/*.md` marked `unreleased` that names a commit with
    no code changed since it -- the build going out. The newest five such lines are read, last first."""
    lines: list[tuple[str, list[str]]] = []
    for p in sorted((root / RELEASES).glob("*.md")) if (root / RELEASES).is_dir() else []:
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.search(r"\bunreleased\b", line, re.I):
                lines.append((f"{RELEASES.as_posix()}/{p.name}:{n}", SHA.findall(line)))
    for where, shas in reversed(lines[-5:]):
        for sha in shas:
            if changed_since(root, sha) == []:
                return None, f"release note: {where} names {sha[:7]} (unreleased), no code changed since"
    return (f"no line marked `unreleased` in {RELEASES.as_posix()}/ names this build -- the `{target}` target owes "
            f"one: add `- <date>, {target}, <git rev-parse --short HEAD>: <what changed> (unreleased)` to "
            f"{RELEASES.as_posix()}/unreleased.md", "release note: no unreleased line names this build")


def reviewed_since(root: Path) -> str:
    """Where the per-change question starts: the head of the newest security verdict -- PASS or MINOR, independent,
    current or not -- that HEAD descends from, so a HIGH change reviewed once is not asked again by every later
    team-only build (the Security-Reviewer's M4); else the release verdict's head; else the first commit."""
    heads = []
    for p in (root / "docs" / "reviews").glob("*-security.md") if (root / "docs" / "reviews").is_dir() else []:
        text = p.read_text(encoding="utf-8", errors="replace")
        v, head = VERDICT.search(text), verdict_head(text)
        if v and v.group(1) != "BLOCKING" and "|" not in v.group(2) and INDEPENDENT.search(text) and head \
                and not REVIEWED_PATCH.search(text) \
                and _git(root, "merge-base", "--is-ancestor", head, "HEAD").returncode == 0:
            count = _git(root, "rev-list", "--count", f"{head}..HEAD").stdout.decode().strip()
            heads.append((int(count) if count.isdigit() else 1 << 30, head))
    if heads:
        return min(heads)[1]
    release = verdict_head((root / SECURITY).read_text(encoding="utf-8", errors="replace")) \
        if (root / SECURITY).is_file() else None
    if release and not _git(root, "rev-parse", "-q", "--verify", f"{release}^{{commit}}").returncode:
        return release
    firsts = _git(root, "rev-list", "--max-parents=0", "HEAD").stdout.decode().split()
    return firsts[-1] if firsts else "HEAD"


def per_change_security(root: Path, target: str) -> tuple[str | None, str]:
    """Harvest Q1(b): an `internal` or `staging` target owes "the per-change verdicts `make review-need` asked
    for" -- no release security delta. Over what no security verdict has read yet (`reviewed_since`), when
    review-need asks for security, one `docs/reviews/*-security.md` must be current for this tree. Its run is
    isolated and writes no bytecode (`-I -B`): this gate reads the tree it would write into."""
    rng = f"{reviewed_since(root)[:12]}..HEAD"
    try:
        r = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve().parent / "review_need.py"),
                            "--range", rng], cwd=root, capture_output=True, encoding="utf-8", errors="replace",
                           timeout=60)
        last = (r.stdout.strip().splitlines() or [""])[-1]
        answer = last.split(":", 1)[1].strip() if r.returncode == 0 and last.startswith("review-need:") else None
        failed = f"exit {r.returncode}: {(last or r.stderr.strip()[-120:] or 'no output')[:120]}"
    except (OSError, subprocess.SubprocessError) as error:
        answer, failed = None, f"{type(error).__name__}: {error}"
    if answer is None:
        return (f"review-need could not answer over {rng} ({failed}) -- an `{target}` target owes the per-change "
                "security verdict it asks for, so mend scripts/review_need.py and ask again",
                "security (per change): review-need could not answer")
    if "security" not in answer:
        return None, f"security: not asked of a `{target}` target -- review-need over {rng} asks none"
    for p in sorted((root / "docs" / "reviews").glob("*-security.md")):
        if REVIEWED_PATCH.search(p.read_text(encoding="utf-8", errors="replace")):
            continue
        why, summary = current(root, Path("docs/reviews") / p.name, "security (per change)", independent=True)
        if why is None:
            return None, summary
    return (f"review-need over {rng} asks for security (a declared HIGH path or a named security-invariant test "
            "changed) and no docs/reviews/*-security.md is current for this tree -- the Security-Reviewer on that "
            "range, its verdict with `**Reviewed head:**`", "security (per change): none current, review-need asks it")


def _release_security(root: Path, heavy: bool) -> tuple[str | None, str]:
    """The release security verdict; in heavy mode (`heavy`: every brief read says heavy) a current
    `m<N>-security.md` of the latest milestone stands for it (v7.2)."""
    security = current(root, SECURITY, "security")
    # A BLOCKING release verdict is a finding nobody fixed: no milestone verdict stands over it.
    blocking = "has no PASS or MINOR verdict" in (security[0] or "") and (root / SECURITY).is_file()
    if security[0] and not blocking and heavy:
        milestone = latest_milestone(root, MILESTONE_SECURITY)
        if milestone is not None:
            alternative = current(root, milestone, "security (heavy mode: the milestone's)", independent=True)
            security = alternative if alternative[0] is None else (
                f"{security[0]}; and the latest milestone verdict does not stand for it: {alternative[0]}",
                security[1])
    return security


def verdicts(root: Path, target: str = "production") -> list[tuple[str | None, str]]:
    """The policy's base, then security, then the Tester, then a team-only target's release note: each (why not
    current | None, summary line). In heavy mode a current `m<N>-security.md` of the latest milestone stands for
    `release-security.md` (v7.2); model_ranking (#283) reads the mode at the protected base as well as in the
    tree, and lets the milestone verdict stand only when neither says light. An `internal` or `staging` target
    owes no release security delta, only the per-change one review-need asks for (harvest Q1, v7.3)."""
    policies, where, _ = _policy(root)
    out: list[tuple[str | None, str]] = []
    redirected = _redirected(root)
    if redirected:
        out.append((redirected, "worktree: redirected"))
    modes = [mode(root)]
    if policies is None:
        out.append((f"the brief's policy fields cannot be read at the protected base ({where}); a deploy is "
                    "judged by the base's brief, never by the change's (#283)", f"policy: unreadable ({where})"))
    else:
        modes = list(dict.fromkeys([*(mode(p) for p in policies), *modes]))
        out.append((None, f"policy: {where}, working mode {modes[0]}"
                          + (f"; the bases and the tree's brief also say {', '.join(modes[1:])}, so each mode's Tester "
                             "verdict" if len(modes) > 1 else "")))
    unnamed = unnamed_starts(root)
    if unnamed is None:
        out.append(("the dispatched deploy workflows cannot all be read, or git cannot list the tree, so whether one "
                    "starts a file without writing its name cannot be told (#549, D-239)",
                    "workflows: cannot be read for a file started without its name"))
    elif unnamed:
        out.append((f"a dispatched deploy workflow starts a file without writing its name (#549, D-239): "
                    f"{'; '.join(unnamed[:5])}{' ...' if len(unnamed) > 5 else ''}; write the file's name there "
                    "instead (a symlink's: its target's), so the file it starts is on the deploy surface",
                    f"workflows: {len(unnamed)} start(s) of a file without its name"))
    else:
        # #556: a PASS names what D-239's check read, so it is evidence and not a silence.
        # The #556 security review: M1, a dispatched name no copy answers to was printed as "read"; R2, a missing
        # record of the read stated "no dispatched deploy workflow" as a fact.
        reading = _UNNAMED_READ.get(str(root))
        if reading is None:
            summary = "workflows: no start of a file without its name (D-239); what was read is not recorded"
        else:
            names, runs = reading
            texts, _ = _workflow_texts(root)
            read, absent = [n for n in names if texts.get(n)], [n for n in names if not texts.get(n)]
            summary = (f"workflows: {', '.join(read)} read, {runs} run command(s)" if read else
                       "workflows: no dispatched deploy workflow read") + (
                f"; dispatched with no copy to read: {', '.join(absent)}" if absent else "") + (
                ", no start of a file without its name (D-239)")
        out.append((None, summary))
    out.append(per_change_security(root, target) if target in TEAM_ONLY
               else _release_security(root, policies is not None and "light" not in modes))
    for working_mode in modes:
        tester, label = tester_path(root, working_mode)
        if tester is None:
            out.append((f"there is no milestone Tester verdict (docs/reviews/m<N>-tester.md) in this tree ({label})",
                        f"{label}: no docs/reviews/m<N>-tester.md"))
        else:
            out.append(current(root, tester, label, independent=True))
    if target in TEAM_ONLY:
        out.append(release_note(root, target))
    return out


# --- matching -------------------------------------------------------------------------------------------

def _note(text: str) -> None:
    if text not in NOTES:
        NOTES.append(text)


def _target_entries(root: Path) -> list[tuple[str, str]]:
    """(the text of each deploy command the tree's or a protected base's brief declares, its class), as
    `declared_targets` reads them, before they are split into words."""
    policies, _, _ = _policy(root)
    briefs = [root, *(policies or [])]
    entries: list[tuple[str, str]] = [(text, "production") for brief in briefs
                                      for text in listing("Deploy commands", brief)]
    for text in [text for brief in briefs for text in listing("Deploy targets", brief)]:
        name, colon, command = text.partition(":")
        target = name.strip().lower()
        if colon and target in CLASSES:
            if target in TEAM_ONLY and not (policies and all(text in listing("Deploy targets", p) for p in policies)):
                _note(f"the deploy target {text!r} is not declared at every protected base, so it is guarded as "
                      "production until a merge puts it there (#283)")
                target = "production"
            entries.append((command, target))
            continue
        _note(f"the brief's deploy target {text!r} names no class ({', '.join(CLASSES)}); it is guarded as "
              "production")
        entries += [(text, "production")] + ([(command, "production")] if colon else [])
    return list(dict.fromkeys(entries))


def declared_targets(root: Path) -> list[tuple[list[str], str]]:
    """The deploy commands the protected base's brief or the tree's declares (#283), each as (lower-cased words,
    its target class): `Deploy commands:` are production; a `Deploy targets:` entry is `<class>: <command>`, and one
    whose class is not in CLASSES is production, read whole and after its first colon, loudly (v7.3). A team-only
    entry is that class only when every protected base's brief holds it too: one the change under evaluation adds
    is production, so no change lowers what a deploy owes (model_ranking, #283). One the shell cannot split is
    skipped loudly: a declaration nobody can match is not a declaration."""
    entries = _target_entries(root)
    out: list[tuple[list[str], str]] = []
    for text, target in entries:
        try:
            words = [w.lower() for w in shlex.split(text)]
        except ValueError:
            _note(f"the brief's deploy command {text!r} cannot be split as the shell would; it is not matched")
            continue
        if words and (words, target) not in out:
            out.append((words, target))
    return out


def declared(root: Path) -> list[list[str]]:
    """The words of every deploy command `declared_targets` reads, whatever its class: each one's files and
    workflows are on the deploy surface (#444, #501), and each one's workflow a deploy workflow (#390)."""
    out: list[list[str]] = []
    for words, _ in declared_targets(root):
        if words not in out:
            out.append(words)
    return out


def _program_position(words: list[str]) -> list[str]:
    """Past assignments and the wrappers in WRAPPERS, each with its own options and (for `timeout`
    and `nice`) its one value."""
    i = 0
    while i < len(words) and ASSIGNMENT.match(words[i]):
        i += 1
    while i < len(words) and os.path.basename(words[i]) in WRAPPERS:
        name = os.path.basename(words[i])
        i += 1
        valued = WRAPPER_VALUED.get(name, WRAPPER_VALUED_DEFAULT)
        while i < len(words) and (words[i].startswith("-") or ASSIGNMENT.match(words[i])):
            if words[i] == "--":
                i += 1
                break
            if words[i] in valued and i + 1 < len(words):
                i += 1
            i += 1
        # #553 M2: `timeout`'s duration comes after its options (`timeout -k 5 60 cmd`)
        if name in ("timeout", "gtimeout") and i < len(words):
            i += 1
    return words[i:]


def _split(words: list[str]) -> list[str]:
    """`--opt=value` and `-o=value` as the option followed by its value: `fly deploy -a=prod-app` is
    `fly deploy -a prod-app` (the Code-Reviewer's M8 on this package)."""
    out: list[str] = []
    for w in words:
        m = re.match(r"^(-{1,2}[^-=\s][^=\s]*)=(.*)$", w)
        out += [m.group(1), m.group(2)] if m else [w]
    return out


def _unread(words: list[str]) -> bool:
    """A word holding an expansion the Bash guard left unread (`$p`, `$(...)`, a backtick): it may be any option."""
    return any("$" in w or "`" in w for w in words)


def matches(words: list[str], declared_words: list[str], any_order: bool = False) -> bool:
    """Whether the declared command is the command these words run, both read through `_split`. With
    `any_order` (a production or external-test declaration, v7.3) every declared word after the program need
    only appear among the command's words: `vercel deploy --prod` is `vercel --prod deploy` and
    `vercel deploy --prebuilt --prod` (the Security-Reviewer's B1 on this package). There a word left unread may
    stand for every missing option and its value, so `p=--prod; netlify deploy $p` is production (run v73 M1)."""
    words = _program_position(words)
    if not words or not declared_words:
        return False
    if os.path.basename(words[0]).lower() != os.path.basename(declared_words[0]):
        return False
    raw, want = [w.lower() for w in words[1:]], _split(declared_words[1:])
    if any_order:
        missing = [i for i, d in enumerate(want) if d not in _split(raw)]
        return not missing or (_unread(raw) and all(want[i].startswith("-") or (i and want[i - 1].startswith("-"))
                                                    for i in missing))
    if not any(d.startswith("-") for d in want):
        # A declaration with no option drops each option word whole, `--opt=value` with its value, before any
        # split (the Security-Reviewer's M6, round 3): `npm --loglevel=warn run deploy:staging` stays that deploy.
        return [w for w in raw if not w.startswith("-")][:len(want)] == want
    return _split(raw)[:len(want)] == want


def _declared_hit(commands: list[list[str]], decl: list[tuple[list[str], str]]) -> tuple[str, str] | None:
    """v7.3: (the declared deploy command these word lists run, its class), or None. For each command a declaration
    of a class only the team runs decides only when it refines every production or external-test declaration the
    command also matches -- it holds all of their words and more, as `fly deploy -c fly.staging.toml` holds
    `fly deploy` and `netlify deploy --dir dist` does not hold `netlify deploy --prod` (the Security-Reviewer's B1,
    round 2); otherwise, a tie included, the stricter class decides. Of those left, the one with the most words.
    Across the commands of one call, one that real users run makes the call theirs."""
    found = []
    for words in commands:
        hits = [(d, t) for d, t in decl if matches(words, d, any_order=t not in TEAM_ONLY)]
        strict = [d for d, t in hits if t not in TEAM_ONLY]
        # An unread word may undo what refines (`fly deploy -c fly.staging.toml $X`): the strictest class decides --
        # when a stricter one matched at all; a program declared for staging only stays that deploy (re-verification M4).
        refining = [] if strict and _unread(_program_position(words)[1:]) else [
            (d, t) for d, t in hits if t in TEAM_ONLY and all(set(_split(p[1:])) < set(_split(d[1:])) for p in strict)]
        pool = refining or [(d, t) for d, t in hits if t not in TEAM_ONLY]
        if pool:
            d, t = max(pool, key=lambda hit: len(_split(hit[0])))
            found.append((t not in TEAM_ONLY, len(_split(d)), " ".join(d), t))
    if not found:
        return None
    best = max(found)
    return best[2], best[3]


def deploy_in(commands: list[list[str]], root: Path) -> str | None:
    """The declared deploy command one of these word lists runs, or the `gh` command among them that starts a
    deploy workflow (#390), or None (`deploy_target` without the class)."""
    found = deploy_target(commands, root)
    return found[0] if found else None


def deploy_target(commands: list[list[str]], root: Path) -> tuple[str, str] | None:
    """(what `deploy_in` names, its target class), or None. A `gh` command that starts a deploy workflow is
    production, and makes a call that also runs a team-only deploy production too."""
    _, where, unverified = _policy(root)
    if unverified and commands:
        # #509: the base's brief is what says which commands deploy, and its bytes are not the base's. Which of
        # these deploys cannot be told, so each is judged as one, and the verdicts refuse it (policy unreadable).
        return (f"{' '.join(commands[0])} (any command: {where}; until the base's objects are whole again -- in "
                "your own terminal, `git fetch origin` then `git fsck --full`)", "production")
    targets = declared_targets(root)
    hit = _declared_hit(commands, targets)
    if hit and hit[1] not in TEAM_ONLY:
        return hit
    decl = declared(root)
    starts = [(words, start) for words in commands if (start := gh_dispatch(words)) is not None]
    if not starts:
        return hit
    texts, complete = _workflow_texts(root)
    workflows = deploy_workflows(root, decl, texts)
    deploys = {name for known in workflows.values() for name in known}
    # A workflow word no file read here is known by is one this cannot name (round 1's M2): it may be a
    # workflow the default branch has and this tree does not, or one a wrapper rewrites.
    known = deploys | {name for file, versions in texts.items() for name in _names(file, versions)}
    for words, start in starts:
        start = {s if s in known else UNKNOWN for s in start}
        if not complete or (workflows and (UNKNOWN in start or start & deploys)):
            what = ("a workflow, and a workflow file at the protected base could not be read" if not complete else
                    "a workflow it does not name" if UNKNOWN in start else "a deploy workflow")
            return (f"{' '.join(_program_position(words))} (it starts {what}; "
                    f"{', '.join(sorted(workflows)) or 'which workflow deploys is not known'} deploys)", "production")
    return hit


# --- gh: what a command starts (#390) -------------------------------------------------------------------

#: A workflow a dispatch starts that its words do not name: an id, an expansion, a pattern, none given, a rerun,
#: an alias or an extension.
UNKNOWN = "\0unknown"
#: Flags of the `gh` commands read here that take a value, so a value is never read as the workflow.
GH_VALUED = {"-R", "--repo", "--hostname", "-r", "--ref", "-f", "--raw-field", "-F", "--field", "-X", "--method",
             "-H", "--header", "--input", "-q", "--jq", "-t", "--template", "-p", "--preview", "--cache", "-j",
             "--job"}
#: gh's own top-level commands and help topics, as `gh help` lists them in gh 2.100.0 (2026-09-03). A NAMED
#: ENUMERATION, kept by hand for a written reason (AGENTS.md section 3.5): the gate runs on every Bash call with
#: no network and cannot ask gh, and whatever is not here is an alias or an extension, whose expansion lives in
#: the user's gh config, out of this gate's sight (round 1's M3). Such a command is UNKNOWN, so a command a newer
#: gh adds is refused while a deploy workflow exists and the verdicts are stale, never allowed. `co` is a default
#: alias, which the user may have redefined, and is left out on purpose.
GH_COMMANDS = frozenset({
    "agent-task", "alias", "api", "attestation", "auth", "browse", "cache", "codespace", "completion", "config",
    "copilot", "discussion", "extension", "gist", "gpg-key", "help", "issue", "label", "licenses", "org", "pr",
    "preview", "project", "release", "repo", "ruleset", "run", "search", "secret", "skill", "ssh-key", "status",
    "variable", "version", "workflow",
    "accessibility", "actions", "environment", "exit-codes", "formatting", "mintty", "reference", "telemetry",
})
#: Where workflow files live: the installed ones, and the proposals the owner copies there (D-217 clause 7).
WORKFLOW_DIRS = (".github/workflows", "scripts/ci")
#: Read on the decoded endpoint, so `.github%2Fworkflows%2Fx.yml` -- a path GitHub accepts -- is one segment.
DISPATCH = re.compile(r"/actions/workflows/(.+?)/dispatches(?:$|[/?#])")
RERUN = re.compile(r"/actions/(?:runs|jobs)/[^/?#]+/rerun")
REPOSITORY_DISPATCH = re.compile(r"(?:^|/)repos/[^/]+/[^/]+/dispatches(?:$|[/?#])")
#: What the Bash guard leaves in a word it cannot read: a parameter, a substitution (written `$(...)`), a backtick.
UNREAD = re.compile(r"[$`]")
#: What the shell, `find -exec` or `xargs -I` may rewrite: a pattern or a brace.
REWRITTEN = re.compile(r"[*?\[\]{}]")
#: A workflow's top-level `name:`, which `gh workflow run` takes as well as the file: quoted, or plain up to a
#: comment.
WORKFLOW_NAME = re.compile(r"""^name:[ \t]*(?:"((?:[^"\\]|\\.)*)"|'((?:[^']|'')*)'|([^\n]*?))[ \t]*(?:#[^\n]*)?$""",
                           re.M)
#: `flyctl` is `fly` (the guard holds both names, D-185): a workflow that runs either runs the declared deploy.
SAME_PROGRAM = {"flyctl": "fly"}


def _gh_positionals(words: list[str]) -> list[str]:
    """The words of a `gh` command (its program word left off) that are neither options nor an option's value."""
    out: list[str] = []
    i = 0
    while i < len(words):
        w = words[i]
        if w == "--":
            return out + words[i + 1:]
        if w.startswith("-") and len(w) > 1:
            i += 2 if ("=" not in w and w in GH_VALUED) else 1
            continue
        out.append(w)
        i += 1
    return out


def _unread_leading_option(words: list[str]) -> bool:
    """Whether an option before gh's command word is one this does not read: not a flag in GH_VALUED (with its
    value), and not help or version."""
    i = 0
    while i < len(words) and words[i].startswith("-") and words[i] != "--" and len(words[i]) > 1:
        name, eq, _ = words[i].partition("=")
        if name in ("-h", "--help", "--version"):
            i += 1
        elif name in GH_VALUED:
            i += 1 if eq else 2
        else:
            return True
    return False


def _workflow_of(word: str) -> str:
    """A workflow word as gh reads it -- a file, a path to one, or a name -- lower-cased; UNKNOWN for an id, a word
    the guard could not read, or one the shell or a wrapper rewrites."""
    if UNREAD.search(word) or REWRITTEN.search(word) or word.strip().isdigit() or not word.strip():
        return UNKNOWN
    return os.path.basename(word.strip().rstrip("/")).lower() or UNKNOWN


def gh_dispatch(words: list[str]) -> set[str] | None:
    """The workflows a `gh` command may start (lower-cased; UNKNOWN among them when its words do not say which),
    or None when it starts none."""
    words = _program_position(words)
    if not words or os.path.basename(words[0]).lower() != "gh":
        return None
    given = _gh_positionals(words[1:])
    pos = [w.lower() for w in given]
    if not pos:
        return None
    # An alias or an extension runs what the user's gh config says, and a definition can be invoked later,
    # unjudged: the invocation is what is judged, and this cannot read it (round 1's M3). gh resolves the command
    # word case-sensitively (`gh Api` may be an alias: round 2's M7), so it is compared as written. An option
    # before it that this does not read may take the next word as its value in gh, so the command gh runs is
    # not the one read here (`gh -z workflow zz` ran the alias `zz`: round 2's M8). `gh extension exec` runs an
    # extension (round 2's M9).
    if (given[0] not in GH_COMMANDS or _unread_leading_option(words[1:])
            or (pos[0] == "alias" and pos[1:2] in (["set"], ["import"]))
            or (pos[0] == "extension" and pos[1:2] == ["exec"])):
        return {UNKNOWN}
    if pos[:2] == ["workflow", "run"]:
        return {_workflow_of(w) for w in pos[2:]} or {UNKNOWN}
    if pos[:2] == ["run", "rerun"]:
        return {UNKNOWN}
    if pos[0] == "api":
        return _gh_api(pos[1:])
    return None


def _gh_api(endpoints: list[str]) -> set[str] | None:
    """What `gh api` starts on these endpoints (lower-cased): a workflow's dispatch, a rerun, a repository
    dispatch."""
    for endpoint in endpoints:
        text = unquote(endpoint)
        if (m := DISPATCH.search(text)):
            return {_workflow_of(m.group(1))}
        if RERUN.search(text) or REPOSITORY_DISPATCH.search(text):
            return {UNKNOWN}
        # An endpoint's tail names it: an expansion there, or one beside a dispatch, may be a dispatch.
        if UNREAD.search(endpoint) and (re.search(r"[$`)][^/]*$", endpoint) or re.search(r"dispatch|rerun", text)):
            return {UNKNOWN}
    return None


def _workflow_texts(root: Path) -> tuple[dict[str, list[str]], bool]:
    """(every workflow file's text by its lower-cased file name -- the tree's, and the protected base's, since a
    dispatch runs the default branch's copy --; whether every file at the base could be read). A file git cannot
    list or show there is not skipped quietly (round 1's N1): the rest are still read, and the read is incomplete,
    which makes every dispatch a deploy. No base at all adds nothing: the verdicts refuse every deploy then (#283)."""
    out: dict[str, list[str]] = {}
    for d in WORKFLOW_DIRS:
        folder = root / d
        for p in sorted(folder.iterdir()) if folder.is_dir() else []:
            if p.suffix in (".yml", ".yaml") and p.is_file():
                out.setdefault(p.name.lower(), []).append(p.read_text(encoding="utf-8", errors="replace"))
    bases = protected_bases(root)
    complete = True
    for base, place in ((base, place) for base in bases for place in WORKFLOW_DIRS):  # #517: the tip's copies too
        try:
            # #509: each file verified against the ids git names it by, as `git show` never checked.
            files, failed = brief_fields.verified_files(root, base, place, (".yml", ".yaml"))
        except RuntimeError:
            complete = False
            continue
        complete = complete and not failed
        for path, body in sorted(files.items()):
            out.setdefault(os.path.basename(path).lower(), []).append(body.decode("utf-8", "replace"))
    return out, complete


def _runs_deploy(text: str, decl: list[list[str]]) -> bool:
    """Whether a line of a workflow file runs a declared deploy command: a `run:` value, or a line of its block,
    with a `\\` continuation joined. Read wide on purpose: a line that only looks like one makes the workflow a
    deploy, which refuses more."""
    for words in _line_commands(text):
        at = len(words) - len(_program_position(words))
        if at < len(words):
            program = os.path.basename(words[at]).lower()
            words = [*words[:at], SAME_PROGRAM.get(program, words[at]), *words[at + 1:]]
        if any(matches(words, d, any_order=True) for d in decl):
            return True
    return False


def _names(file: str, versions: list[str]) -> set[str]:
    """Every name gh knows a workflow file by: the file, its stem, and the `name:` of each copy read."""
    known = {file, re.sub(r"\.ya?ml$", "", file)}
    for text in versions:
        known |= {next(g for g in m.groups() if g is not None).strip().lower() for m in WORKFLOW_NAME.finditer(text)}
    return known - {""}


def deploy_workflows(root: Path, decl: list[list[str]],
                     texts: dict[str, list[str]] | None = None) -> dict[str, set[str]]:
    """Each deploy workflow's file name, with every name gh knows it by: the file, its stem, its `name:`."""
    texts = _workflow_texts(root)[0] if texts is None else texts
    dispatched = {name for d in decl for name in (gh_dispatch(d) or set()) if name != UNKNOWN}
    # #494 M1: a dispatch may name a workflow by its stem or its `name:`; each file it names is a deploy workflow,
    # and a name no file read here answers to stays, as written.
    files = {file for file, versions in texts.items() if dispatched & _names(file, versions)}
    files |= dispatched - {name for file, versions in texts.items() for name in _names(file, versions)}
    files |= {name for name, versions in texts.items() if any(_runs_deploy(t, decl) for t in versions)}
    return {name: _names(name, texts.get(name, [])) for name in files}


def split_line(text: str) -> list[list[str]]:
    """A single command line as simple commands, for the by-hand form: the Bash guard is the reader of
    record (here-documents, substitutions, quoting in full); this splits one line at `;`, `&&`, `||`,
    `|`, `&`, `(`, `)` and newlines, with quotes removed. An unbalanced quote is refused, not guessed."""
    out: list[list[str]] = []
    for line in text.splitlines():
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        cur: list[str] = []
        for token in lexer:  # ValueError on an unclosed quote reaches the caller
            if token and all(ch in ";&|()<>" for ch in token):
                if cur:
                    out.append(cur)
                cur = []
            else:
                cur.append(token)
        if cur:
            out.append(cur)
    return out


# --- the entry points -----------------------------------------------------------------------------------

def toplevel(cwd: Path) -> Path | None:
    try:
        r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], capture_output=True,
                           encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    top = r.stdout.strip() if r.returncode == 0 else ""
    return Path(top) if top else None


def judge(commands: list[list[str]], root: Path, foreign: bool = False, caller_git: tuple[str, ...] = ()) -> int:
    try:
        return _judge(commands, root, foreign, caller_git)
    finally:
        for note in NOTES:
            print(f"deploy gate: {note}", file=sys.stderr)


def _judge(commands: list[list[str]], root: Path, foreign: bool, caller_git: tuple[str, ...]) -> int:
    found = deploy_target(commands, root)
    if not found:
        return 0
    hit, target = found
    if foreign:  # its verdicts are that repository's word, not this project's: they are not read
        print(f"BLOCKED: deploy gate -- `{hit}` is a deploy declared in {root}, which is not this session's "
              "project: the Bash guard judges no other repository's deploys. Deploy it from a session started "
              "in that repository.", file=sys.stderr)
        return 2
    to = "" if target == "production" else f" to a `{target}` target"
    for why, summary in verdicts(root, target):
        if why:
            return refuse(f"`{hit}` is a deploy{to}, and {why}",
                          "" if summary.startswith("release note") else HOW_TO_CLOSE)
    if (why := _git_variables(caller_git)):
        return refuse(f"`{hit}` is a deploy{to}, and {why}")
    return 0


def check(root: Path, caller_git: tuple[str, ...] = (), target: str = "production", named: bool = False) -> int:
    print(f"deploy-check: tree {root} (working tree, nested checkouts excluded)"
          + (f", target class `{target}`" if named else ""))
    bad: list[tuple[str, str]] = []
    for why, summary in verdicts(root, target):
        print(f"deploy-check: {summary}")
        if why:
            bad.append((why, summary))
    if (why := _git_variables(caller_git)):
        bad.append((why, "environment: GIT_* set"))
    for note in NOTES:
        print(f"deploy-check: note: {note}")
    if bad:
        for why, _ in bad:
            print(f"deploy-check FAIL: {why}")
        if any(not summary.startswith("release note") for _, summary in bad):
            print(f"  {HOW_TO_CLOSE}")
        return 1
    if target in TEAM_ONLY:
        print(f"deploy-check PASS: the milestone Tester's verdict, the per-change security review-need asks for and "
              f"an unreleased release-note line are current for this tree (`{target}`)")
    else:
        print("deploy-check PASS: the security verdict and the milestone Tester's verdict are current for this tree")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--judge"]:
        root = Path.cwd()  # the guard runs this in the repository it resolved from the call's directory
        try:
            payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
            commands = payload["commands"]
            if not isinstance(commands, list) or not all(
                    isinstance(c, list) and all(isinstance(w, str) for w in c) for c in commands):
                raise ValueError("commands is not a list of word lists")
            foreign = payload.get("foreign", False)
            if not isinstance(foreign, bool):
                raise ValueError("foreign is not true or false")
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            return refuse(f"the guard's payload cannot be read ({type(error).__name__}: {error})")
        return judge(commands, root, foreign, CALLER_GIT)
    cwd = Path.cwd()
    root = toplevel(cwd)
    if argv[:1] == ["--check"] and (len(argv) == 1 or (len(argv) == 3 and argv[1] == "--target")):
        target = argv[2].strip().lower() if len(argv) == 3 else "production"
        if target not in CLASSES:
            print(f"deploy-check CANNOT RUN: TARGET={argv[2]} is not a target class -- {', '.join(CLASSES)}")
            return 2
        if root is None:
            print(f"deploy-check FAIL: {cwd} is not inside a git work tree, so nothing can be compared")
            return 1
        return check(root, CALLER_GIT, target, named=len(argv) == 3)
    if len(argv) != 1 or argv[0].startswith("--"):
        print('usage: deploy_gate.py "<command>" | --judge | --check [--target <class>]', file=sys.stderr)
        return 2
    try:
        commands = split_line(argv[0])
    except ValueError as error:
        return refuse(f"the command cannot be split as the shell would ({error})")
    return judge(commands, root or cwd, caller_git=CALLER_GIT)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
