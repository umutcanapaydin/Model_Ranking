#!/usr/bin/env python3
"""Write `.gp/installed` — the marker that records which GP version this tree installed.

Condition 16-3 (Increment 16), closing GPF-B03. Four consecutive field harvests had to GUESS the
installed version. Three of them read the prose claim in `docs/decisions.md`; the 2026-08-19 harvest
checked that claim against what the packages actually ship and found a repo asserting v4.2 while
missing six of v4.2's install artefacts. **A version a tree asserts about itself is a claim. This
file is a measurement, written by the install step that did the installing.**

Derived, never enumerated (V5C-110): the version is read from the governance records' own
`process_version` frontmatter, and the manifest hash is computed from the manifest file. Neither
value is typed into this script, so neither can drift from it.

Fail-closed (Security seat, Increment 16): an absent manifest, an unreadable record, or a tree whose
records disagree about their version is a FAILURE that refuses to write a marker. A marker nobody
can trust is worse than no marker, because the next harvest would believe it.

Exit: 0 written · 1 refused (reason on stderr) · 2 internal error.
"""
import hashlib
import pathlib
import re
import subprocess
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "INSTALL-MANIFEST.md"
MARKER_DIR = ROOT / ".gp"
MARKER = MARKER_DIR / "installed"

# The records the version is derived FROM. Both are PROJECT-class, so both exist in any correct
# installation; `install-check` M1 is what guarantees that, and this refuses rather than guessing
# if it is wrong. They are named here as inputs, not as a copy of the answer.
VERSION_SOURCES = ("docs/decisions.md", "docs/watchlist.md")

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
PROCESS_VERSION_RE = re.compile(r"^process_version:\s*(\S+)\s*$", re.M)


def read_process_version(path: pathlib.Path) -> str | None:
    """Return the `process_version` in a record's frontmatter, or None if it has none."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    block = FRONTMATTER_RE.match(text)
    if not block:
        return None
    found = PROCESS_VERSION_RE.search(block.group(1))
    return found.group(1) if found else None


def main() -> int:
    if not MANIFEST.is_file():
        print(f"REFUSED: no {MANIFEST.name} — this tree has no declared installation contract, so "
              f"there is no version to record.", file=sys.stderr)
        return 1

    versions = {}
    for rel in VERSION_SOURCES:
        version = read_process_version(ROOT / rel)
        if version is None:
            print(f"REFUSED: {rel} carries no `process_version` frontmatter. The marker is derived "
                  f"from the records; a record that does not declare its version cannot be the "
                  f"source of one.", file=sys.stderr)
            return 1
        versions[rel] = version

    distinct = set(versions.values())
    if len(distinct) != 1:
        detail = " · ".join(f"{k} = {v}" for k, v in versions.items())
        print(f"REFUSED: the records disagree about which version this is ({detail}). A marker "
              f"written from a disagreement would launder it into the next harvest's telemetry.",
              file=sys.stderr)
        return 1
    version = distinct.pop()

    manifest_hash = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()

    # Best effort, and labelled as such: a tree with no git history is a legitimate installation.
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=10).stdout.strip() or "none"
    except (OSError, subprocess.SubprocessError):
        commit = "none"

    MARKER_DIR.mkdir(exist_ok=True)
    MARKER.write_text(
        "# Written by `make install`. Do not edit by hand — it is a measurement, not a claim.\n"
        "# A harvest reads this instead of believing what a document says about its own version.\n"
        f"gp_version: {version}\n"
        f"manifest_sha256: {manifest_hash}\n"
        f"manifest_path: {MANIFEST.name}\n"
        f"installed_from_commit: {commit}\n"
        f"installed_on: {date.today().isoformat()}\n"
        f"version_derived_from: {', '.join(VERSION_SOURCES)}\n",
        encoding="utf-8")

    print(f"install marker: {version} · manifest {manifest_hash[:12]} → {MARKER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"write_install_marker internal error: {exc}", file=sys.stderr)
        sys.exit(2)
