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

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

# No bytecode: a `__pycache__` written beside the gate would itself read as a code change in a tree
# that does not ignore it, and the tree about to ship is what this compares.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import brief_fields  # noqa: E402
from brief_fields import (  # noqa: E402
    Unverified,
    listing,
    mode,
    protected_base,
    protected_bases,
    root_at,
)

#: #410 round 1's B1: git honours `refs/replace/` refs everywhere, so one written by the change under evaluation
#: could stand in for the pinned commit or the protected base. Every git this gate starts, directly or through
#: `brief_fields`, ignores them.
os.environ["GIT_NO_REPLACE_OBJECTS"] = "1"

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


_POLICIES: dict[str, tuple[list[Path] | None, str, bool]] = {}


def _policy(root: Path) -> tuple[list[Path] | None, str, bool]:
    """(the policy roots -- the brief at the merge-base, and at the default branch's tip when it differs (#517,
    D-232 clause 1) --, or None when one cannot be read; the line that says which; whether a base's brief failed its
    hash check: #509)."""
    key = str(root)
    if key not in _POLICIES:
        bases = protected_bases(root)
        if not bases:
            _POLICIES[key] = (None, "no merge-base of HEAD with a default branch (origin/HEAD, origin/main, "
                                    "origin/master, main, master)", False)
        else:
            where = (f"the brief at {bases[0][:12]}, the merge-base of HEAD with the default branch"
                     + (f", and at {bases[1][:12]}, its tip" if len(bases) > 1 else ""))
            try:
                _POLICIES[key] = ([root_at(base, root) for base in bases], where, False)
            except Unverified as error:
                _POLICIES[key] = (None, str(error), True)
            except RuntimeError as error:
                _POLICIES[key] = (None, str(error), False)
    return _POLICIES[key]


def policy_root(root: Path) -> tuple[Path | None, str]:
    """(a root holding the brief as the protected base -- the merge-base -- of the repository at `root` holds it, or
    None when a base cannot be read; the line that says which). The gate itself reads every root `_policy` gives."""
    policies, where, _ = _policy(root)
    return (policies[0] if policies else None), where


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
    compare. Committed, uncommitted and untracked alike. None as well
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
    code = [p for p in paths if not is_deploy_record(p)]
    return [p for p in code if not shipped_unchanged(root, p)]


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
        # #509: verified, as the gate reads every base file whose content it trusts; a forged pin exempts nothing.
        text = (verified_blob(root, base, DEVFLOW_PIN) or b"").decode("utf-8", "replace") if base else None
        m = re.fullmatch(r"\s*v\S+\s+([0-9a-f]{40})\s*", text or "")
        _PINS[key] = m.group(1) if m else None
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
    pinned = devflow_pin(root)
    target = root / rel
    if pinned is None or target.is_symlink() or not target.is_file():
        return False
    surface = deploy_surface(root)
    if surface is None or rel in surface:
        return False
    shipped = verified_blob(root, pinned, rel)
    return shipped is not None and shipped == target.read_bytes()


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


def _runs_unread(text: str) -> bool:
    """Whether a line of a workflow file starts a program in UNREAD_RECIPES (read as `_runs_deploy` reads one)."""
    return any((run := _program_position(words)) and os.path.basename(run[0]).lower() in UNREAD_RECIPES
               for words in _line_commands(text))


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
            workflows = {path for d in WORKFLOW_DIRS for name in starts for path in files.get(f"{d}/{name}", set())}
            _SURFACES[key] = frozenset(named | workflows | {f"{d}/{name}" for d in WORKFLOW_DIRS for name in starts})
    return _SURFACES[key]


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


def verdicts(root: Path) -> list[tuple[str | None, str]]:
    """The policy's base, then security, then the Tester: each (why not current | None, summary line). In
    heavy mode a current `m<N>-security.md` of the latest milestone stands for `release-security.md` (v7.2);
    model_ranking (#283) reads the mode at the protected base as well as in the tree, and lets the milestone
    verdict stand only when neither says light."""
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
    security = current(root, SECURITY, "security")
    # A BLOCKING release verdict is a finding nobody fixed: no milestone verdict stands over it.
    blocking = "has no PASS or MINOR verdict" in (security[0] or "") and (root / SECURITY).is_file()
    if security[0] and not blocking and policies is not None and "light" not in modes:
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
    policies, _, _ = _policy(root)
    texts = listing("Deploy commands", root)
    for policy in policies or []:
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
    _, where, unverified = _policy(root)
    if unverified and commands:
        # #509: the base's brief is what says which commands deploy, and its bytes are not the base's. Which of
        # these deploys cannot be told, so each is judged as one, and the verdicts refuse it (policy unreadable).
        return (f"{' '.join(commands[0])} (any command: {where}; until the base's objects are whole again -- in "
                "your own terminal, `git fetch origin` then `git fsck --full`)")
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
