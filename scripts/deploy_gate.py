#!/usr/bin/env python3
"""The deploy gate: nothing deploys that no security review and no milestone Tester has seen.

Three ways in, one question -- is the release verdict current for THIS tree?

    python3 scripts/deploy_gate.py --judge          # the Bash guard: program words as JSON on stdin
    python3 scripts/deploy_gate.py "<command>"      # by hand: one command line
    python3 scripts/deploy_gate.py --check          # `make deploy-check`: no command, the verdicts only

The Bash guard (`.claude/hooks/bash_guard.py`) lexes every Bash tool call into simple commands and hands
this script, with `--judge`, the words of each one in program position: `{"commands": [["fly",
"deploy", "--remote-only"], ...]}` -- only when this file carries the line `JUDGE_PROTOCOL = <n>` (below),
so an older gate is refused rather than asked a question it would answer with exit 0. A command is a deploy when one the brief lists as `Deploy commands:`
(`docs/project-brief.md`; `/setup-project` asks for them; none listed, nothing is a deploy) matches it
word for word from the first word: the program by its basename (`/usr/local/bin/fly` is `fly`), the
rest exactly, all case-insensitive, with the invoked command's own options ignored unless the declared
command carries options itself (`fly deploy` matches `fly --verbose deploy` and `fly deploy -a app`;
`./deploy.sh --prod` matches `./deploy.sh --prod` only). A commit message, an echo or a heredoc that
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
to ship must be the code that was reviewed. What is code is one function, `is_deploy_record`: records
are `docs/` and `*.md` anywhere else; everything under `.claude/`, `.githooks/`, `scripts/`,
`conformance/`, `.github/` and the `Makefile` IS code whatever its extension, because a reviewer
profile, a skill, a hook or a gate changes what ships and what guards it. A nested checkout (a
worktree under `.claude/worktrees/`, which git lists as `dir/`) is another tree's business. What git cannot see -- a gitignored config file -- no
git-based check can see either; `/going-live` reads the brief's declared runtime config files by hand.

A delta review closes a stale verdict: the reviewer reads `<reviewed head>..HEAD` and writes the new
head into the same file.

THE BRIEF'S POLICY IS THE BASE'S (AGENTS.md section 5, base-pinned policy; #283). `Working mode:` (which
Tester verdict) and `Deploy commands:` are read from the brief at the protected base -- the merge-base of
HEAD with the default branch (`brief_fields.protected_base`) -- not from the tree about to ship:
  * a deploy is any command the base's brief OR the tree's declares, so a change can add a deploy command
    but cannot remove one;
  * the Tester verdict is the one the base's mode names; when the tree's brief names the other mode, the
    verdicts of both are required, so a change of mode moves no deploy to the verdict it prefers;
  * a base git cannot read refuses every declared deploy, and `--check` fails: a policy read from nowhere
    is not the change's own. Matching still reads the tree's brief then, so a non-deploy is never refused.

`--check` prints one line per verdict (security, tester) so the closure checklist and `/going-live`
can paste them, then `deploy-check PASS` or `deploy-check FAIL: <why>`.

WHY. Three field projects, four real deploys in two weeks: three were run by the owner outside any
command guard and two of those had no current security verdict; one went through the guard and
passed correctly. The guard's eleven refusals were all on text that mentioned a deploy command. The
owner's deploys needed a question the guard cannot ask from a terminal: `make deploy-check` is that
question. Exit 0 not a deploy, or current · 1 `--check` found a verdict not current · 2 a deploy
refused, or this could not run.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

# No bytecode: a `__pycache__` written beside the gate would itself read as a code change in a tree
# that does not ignore it, and the tree about to ship is what this compares.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brief_fields import listing, mode, protected_base, root_at  # noqa: E402

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
#: Words that run the command after them, skipped with their own options to reach the program.
WRAPPERS = {"env", "command", "builtin", "time", "exec", "nohup", "nice", "sudo", "doas", "timeout",
            "gtimeout", "caffeinate", "noglob", "nocorrect", "stdbuf", "setsid", "unbuffer", "chronic", "ionice"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\+?=")
HOW_TO_CLOSE = ("Run the reviewer on the delta (the Security-Reviewer, .claude/agents/Security-Reviewer.md; "
                "the Tester, .claude/agents/Tester.md) and record its head in the verdict file, then deploy.")


def refuse(why: str) -> int:
    print(f"BLOCKED: deploy gate -- {why}. {HOW_TO_CLOSE}", file=sys.stderr)
    return 2


# --- the verdicts --------------------------------------------------------------------------------------

def is_deploy_record(path: str) -> bool:
    """Whether a repository-relative path (POSIX, as `git diff --name-only` prints it) is a RECORD the
    deploy gate ignores, as opposed to CODE that must have been reviewed. A record is anything under
    `docs/` and any `.md` file -- except under `.claude/`, `.githooks/`, `scripts/`, `conformance/`,
    `.github/` or the `Makefile` itself, which are code whatever their extension. The one place this
    classification lives; `closure_check.py` reads the same rule."""
    if path in CODE_FILES or path.startswith(CODE_DIRS):
        return False
    # `.gp/installed` is the install's measurement (`make install` writes it), not the product.
    return path.startswith("docs/") or path.endswith(".md") or path == ".gp/installed"


def latest_milestone(root: Path, pattern: re.Pattern) -> Path | None:
    """The highest-numbered `docs/reviews/m<N>-...` verdict the pattern names, or None."""
    reviews = root / "docs" / "reviews"
    found = [(int(m.group(1)), Path("docs/reviews") / p.name) for p in (reviews.iterdir() if reviews.is_dir() else [])
             if (m := pattern.match(p.name))]
    return max(found)[1] if found else None


def policy_root(root: Path) -> tuple[Path | None, str]:
    """(a root holding the brief as the protected base of the repository at `root` holds it, or None when
    that base cannot be read; the line that says which)."""
    base = protected_base(root)
    if base is None:
        return None, ("no merge-base of HEAD with a default branch (origin/HEAD, origin/main, origin/master, "
                      "main, master)")
    try:
        return root_at(base, root), f"the brief at {base[:12]}, the merge-base of HEAD with the default branch"
    except RuntimeError as error:
        return None, str(error)


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


def changed_since(root: Path, head: str) -> list[str] | None:
    """Every code path that differs from `head` in the working tree of `root`, or None when git cannot
    compare. Committed, uncommitted and untracked alike; nested checkouts (`dir/`) are not this tree."""
    try:
        # Against the WORKING TREE, not HEAD: an uncommitted edit deploys as surely as a commit.
        out = subprocess.run(["git", "-C", str(root), "diff", "--name-only", head], capture_output=True,
                             encoding="utf-8", errors="replace", check=True, timeout=60).stdout.splitlines()
        out += subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
                              capture_output=True, encoding="utf-8", errors="replace", check=True,
                              timeout=60).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return None
    paths = [p.strip() for p in out if p.strip()]
    code = [p for p in paths if not p.endswith("/") and not is_deploy_record(p)]
    return [p for p in code if not shipped_unchanged(root, p)]


#: Where DevFlow's own tooling lives. Only a file here can be "DevFlow's, unchanged": the product scaffold
#: the package also ships (`src/`, `tests/`, `pyproject.toml`) is the product's code from the first commit.
DEVFLOW_TOOLING = (".claude/", ".githooks/", "scripts/", "conformance/", ".agents/", ".github/")
DEVFLOW_TOOLING_FILES = {"Makefile"}

#: Always code, even byte-identical to DevFlow's commit: the guard, its settings and the gate are the safety surface
#: the verdicts stand on, and the product's deploy scripts decide what ships where (#410, D-223 clause 5).
SAFETY_SURFACE = {".claude/hooks/bash_guard.py", ".claude/settings.json", "scripts/deploy_gate.py",
                  "scripts/brief_fields.py", "scripts/deploy_hosted_engine.sh", "scripts/nightly_hosted.sh"}
SAFETY_SURFACE_DIRS = ("scripts/ci/",)
#: #410 (D-223 clause 5): `<version> <commit>`, the DevFlow commit whose bytes the exemption compares with. Read
#: at the protected base only: an agent's branch can neither move it nor forge it, and an upgrade the owner merges
#: moves it. `.gp/installed` and the local tags are not read: both are writable by the change under evaluation.
DEVFLOW_PIN = "docs/devflow-pin.txt"
_PINS: dict[str, str | None] = {}


def devflow_pin(root: Path) -> str | None:
    """The DevFlow commit pinned at the protected base of `root`, or None (no base, no pin, or not a commit)."""
    key = str(root)
    if key not in _PINS:
        base = protected_base(root)
        text = git_show(root, base, DEVFLOW_PIN) if base else None
        m = re.fullmatch(r"\s*v\S+\s+([0-9a-f]{40})\s*", text or "")
        _PINS[key] = m.group(1) if m else None
    return _PINS[key]


def git_show(root: Path, rev: str, rel: str) -> str | None:
    try:
        done = subprocess.run(["git", "-C", str(root), "show", f"{rev}:{rel}"], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def shipped_unchanged(root: Path, rel: str) -> bool:
    """Whether `rel` is a file DevFlow shipped, byte for byte as the commit pinned at the protected base has it --
    DevFlow's own tooling after an upgrade, which is not this product's code (v7.2, the owner's ruling of
    2026-10-17: every upgrade made both release verdicts stale). False with no pin at the base, for the safety
    surface, and for anything the project changed (#410: never from a local tag or the untracked marker)."""
    if rel in SAFETY_SURFACE or rel.startswith(SAFETY_SURFACE_DIRS) \
            or not (rel in DEVFLOW_TOOLING_FILES or rel.startswith(DEVFLOW_TOOLING)):
        return False
    pinned = devflow_pin(root)
    target = root / rel
    if pinned is None or not target.is_file():
        return False
    try:
        shipped = subprocess.run(["git", "-C", str(root), "cat-file", "-p", f"{pinned}:{rel}"],
                                 capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return shipped.returncode == 0 and shipped.stdout == target.read_bytes()


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


def verdicts(root: Path) -> list[tuple[str | None, str]]:
    """The policy's base, then security, then the Tester: each (why not current | None, summary line). In
    heavy mode a current `m<N>-security.md` of the latest milestone stands for `release-security.md` (v7.2);
    model_ranking (#283) reads the mode at the protected base as well as in the tree, and lets the milestone
    verdict stand only when neither says light."""
    policy, where = policy_root(root)
    out: list[tuple[str | None, str]] = []
    modes = [mode(root)]
    if policy is None:
        out.append((f"the brief's policy fields cannot be read at the protected base ({where}); a deploy is "
                    "judged by the base's brief, never by the change's (#283)", f"policy: unreadable ({where})"))
    else:
        modes = list(dict.fromkeys([mode(policy), *modes]))
        out.append((None, f"policy: {where}, working mode {modes[0]}"
                          + (f"; the tree's brief says {modes[1]}, so both modes' Tester verdicts" if len(modes) > 1
                             else "")))
    security = current(root, SECURITY, "security")
    # A BLOCKING release verdict is a finding nobody fixed: no milestone verdict stands over it.
    blocking = "has no PASS or MINOR verdict" in (security[0] or "") and (root / SECURITY).is_file()
    if security[0] and not blocking and policy is not None and "light" not in modes:
        milestone = latest_milestone(root, MILESTONE_SECURITY)
        if milestone is not None:
            alternative = current(root, milestone, "security (heavy mode: the milestone's)", independent=True)
            security = alternative if alternative[0] is None else (
                f"{security[0]}; and the latest milestone verdict does not stand for it: {alternative[0]}",
                security[1])
    out.append(security)
    for working_mode in modes:
        tester, label = tester_path(root, working_mode)
        if tester is None:
            out.append((f"there is no milestone Tester verdict (docs/reviews/m<N>-tester.md) in this tree ({label})",
                        f"{label}: no docs/reviews/m<N>-tester.md"))
        else:
            out.append(current(root, tester, label, independent=True))
    return out


# --- matching -------------------------------------------------------------------------------------------

def declared(root: Path) -> list[list[str]]:
    """The deploy commands the protected base's brief or the tree's declares (#283), each as lower-cased
    words. One the shell cannot split is skipped loudly: a declaration nobody can match is not a declaration."""
    policy, _ = policy_root(root)
    texts = listing("Deploy commands", root)
    if policy is not None:
        texts += [t for t in listing("Deploy commands", policy) if t not in texts]
    out: list[list[str]] = []
    for text in texts:
        try:
            words = [w.lower() for w in shlex.split(text)]
        except ValueError:
            print(f"deploy gate: the brief's deploy command {text!r} cannot be split as the shell would; "
                  "it is not matched", file=sys.stderr)
            continue
        if words:
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
        if name in ("timeout", "gtimeout") and i < len(words) and not words[i].startswith("-"):
            i += 1
        while i < len(words) and (words[i].startswith("-") or ASSIGNMENT.match(words[i])):
            if words[i] in ("-n", "-u", "-g", "-k", "-s", "--signal", "-C", "-t") and i + 1 < len(words):
                i += 1
            i += 1
    return words[i:]


def matches(words: list[str], declared_words: list[str]) -> bool:
    """Whether the declared command is the command these words run."""
    words = _program_position(words)
    if not words or not declared_words:
        return False
    if os.path.basename(words[0]).lower() != os.path.basename(declared_words[0]):
        return False
    rest = [w.lower() for w in words[1:]]
    if not any(d.startswith("-") for d in declared_words[1:]):
        rest = [w for w in rest if not w.startswith("-")]
    return rest[:len(declared_words) - 1] == declared_words[1:]


def deploy_in(commands: list[list[str]], root: Path) -> str | None:
    """The declared deploy command one of these word lists runs, or the `gh` command among them that starts a
    deploy workflow (#390), or None."""
    decl = declared(root)
    for d in decl:
        for words in commands:
            if matches(words, d):
                return " ".join(d)
    starts = [(words, start) for words in commands if (start := gh_dispatch(words)) is not None]
    if not starts:
        return None
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
                    f"{', '.join(sorted(workflows)) or 'which workflow deploys is not known'} deploys)")
    return None


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
    base = protected_base(root)
    if base is None:
        return out, True
    try:
        listed = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "-z", "--name-only", base, "--",
                                 *WORKFLOW_DIRS], capture_output=True, check=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return out, False
    complete = True
    for path in (p.decode("utf-8", "replace") for p in listed.split(b"\0") if p):
        if not path.endswith((".yml", ".yaml")):
            continue
        try:
            shown = subprocess.run(["git", "-C", str(root), "show", f"{base}:{path}"], capture_output=True,
                                   check=True, timeout=30).stdout.decode("utf-8", "replace")
        except (OSError, subprocess.SubprocessError):
            complete = False
            continue
        out.setdefault(os.path.basename(path).lower(), []).append(shown)
    return out, complete


