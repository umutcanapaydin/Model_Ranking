#!/usr/bin/env python3
"""check_records.py — governance-record validator (V4C-30, Increment 11).

STDLIB ONLY. No dependencies, ever: this file sits on a governance path, and the round's most
transferable empirical result was "adopt formats, write your own 150 lines, never adopt a 10-star
dependency for governance" (V4C-41).

Idiom copied from python/peps' check-peps.py: required-field sets, one validator per field,
`path:line: message` output, non-zero exit. Prose stays canonical markdown; this reads only the
YAML frontmatter block and a few cross-file facts.

WHAT IT CHECKS
  Per record (frontmatter):   R1 required fields · R2 closed enums · R3 id format+uniqueness
  Cross-record:               X1 supersedes/requires resolve · X2 no cycle · X3 status-flow order
  Propagation (V4C-36):       P1 declared propagation rows are not `pending`
                              P2 each package's pipeline-design.md keeps its §0 changelog heading
                                 (the ONE verified field incident: v3.3 lost it)
                              P3 executive-overview file count == actual package file count
                                 (the second, already-auto-fixed incident — kept as a regression test)
  Pins (V4C-43-adjacent):     N1 no /blob/main|master/ URL is called a "pin"
  Conditions (V4C-25, v4.2):  C1a a condition's closure artifact must be NAMEABLE (path or record
                                  id in backticks), forward-only from v4.2
                              C1b a DUE condition whose named artifact is absent = EVAPORATED;
                                  an artifact may be `path#anchor`, and the anchor string
                                  must be IN the file (v4.3: 'the file exists' was not
                                  evidence the change landed)
                                  (the V4C-25 and V4C-12 incidents; see council-telemetry.md)
  Drift (v4.2):               D1 the shipped validator copy == the one CI runs
  Install (v4.3):             M1 a PROJECT path is missing from an install (--install)
                              M2 a GP-INTERNAL path leaked into an install (--install)
                              M3 a package path is in neither list (manifest rot)
  Language (v4.3):            L1 the repository is written in ENGLISH (V4C-79); reasoned
                                 allowlist at .language-allow
  Warnings (v4.3):            C2a a warning may not survive the close it was raised in
                              C2b the same control ACCEPTED 3x -> the CONTROL goes under review
                              C2c ACCEPTED without a reason and an owning milestone

WHAT IT DELIBERATELY DOES NOT CHECK (V4C-35 narrowness rule): prose quality, rationale truth,
whether a review was independent, or anything a human must judge. Shape only.

Usage:
  python3 scripts/check_records.py                 # validate the repo
  python3 scripts/check_records.py --self-test     # run conformance/ fixtures (CI self-test, V4C-32)
  python3 scripts/check_records.py --historical    # informational: ALL packages (day-1 falsification)
Exit: 0 clean · 1 findings · 2 usage/internal error.

COST LINE (V4C-13, binding condition of Increment 11): fires on every push and pre-commit;
~1-3 s per run; bypass = `git commit --no-verify` or an admin merge, both recorded in the
wave-checklist row-9 bypass ledger. Owner may bypass; agents may not.
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

# ── declared vocabulary (narrow by rule V4C-35: every field drives a check below) ──────────
# v4.3.2. The first seven are GP's OWN governance species. The rest are a PROJECT's, added when an
# external reviewer pointed out that `.governed-records` shipped naming project files that could never
# pass `R2` — the record model literally had no word for a closure report. **A governance model that
# cannot name the artefacts of the thing it governs is not installed, it is on display.**
RECORD_TYPES = {"ratification", "register", "adr", "experience", "handover", "design", "council",
                "closure", "wave", "fixpack", "brief", "status", "license-review", "warnings"}
STATUS_FLOW = ["draft", "candidate", "ratified", "superseded", "retired"]  # X3 ordering
REQUIRED = ("record_type", "id", "status")
OPTIONAL = ("process_version", "supersedes", "requires", "subject_ref", "propagation",
            "evidence_ref", "approvers", "date")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9.\-]{2,63}$")
FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
PIN_RE = re.compile(r"https?://\S*/blob/(?:main|master)/\S*")


def _today() -> str:
    """Overridable so the C1 fixtures can pin a date instead of drifting into failure over time."""
    return os.environ.get("CHECK_RECORDS_TODAY") or datetime.date.today().isoformat()


class Finding:
    __slots__ = ("line", "msg", "path", "rule")

    def __init__(self, path, line, rule, msg):
        self.path, self.line, self.rule, self.msg = path, line, rule, msg

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.msg}"


# ── a deliberately tiny YAML subset: scalars, inline lists, and one level of list-of-maps ──
def parse_frontmatter(text: str) -> tuple[dict | None, int]:
    """Return (fields, first_line_of_frontmatter) or (None, 0) when absent."""
    m = FM_RE.match(text)
    if not m:
        return None, 0
    out: dict = {}
    key = None
    for raw in m.group(1).splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^\s*-\s", line):  # list item under the last key
            item = line.split("-", 1)[1].strip()
            if key:
                out.setdefault(key, [])
                if isinstance(out[key], list):
                    out[key].append(item.strip("\"'"))
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                out[key] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
            elif v == "":
                out[key] = []
            else:
                out[key] = v.strip("\"'")
    return out, 2


def validate_record(path: Path, root: Path) -> tuple[list[Finding], dict | None]:
    f: list[Finding] = []
    rel = path.relative_to(root)
    text = path.read_text(encoding="utf-8", errors="replace")
    fields, ln = parse_frontmatter(text)
    if fields is None:
        return [Finding(rel, 1, "R1", "no YAML frontmatter block (record is unparsed prose)")], None

    for k in REQUIRED:                                              # R1
        if not fields.get(k):
            f.append(Finding(rel, ln, "R1", f"missing required field `{k}`"))
    rt = fields.get("record_type")
    if rt and rt not in RECORD_TYPES:                               # R2
        f.append(Finding(rel, ln, "R2", f"record_type `{rt}` not in {sorted(RECORD_TYPES)}"))
    st = fields.get("status")
    if st and st not in STATUS_FLOW:                                # R2
        f.append(Finding(rel, ln, "R2", f"status `{st}` not in {STATUS_FLOW}"))
    rid = fields.get("id")
    if rid and not ID_RE.match(str(rid)):                           # R3
        f.append(Finding(rel, ln, "R3", f"id `{rid}` must match {ID_RE.pattern}"))
    for k in fields:                                                # V4C-35: no undeclared fields
        if k not in REQUIRED + OPTIONAL:
            f.append(Finding(rel, ln, "R2", f"undeclared field `{k}` "
                                            "(V4C-35: only fields that drive a check may exist)"))
    for row in fields.get("propagation", []) or []:                 # P1
        if "pending" in str(row):
            f.append(Finding(rel, ln, "P1", f"propagation row still pending: {row}"))
    for i, line in enumerate(text.splitlines(), 1):                 # N1
        if PIN_RE.search(line) and re.search(r"\bpin(ned)?\b", line, re.I):
            f.append(Finding(rel, i, "N1", "a /blob/main/ URL is described as a pin — "
                                           "it tracks HEAD; use a commit SHA"))
    return f, fields


def cross_record(records, root: Path) -> list[Finding]:
    """Cross-file rules. `records` is a LIST of (path, fields).

    v4.2 REPAIR (Increment 12, Quality seat): this used to take a dict keyed by record id, built by
    `collect()`. Two records sharing an id therefore collapsed into one entry BEFORE arriving here,
    so the R3 uniqueness branch below could never fire on any path — dead code since v4.1. Taking a
    list means duplicates survive to be seen. Cluster A again, inside the validator itself.
    """
    if isinstance(records, dict):        # tolerate the old call shape
        records = list(records.values())
    f: list[Finding] = []
    seen: dict[str, Path] = {}
    for path, fields in records:
        rid = str(fields.get("id", ""))
        if rid in seen and seen[rid] != path:                       # R3 uniqueness
            f.append(Finding(path.relative_to(root), 2, "R3",
                             f"duplicate id `{rid}` (also {seen[rid].relative_to(root)})"))
        seen.setdefault(rid, path)
    by_id = {str(fl.get("id", "")): (p, fl) for p, fl in records}
    for path, fields in records:
        rel = path.relative_to(root)
        for ref in (fields.get("supersedes", []) or []) + (fields.get("requires", []) or []):
            if ref and ref not in seen:                             # X1
                f.append(Finding(rel, 2, "X1", f"reference `{ref}` resolves to no record"))
        sup = fields.get("supersedes", []) or []
        for ref in sup:                                             # X2 (1-hop cycle)
            other = by_id.get(ref)
            if other and str(fields.get("id")) in (other[1].get("supersedes", []) or []):
                f.append(Finding(rel, 2, "X2", f"supersession cycle with `{ref}`"))
        for ref in fields.get("requires", []) or []:                # X3 status-flow ordering
            other = by_id.get(ref)
            if not other:
                continue
            try:
                if STATUS_FLOW.index(str(fields.get("status"))) > STATUS_FLOW.index(
                        str(other[1].get("status"))):
                    f.append(Finding(rel, 2, "X3",
                                     f"status `{fields.get('status')}` is ahead of its dependency "
                                     f"`{ref}` (`{other[1].get('status')}`)"))
            except ValueError:
                pass
    return f


def current_package(root: Path) -> Path | None:
    """The version the repo is shipping = the highest general_pipeline_v* by numeric order."""
    def key(p: Path):
        return [int(x) if x.isdigit() else 0
                for x in re.findall(r"\d+", p.name.replace("general_pipeline_v", ""))]
    pkgs = [p for p in root.glob("general_pipeline_v*") if p.is_dir()]
    return max(pkgs, key=key) if pkgs else None


def package_invariants(root: Path, scope: str = "current") -> list[Finding]:
    """P2/P3 — the two propagation regressions we actually paid for.

    scope="current": only the shipping version BLOCKS. Prior packages are FROZEN by the standing
    versioning rule (never edit a prior version to produce a new one), so a finding there is
    history, not a defect to fix — surface it with `--historical`.
    """
    f: list[Finding] = []
    cur = current_package(root)
    for pkg in sorted(root.glob("general_pipeline_v*")):
        if not pkg.is_dir():
            continue
        if scope == "current" and pkg != cur:
            continue
        if pkg.name == "general_pipeline_v2.0":
            continue  # the §0-changelog convention begins at v2.1; v2.0 predates it (scoped, not ignored)
        design = pkg / "pipeline-design.md"
        if not design.exists():
            design = pkg / "pipeline-v2-design.md"
        if design.exists():                                          # P2
            body = design.read_text(encoding="utf-8", errors="replace")
            if not re.search(r"^##\s*§0\s*[—-]\s*Changelog", body, re.M):
                f.append(Finding(design.relative_to(root), 1, "P2",
                                 "§0 changelog heading missing (the v3.3 propagation incident: "
                                 "a patch helper consumed it and no check noticed)"))
        overview = pkg / "docs" / "executive-overview.md"
        if overview.exists():                                        # P3
            actual = sum(1 for p in pkg.rglob("*")
                         if (p.is_file() or p.is_symlink()) and "__pycache__" not in p.parts)
            body = overview.read_text(encoding="utf-8", errors="replace")
            claimed = {int(m) for m in re.findall(r"(?:about |\()(\d{2,3}) files", body)}
            for c in claimed:
                if c != actual:
                    f.append(Finding(overview.relative_to(root), 1, "P3",
                                     f"claims {c} files, package contains {actual}"))
    return f


# ── C1: condition closure (V4C-25, Increment 12) ────────────────────────────────────────────
# WHY. V4C-22 ratified "conditions carry owner + date + closure artifact" and "a condition without
# its artifact evaporates" — and created NO check that the artifact existed at the date. Two
# conditions then evaporated in silence: V4C-25 (caught by the Skeptic seat) and V4C-12 (caught by
# nobody until council-telemetry.md was written). See council-telemetry.md TB-006/TB-007.
#
# THE HONEST SCOPE, and it is a concession to the Software seat's audit. The corpus contains TWO
# incompatible condition formats. v4.0-ratification.md embeds conditions as free prose in a ballot
# table's 4th column, whose "dates" are release names ("v4.1 cut", "this cut", "at cut") and whose
# artifacts are prose ("telemetry spec + first traceback report") — machine-unresolvable by
# construction. A parser tuned to the newer 5-column table would NOT have caught TB-006/007, which
# is precisely the false precision the seat warned about. So C1 does not pretend:
#   C1a  FORWARD-ONLY, BLOCKING. In records at process_version >= v4.2, every condition row must
#        name a closure artifact that is machine-resolvable — a backticked path that exists, or a
#        record id that resolves. An unresolvable prose artifact FAILS. This is what makes C1b
#        possible at all, and it is why the rule is worth having.
#   C1b  BLOCKING wherever the artifact IS resolvable and the due marker has passed: the artifact
#        must exist. "Evaporated" is the finding.
# Legacy prose conditions are reported by --historical, never silently treated as satisfied.
#
# COST LINE (V4C-13): ~70 lines, no dependency, <0.1 s. One new failure mode — a malformed
# conditions table reads as "no conditions" — which is why conformance/fail/ ships
# `condition-evaporated.md` AND `condition-unresolvable-artifact.md`, and why the self-test asserts
# on a degenerate table too. A check with no fixture is the thing this rule exists to punish.
ISO_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
CUT_RE = re.compile(r"\bv(\d+\.\d+)\b|\b(?:this|the) cut\b|\bat cut\b", re.I)
TICK_RE = re.compile(r"`([^`]+)`")
PATHISH_RE = re.compile(r"(?:^|/)[\w.-]+\.(?:md|py|sh|ya?ml|html|json|txt|pdf|xlsx|csv)$|/")


def _version_tuple(s: str):
    return tuple(int(x) for x in re.findall(r"\d+", s))


def _shipped_versions(root: Path) -> set:
    return {p.name.replace("general_pipeline_v", "")
            for p in root.glob("general_pipeline_v*") if p.is_dir()}


def condition_rows(text: str):
    """Yield (line_no, cells) for rows of a CONDITIONS table.

    v4.2 fix (pre-ship external audit): the first version matched only tables under a heading
    literally reading "binding conditions". A zero-context reviewer ran it across the corpus and
    found it saw **1 of 16** governed records — every ratification record uses a different heading,
    so C1 could not fire on the one document carrying live obligations even months past due. The
    headline repair of this cut was itself a dead control.

    A table is a conditions table when its HEADER ROW names all three parts of the V4C-22 contract:
    a condition, a date/due, and a closure artifact. Structure, not prose. That is also exactly the
    shape V4C-22 requires, so a table that does not match is not a conditions table by definition.
    """
    hdr_cond = re.compile(r"condition", re.I)
    hdr_date = re.compile(r"\bdate\b|\bdue\b", re.I)
    hdr_art = re.compile(r"artifact|artefact|closure|evidence", re.I)
    in_tbl = False
    for i, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            in_tbl = False
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            in_tbl = False
            continue
        if set("".join(cells)) <= set("-: "):          # separator row — keep state
            continue
        # A HEADER row is short and unformatted. Without this, traceback DATA rows whose prose
        # happens to contain "condition", a date and "artifact" were read as headers — found by
        # running the rule against the corpus, which is how the previous version's blindness was
        # found too. The three matches must also land on THREE DISTINCT cells: v4.0-ratification's
        # legacy ballot column is literally headed "Binding conditions (owner · date · closure
        # artifact)", one cell doing all three jobs, and that format is deprecated, not parsed.
        if all(len(c) <= 30 and "`" not in c and "**" not in c for c in cells):
            i_c = {n for n, c in enumerate(cells) if hdr_cond.search(c)}
            i_d = {n for n, c in enumerate(cells) if hdr_date.search(c)}
            i_a = {n for n, c in enumerate(cells) if hdr_art.search(c)}
            if i_c and i_d and i_a and len(i_c | i_d | i_a) >= 3:
                in_tbl = True                          # this is the header row
                continue
        if in_tbl:
            yield i, cells


def condition_closure(root: Path, records, scope: str = "current") -> list[Finding]:
    f: list[Finding] = []
    ids = {str(fl.get("id", "")) for _, fl in records}
    shipped = _shipped_versions(root)
    today = _today()
    for path, fields in records:
        pv = str(fields.get("process_version") or "")
        # C1a (artifact must be machine-resolvable) is FORWARD-ONLY: ratified history is frozen and
        # its prose conditions cannot be retroactively rewritten. C1b (a due, resolvable artifact
        # must exist) applies to EVERY record — restricting it by generation was the first bug in
        # this rule, and it silently exempted the exact register that carries the live conditions.
        forward = bool(pv) and _version_tuple(pv) >= (4, 2)
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="replace")
        for ln, cells in condition_rows(text):
            row = " ".join(cells)
            artifact_cell = cells[-1]
            # ---- is it due? -------------------------------------------------------------
            due = False
            iso = ISO_RE.search(row)
            if iso:
                due = iso.group(1) <= today
            else:
                m = CUT_RE.search(row)
                if m:
                    due = (m.group(1) in shipped) if m.group(1) else (pv in shipped)
            # ---- name the artifact ------------------------------------------------------
            # The FIRST version of this block asked "is the artifact resolvable?" and then failed
            # only when a resolvable artifact was missing — which is circular: resolvable meant it
            # existed, so the branch could never fire. Caught by falsifying it before shipping.
            # A named-but-absent artifact and an unnameable one are DIFFERENT findings.
            # v4.3 REPAIR. C1b used to accept "the file exists". Three conditions of this very cut
            # named artefacts that ALREADY existed before the condition was written — so each one
            # satisfied itself, and the validator passed green while none of the work had been done.
            # Found by the owner asking for a full sweep. Same class as everything else this session:
            # a control that cannot distinguish "arrived" from "was already there".
            # FIX: an artefact may name `path#anchor`. The anchor is a literal string that must appear
            # IN the file. That turns "the file exists" into "the change landed."
            satisfied = False        # a token that resolves: an existing path, or a real record id
            missing: list = []       # path-shaped tokens that are absent, or whose anchor is absent
            for tok in TICK_RE.findall(artifact_cell):
                _parts = tok.strip().split()
                if not _parts:        # an empty backtick pair -> IndexError, exit 1, later rules aborted
                    continue
                tok = _parts[0].rstrip(",;:)")
                path_part, _, anchor = tok.partition("#")
                target = root / path_part
                if anchor:
                    if target.is_file() and anchor in target.read_text(
                            encoding="utf-8", errors="replace"):
                        satisfied = True
                        break
                    if PATHISH_RE.search(path_part):
                        missing.append(tok)
                    continue
                if tok in ids or target.exists():
                    satisfied = True
                    break
                if PATHISH_RE.search(tok):
                    missing.append(tok)
            # ---- C1b: due, an artifact was NAMED, and it is not there --------------------
            if due and not satisfied and missing:
                tok = missing[0]
                why = ("does not exist" if "#" not in tok else
                       "exists but does not contain the anchor the condition named — the file was "
                       "already there; the CHANGE did not land")
                f.append(Finding(rel, ln, "C1b",
                                 f"condition EVAPORATED — it is due and its named closure artifact "
                                 f"`{tok}` {why} (V4C-22: a condition without its artifact is not "
                                 "a condition)"))
            # ---- C1a: forward-only — the artifact must be nameable at all ----------------
            # The dash variants below are DATA, not prose: a record may write "no artifact" as an
            # em dash, an en dash, a hyphen or `n/a`, and the rule accepts all four. Flagging the
            # en dash as a typo would be right in a sentence and wrong in a set of accepted spellings.
            elif forward and not satisfied and not missing \
                    and artifact_cell not in ("", "—", "-", "n/a", "–"):  # noqa: RUF001
                f.append(Finding(rel, ln, "C1a",
                                 "condition's closure artifact is not machine-resolvable — name a "
                                 "`path` or a record `id` in backticks, not prose "
                                 f"(row: {cells[0][:24]!r})"))
    return f


# ── M1/M2/M3: the install manifest (V4C-72/76, v4.3) ────────────────────────────────────────
# WHY. For twelve cuts nobody declared which files constitute an installation, and the field showed
# the copy step was wrong in BOTH directions simultaneously: a correct install carried 19 GP-internal
# files (11 handovers, 2 decks, the design docs, the exec overview) into a customer delivery tree,
# while the actual install silently dropped `.agents/rules/`, `.claude/` and `docs/closure-checklist.md`
# — the house rules, the hooks, and the checklist Stage 4 opens by walking. Two milestones closed
# without them. A copy step with no declared contract cannot be wrong, because nothing said what
# right was. See INSTALL-MANIFEST.md.
#
# COST LINE (V4C-13): ~60 lines, stdlib, <0.1 s. New failure mode: a legitimately new package file
# FAILS M3 until classified. Deliberate. Fixtured, so the rule is proven to fire.
# v4.3.2 REPAIR (audit B2). The walk had no exclusions, so `make check` -- whose first steps create a
# virtualenv -- then failed L1 on Turkish characters inside `pip/_vendor/rich/_emoji_codes.py`. The gate
# poisoned itself with the output of its own first step, and told the user to translate pip's source or
# add it to `.language-allow`. **README promised "green on day 1"; it was red the moment you installed.**
SKIP_DIRS = {".venv", "venv", ".git", "node_modules", "site-packages", "__pycache__",
             ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build", ".tox", ".eggs"}


def _skip(rel: Path) -> bool:
    return any(part in SKIP_DIRS or part.endswith(".egg-info") for part in rel.parts)


LOCK_NAME = ".install-lock"          # per-directory file counts, written at export
DIST_MARKER = ".gp-distribution"   # present in the package, never in an install
MANIFEST_NAME = "INSTALL-MANIFEST.md"
FENCE_RE = re.compile(r"^```")


def parse_manifest(path: Path) -> tuple[set, set, set]:
    """Return (project_paths, gp_internal_paths, ships_empty) from the fenced sections."""
    project: set = set()
    internal: set = set()
    empty: set = set()
    bucket = None
    in_fence = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^##\s+PROJECT\b", line):
            bucket, in_fence = project, False
            continue
        if re.match(r"^###\s+Ships empty\b", line):
            bucket, in_fence = empty, False
            continue
        if re.match(r"^##\s+GP-INTERNAL\b", line):
            bucket, in_fence = internal, False
            continue
        if re.match(r"^##\s+What the check does|^##\s+Cost line|^##\s+How to read", line):
            bucket = None
            continue
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence and bucket is not None:
            tok = line.split("#")[0].split("(")[0].strip().strip("`")
            while tok.startswith("./"):      # NOT lstrip("./") -- that eats the dot in `.agents/`
                tok = tok[2:]
            # v4.3 REPAIR (auditor N4): an absolute or escaping declaration satisfied M1 trivially.
            if not tok or tok.startswith("/") or ".." in Path(tok).parts:
                continue
            bucket.add(tok.rstrip("/") + ("/" if tok.endswith("/") else ""))
    return project, internal, empty


def _pkg_paths(pkg: Path) -> set:
    # S1: the exclusion had been wired into L1 only, so M3 emitted one finding per venv file.
    """Every path in a package, as manifest-shaped strings; a declared dir collapses its subtree."""
    out = set()
    for p in pkg.rglob("*"):
        # S1: the SKIP_DIRS exclusion had been wired into L1 only, so a `.venv` in the package made
        # M3 emit one finding per vendored file and P3 fail on the count. Half a repair reads as none.
        if _skip(p.relative_to(pkg)):
            continue
        rel = p.relative_to(pkg).as_posix()
        out.add(rel + "/" if p.is_dir() else rel)
    return out


def _covered(rel: str, declared: set) -> bool:
    """A file is covered if itself is declared, or any ancestor directory is."""
    if rel in declared:
        return True
    parts = rel.split("/")
    return any("/".join(parts[:i]) + "/" in declared for i in range(1, len(parts)))


def _installed(p: Path, empty_ok: bool = False, expect_min: int | None = None) -> bool:
    """Present AND carrying content.

    v4.3 REPAIR (auditor B5). `.exists()` accepted a 0-byte file and an empty directory, so a filtered
    `rsync` that creates the tree and copies nothing passed M1 with exit 0. The auditor emptied
    `AGENTS.md`, `.claude/skills/`, `subagent-profiles/` and `conformance/` — 105 files down to 68 — and
    got `PASS: no findings`. **That is the field incident this rule exists for, wearing a different hat.**
    """
    if p.is_dir():
        # A directory holding only `.gitkeep` is INTENTIONALLY empty and is correctly installed. The
        # size>0 rule (added to catch a filtered copy that made directories and copied nothing) flagged
        # `docs/plans/`, `docs/reviews/` and `docs/retrospectives/` as missing, because `.gitkeep` is
        # zero bytes by definition. **A repair that cannot tell "deliberately empty" from "silently
        # dropped" has replaced one false report with another.**
        # v4.3.2 REPAIR, SECOND ATTEMPT (audit B4). The first `.gitkeep` exemption applied to every
        # declared directory: an auditor cut `.claude/skills/`, `subagent-profiles/` and `conformance/`
        # to one 0-byte `.gitkeep` each -- 118 files to 42 -- and got PASS. The chair's first repair of
        # THAT read "only `.gitkeep` present is fine", which is the identical hole restated. Emptiness
        # cannot be inferred from the tree, because an emptied directory and a deliberately empty one
        # look the same. **It has to be DECLARED**, so `empty_ok` comes from the manifest's own
        # "Ships empty" section and nowhere else.
        if empty_ok:
            return True
        # THIRD iteration of this hole (105->68, then 118->42, then 121->67). Each repair moved the
        # threshold -- `.exists()`, then "any file", then "any non-empty file" -- and each time an
        # auditor satisfied the new threshold with a token file. A byte count cannot express "this
        # directory still contains what it shipped with". **Compare against the manifest's own count.**
        # Count the SAME WAY the lock counts, or the two disagree and the gate fails correct work:
        # the first pairing had the lock count all files and this count only non-empty ones, so a
        # legitimately empty `src/__init__.py` made `src/` look incomplete. When a count is available
        # the size threshold is redundant AND wrong; it only matters as a fallback.
        files = [q for q in p.rglob("*") if q.is_file() and q.name != ".gitkeep"
                 and not _skip(q.relative_to(p))]
        if expect_min is not None:
            return len(files) >= expect_min
        return any(q.stat().st_size > 0 for q in files)
    return p.is_file() and p.stat().st_size > 0


def manifest_rules(root: Path, install: Path | None = None) -> list[Finding]:
    """M1/M2/M3 against INSTALL-MANIFEST.md.

    v4.3 REPAIR, found by a zero-context reviewer minutes after the rule shipped. The first version
    located the manifest only inside `current_package(root)` — a `general_pipeline_v*` directory. But
    every shipped invocation (`make install-check`, the CI leg, the pre-commit hook) runs with root
    ".", and **once those files are copied into a customer project there is no such directory** — that
    is precisely what M2 exists to guarantee. So the headline rule of this release passed silently,
    with exit 0, in the one place it was written to run. The reviewer proved it with a fake project
    containing both a missing PROJECT path and a leaked GP-INTERNAL file: `no findings`.
    **A control that cannot fire where it matters is a dead control, however well it works elsewhere.**

    FIX: the manifest is a declared PROJECT file, so an installed tree carries its own copy. Look for
    it in the install tree FIRST, then fall back to the package.
    """
    f: list[Finding] = []
    cur = current_package(root)
    man = None
    if install and (install / DIST_MARKER).is_file():
        # v4.3.2. `README.md` says "first command: make install-check", and a person who has just
        # copied the package runs it THERE. It then reported 23 findings -- 19 GP-INTERNAL files
        # "leaked" and three `.gitkeep` directories "missing" -- because the distribution package is
        # not an installation and never was. Both concepts had the same directory.
        # **Refusing loudly with the right command is the only honest answer; passing would be a lie
        # and 23 findings is noise that teaches people to ignore the gate.**
        return [Finding(Path(DIST_MARKER), 1, "M0",
                        "this is the DISTRIBUTION package, not an installation -- it is supposed to "
                        "contain every GP-INTERNAL file. Run `make export-project DEST=/path/to/your-project` "
                        "to produce an installation, then run install-check inside THAT tree")]
    if install and (install / MANIFEST_NAME).is_file():
        man = install / MANIFEST_NAME                    # the installed tree carries its own contract
    elif cur:
        man = cur / MANIFEST_NAME
    if man is None:
        if install:
            return [Finding(Path(MANIFEST_NAME), 1, "M3",
                            f"no {MANIFEST_NAME} in the install at {install.name} and no package to "
                            "fall back on — this tree cannot be checked for completeness, which is "
                            "NOT the same as being complete")]
        return f
    if not cur and not install:
        return f
    if not man.is_file():
        return [Finding(Path(MANIFEST_NAME), 1, "M3",
                        "no INSTALL-MANIFEST.md — the package does not declare what an "
                        "installation is, which is how a copy step becomes unfalsifiable")]
    project, internal, empty = parse_manifest(man)
    lock: dict = {}
    if install:
        lf = install / LOCK_NAME
        if lf.is_file():
            for line in lf.read_text(encoding="utf-8", errors="replace").splitlines():
                k, _, v = line.partition("\t")
                if v.strip().isdigit():
                    lock[k.strip()] = int(v)
        else:
            f.append(Finding(Path(LOCK_NAME), 1, "M4",
                             f"no {LOCK_NAME} -- this tree was not produced by `make export-project`, "
                             "so nothing records how many files each directory shipped with. Three "
                             "separate audits gutted an install past M1 using one placeholder file "
                             "per directory; a hand-copied tree cannot be checked for completeness"))
    try:
        rel_man = man.relative_to(root)
    except ValueError:
        rel_man = Path(MANIFEST_NAME)

    # M3 — every package path is classified. Keeps the manifest from rotting silently.
    for rel in sorted(_pkg_paths(cur) if cur else set()):
        if rel.endswith("/"):
            continue                                     # dirs are covered via their declaration
        if not (_covered(rel, project) or _covered(rel, internal)):
            f.append(Finding(rel_man, 1, "M3",
                             f"`{rel}` exists in the package but is in neither list — classify it "
                             "PROJECT or GP-INTERNAL"))

    # M1/M2 — only meaningful against an actual project tree
    if install:
        for decl in sorted(project):
            if decl.endswith("/"):
                # How many files did the PACKAGE ship in this directory? An install must carry at least that
                # many. This is the only test that cannot be satisfied by a placeholder.
                # FOURTH attempt (audit S3). `.exists()`, then "any file", then "any non-empty file"
                # -- each threshold was satisfied by one token placeholder per directory: 105->68,
                # 118->42, 121->67. The third repair compared against the source package, which does
                # not exist in a customer project, so it did nothing in the only place it mattered.
                # (It also referenced an undefined `pkg` and would have raised NameError had `cur`
                # ever been set here -- a dead branch hiding a crash.)
                # **The expected count must TRAVEL WITH the install.** No placeholder satisfies a count.
                want = lock.get(decl.rstrip("/"))
                if not _installed(install / decl.rstrip("/"), decl.rstrip("/") in empty, want):
                    f.append(Finding(rel_man, 1, "M1",
                                     f"PROJECT path `{decl}` is MISSING from the install at "
                                     f"{install.name} — the install is incomplete"))
            elif not _installed(install / decl):
                f.append(Finding(rel_man, 1, "M1",
                                 f"PROJECT path `{decl}` is MISSING from the install at "
                                 f"{install.name} — the install is incomplete"))
        for decl in sorted(internal):
            if (install / decl.rstrip("/")).exists():
                f.append(Finding(rel_man, 1, "M2",
                                 f"GP-INTERNAL path `{decl}` is PRESENT in the install at "
                                 f"{install.name} — GP's own history does not belong in a delivery"))
    return f


# ── C2: a warning that nothing consumes is not a warning (V4C-77, v4.3) ─────────────────────
# WHY, and this is the owner's own diagnosis (translated from Turkish): *"after the gates raise a
# warning, making sure it is examined in context and actually acted on."* A gate that warns and produces no consequence is
# indistinguishable from an absent gate. Measured: `gates SKIPPED: contract suite` appeared in FIVE
# consecutive wave checklists; V4C-13's rule says the same control skipped 3x triggers review OF THE
# CONTROL; `grep -rn "control-bypass" docs/` returned ZERO. The template recorded the truth every
# time. Nothing read it. The Architecture seat named the class: a telemetry sink with no consumer.
#
# The cost of those five unconsumed warnings, measured: when the skipped suite finally ran once, it
# produced SIX engine defects no unit test could reach, because every test double modelled the engine
# the team believed in.
#
# This is C1's sibling. C1 made a CONDITION's closure checkable. C2 does it for a WARNING.
# COST LINE (V4C-13): ~45 lines, stdlib, <0.1 s. New failure mode: a project must keep the ledger
# current or the validator fails — which is the entire point, and is fixtured.
WARN_LEDGER = "docs/warnings.ledger.md"
WARN_STATUSES = {"OPEN", "FIXED", "ACCEPTED", "ESCALATED"}
ACCEPT_LIMIT = 3


def warning_ledger(root: Path) -> list[Finding]:
    led = root / WARN_LEDGER
    if not led.is_file():
        return []                                        # M1 enforces its existence in a project
    f: list[Finding] = []
    rel = led.relative_to(root)
    accepted: dict = {}
    for i, line in enumerate(led.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or set("".join(cells)) <= set("-: "):
            continue
        if cells[0].lower() in ("id", "warn id"):
            continue                                     # header
        # v4.3 REPAIR (auditor B1). The template MANDATES a dated "no warning observed" row so that an
        # empty ledger is a CLAIM rather than a silence — and then this rule failed that very row. Every
        # correct install was RED on its first `make check`, against a README promising "green on day 1".
        # The control was right and had simply never been run against the artefact the design requires.
        if all(c.strip() in {"-", "\u2014", ""} for c in cells[:5]):
            continue
        wid, rule, seen, status = cells[0], cells[1], cells[2], cells[4].upper()
        why = cells[5] if len(cells) > 5 else ""
        if status not in WARN_STATUSES:
            f.append(Finding(rel, i, "C2c",
                             f"`{wid}` status `{cells[4]}` not in {sorted(WARN_STATUSES)}"))
            continue
        # C2a — a warning may not survive the close it was raised in
        if status == "OPEN" and seen and seen.lower() not in ("current", "this wave", "-"):
            f.append(Finding(rel, i, "C2a",
                             f"`{wid}` is still OPEN and was first seen at `{seen}` — a warning may "
                             "not survive the close it was raised in. Disposition it: FIXED, "
                             "ACCEPTED (reason + owning milestone), or ESCALATED"))
        # C2c — ACCEPTED is a decision and must be signed
        if status == "ACCEPTED" and (len(why) < 12 or not re.search(r"[mM]\d|milestone", why)):
            f.append(Finding(rel, i, "C2c",
                             f"`{wid}` is ACCEPTED without a reason AND an owning milestone — "
                             "'accepted' with no owner is how a warning becomes permanent"))
        if status == "ACCEPTED":
            accepted.setdefault(rule, []).append(wid)
    # C2b — V4C-13's 3x trigger, finally countable by something
    for rule, ids in sorted(accepted.items()):
        if len(ids) >= ACCEPT_LIMIT:
            f.append(Finding(rel, 1, "C2b",
                             f"`{rule}` has been ACCEPTED {len(ids)}x ({', '.join(ids)}) — at "
                             f"{ACCEPT_LIMIT} the CONTROL goes under review, not the people "
                             "(V4C-13). Review it or refuse it; do not accept a fourth time"))
    return f


# ── L1: the repository is written in ENGLISH (V4C-79, owner directive 2026-08-12) ────────────
# WHY. The owner works with the chair in Turkish and ships the repository to everyone else:
# developers, other agents, and eventually customers. A repository half in one language is readable
# by neither audience in full. His directive, translated: *"even though I prompt you in Turkish here,
# you will keep BOTH the v4.3 repo and the main repo in English EVERYWHERE."*
#
# Detection is by Turkish-specific letters, which English does not use. This is deliberately a
# CHARACTER test and not a language model: it is exact, it is free, and it cannot drift. It will not
# catch Turkish written without diacritics — stated openly rather than implied, because the honest
# limit of a check belongs next to the check.
#
# Owner quotes stay in the record as EVIDENCE, translated into English and marked as translated. The
# original wording is not the artefact; the ruling is.
#
# COST LINE (V4C-13): ~25 lines, stdlib, <0.2 s. Failure mode: a legitimate proper noun -- a Turkish
# surname, say -- trips it. Handled by the allowlist, which requires a written reason per entry.
# (This comment originally SPELLED such a surname as its example and L1 flagged its own source
#  on the first run. Left recorded rather than tidied away: it is the cheapest possible proof
#  that the rule fires, and it fired on the person who wrote it.)
TR_CHARS = re.compile(r"[\u011f\u0131\u015f\u00e7\u00f6\u00fc\u011e\u0130\u015e\u00c7\u00d6\u00dc]")
LANG_ALLOW = ".language-allow"
LANG_SUFFIXES = {".md", ".py", ".sh", ".yml", ".yaml", ".json", ".html", ".txt", ".toml"}
LANG_EXTENSIONLESS = {"Makefile", "Dockerfile", "CODEOWNERS", "LICENSE"}


def telemetry_verdicts(root: Path) -> list[Finding]:
    """T1 — every traceback carries a verdict (V4C-86).

    `council-telemetry.md` §3.2 makes it a condition of REPORTED that every entry resolves to a record
    id or `NONE-PROPOSED`. Thirty-six did not, and the register had drifted from a nine-column table to
    prose sections without anything noticing -- richer to read, structurally invisible. Four ids were
    cited by an instrument and had no entry at all; two KEEP verdicts rested on them.

    **The instrument built to hold the council accountable could not hold itself to its own bright
    line, for three cuts.** Found by a seat counting, not by any check.

    A traceback id counts as covered if it appears in a table row -- the original nine-column format or
    the §15 verdict index -- with a non-empty verdict cell.
    """
    f: list[Finding] = []
    tel = root / "council-telemetry.md"
    if not tel.is_file():
        return f
    body = tel.read_text(encoding="utf-8", errors="replace")
    covered: set[str] = set()
    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        m = re.match(r"\*?\*?(TB-\d+)", cells[0]) if cells else None
        if m and len(cells) >= 3 and any(c and set(c) - set("-* ") for c in cells[2:]):
            covered.add(m.group(1))
    seen = set(re.findall(r"TB-\d+", body))
    for tid in sorted(seen - covered, key=lambda x: int(x[3:])):
        f.append(Finding(Path("council-telemetry.md"), 1, "T1",
                         f"`{tid}` has no table row carrying a verdict. Section 3.2 makes that a "
                         "condition of REPORTED: a verdict resolves to a record id or `NONE-PROPOSED`. "
                         "**An entry with no disposition is an open loop wearing a finding's clothes** "
                         "-- and four such ids were cited as evidence by a control screen while having "
                         "no entry at all"))
    return f


def language_rule(root: Path) -> list[Finding]:
    """L1 — no Turkish-specific letter in a tracked file, outside the reasoned allowlist."""
    allow: list = []
    af = root / LANG_ALLOW
    if af.is_file():
        for ln in af.read_text(encoding="utf-8", errors="replace").splitlines():
            body = ln.split("#")[0].strip()
            if body:
                allow.append(body)
    f: list[Finding] = []
    for p in sorted(root.rglob("*")):
        if _skip(p.relative_to(root)):
            continue
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(".git/") or "__pycache__" in rel or rel == LANG_ALLOW:
            continue
        # v4.3 REPAIR: the first version skipped extensionless files, and a raw untranslated owner
        # quote sat in `Makefile` for exactly that reason. A reviewer found it. Extensionless text
        # files (Makefile, CODEOWNERS, Dockerfile) are scanned too.
        if p.suffix and p.suffix not in LANG_SUFFIXES:
            continue
        if not p.suffix and p.name not in LANG_EXTENSIONLESS:
            continue
        if any(rel.startswith(a) for a in allow):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            # A file the language rule cannot READ used to be skipped in silence, which means the
            # gate reported clean on a file it never looked at — the exact shape this project has
            # been caught by five times. It is now a FINDING, so an unreadable record is visible.
            f.append(Finding(Path(rel), 0, "L1",
                             f"could not be read for the English-only check: {exc}"))
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if TR_CHARS.search(line):
                f.append(Finding(Path(rel), i, "L1",
                                 "Turkish text in an English-only repository (V4C-79). Translate it; "
                                 "if it is an owner quote, translate and mark it "
                                 "'(owner, translated from Turkish)'. If the file is genuinely exempt, "
                                 f"add its path prefix to `{LANG_ALLOW}` WITH A WRITTEN REASON"))
                break                                    # one finding per file is enough to act on
    return f


def collect(root: Path, paths: list[Path]) -> tuple[list[Finding], list]:
    findings: list[Finding] = []
    records: list[tuple[Path, dict]] = []          # v4.2: a LIST, not an id-keyed dict (see cross_record)
    for p in sorted(paths):
        fs, fields = validate_record(p, root)
        findings += fs
        if fields and fields.get("id"):
            records.append((p, fields))
    findings += cross_record(records, root)
    return findings, records


def governed_records(root: Path) -> list[Path]:
    """Records under governance: repo-root decision trail. Narrow on purpose (V4C-35)."""
    pats = ["v*-ratification.md", "increment-*-ratification.md", "v*-candidate-register.md",
            "council-design.md", "differentiator-ledger.md",
            # v4.2 (Increment 12, Skeptic + Software + Quality + DevOps + PM — all six seats):
            # `council-telemetry.md` and `friction-ledger.md` were filed as governance instruments
            # and matched NONE of the globs above, so the validator could not see the two documents
            # the whole hearing ran on. Widened, and kept explicit rather than a bare *.md glob so
            # the narrowness rule (V4C-35) still holds.
            "council-telemetry.md", "friction-ledger.md", "CONTROL-SCREEN.md", "increment-*-packet.md"]
    # A repo may override the list with `.governed-records` (one glob per line, `#` comments).
    # Added at v4.2 so GDF — a DIFFERENT repo with a different record set — can run this exact
    # file rather than a forked near-copy. Narrow by rule (V4C-35): the manifest exists only
    # because this function consumes it, and an empty/absent manifest falls back to the GP list.
    manifest = root / ".governed-records"
    if manifest.is_file():
        lines = [ln.strip() for ln in manifest.read_text(encoding="utf-8", errors="replace").splitlines()]
        override = [ln for ln in lines if ln and not ln.startswith("#")]
        if override:
            pats = override
    out: list[Path] = []
    for pat in pats:
        out += [p for p in root.glob(pat) if p.is_file()]
    return out


def duplicate_drift(root: Path) -> list[Finding]:
    """D1 — the shipped copy of this validator must match the one CI runs.

    v4.2 (Increment 12, Software seat): `scripts/check_records.py` and
    `general_pipeline_v<current>/scripts/check_records.py` were byte-identical at v4.1 and **nothing
    checked that they stayed that way** — an unmonitored drift between the live validator and the
    template projects copy. A divergence would mean projects ship a different governance contract
    from the one this repo enforces, silently.
    """
    f: list[Finding] = []
    cur = current_package(root)
    if not cur:
        return f
    for rel in ("scripts/check_records.py", "schemas/record.schema.json"):
        a, b = root / rel, cur / rel
        if not a.is_file() or not b.is_file():
            continue
        if a.read_bytes() != b.read_bytes():
            f.append(Finding(b.relative_to(root), 1, "D1",
                             f"drifted from the live copy at {rel} — the shipped template and the "
                             "validator CI runs must be byte-identical"))
    return f


def report(findings: list[Finding], label: str) -> int:
    if findings:
        for x in sorted(findings, key=lambda y: (str(y.path), y.line)):
            print(x)
        print(f"\ncheck_records FAIL [{label}]: {len(findings)} finding(s)")
        return 1
    print(f"check_records PASS [{label}]: no findings")
    return 0


def self_test(root: Path) -> int:
    """V4C-32: every fail fixture must fail WITH its declared expected diagnostic.

    v4.2 REPAIRS (Increment 12, Quality seat — verified by that seat with a built reproduction):
      1. `self_test` never called `package_invariants()`, so **P2 and P3 were structurally
         unreachable from the self-test** regardless of how many fixtures existed. P2/P3 are the
         two rules this validator is actually credited with (the v3.3 §0-heading loss, the file-count
         discrepancy) and the self-test was silent on both. Now asserted directly.
      2. The fixture namespace was an id-keyed dict, so a duplicate-id fixture OVERWROTE the pass
         record it was supposed to collide with — the same collapse bug as `collect()`. Now a list.
      3. The `expect:` marker only matched `[A-Z]\\d`, which cannot express `C1a`/`C1b`.
    A self-test that cannot reach a rule certifies nothing about it. That is V4C-50, applied here.
    """
    conf = root / "conformance"
    if not conf.is_dir():
        print("self-test FAIL: conformance/ missing", file=sys.stderr)
        return 1
    bad = 0
    # The pass corpus is also the reference namespace for cross-record rules (X1/X2/X3),
    # so a fail fixture's dangling reference is genuinely dangling.
    pass_files = sorted((conf / "pass").glob("*.md"))
    base_records: list[tuple[Path, dict]] = []
    for p in pass_files:
        fs, fields = validate_record(p, root)
        if fields and fields.get("id"):
            base_records.append((p, fields))
        if fs:
            bad += 1
            print(f"self-test FAIL: {p.name} should PASS but produced: {[f.rule for f in fs]}")
        else:
            print(f"self-test ok: pass/{p.name}")
    if cross_record(base_records, root):
        bad += 1
        print("self-test FAIL: the pass corpus is not cross-record clean")

    for p in sorted((conf / "fail").glob("*.md")):
        expect = ""
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"<!--\s*expect:\s*([A-Z]\d[a-z]?)\s*-->", line.strip())
            if m:
                expect = m.group(1)
                break
        fs, fields = validate_record(p, root)
        if fields and fields.get("id"):  # cross-record rules need the fixture IN a namespace
            ns = [*base_records, (p, fields)]
            fs = fs + [x for x in cross_record(ns, root) if x.path == p.relative_to(root)]
            fs = fs + [x for x in condition_closure(root, [(p, fields)], scope="all")]   # C1
        rules = {f.rule for f in fs}
        if not expect:
            bad += 1
            print(f"self-test FAIL: fail/{p.name} declares no `<!-- expect: RULE -->` line")
        elif expect not in rules:
            bad += 1
            print(f"self-test FAIL: fail/{p.name} expected {expect}, got {sorted(rules) or 'NOTHING'}")
        else:
            print(f"self-test ok: fail/{p.name} → {expect}")
    # ── P2/P3 reachability (v4.2 repair #1) ─────────────────────────────────────────────
    # Build a deliberately broken throwaway package and assert package_invariants() reports BOTH.
    # Without this the self-test could pass while P2/P3 were no-ops, which is exactly what v4.1 did.
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        probe = Path(td)
        pkg = probe / "general_pipeline_v9.9"
        (pkg / "docs").mkdir(parents=True)
        (pkg / "pipeline-design.md").write_text("# design\n\nno changelog heading here\n")
        (pkg / "docs" / "executive-overview.md").write_text("the package is about 77 files today\n")
        cprobe = probe / "probe-conditions.md"
        cprobe.write_text("---\nrecord_type: ratification\nid: probe-cond\nstatus: ratified\n"
                          "process_version: v4.2\n---\n# probe\n\n"
                          "| # | Condition | Owner | Date | Closure artifact |\n"
                          "|---|---|---|---|---|\n"
                          "| 1 | probe | chair | 2020-01-01 | `docs/never-written.md` |\n")
        _, cfields = validate_record(cprobe, probe)
        (probe / "scripts").mkdir(parents=True, exist_ok=True)
        (pkg / "scripts").mkdir(parents=True, exist_ok=True)
        (probe / "scripts" / "check_records.py").write_text("# live\n")
        (pkg / "scripts" / "check_records.py").write_text("# DRIFTED\n")
        got = {x.rule for x in package_invariants(probe, scope="current")}
        got |= {x.rule for x in duplicate_drift(probe)}                      # D1
        got |= {x.rule for x in condition_closure(probe, [(cprobe, cfields)], scope="all")}  # C1b
        # v4.3 probes — M3 (manifest rot) and C2a/C2b/C2c (an unconsumed warning). Both are
        # package/project-level rules that cannot be expressed inside a single record fixture, so
        # they are asserted here against synthetic trees. Without this they would be unreachable
        # from --self-test, which is exactly the defect the Quality seat found in P2/P3 at v4.2.
        (pkg / "INSTALL-MANIFEST.md").write_text(
            "# probe\n\n## PROJECT\n```\npipeline-design.md\n```\n\n"
            "## GP-INTERNAL\n```\nnothing-here.md\n```\n")
        (pkg / "UNCLASSIFIED.md").write_text("x\n")
        got |= {x.rule for x in manifest_rules(probe)}                        # M3
        (probe / "docs").mkdir(exist_ok=True)
        (probe / "docs" / "warnings.ledger.md").write_text(
            "| id | rule | first seen | path | status | reason |\n|---|---|---|---|---|---|\n"
            "| W-1 | contract-suite | m1-wave-2 | t/ | OPEN | |\n"
            "| W-2 | cold-start | m2-wave-0 | s/ | ACCEPTED | later |\n"
            "| W-3 | contract-suite | m2-w0 | t/ | ACCEPTED | no engine; owner runs it — milestone M2 |\n"
            "| W-4 | contract-suite | m2-w1 | t/ | ACCEPTED | no engine; owner runs it — milestone M2 |\n"
            "| W-5 | contract-suite | m2-w2 | t/ | ACCEPTED | no engine; owner runs it — milestone M2 |\n")
        got |= {x.rule for x in warning_ledger(probe)}                        # C2a/C2b/C2c
        (probe / "turkish.md").write_text("bu satir Turkce karakter tasiyor: \u015fey\n")
        got |= {x.rule for x in language_rule(probe)}                         # L1
        # M1/M2 — the release's headline rules. They had NO coverage at all until a zero-context
        # reviewer found they could not fire through any shipped invocation path. Probed here from
        # the same direction a customer project runs them: a tree carrying its own manifest.
        inst = probe / "fake-install"
        (inst / "docs").mkdir(parents=True)
        (inst / MANIFEST_NAME).write_text(
            "# probe\n\n## PROJECT\n```\nAGENTS.md\nMakefile\n```\n\n"
            "## GP-INTERNAL\n```\ndocs/HANDOVER-v9.9-material.md\n```\n")
        (inst / "AGENTS.md").write_text("x\n")                       # Makefile MISSING      -> M1
        (inst / "docs" / "HANDOVER-v9.9-material.md").write_text("x\n")  # leaked GP-INTERNAL -> M2
        got |= {x.rule for x in manifest_rules(probe, install=inst)}          # M1/M2
        for rule, why in (("P2", "missing §0 changelog heading"), ("P3", "false file count"),
                          ("D1", "drifted shipped-vs-live validator copy"),
                          ("C1b", "a due condition whose named artifact is absent"),
                          ("M3", "an unclassified package path (manifest rot)"),
                          ("C2a", "a warning that outlived its close"),
                          ("C2b", "the same control ACCEPTED three times"),
                          ("C2c", "ACCEPTED with no reason and no owning milestone"),
                          ("L1", "Turkish text in an English-only repository"),
                          ("M1", "a PROJECT path missing from an install"),
                          ("M2", "a GP-INTERNAL path leaked into an install")):
            if rule in got:
                print(f"self-test ok: probe/{rule} fires on a {why}")
            else:
                bad += 1
                print(f"self-test FAIL: {rule} did NOT fire on a {why} — the rule is unreachable "
                      f"(got {sorted(got) or 'NOTHING'})")
        shutil.rmtree(pkg, ignore_errors=True)

    print(f"\nself-test {'FAIL' if bad else 'PASS'}: {bad} problem(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="governance-record validator (V4C-30)")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--self-test", action="store_true", help="run conformance fixtures (V4C-32)")
    ap.add_argument("--install", default=None,
                    help="a project tree to check against INSTALL-MANIFEST.md (M1/M2)")
    ap.add_argument("--historical", action="store_true",
                    help="day-1 falsification: package invariants across ALL shipped versions")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    if a.self_test:
        return self_test(root)
    if a.historical:
        _, hrecords = collect(root, governed_records(root))
        return report(package_invariants(root, scope="all")
                      + condition_closure(root, hrecords, scope="all"),
                      "historical package invariants + legacy prose conditions "
                      "(informational: prior versions are FROZEN)")

    findings, records = collect(root, governed_records(root))
    findings += package_invariants(root, scope="current")
    findings += condition_closure(root, records, scope="current")     # C1 (V4C-25)
    findings += duplicate_drift(root)                                 # D1
    findings += manifest_rules(root, install=Path(a.install).resolve() if a.install else None)
    findings += warning_ledger(root)                                  # C2
    findings += language_rule(root)                                   # L1
    findings += telemetry_verdicts(root)                              # T1
    print(f"(scanned {len(records)} record(s) with frontmatter)")
    return report(findings, "repo")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
