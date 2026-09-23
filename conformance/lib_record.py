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


def scrubbed_env(extra: dict | None = None) -> dict:
    """os.environ without the repository-local git variables, plus `extra`."""
    try:
        names = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True,
                               encoding="utf-8", errors="replace",
                               timeout=10).stdout.split() or list(_GIT_LOCAL_FALLBACK)
    except (OSError, subprocess.SubprocessError):
        names = list(_GIT_LOCAL_FALLBACK)
    env = {k: v for k, v in os.environ.items() if k not in names and not k.startswith("GIT_CONFIG_KEY_")
           and not k.startswith("GIT_CONFIG_VALUE_")}
    env.update(extra or {})
    return env


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


def documents(root, skip=None):
    """Every shipped document under `root`, markdown and HTML alike, sorted, symlinks excluded."""
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink() or p.suffix not in DOC_SUFFIXES:
            continue
        if any(part in {".git", "__pycache__", ".venv"} for part in p.parts):
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