def _runs_deploy(text: str, decl: list[list[str]]) -> bool:
    """Whether a line of a workflow file runs a declared deploy command: a `run:` value, or a line of its block,
    with a `\\` continuation joined. Read wide on purpose: a line that only looks like one makes the workflow a
    deploy, which refuses more."""
    for line in re.sub(r"\\\n\s*", " ", text).splitlines():
        line = re.sub(r"^\s*(?:-\s*)?(?:run:\s*)?", "", line)
        try:
            commands = split_line(line)
        except ValueError:
            commands = [line.split()]
        for words in commands:
            at = len(words) - len(_program_position(words))
            if at < len(words):
                program = os.path.basename(words[at]).lower()
                words = [*words[:at], SAME_PROGRAM.get(program, words[at]), *words[at + 1:]]
            if any(matches(words, d) for d in decl):
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
    files = {name for d in decl for name in (gh_dispatch(d) or set()) if name != UNKNOWN}
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


def judge(commands: list[list[str]], root: Path, foreign: bool = False) -> int:
    hit = deploy_in(commands, root)
    if not hit:
        return 0
    if foreign:  # its verdicts are that repository's word, not this project's: they are not read
        print(f"BLOCKED: deploy gate -- `{hit}` is a deploy declared in {root}, which is not this session's "
              "project: the Bash guard judges no other repository's deploys. Deploy it from a session started "
              "in that repository.", file=sys.stderr)
        return 2
    for why, _ in verdicts(root):
        if why:
            return refuse(f"`{hit}` is a deploy, and {why}")
    return 0


def check(root: Path) -> int:
    print(f"deploy-check: tree {root} (working tree, nested checkouts excluded)")
    bad: list[str] = []
    for why, summary in verdicts(root):
        print(f"deploy-check: {summary}")
        if why:
            bad.append(why)
    if bad:
        for why in bad:
            print(f"deploy-check FAIL: {why}")
        print(f"  {HOW_TO_CLOSE}")
        return 1
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
        return judge(commands, root, foreign)
    cwd = Path.cwd()
    root = toplevel(cwd)
    if argv == ["--check"]:
        if root is None:
            print(f"deploy-check FAIL: {cwd} is not inside a git work tree, so nothing can be compared")
            return 1
        return check(root)
    if len(argv) != 1 or argv[0].startswith("--"):
        print('usage: deploy_gate.py "<command>" | --judge | --check', file=sys.stderr)
        return 2
    try:
        commands = split_line(argv[0])
    except ValueError as error:
        return refuse(f"the command cannot be split as the shell would ({error})")
    return judge(commands, root or cwd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
