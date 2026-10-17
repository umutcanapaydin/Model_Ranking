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
    return path.startswith("docs/") or path.endswith(".md")


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
    return [p for p in paths if not p.endswith("/") and not is_deploy_record(p)]


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
    """The policy's base, then security, then the Tester: each (why not current | None, summary line)."""
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
    out.append(current(root, SECURITY, "security"))
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
    """The declared deploy command one of these word lists runs, or None."""
    for d in declared(root):
        for words in commands:
            if matches(words, d):
                return " ".join(d)
    return None


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
