#!/usr/bin/env python3
"""Every deployment-facing gate must name the artefact it reads.

A gate that inspects the repository while the deployment consumes something else is green and
uninformative. The field case: a project's go-live gate checked manifests the cluster did not run,
and stayed green straight through a customer deployment. Every claim it made was true about a file
nobody deployed. That is not a false pass; it is a true statement bound to the wrong object.

So each deployment-facing row in the closure checklist carries `binds:` -- the artefact it
inspects, and whether that artefact is what the deployment actually consumes. This test does not
evaluate the binding; it refuses to let a row exist without one, which is the only part a text
gate can honestly claim.

DERIVED, not enumerated: the rows are found by scanning §E.2's own section for checkbox lines that
invoke a `make` target. Nothing here lists which rows those are -- a hand-kept list of gates beside
the gates would drift from them.

Fail-closed: if the section cannot be located, or the derived set is empty, that is a FAILURE. A
vacuous pass is what a checklist gate looks like just before it stops meaning anything.

Exit: 0 pass · 1 any row missing `binds:` · 2 cannot evaluate.
"""
import pathlib
import re
import sys

PKG = pathlib.Path(__file__).resolve().parent.parent
CHECKLIST = PKG / "docs" / "closure-checklist.md"

# The deployment-facing section: E.2 is "Deploy + go-live readiness" (it was B.3 until deploy moved
# out of the milestone close into the once-only Release stage). Its heading is matched, not copied --
# the test follows the document if the heading is reworded around the anchor "E.2".
SECTION_RE = re.compile(r"^### E\.2\b.*?(?=^### |\Z)", re.M | re.S)
CHECKBOX_RE = re.compile(r"^- \[[ x]\] .*$", re.M)
MAKE_RE = re.compile(r"`make [a-z][\w-]*")
STRUCK_RE = re.compile(r"~~")


def main() -> int:
    if not CHECKLIST.is_file():
        print(f"test-binds-declared CANNOT RUN: no {CHECKLIST.relative_to(PKG)}")
        return 2

    body = CHECKLIST.read_text(encoding="utf-8")
    section = SECTION_RE.search(body)
    if not section:
        print("test-binds-declared FAIL: section E.2 (deploy + go-live readiness) not found. The "
              "deployment-facing gates are where this checks; if the section moved, this check is "
              "reading nothing and must not report success.")
        return 1

    rows = [r for r in CHECKBOX_RE.findall(section.group(0))
            if MAKE_RE.search(r) and not STRUCK_RE.search(r)]
    if not rows:
        print("test-binds-declared FAIL: no live deployment-facing gate rows derived from E.2. An "
              "empty derived set is a failure, never a vacuous pass -- either the gates were "
              "removed or this check no longer finds them, and both need a human.")
        return 1

    unbound = [r for r in rows if "binds:" not in r]
    for row in unbound:
        label = MAKE_RE.search(row).group(0).strip("`")
        print(f"  no `binds:` -- {label}: this row inspects something, and does not say what. A "
              f"gate bound to an artefact the deployment does not consume is NOT-BINDING, and "
              f"nobody can tell which it is from here.")

    verdict = "FAIL" if unbound else "PASS"
    print(f"test-binds-declared {verdict}: {len(rows)} deployment-facing gate(s), "
          f"{len(unbound)} without a `binds:` declaration")
    return 1 if unbound else 0


if __name__ == "__main__":
    sys.exit(main())
