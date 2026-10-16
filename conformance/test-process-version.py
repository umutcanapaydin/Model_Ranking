#!/usr/bin/env python3
"""Every delivered record and template declares the version this package IS, derived from UPGRADING.md.

WHY (v7.1, found by exporting the package and running `make install` in the export). The install marker
(`scripts/write_install_marker.py`) derives a project's version from the delivered records'
`process_version:` frontmatter -- and v7.1 shipped eleven records and templates still
saying `v7.0`, so every project installing v7.1 would have recorded `gp_version: v7.0`, and
`check_records.py` V1 would then have refused the brief that said `v7.1`. `test-delivered-tree`
compared the marker to `docs/decisions.md` -- to one of the stale records -- and passed.

DERIVED, not enumerated: the current version is the first `**`vX.Y`**` entry of UPGRADING.md's
"What changed for you" (newest first; a delivered document the upgrader reads), and the set of
records graded is every delivered `.md` outside `conformance/` whose frontmatter declares
`process_version:`. A fixture declares the version its rules are meant for and is not graded;
GP-internal records (the manifest's list) do not reach a project. An empty derived set on either
side is a failure, never a vacuous pass.

Exit: 0 clean - 1 findings - 2 cannot run (no UPGRADING.md).
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import manifest_internal   # noqa: E402

PKG = pathlib.Path(__file__).resolve().parent.parent
UPGRADING = PKG / "UPGRADING.md"
CURRENT_RE = re.compile(r"^\*\*`(v\d+(?:\.\d+)+)`\*\*", re.M)
DECLARED_RE = re.compile(r"\A---\s*\n(?:.*\n)*?process_version:\s*(\S+)\s*\n(?:.*\n)*?---", re.M)


def current_version() -> str | None:
    if not UPGRADING.is_file():
        return None
    text = UPGRADING.read_text(encoding="utf-8", errors="replace")
    at = text.find("## What changed for you")
    m = CURRENT_RE.search(text, at if at >= 0 else 0)
    return m.group(1) if m else None


def shipped_files() -> set | None:
    """In an installation (no `.gp-distribution`), the files the package delivers, named one by one in
    `INSTALL-MANIFEST.md` above its GP-INTERNAL section; None in the distribution package. model_ranking,
    D-199: an upgraded project's own records keep the version they were written under (wave_check and
    closure_check grade them by it), so only what the package ships is held to the package's version."""
    if (PKG / ".gp-distribution").is_file():
        return None
    man = PKG / "INSTALL-MANIFEST.md"
    if not man.is_file():
        return None
    text = man.read_text(encoding="utf-8", errors="replace")
    head = text.find("## GP-INTERNAL")
    names: set = set()
    for block in re.findall(r"```(.*?)```", text[:head] if head >= 0 else text, re.S):
        names.update(line.split()[0] for line in block.splitlines()
                     if line.strip() and not line.strip().startswith("#") and line.split()[0].endswith(".md"))
    return names


def main() -> int:
    want = current_version()
    if want is None:
        print("test-process-version CANNOT RUN: UPGRADING.md has no `**`vX.Y`**` entry under "
              "\"What changed for you\" -- nothing says which version this package is")
        return 2
    internal = manifest_internal(PKG) or set()
    shipped = shipped_files()
    bad: list[str] = []
    graded = 0
    for f in sorted(PKG.rglob("*.md")):
        rel = f.relative_to(PKG).as_posix()
        if rel.startswith(("conformance/", ".venv/")) or rel in internal or any(
                rel.startswith(d) for d in internal if d.endswith("/")):
            continue
        if shipped is not None and rel not in shipped:
            continue
        m = DECLARED_RE.match(f.read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        graded += 1
        if m.group(1) != want:
            bad.append(f"{rel}: declares `process_version: {m.group(1)}`, and this package is {want} "
                       "(UPGRADING.md) -- the install marker derives a project's version from this "
                       "line, so a stale one installs the wrong version")
    if graded == 0:
        print("test-process-version FAIL: no delivered record declares `process_version:` -- an "
              "empty derived set is a failure, never a vacuous pass")
        return 1
    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-process-version {'FAIL' if bad else 'PASS'}: {graded} delivered record(s) and "
          f"template(s) declare a process_version, {len(bad)} not {want}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
