#!/usr/bin/env python3
"""Every file a shipped document points at must exist.

`test-documented-commands` grades `make` targets; `test-documented-skills` grades `/skills`. Both
rest on V4C-80's one line: **anything a reader is told to type is an interface.** A path in a
document is the same promise in a different shape -- *"go read this file"* -- and it was graded by
nothing at all.

Measured on 2026-09-22 by the mutation census (`census-2026-09-22.md`): of five classes of defect
planted in the shipped prose, `make` targets died at 76% and **file paths at 0%**. Renaming
`` `.mcp.json` `` to `` `.mcp-gone.json` `` inside `docs/executive-overview.md` -- the file whose
whole job is to be a reference map of the package -- left the gate green. That is the same dead end
the 62 dangling skill references gave a reader, one interface over.

DERIVED, NOT ENUMERATED: the reference set is every backticked path-shaped token in every shipped
`*.md`, and the ground truth is the package tree itself. There is no list of "files we have" to
drift from the files we have.

WHAT IS NOT A DEFECT, and why it needs declaring rather than guessing. A starter package documents
files a PROJECT creates and GP does not ship -- `docs/warnings.ledger.md`, `note.txt`, a wave plan.
Those are declared in `.path-refs-allow` as glob patterns, each with a written reason. A pattern
with no reason does not count as declared: an allowlist that accepts bare lines is how a control
gets quietly widened until it grades nothing.

Backticked only. `test-documented-commands` learned that the hard way -- ungated prose produces
`make it` and `make the`, and a control that cries wolf is one nobody reads.

Exit: 0 clean · 1 findings · 2 cannot run.
"""
import fnmatch
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import doc_text, documents                      # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
ALLOW = PKG / ".path-refs-allow"

EXT = "md|py|sh|yml|yaml|toml|json|html|txt|csv|cfg|ini|lock|xml|env"
REF = re.compile(rf"`([A-Za-z0-9_][\w./-]*\.(?:{EXT}))`")
# Historical records describe what PAST versions shipped; a path that was true then is not a
# broken promise now. Same exemption `test-documented-skills` carries, for the same reason.
SKIP = re.compile(r"HANDOVER-v[\d.]+-material\.md$|practices-cut\.md$")
# Conformance fixtures are INPUTS a validator must reject; `condition-evaporated.md` names a
# missing artifact on purpose, and demanding that it exist would delete the fixture's point.
FIXTURE = re.compile(r"^conformance/(fail|pass|wave)/")
MANIFEST = PKG / "INSTALL-MANIFEST.md"


def gp_internal() -> set[str]:
    """The files that are never copied into a project, DERIVED from the manifest that decides it.

    GP's own design document cites GP's own decision trail -- `v3.4-ratification.md` and the rest
    live one directory up, in the repository that authors the package, and the citation is correct
    where it stands. The promise this control grades is the one made to a READER OF THE PRODUCT,
    so the subject is the delivered surface. Getting that boundary from the manifest rather than a
    second list here is the whole point: M2/M3 already keep the manifest honest.
    """
    if not MANIFEST.is_file():
        print("test-documented-paths CANNOT RUN: INSTALL-MANIFEST.md is missing, so the delivered "
              "surface cannot be established. A guess would grade the wrong tree.")
        raise SystemExit(2)
    text = MANIFEST.read_text(encoding="utf-8")
    head = text.find("## GP-INTERNAL")
    if head < 0:
        print("test-documented-paths CANNOT RUN: no `## GP-INTERNAL` section in INSTALL-MANIFEST.md.")
        raise SystemExit(2)
    names: set[str] = set()
    for block in re.findall(r"```(.*?)```", text[head:], re.S):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                names.add(line)
    if not names:
        print("test-documented-paths CANNOT RUN: the GP-INTERNAL section declares nothing. An "
              "empty exclusion set is a failure, never a vacuous pass.")
        raise SystemExit(2)
    return names


def declared() -> list[tuple[str, str]]:
    """Glob patterns a project creates. A row without a reason is not a declaration."""
    out = []
    if not ALLOW.is_file():
        return out
    for raw in ALLOW.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pat, _, reason = line.partition("#")
        if reason.strip():
            out.append((pat.strip(), reason.strip()))
    return out


def main() -> int:
    docs = documents(PKG)
    if not docs:
        print("test-documented-paths FAIL: no *.md found in the package. An empty derived set is a "
              "failure, never a vacuous pass.")
        return 1

    # A reference with no directory in it names a file, it does not route to one: prose says
    # `check_records.py`, and a reader finds it. Requiring the full path there produced 60-odd
    # findings on files that ship -- the cry-wolf shape `test-documented-commands` was built to
    # avoid. A name that ships NOWHERE is still dangling, which is what the census planted.
    basenames = {p.name for p in PKG.rglob("*") if p.is_file() or p.is_symlink()}

    internal = gp_internal()
    docs = [d for d in docs if str(d.relative_to(PKG)) not in internal]
    allow = declared()
    findings: list[str] = []
    refs = 0
    for doc in docs:
        if SKIP.search(doc.name) or FIXTURE.match(str(doc.relative_to(PKG))):
            continue
        rel_doc = doc.relative_to(PKG)
        for line_no, line in enumerate(doc_text(doc).splitlines(), 1):
            for m in REF.finditer(line):
                target = m.group(1)
                refs += 1
                if (PKG / target).exists() or (doc.parent / target).exists():
                    continue
                if "/" not in target and target in basenames:
                    continue
                # Declared absent, by the authority that decides delivery. In an INSTALLATION the
                # GP-internal files are gone by design, and the manifest names them precisely
                # because they are not shipped. An allowlist row here would be a second list
                # saying what the manifest already says.
                if target in internal or any(i.endswith("/" + target) for i in internal):
                    continue
                # fnmatch, not PurePath.match: `**` is not recursive in PurePath.match before
                # 3.13, so `src/**/*` silently matched nothing and a declared row graded as undeclared.
                if any(fnmatch.fnmatch(target, pat) for pat, _ in allow):
                    continue
                findings.append(f"{rel_doc}:{line_no}: `{target}` -- no such file ships, and no "
                                f"row in .path-refs-allow declares it")

    for f in findings:
        print(f"  FAIL {f}")
    print(f"test-documented-paths {'FAIL' if findings else 'PASS'}: {refs} path reference(s) across "
          f"{len(docs)} DELIVERED document(s), {len(internal)} GP-internal path(s) excluded by the "
          f"manifest, {len(allow)} declared pattern(s), {len(findings)} dangling")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
