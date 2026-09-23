#!/usr/bin/env python3
"""Every file a shipped document points at must exist.

`test-documented-commands` grades `make` targets; `test-documented-skills` grades `/skills`. Both
rest on one principle: **anything a reader is told to type is an interface.** A path in a document
is the same promise in a different shape -- *"go read this file"*. Planted defects measured it:
renamed `make` targets were caught three times in four, renamed file paths never, until this ran.

DERIVED, NOT ENUMERATED: the reference set is every backticked path-shaped token in every delivered
document (`.md` and `.html`), and the ground truth is the tree itself. There is no list of "files
we have" to drift from the files we have.

WHAT IS NOT A DEFECT, and why it needs declaring rather than guessing. A starter package documents
files a PROJECT creates and the package does not ship -- `docs/EXPERIENCE.md`,
`.agents/rules/environment.md`, a wave plan. Those are declared in `.path-refs-allow` as glob
patterns, each with a written reason. A pattern with no reason does not count as declared: an
allowlist that accepts bare lines is how a control gets quietly widened until it grades nothing.

Backticked only. `test-documented-commands` learned that the hard way -- ungated prose produces
`make it` and `make the`, and a control that cries wolf is one nobody reads.

Exit: 0 clean · 1 findings · 2 cannot run.
"""
import fnmatch
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import doc_text, documents, is_record, manifest_internal, scrubbed_env  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
ALLOW = PKG / ".path-refs-allow"

EXT = "md|py|sh|yml|yaml|toml|json|html|txt|csv|cfg|ini|lock|xml|env"
REF = re.compile(rf"`([A-Za-z0-9_][\w./-]*\.(?:{EXT}))`")
# Conformance fixtures are INPUTS a checker must reject or accept; `condition-evaporated.md` names a
# missing artifact on purpose, and a filled wave close or closure report cites the review files of a
# project that does not exist. Demanding that those paths exist would delete the fixtures' point.
FIXTURE = re.compile(r"^conformance/(fail|pass|wave|closure|reviews)/")
MANIFEST = PKG / "INSTALL-MANIFEST.md"


def gp_internal() -> set[str]:
    """The files that are never copied into a project, DERIVED from the manifest that decides it.

    A GP-internal document may cite files that live only in the repository that authors the
    package, and the citation is correct where it stands. The promise this control grades is the
    one made to a READER OF THE PRODUCT, so the subject is the delivered surface. Getting that
    boundary from the manifest rather than a second list here is the point: M2/M3 already keep the
    manifest honest.
    """
    if not MANIFEST.is_file():
        print("test-documented-paths CANNOT RUN: INSTALL-MANIFEST.md is missing, so the delivered "
              "surface cannot be established. A guess would grade the wrong tree.")
        raise SystemExit(2)
    names = manifest_internal(PKG)
    if names is None:
        print("test-documented-paths CANNOT RUN: no `## GP-INTERNAL` section in INSTALL-MANIFEST.md.")
        raise SystemExit(2)
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


def visible_files() -> tuple[set[str], str]:
    """The files a fresh clone would have: tracked, plus new files git would commit (not ignored).

    Existence on DISK was once the test, so a gitignored, generated file --
    `coverage.json`, a status record written beside a database -- satisfied it on the developer's
    machine and was missing on the CI runner: the same commit green locally and red in CI. What CI
    will see is what git would hand it. Not a git work tree (or no git): the disk, and it says so.
    """
    try:
        r = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=PKG, capture_output=True, encoding="utf-8", errors="replace",
                           timeout=30, env=scrubbed_env())
        if r.returncode == 0 and r.stdout.strip():
            return set(r.stdout.split("\n")) - {""}, "git"
    except (OSError, subprocess.SubprocessError):
        pass
    return {str(p.relative_to(PKG)) for p in PKG.rglob("*") if p.is_file() or p.is_symlink()}, "disk"


def main() -> int:
    docs = documents(PKG)
    if not docs:
        print("test-documented-paths FAIL: no document (.md or .html) found. An empty derived set "
              "is a failure, never a vacuous pass.")
        return 1

    # A reference with no directory in it names a file, it does not route to one: prose says
    # `check_records.py`, and a reader finds it. Requiring the full path there produced 60-odd
    # findings on files that ship -- the cry-wolf shape `test-documented-commands` was built to
    # avoid. A name that ships NOWHERE is still dangling, which is what the census planted.
    files, source = visible_files()
    dirs = {str(pathlib.PurePosixPath(f).parent) for f in files}
    dirs |= {str(q) for f in files for q in pathlib.PurePosixPath(f).parents}
    basenames = {pathlib.PurePosixPath(f).name for f in files}

    def resolves(target: str, rel_doc: pathlib.Path) -> bool:
        t = target.rstrip("/")
        for cand in (t, os.path.normpath(str(rel_doc.parent / t))):
            if cand in files or cand in dirs:
                return True
        # A Python project names modules relative to the package -- `workflows/x.py`
        # for `src/app/workflows/x.py`. Exactly ONE visible file ending in `/<target>` is that
        # file; two or more is ambiguous and still fails.
        if "/" in t and sum(1 for f in files if f.endswith("/" + t)) == 1:
            return True
        return "/" not in t and t in basenames

    internal = gp_internal()
    docs = [d for d in docs if str(d.relative_to(PKG)) not in internal]
    allow = declared()
    findings: list[str] = []
    historical = 0
    refs = 0
    for doc in docs:
        if FIXTURE.match(str(doc.relative_to(PKG))):
            continue
        rel_doc = doc.relative_to(PKG)
        for line_no, line in enumerate(doc_text(doc).splitlines(), 1):
            for m in REF.finditer(line):
                target = m.group(1)
                refs += 1
                if resolves(target, rel_doc):
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
                # A RECORD -- a review, a wave close, a closure report, an ADR -- is
                # append-only evidence of what was true when it was written. Grading it against
                # today's tree turned every retired file into a permanent failure in every record
                # that ever quoted it (91 on one project's first run, none a broken instruction).
                # Records are counted, not failed. Templates are instructions and stay strict.
                if (is_record(doc, PKG) and not doc.name.endswith(".template.md")
                        and not str(rel_doc).startswith("conformance/")):
                    historical += 1
                    continue
                findings.append(f"{rel_doc}:{line_no}: `{target}` -- no such file ships, and no "
                                f"row in .path-refs-allow declares it")

    for f in findings:
        print(f"  FAIL {f}")
    print(f"test-documented-paths {'FAIL' if findings else 'PASS'}: {refs} path reference(s) across "
          f"{len(docs)} DELIVERED document(s), {len(internal)} GP-internal path(s) excluded by the "
          f"manifest, {len(allow)} declared pattern(s), {len(findings)} dangling; {historical} in "
          f"records (evidence, not graded); files seen via {source}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
