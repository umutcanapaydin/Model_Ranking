"""One question, answered once: is this file a RECORD or an INSTRUCTION SURFACE?

A record -- a review, a wave close, a closure report, an ADR -- describes the past, and the past
legitimately names removed targets and retired files. An instruction surface tells a reader what to
do now. Checks that confuse the two go wrong in the same three ways:

- `test-documented-commands` failing a historical closure report for citing a `make` target that
  was removed later.
- `test-git-authority` flagging a reviewer's compliance ATTESTATION ("no git commit was run") as a
  git violation -- the artefact that PROVES compliance read as the breach.
- `L1` making it impossible to describe L1 inside the repository it governs: any accurate
  description quotes the characters it detects.

Decide by ARTIFACT CLASS, never by a growing list of negation words: a word list fails OPEN (a live
`git push --force` instruction under a "we never bypass review" heading passes it). Words are a
bypass surface; a frontmatter field is not.

A file is a record iff it carries `record_type:` frontmatter, or lives under a directory whose whole
population is records (`docs/reviews/`).
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

# Git exports GIT_DIR (and friends) to every hook, and in a worktree GIT_DIR is ABSOLUTE. A control
# that runs git in a throwaway repository inherits it and acts on the repository being graded
# instead: a pre-push gate run from a worktree overwrote the repository's identity, set
# `core.bare = true` and committed a scratch tree over the real one. Every git a control spawns
# outside the repository under evaluation takes this environment. The list is asked of git itself;
# the literal is only the fallback when git cannot answer.
_GIT_LOCAL_FALLBACK = ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS",
                       "GIT_CONFIG_COUNT", "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE",
                       "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE", "GIT_INDEX_FILE",
                       "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX",
                       "GIT_SHALLOW_FILE", "GIT_COMMON_DIR")
#: `git commit` also exports the commit's identity and dates to its hooks, and the commit-msg gate runs
#: the controls there: a throwaway repository's planted authors and dates were overwritten by the
#: commit being made, and the identity control's self-test went wrong (#258). A control that wants an
#: identity passes it in `extra`.
_GIT_IDENTITY = ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_AUTHOR_DATE", "GIT_COMMITTER_NAME",
                 "GIT_COMMITTER_EMAIL", "GIT_COMMITTER_DATE")


_CALLER_ONLY = {"CLAUDE_CODE_SESSION_ID", "MAKEFLAGS", "MFLAGS", "MAKEOVERRIDES", "MAKELEVEL"}


def pool_jobs(cap: int, inside: bool = False) -> tuple[int, int]:
    """(a pool's size, the DEVFLOW_SHARE run-all hands each test): the one reader of DEVFLOW_JOBS (#114).

    The size is DEVFLOW_JOBS, else min(cap, CPUs). Each test gets DEVFLOW_SHARE, twice the CPUs over the
    pool's size, because the tests wait about as long as they compute. Eight tests that each started eight
    runs made the gate slower; one run each left test-deploy-classes serial for the whole leg (measured).
    A test's own pool (`inside`) takes DEVFLOW_SHARE when a runner set it. A runner reads DEVFLOW_JOBS only:
    held to a share, test-delivered-tree's nested run-all ran two tests at a time. A set DEVFLOW_JOBS is the
    whole budget, so each test gets 1 and DEVFLOW_JOBS=1 runs every pool one at a time, except test-bash-guard's,
    which keeps min(8, CPUs) and is the distribution's longest test. Unreadable,
    either one, is 1 and 1."""
    if inside and "DEVFLOW_SHARE" in os.environ:
        try:
            return max(1, int(os.environ["DEVFLOW_SHARE"])), 1
        except ValueError:
            return 1, 1
    raw = os.environ.get("DEVFLOW_JOBS")
    try:
        jobs = max(1, int(raw)) if raw else min(cap, os.cpu_count() or 1)
    except ValueError:
        return 1, 1
    return jobs, 1 if raw else max(1, 2 * (os.cpu_count() or 1) // jobs)


def scrubbed_env(extra: dict | None = None) -> dict:
    """os.environ without the repository-local git variables or a commit's identity, plus `extra`."""
    try:
        names = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True,
                               encoding="utf-8", errors="replace",
                               timeout=10).stdout.split() or list(_GIT_LOCAL_FALLBACK)
    except (OSError, subprocess.SubprocessError):
        names = list(_GIT_LOCAL_FALLBACK)
    # The Claude Code session id goes too: a scratch tree is not the tree the session started in, so
    # `make session-check` would rightly refuse every one of them.
    # And make's own variables: a test run from a make recipe (`make check-fast CHECK_FAST_ARGS=...`, the
    # post-edit hook) handed its flags and command-line variables to every throwaway make, and
    # test-gate-stamp read each of its fixtures as "not a plain make gate" (Project-J, v7.2).
    env = {k: v for k, v in os.environ.items() if k not in names and k not in _GIT_IDENTITY
           and not k.startswith("GIT_CONFIG_KEY_")
           and not k.startswith("GIT_CONFIG_VALUE_") and k not in _CALLER_ONLY}
    env.update(extra or {})
    return env


