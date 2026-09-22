"""One question, answered once: is this file a RECORD or an INSTRUCTION SURFACE?

Three conformance checks and one validator rule independently confused the two, and the cost is
GPF-001, GPF-004 and GPF-005 — four recurrences in a single field milestone:

- `test-documented-commands` failed historical closure reports for citing a `make` target that was
  later removed. A record describes the past; the past legitimately contains removed targets.
- `test-git-authority` flagged a reviewer's compliance ATTESTATION ("no git commit was run") as a
  local-lane git violation — the artifact that PROVES compliance read as the breach.
- `L1` made it impossible to describe L1 inside the repository it governs: any accurate description
  quotes the characters it detects.

The council's condition was explicit: fix this by ARTIFACT CLASS, never by growing the NEGATION word
list — the Security seat measured that list failing OPEN four ways in ten minutes (a live
`git push --force` instruction under a "we never bypass review" heading passes it today). Words are
a bypass surface; a frontmatter field is not.

A file is a record iff it carries `record_type:` frontmatter, or lives under a directory whose whole
population is records (`docs/reviews/`, `docs/retrospectives/`, `docs/handovers/`).
"""
import re
from pathlib import Path

RECORD_DIRS = ("docs/reviews", "docs/retrospectives", "docs/handovers")
_FM = re.compile(r"\A---\s*\n(?:.*\n)*?record_type:\s*\S+", re.M)


def is_record(path: Path, root: Path | None = None) -> bool:
    p = Path(path)
    rel = str(p if root is None else p.relative_to(root)).replace("\\", "/")
    if any(rel.startswith(d + "/") or ("/" + d + "/") in rel for d in RECORD_DIRS):
        return True
    if p.suffix != ".md" or not p.is_file():
        return False
    try:
        head = p.read_text(encoding="utf-8", errors="replace")[:400]
    except OSError:
        return False
    return bool(_FM.match(head))


# ── v6.0, 2026-09-22: the controls stopped at markdown, and the one delivered HTML went unread ──
#
# `test-documented-commands`, `-skills` and `-paths` all globbed `*.md`. `pipeline-schema.html` is
# the package's only other delivered document -- the "show the picture" moment in a demo -- and
# nothing had ever looked at it. Measured when something finally did: version stamps frozen at
# v4.3, `<code>/quarterly-handover</code>` and `<code>/fix-issue-implement</code>` (both folded
# into other skills at v6.0), and `make check-templates` (a target removed two cuts ago).
#
# A document is a document whatever its extension. HTML writes `<code>x</code>` where markdown
# writes `` `x` ``, so the text is normalised once, here, and every control keeps its own patterns.
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
