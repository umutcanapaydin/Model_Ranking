#!/usr/bin/env python3
"""Every delivered record and template declares the version this package IS, derived from UPGRADING.md.

WHY (v7.1, found by exporting the package and running `make install` in the export). The install marker
(`scripts/write_install_marker.py`) derives a project's version from the delivered records'
`process_version:` frontmatter -- and v7.1 shipped eleven records and templates still
saying `v7.0`, so every project installing v7.1 would have recorded `gp_version: v7.0`, and
`check_records.py` V1 would then have refused the brief that said `v7.1`. `test-delivered-tree`
compared the marker to `docs/decisions.md` -- to one of the stale records -- and passed.

WHY THE SET IS THE MANIFEST'S (v7.1.1). v7.1 graded every `.md` under the package root, and in an
installation that root is the PROJECT: every upgraded project's own plans, closes and reviews -- graded
by the version they declare, never by today's -- went red, 109 of 121 in fitness_app and 280 of 292 in
model_ranking, and both hand-patched this file. A project record the package does not deliver is never
graded here.

DERIVED, not enumerated: the current version is the first `**`vX.Y`**` entry of UPGRADING.md's
"What changed for you" (newest first; a delivered document the upgrader reads), and the set graded is
every `.md` FILE that `INSTALL-MANIFEST.md`'s PROJECT section names one by one (`lib_record`), less
its GP-INTERNAL list, that declares `process_version:` -- the same set in the package and in an
installation. A directory entry (`docs/plans/`, `docs/reviews/`) holds the project's own records in an
installation, so nothing under one is graded; in the package (`.gp-distribution`) a `.md` under one
that declares a version is a finding, because an installation could not grade it. Fixtures
(`conformance/`) declare the version their rules are meant for and are not graded. An empty derived
set on either side is a failure, never a vacuous pass. Two cases in a throwaway tree prove both
polarities on every run: an old project record planted beside the delivered set stays green, and a
delivered template made stale goes red.

Exit: 0 clean - 1 findings - 2 cannot run (no UPGRADING.md).
"""
import pathlib
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import manifest_internal, manifest_project   # noqa: E402

PKG = pathlib.Path(__file__).resolve().parent.parent
CURRENT_RE = re.compile(r"^\*\*`(v\d+(?:\.\d+)+)`\*\*", re.M)
DECLARED_RE = re.compile(r"\A---\s*\n(?:.*\n)*?process_version:\s*(\S+)\s*\n(?:.*\n)*?---", re.M)


def current_version(root: pathlib.Path) -> str | None:
    upgrading = root / "UPGRADING.md"
    if not upgrading.is_file():
        return None
    text = upgrading.read_text(encoding="utf-8", errors="replace")
    at = text.find("## What changed for you")
    m = CURRENT_RE.search(text, at if at >= 0 else 0)
    return m.group(1) if m else None


def delivered(root: pathlib.Path) -> tuple[list[str], list[str]] | None:
    """(the `.md` files the manifest names one by one, its PROJECT directory entries), GP-internal and
    fixtures excluded; None when the manifest cannot be read."""
    entries = manifest_project(root)
    if entries is None:
        return None
    internal = manifest_internal(root) or set()
    files = sorted(e for e in entries if not e.endswith("/") and e.endswith(".md") and e not in internal
                   and not e.startswith("conformance/"))
    dirs = sorted(e for e in entries if e.endswith("/") and e != "conformance/")
    return files, dirs


def declared(f: pathlib.Path) -> str | None:
    if not f.is_file():
        return None
    m = DECLARED_RE.match(f.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else None


def grade(root: pathlib.Path) -> tuple[int, list[str], str]:
    """(records graded, findings, the version wanted) for the tree at `root`."""
    want = current_version(root)
    if want is None:
        return 0, [], ""
    got = delivered(root)
    if got is None:
        return 0, ["INSTALL-MANIFEST.md has no PROJECT section here -- the delivered set cannot be "
                   "derived, and a guess would grade the project's own records (fail closed)"], want
    files, dirs = got
    bad: list[str] = []
    graded = 0
    for rel in files:
        v = declared(root / rel)
        if v is None:
            continue
        graded += 1
        if v != want:
            bad.append(f"{rel}: declares `process_version: {v}`, and this package is {want} "
                       "(UPGRADING.md) -- the install marker derives a project's version from this "
                       "line, so a stale one installs the wrong version")
    if (root / ".gp-distribution").is_file():
        for d in dirs:
            for f in sorted((root / d).rglob("*.md")):
                rel = f.relative_to(root).as_posix()
                if rel not in files and declared(f) is not None:
                    bad.append(f"{rel}: declares `process_version:` and is delivered only under the "
                               f"directory entry `{d}` -- an installation cannot tell it from the "
                               "project's own records, so it is never graded there; name it in "
                               "INSTALL-MANIFEST.md")
    return graded, bad, want


def self_cases() -> list[str]:
    """Both polarities, in a throwaway copy of the delivered set: a planted old project record stays
    green, and a delivered template made stale goes red."""
    got = delivered(PKG)
    if got is None:
        return []
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        tree = pathlib.Path(d)
        for rel in ["INSTALL-MANIFEST.md", "UPGRADING.md"] + got[0]:
            if (PKG / rel).is_file():
                (tree / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(PKG / rel, tree / rel)
        old = "---\nrecord_type: wave\nid: m1-wave-1-close\nstatus: ratified\nprocess_version: v6.0\n---\n"
        for rel in ("docs/plans/m1-wave-1-close.md", "docs/reviews/m1-wave-1-review.md",
                    "docs/notes/old-plan.md"):
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            (tree / rel).write_text(old, encoding="utf-8")
        graded, findings, _ = grade(tree)
        if findings or graded == 0:
            bad.append("an installation's own older records (docs/plans/, docs/reviews/, an unlisted "
                       f"file) declaring v6.0 must not be graded, and the throwaway tree gave {graded} "
                       f"graded, {len(findings)} finding(s): {findings[:2]}")
        stale = next((rel for rel in got[0] if rel.endswith(".template.md")
                      and declared(tree / rel) is not None), None)
        if stale is None:
            bad.append("no delivered template declares `process_version:` -- the red case has nothing to "
                       "make stale (an empty derived set is a failure)")
        else:
            f = tree / stale
            f.write_text(re.sub(r"(?m)^process_version:.*$", "process_version: v0.0",
                                f.read_text(encoding="utf-8"), count=1), encoding="utf-8")
            _, findings, _ = grade(tree)
            if not any(x.startswith(stale + ":") for x in findings):
                bad.append(f"the delivered template {stale} made stale (v0.0) was not refused -- the "
                           "check grades nothing it delivers")
    return bad


def main() -> int:
    graded, bad, want = grade(PKG)
    if not want:
        print("test-process-version CANNOT RUN: UPGRADING.md has no `**`vX.Y`**` entry under "
              "\"What changed for you\" -- nothing says which version this package is")
        return 2
    if graded == 0 and not bad:
        print("test-process-version FAIL: no delivered record declares `process_version:` -- an "
              "empty derived set is a failure, never a vacuous pass")
        return 1
    bad += [f"self-case: {b}" for b in self_cases()]
    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-process-version {'FAIL' if bad else 'PASS'}: {graded} delivered record(s) and "
          f"template(s) named in INSTALL-MANIFEST.md declare a process_version, {len(bad)} finding(s) "
          f"against {want}; a planted old project record stays green, a stale template goes red")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