# ── A fixture repository, as git leaves it (#48) ─────────────────────────────────────────────
#
# A fixture's own commit starts git's background auto-maintenance, which creates and removes
# `.git/objects/maintenance.lock`; a copy taken meanwhile listed the lock, then could not copy it --
# the one recurring CI flake of three field projects. A fixture repository runs with maintenance off
# (QUIET_GIT, right after `git init`), and every copy of a tree a test makes skips git's locks.

#: git's own lock files: transient, never part of what a fixture holds.
LOCKS = shutil.ignore_patterns("*.lock")
#: Set in a fixture repository right after `git init`: no auto-maintenance, no auto-gc.
QUIET_GIT = (("maintenance.auto", "false"), ("gc.auto", "0"))


def copy_repo(src, dst) -> None:
    """Copy a tree -- a fixture repository above all -- as copytree does, leaving out every `*.lock`."""
    shutil.copytree(src, dst, symlinks=True, ignore=LOCKS)


# ── A missing tool is an environment, not a verdict ──────────────────────────────────────────
#
# Without `make` on PATH one test died with a traceback and another blamed the hooks it could not
# run: the report accused working controls. A test that needs a tool asks for it first and, when it
# is absent, says `<tool> not installed: cannot <what>` and exits 2 (NOT-EVALUABLE).

def missing_tool(tool: str, what: str) -> str | None:
    """`<tool> not installed: cannot <what>` when `tool` is not on PATH, else None."""
    return None if shutil.which(tool) else f"{tool} not installed: cannot {what}"


def runnable_bash(what: str) -> tuple[str | None, str]:
    """(the bash to run, "") when one runs `echo ok`; (None, the NOT-EVALUABLE line) otherwise.

    Always the path `shutil.which` found, never the bare name: on Windows `CreateProcess` searches
    System32 before PATH, so `["bash", ...]` starts the WSL launcher, which fails with no distro
    installed -- and every hook case then read as a hook defect.
    """
    path = shutil.which("bash")
    if not path:
        return None, f"bash not installed: cannot {what}"
    try:
        r = subprocess.run([path, "-c", "echo ok"], capture_output=True, encoding="utf-8",
                           errors="replace", timeout=30)
        ok = r.returncode == 0 and r.stdout.strip() == "ok"
    except (OSError, subprocess.SubprocessError):
        ok = False
    return (path, "") if ok else (None, f"bash not runnable here ({path}): cannot {what}")


def manifest_project(root) -> list[str] | None:
    """The PROJECT entries `INSTALL-MANIFEST.md` under `root` declares (a trailing `/` marks a
    directory), or None when there is no manifest or no such section. The delivered set is the
    manifest's to decide; a control that walked the tree instead would grade GP's own tooling."""
    man = Path(root) / "INSTALL-MANIFEST.md"
    if not man.is_file():
        return None
    text = man.read_text(encoding="utf-8", errors="replace")
    head, tail = text.find("## PROJECT"), text.find("## GP-INTERNAL")
    if head < 0:
        return None
    names: list[str] = []
    for block in re.findall(r"```(.*?)```", text[head:tail if tail > head else None], re.S):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                names.append(line.split()[0])
    return names


def manifest_internal(root) -> set | None:
    """The GP-INTERNAL paths `INSTALL-MANIFEST.md` under `root` declares, or None when there is no
    manifest or no such section. Derived from the file that decides delivery -- never a second list
    kept beside it. A delivered-document control excludes these: they are not what a reader receives.
    """
    man = Path(root) / "INSTALL-MANIFEST.md"
    if not man.is_file():
        return None
    text = man.read_text(encoding="utf-8", errors="replace")
    head = text.find("## GP-INTERNAL")
    if head < 0:
        return None
    names: set = set()
    for block in re.findall(r"```(.*?)```", text[head:], re.S):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                names.add(line.split()[0])
    return names


RECORD_DIRS = ("docs/reviews",)
_FM = re.compile(r"\A---\s*\n(?:.*\n)*?record_type:\s*\S+", re.M)


_PLAN = re.compile(r"(?:^|/)docs/plans/m(\d+)-plan\.md$")


