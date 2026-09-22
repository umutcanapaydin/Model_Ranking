#!/usr/bin/env python3
"""Every `/skill` a shipped document tells a reader to invoke must exist.

`test-documented-commands` has enforced this for `make` targets since v5, on V4C-80's one-line
principle: **anything a reader is told to type is an interface.** Skills were never graded, and
they had drifted further than the targets ever did. Measured at v6.0, in shipped documents:

    /security-review      8 files     never existed here; it was a host built-in
    /review               6 files     the skill is `repo-review`
    /retrospect           6 files     folded into `cycle-close` at v6.0
    /quarterly-handover   6 files     folded into `cycle-close` at v6.0
    /fix-issue-prepare    4 files     merged into `fix-issue` at v6.0
    /fix-issue-implement  3 files     merged into `fix-issue` at v6.0
    /test-and-commit      2 files     never existed under that name
    /standup              1 file      it is `make standup`, and always was
    /code-review          1 file      the skill is `repo-review`

Ten names, twenty-odd references. `subagent-profiles/README.md` alone pointed at three skills that
do not ship, in the file whose job is to say how the profiles are invoked. A reader following it
types a slash command and gets nothing -- the same dead end `make journey` gave a customer, one
interface over.

DERIVED: the shipped set is the directories under `.claude/skills/`. Non-skill `/tokens` -- HTTP
routes, filesystem paths -- are declared in `.skill-refs-allow`, each with a written reason.
Backticked ONLY, which is how `test-documented-commands` learned to stop reporting `make it` and
`make the` from ordinary prose.

Exit: 0 clean · 1 findings · 2 cannot run.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import doc_text, documents                      # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
SKILLS = PKG / ".claude" / "skills"
ALLOW = PKG / ".skill-refs-allow"

# Historical records describe what PAST versions ran; they are not instructions.
SKIP = re.compile(r"HANDOVER-v[\d.]+-material\.md$|CHANGELOG|practices-cut\.md$")
REF = re.compile(r"`/([a-z][a-z0-9-]{2,})`")


def shipped() -> set[str]:
    # A missing skills directory is NOT "cannot run". The manifest guarantees
    # `.claude/skills` ships, so its absence is an incomplete install -- and a check
    # that shrugs at an empty input is the vacuous pass this file exists to end.
    names = ({d.name for d in SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()}
             if SKILLS.is_dir() else set())
    if not names:
        print("test-documented-skills FAIL: no skill with a SKILL.md under .claude/skills/. An "
              "empty derived set is a failure, never a vacuous pass.")
        raise SystemExit(1)
    return names


def allowed() -> set[str]:
    """Declared non-skill tokens. A row with no reason does not count as declared."""
    if not ALLOW.is_file():
        return set()
    out = set()
    for raw in ALLOW.read_text(encoding="utf-8").splitlines():
        line = raw.split("#")[0].rstrip()
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
            out.add(parts[0].strip())
    return out


def unreachable(skills: set, docs_text: dict) -> list:
    """The other direction: a skill that SHIPS and that no shipped document ever names.

    This file has always asked *"does the skill this document names exist?"* -- 62 dangling
    references at v6.0. It never asked the mirror question, and the mirror question had six
    answers: `going-live`, `start-session`, `wiring-an-integration`, `work-enhancement`,
    `work-issue` and `writing-a-control` shipped in every install and were named by nothing --
    not a document, not the Makefile, not a profile. A reader following the package to the end
    never learned they existed.

    It is `make gate`'s caller-liveness rule applied to the other interface: a control nobody can
    reach is not a control, and a skill nobody can find is not a skill. The fix is a sentence in
    the document that owns the moment the skill belongs to -- never a list of skills somewhere,
    which would be an enumeration beside the thing it enumerates.
    """
    orphans = []
    for name in sorted(skills):
        home = f".claude/skills/{name}/"
        if any(name in t for rel, t in docs_text.items() if not rel.startswith(home)):
            continue
        orphans.append(name)
    return orphans


def main() -> int:
    skills, allow = shipped(), allowed()
    bad, n, corpus = [], 0, {}
    # v6.0: markdown AND html. `pipeline-schema.html` named two skills that no longer ship and
    # nothing had ever read it -- every control globbed `*.md`.
    for f in documents(PKG):
        rel = str(f.relative_to(PKG))
        if SKIP.search(rel) or ".venv" in f.parts or "archive" in f.parts:
            continue
        try:
            text = doc_text(f)
        except (UnicodeDecodeError, OSError):
            continue
        corpus[rel] = text
        for i, line in enumerate(text.splitlines(), 1):
            for m in REF.finditer(line):
                name = m.group(1)
                n += 1
                if name not in skills and name not in allow:
                    bad.append(f"{rel}:{i} tells a reader to run `/{name}`, and no such skill "
                               f"ships. Name a skill that exists, or declare the token in "
                               f"`.skill-refs-allow` with its reason")
    for name in unreachable(skills, corpus | {
            "Makefile": (PKG / "Makefile").read_text(encoding="utf-8", errors="replace")}):
        bad.append(f"`{name}` SHIPS and no shipped document names it. A skill nobody can find is "
                   f"not a skill -- name it where its moment is described, or stop shipping it")

    for b in bad[:30]:
        print(f"  FAIL {b}")
    if len(bad) > 30:
        print(f"  ... and {len(bad) - 30} more")
    print(f"test-documented-skills {'FAIL' if bad else 'PASS'}: {n} reference(s) across "
          f"{len(skills)} shipped skill(s), {len(bad)} dangling")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
