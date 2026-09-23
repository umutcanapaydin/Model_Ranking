#!/usr/bin/env python3
"""Every `/skill` a shipped document tells a reader to invoke must exist.

`test-documented-commands` enforces this for `make` targets, on one principle: **anything a
reader is told to type is an interface.** Skills drift further than targets do: skills get renamed,
merged into others or folded away, and the documents that name them keep the old name. When this
was first measured, ten names that did not ship were named sixty-odd times across the delivered
documents -- including three in the very file whose job was to say how the reviewer profiles are
invoked. A reader following one types a slash command and gets nothing.

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
from lib_record import doc_text, documents, is_record, manifest_internal  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
SKILLS = PKG / ".claude" / "skills"
ALLOW = PKG / ".skill-refs-allow"

REF = re.compile(r"`/([a-z][a-z0-9-]{2,})`")
# Backticks alone are not enough: the CI issue agent's prompt -- a workflow file, plain text -- once
# told the agent to "run the /fix-issue-prepare skill", a skill that no longer existed, so every run
# of that lane asked for nothing. Prose that SAYS "skill" next to the name is a reference however it
# is typeset.
REF_PLAIN = re.compile(r"(?<![\w`/.])/([a-z][a-z0-9-]{2,})(?= skill\b)")
WORKFLOWS = PKG / ".github" / "workflows"


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

    The first question is *"does the skill this document names exist?"*. The mirror question had
    six answers when it was first asked: six skills shipped in every install and were named by
    nothing -- not a document, not the Makefile, not a profile. A reader following the package to
    the end never learned they existed.

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
    # Markdown AND html: `pipeline-schema.html` once named two skills that no longer shipped, and
    # nothing read it while every control globbed `*.md`.
    # GP-INTERNAL documents never reach a reader of the product, and may name what a project does
    # not have; the manifest that decides delivery says which they are.
    internal = manifest_internal(PKG) or set()
    for f in documents(PKG) + sorted(WORKFLOWS.glob("*.y*ml")):
        rel = str(f.relative_to(PKG))
        if ".venv" in f.parts or rel in internal:
            continue
        try:
            text = doc_text(f)
        except (UnicodeDecodeError, OSError):
            continue
        corpus[rel] = text
        # model_ranking (D-155; independent review MAJOR-2): a RECORD describes the past and may name
        # a skill that was retired since, as `test-documented-commands` already allows for make
        # targets. Without this, the only remedy was a token row valid EVERYWHERE, which let a live
        # AGENTS.md tell a reader to run a retired skill.
        if is_record(f, PKG):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in list(REF.finditer(line)) + list(REF_PLAIN.finditer(line)):
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