def _current_plan_number(p: Path) -> int | None:
    """The highest milestone number among `docs/plans/m<N>-plan.md` beside `p`."""
    numbers = [int(m.group(1)) for q in p.parent.glob("m*-plan.md")
               if (m := _PLAN.search(q.as_posix()))]
    return max(numbers) if numbers else None


def is_record(path: Path, root: Path | None = None) -> bool:
    p = Path(path)
    rel = str(p if root is None else p.relative_to(root)).replace("\\", "/")
    if any(rel.startswith(d + "/") or ("/" + d + "/") in rel for d in RECORD_DIRS):
        return True
    # model_ranking, DevFlow v6.0 adoption (D-155; independent review MAJOR-1). Frontmatter alone
    # made every TEMPLATE and the CURRENT milestone plan a "record", so a template or the plan being
    # worked could tell an agent to `git push origin main` and pass the git-authority and
    # documented-command checks -- 235 of 302 documents skipped. A template is copied into every new
    # record and a current plan is being followed: both are instruction surfaces whatever their
    # frontmatter says. A plan for an EARLIER milestone describes the past and stays a record.
    if p.name.endswith(".template.md"):
        return False
    plan = _PLAN.search(rel)
    if plan:
        current = _current_plan_number(p)
        if int(plan.group(1)) == current:
            return False
        if current is not None and int(plan.group(1)) < current:
            return True   # a closed milestone's plan describes the past, frontmatter or not
    if p.suffix != ".md" or not p.is_file():
        return False
    try:
        head = p.read_text(encoding="utf-8", errors="replace")[:400]
    except OSError:
        return False
    return bool(_FM.match(head))


# ── A document is a document whatever its extension ──────────────────────────────────────────
#
# `pipeline-schema.html` is delivered too. A control that globs `*.md` never reads it, and an HTML
# page nobody reads drifts: it went on naming skills and targets long after they were removed.
# HTML writes `<code>x</code>` where markdown writes `` `x` ``, so the text is normalised once,
# here, and every control keeps its own patterns.
DOC_SUFFIXES = {".md", ".html"}
_CODE_TAG = re.compile(r"<code>(.*?)</code>", re.S | re.I)


def _ignored_untracked(root) -> tuple[set[str], tuple[str, ...]] | None:
    """#325: the paths git ignores and does not track, as files and directory prefixes, or None without
    git. Scratch under `build/` is not a shipped document; a tracked file under an ignore rule still is."""
    try:
        r = subprocess.run(["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"],
                           cwd=root, capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    names = [n for n in r.stdout.decode("utf-8", errors="replace").split("\0") if n]
    return {n for n in names if not n.endswith("/")}, tuple(n for n in names if n.endswith("/"))


def documents(root, skip=None):
    """Every shipped document under `root`, markdown and HTML alike, sorted, symlinks excluded. A path git
    ignores and does not track is no shipped document (#325); without git, every path is read."""
    out = []
    ignored = _ignored_untracked(root)
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink() or p.suffix not in DOC_SUFFIXES:
            continue
        if any(part in {".git", "__pycache__", ".venv"} for part in p.parts):
            continue
        if ignored is not None:
            rel = p.relative_to(root).as_posix()
            if rel in ignored[0] or rel.startswith(ignored[1]):
                continue
        if skip and skip(p):
            continue
        out.append(p)
    return out


def doc_text(path) -> str:
    """The document's text with HTML code spans written the way markdown writes them.

    Nothing else about the HTML is interpreted: a control that started parsing markup would be a
    second, worse HTML parser living inside a governance check.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".html":
        return _CODE_TAG.sub(lambda m: f"`{m.group(1).strip()}`", text)
    return text


# ── Names held only as hashes (`docs/project-aliases.md`, "Names held privately") ──────────────────
_WORD = re.compile(r"[A-Za-z0-9]+")


def name_hash(name: str) -> str:
    """sha256 of a name's letters and digits, lowercased and joined: every separator and case of one
    name hashes alike (`Name-Two`, `name_two`, `Name Two`, `NameTwo` -> `nametwo`)."""
    import hashlib  # noqa: PLC0415
    return hashlib.sha256("".join(w.lower() for w in _WORD.findall(name)).encode()).hexdigest()


def hashed_name_hits(line: str, hashes: set[str], longest: int = 3) -> bool:
    """Whether any run of one to `longest` adjacent words of `line`, joined, hashes to one of `hashes`.
    Word runs, not substrings: a longer word that merely starts with a name is a different word."""
    if not hashes:
        return False
    words = [w.lower() for w in _WORD.findall(line)]
    for n in range(1, longest + 1):
        for i in range(len(words) - n + 1):
            if name_hash("".join(words[i:i + n])) in hashes:
                return True
    return False
