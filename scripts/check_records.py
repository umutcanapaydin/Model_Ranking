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
                              X5 a rule id the package cites exists in the decision trail
                              X4 a path a ROOT document points at resolves — in the tree,
                                 in the tag its path names, or declared in
                                 .root-path-refs-allow with a reason
  Propagation (V4C-36):       P1 declared propagation rows are not `pending`
                              P2 each package's pipeline-design.md keeps its §0 changelog heading
                                 (the ONE verified field incident: v3.3 lost it)
                              (P3, the executive-overview file count, RETIRED at v6.0 with the
                                 document it graded — see package_invariants)
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
import fnmatch
import functools
import os
import re
import subprocess
import sys
from pathlib import Path

# ── declared vocabulary (narrow by rule V4C-35: every field drives a check below) ──────────
# v4.3.2. The first seven are GP's OWN governance species. The rest are a PROJECT's, added when an
# external reviewer pointed out that `.governed-records` shipped naming project files that could never
# pass `R2` — the record model literally had no word for a closure report. **A governance model that
# cannot name the artefacts of the thing it governs is not installed, it is on display.**
RECORD_TYPES = {"ratification", "register", "adr", "experience", "handover", "design", "council",
                "closure", "wave", "fixpack", "brief", "status", "license-review", "warnings",
                # M11-W1, found by the independent seat the same wave created. `review` was absent
                # while 44 files carried `record_type: review` -- and they PASSED, because
                # `.governed-records` did not list `docs/reviews/` either, so none of them was ever
                # scanned. Two absences cancelling into a green gate. Adding `seat` to the schema
                # without this would have made D-133's mandated frontmatter UNREPRESENTABLE:
                # declare `review` and R2 fires, declare anything else and R6 fires.
                # N3, same wave, same class as `review` above: `docs/plans/m11-plan.md` declares
                # `record_type: plan`, which was also absent. Ungoverned TODAY (the manifest reaches
                # only wave-close records under `docs/plans/`) — named here so the type is legal the
                # day it is governed, rather than becoming a second B1.
                "review", "plan",
                # DevFlow v6.0 adoption (model_ranking, 2026-09-23). Nine retrospectives under
                # `docs/retrospectives/` declare `record_type: retrospective` and were never scanned
                # while selection was by glob. Deriving the set from frontmatter found them all
                # "invalid" -- the schema had no word for a record `/cycle-close` itself writes.
                "retrospective",
                # v5.2 (17-8). `harvest` was missing for five versions. Field harvests are the
                # evidence every council runs on, and the schema had no word for them -- which went
                # unnoticed because the filename-glob selector never reached one. Deriving the set
                # from `record_type:` surfaced nine of them at once, all "invalid".
                "harvest",
                # v5.2 (17-8). A harvest may ship a companion GPF register -- defects in
                # GP's OWN machinery, filed separately and filed hard. Two exist in the
                # corpus and neither was ever governed.
                "field-findings"}
#: Control identifiers as this project writes them: K.7, V3C-02, V4C-13, L.7, E.4, INV-23.
#: Deliberately NOT `D-\d+` or `REQ-...`: a decision is not a control that gets bypassed, and
#: counting them would make C2b fire on rows that merely cite an ADR.
#: An inline code span. A rule about the language of this repository reads PROSE; what is quoted
#: inside backticks is evidence, and evidence has to be allowed to be in the language it is about.
#: A code span, in the two forms CommonMark defines. The double-backtick form must be tried FIRST:
#: it is the delimiter you are required to use when the quoted text itself contains a backtick, and
#: the single-backtick pattern reads ``a `b` c`` as two empty spans with the content between them
#: left exposed as prose. Measured at M12-W5 (Stage 4.0 MINOR-2): a correctly-formed double-backtick
#: quotation of a Turkish product string produced an L1 finding inside the security review itself.
#:
#: **Under-enforcing on an unbalanced fence and over-enforcing on a legitimate quotation is the
#: pairing that gets a rule switched off**, and both halves were live in the same rule at once.
INLINE_CODE = re.compile(r"``.+?``|`[^`]*`", re.S)

#: A code span longer than this is prose wearing backticks.
#:
#: The exemption exists so a record can quote a defect verbatim — a symbol, a path, a flag, a short
#: sentence of shipped output. This project habitually backticks everything, so without a bound the
#: substance of an entire record can be non-English and pass. Chosen by measurement, not taste: the
#: longest legitimate code span in this repository's non-exempt records is well under this, and the
#: records that genuinely quote a long Turkish sentence as evidence are named in `.language-allow`
#: for exactly that reason.
INLINE_CODE_MAX = 120

CONTROL_ID = re.compile(r"\b(K\.\d+|V3C-\d+|V4C-\d+|[A-L]\.\d+|INV-\d+)\b")
#: The one token that discharges C2b: written deliberately, naming the decision that reviewed the
#: control. Never a bare ADR reference -- rows cite ADRs for a dozen unrelated reasons.
#: `@N` anchors the discharge to the count it was written against. A marker with no anchor, or an
#: anchor below today's count, does NOT discharge: the control has been accepted again SINCE it was
#: reviewed, which is the thing V4C-13 exists to notice. A trigger that can never fire twice is the
#: defect this milestone spent itself finding.
C2B_REVIEWED = re.compile(r"C2b-reviewed:\s*[DP]-\d{3}\s*@(\d+)")

STATUS_FLOW = ["draft", "candidate", "ratified", "superseded", "retired"]  # X3 ordering
REQUIRED = ("record_type", "id", "status")
#: Who reviewed. `author` = the seat that wrote the code reviewed it; `independent` = a seat that
#: did not. OPTIONAL rather than required, deliberately: 44 review records predate this field, and
#: GPF-001 already ruled that a tool may not retroactively invalidate records written before it
#: existed. `wave_check.py` REQUIRES it on any review a v5.0 wave-close record cites, which is where
#: the consequence belongs — this file checks SHAPE and never judges independence (see the module
#: docstring).
SEATS = ("author", "independent")
# v5.2 (17-8): the fields the harvest prompt's third edition requires a field agent to declare.
# V4C-35 DEBT, recorded rather than hidden: `harvest_context_sha256` has no machine consumer yet --
# the Security seat measured that its three-outcome policy (match / missing / MISMATCH files an
# injection-class finding) exists only as a docstring. Declaring the field here does not discharge
# that; condition 18-x owes the consumer, and if it is not written these fields are deleted after
# two cuts per V4C-35 rather than carried as decoration.
HARVEST_FIELDS = ("process_version_harvested", "process_version_target", "project",
                  "harvest_context_sha256", "harvester_conflict", "companion", "parent")
OPTIONAL = (*HARVEST_FIELDS, "seat", "process_version", "supersedes", "requires", "subject_ref", "propagation",
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
    seat = fields.get("seat")
    if seat is not None and seat not in SEATS:
        f.append(Finding(rel, ln, "R6", f"seat `{seat}` not in {sorted(SEATS)} -- a review either "
                         "was reviewed by the seat that wrote the code, or it was not"))
    if seat is not None and rt != "review":
        f.append(Finding(rel, ln, "R6", f"`seat` on a `{rt}` record -- the field is consumed only "
                         "for reviews (V4C-35: a field may exist only if a check consumes it)"))
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
        # v5.1 hardening. A `supersedes:` carrying a prose STRING (not a list, not an id) crashed this
        # line with a TypeError -- and a crashed validator aborts every later rule while looking like
        # a finding. Found by the chair breaking it accidentally minutes after editing a frontmatter;
        # the crash class is TB-047's (a broken instrument reporting as evidence). Wrong-typed fields
        # are now a FINDING, never an exception.
        _reported: set = set()
        def _refs(key):
            v = fields.get(key) or []
            if isinstance(v, str):
                if key in _reported:
                    return []
                _reported.add(key)
                f.append(Finding(rel, 1, "R2",
                                 f"`{key}` is prose (`{v[:40]}...`) -- it must be a list of record "
                                 "ids. A reference nothing can resolve is a reference to nothing"))
                return []
            return v if isinstance(v, list) else []
        for ref in _refs("supersedes") + _refs("requires"):
            if ref and ref not in seen:                             # X1
                f.append(Finding(rel, 2, "X1", f"reference `{ref}` resolves to no record"))
        sup = _refs("supersedes")
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


_HIST_CACHE: dict = {}


def _historical_paths(root: Path) -> dict:
    """Every path this repository has shipped under any tag, indexed by basename.

    One `git ls-tree` per tag, cached for the run -- sixteen git calls, not one per citation. The
    alternative was asking git about each unresolved path separately, which is how a validator that
    runs on every push becomes a validator people disable.
    """
    key = str(root)
    if key in _HIST_CACHE:
        return _HIST_CACHE[key]
    index: dict = {}
    try:
        tags = subprocess.run(["git", "-C", str(root), "tag"],
                              capture_output=True, text=True, timeout=10)
        names = [t for t in tags.stdout.split() if t] if tags.returncode == 0 else []
        for tag in names:
            out = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "--name-only", tag],
                                 capture_output=True, text=True, timeout=20)
            if out.returncode != 0:
                continue
            for line in out.stdout.splitlines():
                index.setdefault(line.rsplit("/", 1)[-1], set()).add(line)
    except (OSError, subprocess.SubprocessError):
        index = {}
    _HIST_CACHE[key] = index
    return index


def _git_blob(root: Path, path_part: str) -> str | None:
    """Read `general_pipeline_vX.Y/...` out of the tag `vX.Y` when the directory is no longer checked out.

    Returns the file's text, or None if the repository does not hold it either. A missing `git`, a
    tree that is not a repository, or an absent tag all return None -- this only ever RESCUES a
    citation, it can never satisfy one that the repository cannot produce.
    """
    tag = path_part.split("/", 1)[0][len("general_pipeline_"):]
    if not tag:
        return None
    try:
        out = subprocess.run(["git", "-C", str(root), "show", f"{tag}:{path_part}"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def current_package(root: Path) -> Path | None:
    """The version the repo is shipping = the highest general_pipeline_v* by numeric order."""
    def key(p: Path):
        return [int(x) if x.isdigit() else 0
                for x in re.findall(r"\d+", p.name.replace("general_pipeline_v", ""))]
    pkgs = [p for p in root.glob("general_pipeline_v*") if p.is_dir()]
    return max(pkgs, key=key) if pkgs else None


def package_invariants(root: Path, scope: str = "current") -> list[Finding]:
    """P2 — the propagation regression we actually paid for.

    P3 RETIRED, v6.0 (owner, 2026-09-22). It graded one sentence — the file count in
    `docs/executive-overview.md` — and the document it graded was deleted: seven cuts stale (it
    narrated v4.3), withheld from every delivery, and its header overwritten by its own generator's
    stdout, which no control saw because P3 read one number and nothing else. A rule left standing
    behind `if overview.exists()` would have gone quietly inert; retired by name instead.

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
#   C1c  FORWARD-ONLY, BLOCKING (v5.3, TB-082). In records at process_version >= v5.2, a condition
#        whose artifact ALREADY EXISTS must name `path#anchor` — a literal string the change adds.
#        Without one the row satisfies itself the day it is signed and can never fail. Increment 16
#        wrote twelve such rows and ten of them went unwritten for nineteen days, green.
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
    # v6.0. A THIRD verdict, SUPERSEDED, added the first time a condition needed it. 18-6's
    # closure artifact was `$CUT/.claude/skills/retrospect/SKILL.md`; v6.0 merged that skill into
    # `cycle-close` and the path stopped existing. The condition was BUILT -- retiring it would
    # say the work was abandoned and refusing it would say it was declined, and both are false.
    #
    # It also exposes a tension section 1.3 created at Increment 18. `$CUT` was adopted so a
    # condition naming a FROZEN package could still close; the cost is that a condition now
    # follows the cut forward and breaks whenever the cut reorganises. Neither resolution is free:
    # pin to the cut that satisfied it and you cannot see later removals, follow the cut and every
    # rename is an evaporation. SUPERSEDED is the record of that choice being made per condition.
    #
    # v5.3, 18-x (Increment 18). Conditions the council has RETIRED or REFUSED. Until now a
    # condition could only be built or report EVAPORATED forever -- there was no third state, so
    # the owner's "leave nothing open" instruction was unexecutable. Ratified tables are never
    # rewritten; this register sits beside them. Fail-closed: an entry naming a condition no
    # ratified table contains is a finding, reported by `retirement_integrity()`.
    retired: set[str] = set()
    _ret = root / "retired-conditions.md"
    if _ret.is_file():
        for _ln in _ret.read_text(encoding="utf-8", errors="replace").splitlines():
            _m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*(RETIRED|REFUSED|SUPERSEDED)", _ln)
            if _m:
                retired.add(_m.group(1).strip())

    today = _today()
    for path, fields in records:
        pv = str(fields.get("process_version") or "")
        # C1a (artifact must be machine-resolvable) is FORWARD-ONLY: ratified history is frozen and
        # its prose conditions cannot be retroactively rewritten. C1b (a due, resolvable artifact
        # must exist) applies to EVERY record — restricting it by generation was the first bug in
        # this rule, and it silently exempted the exact register that carries the live conditions.
        forward = bool(pv) and _version_tuple(pv) >= (4, 2)
        # C1c has its own epoch: it was adopted at v5.2 and, like C1a, does not reach back
        # into ratified history. Applying it at C1a's v4.2 epoch produced 43 findings on
        # frozen records the council cannot rewrite -- a rule that indicts the past instead
        # of binding the future, which is noise and teaches the reader to skip the report.
        forward_c1c = bool(pv) and _version_tuple(pv) >= (5, 2)
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="replace")
        for ln, cells in condition_rows(text):
            if cells and cells[0].strip().strip("`") in retired:
                continue
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
            anchored = False         # v5.2 C1c: did ANY token name `path#anchor`?
            for tok in TICK_RE.findall(artifact_cell):
                # v5.3, TB-084. The `.split()` guard here was added to survive an empty backtick
                # pair, and it silently TRUNCATED EVERY ANCHOR AT ITS FIRST SPACE. Measured against
                # Increment 17's own conditions table: `#A RULE MAY NOT OUTLIVE ITS GATE` resolved
                # to `A`, `#A skip is not a pass` to `A`, `#a second independent outsider grading`
                # to `a`. **Three of thirteen rows were satisfied by any non-empty file** -- exactly
                # the bare `target.exists()` that C1c was written to end, inside C1c's own repair.
                #
                # The chair greped the full literal by hand and got 12/12; the checker greped `A`,
                # `A`, `a`. A human grep and the machine's grep disagreed on nine of thirteen rows,
                # and the human's is what got recorded as verification. Found by the DX seat.
                #
                # Split on `#` FIRST, then take the first whitespace token of the path only. The
                # anchor keeps every word.
                raw = tok.strip().rstrip(",;:)")
                if not raw:           # an empty backtick pair -> IndexError, exit 1, later rules aborted
                    continue
                path_part, _, anchor = raw.partition("#")
                _pp = path_part.split()
                path_part = _pp[0] if _pp else ""
                anchor = anchor.strip()
                tok = raw
                target = root / path_part
                # v5.3, §1.3 (Increment 18), proposed independently by three seats. A condition
                # naming a path into a FROZEN package can never close: 15-6's work shipped as
                # `general_pipeline_v5.2/scripts/coverage_floor.py` while the row names
                # `general_pipeline_v5.1/...`, so `C1b` reported it EVAPORATED forever although the
                # work was done. A permanent false RED teaches the same blindness as a false
                # GREEN -- it is how `slopsquat` survived five versions.
                #
                # So a version-pinned artifact also resolves against the CURRENT package. Write
                # `$CUT/` in new conditions and this is unnecessary; the fallback exists for rows
                # the council ratified before the rule.
                if not target.exists() and path_part.startswith("general_pipeline_v"):
                    cur = current_package(root)
                    if cur is not None:
                        alt = cur / path_part.split("/", 1)[1] if "/" in path_part else None
                        if alt is not None and alt.exists():
                            target = alt
                    # v6.0, 2026-09-22. The spring cleaning removed fifteen frozen package
                    # directories from the WORKING TREE after tagging each cut. The decision trail
                    # cites 108 paths inside them, and one of those citations is a closure artifact
                    # -- so `C1b` reported a condition EVAPORATED whose artifact was never lost, only
                    # moved out of the checkout. **The working tree is not the repository.** A path
                    # under `general_pipeline_vX.Y/` resolves against the tag `vX.Y` when the
                    # directory is gone, which is how the citations stay true without rewriting 108
                    # records to say the same thing differently.
                    if not target.exists():
                        blob = _git_blob(root, path_part)
                        if blob is not None:
                            if anchor:
                                anchored = True
                                if anchor in blob:
                                    satisfied = True
                                    break
                                missing.append(tok)
                                continue
                            satisfied = True
                            break
                elif path_part.startswith("$CUT/"):
                    cur = current_package(root)
                    if cur is not None:
                        target = cur / path_part[len("$CUT/"):]
                if anchor:
                    anchored = True
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
            # ---- C1c: forward-only — a condition may not be able to satisfy itself --------
            # v5.3, TB-082, and it is the defect that cost this lineage nineteen days.
            #
            # `C1b` treats a condition as satisfied when its artifact `target.exists()`. Increment
            # 16 wrote TWELVE conditions, every one naming a file that ALREADY EXISTED — Makefile,
            # closure-checklist.md, the harvest prompt. **All twelve satisfied themselves on the day
            # they were signed.** The validator was correctly, honestly green for nineteen days
            # while ten of them had not been written, and `V5C-110` — adopted 6/6 — existed in no
            # file outside the ratification that adopted it.
            #
            # The v4.3 repair above made `path#anchor` POSSIBLE and left it OPTIONAL, so the defect
            # recurred at full scale one cut later. Optional is how a control becomes folklore.
            # Forward-only for the same reason C1a is: ratified history is frozen.
            #
            # A condition that names an existing file without an anchor cannot fail. It is not a
            # condition; it is a sentence. Found by the DX seat at Increment 17, not by the chair,
            # whose own closure record misdiagnosed it as a governed-records glob problem.
            if forward_c1c and satisfied and not anchored \
                    and artifact_cell not in ("", "—", "-", "n/a", "–"):
                f.append(Finding(rel, ln, "C1c",
                                 "condition satisfies itself — its artifact already exists and no "
                                 "`#anchor` was named, so this row can never fail. Name "
                                 "`path#a-literal-string-the-change-adds` "
                                 f"(row: {cells[0][:24]!r})"))
            # ---- C1a: forward-only — the artifact must be nameable at all ----------------
            # The dash variants below are DATA, not prose: a record may write "no artifact" as an
            # em dash, an en dash, a hyphen or `n/a`, and the rule accepts all four. Flagging the
            # en dash as a typo would be right in a sentence and wrong in a set of accepted spellings.
            elif forward and not satisfied and not missing \
                    and artifact_cell not in ("", "—", "-", "n/a", "–"):
                f.append(Finding(rel, ln, "C1a",
                                 "condition's closure artifact is not machine-resolvable — name a "
                                 "`path` or a record `id` in backticks, not prose "
                                 f"(row: {cells[0][:24]!r})"))
    return f


# ── M1/M2/M3: the install manifest (V4C-72/76, v4.3) ────────────────────────────────────────
# Written by `scripts/write_install_marker.py` (MARKER_DIR / "installed") in the project that runs
# `make install`. A literal, not an import: this validator also runs at GP's root, where that
# script does not exist. `test-delivered-tree` proves the two agree, in the delivery.
INSTALL_MARKER = ".gp/installed"
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


@functools.cache
def _ignored(pkg: Path) -> frozenset:
    """Paths git is already ignoring in this tree — the exclusion, DERIVED (V5C-110).

    v6.0. `SKIP_DIRS` above excludes junk DIRECTORIES and no junk FILES, so a `.DS_Store` — which
    macOS writes the moment anyone opens the folder in Finder, and which `.gitignore` has excluded
    since the first cut — turned this gate red on TWO findings at once: `M3` (a path in neither
    manifest list) and `P3` ("claims 160 files, package contains 161"). The false count landed on
    the one doc-sync check GP owns. That is this list's third repair in three cuts — `.venv` at
    v4.3.2, the half-wired exclusion at v5.3, junk files now — and a hand-kept list beside the
    thing it guards, drifting, IS the finding V5C-110 names. `.gitignore` one directory away has
    held the answer the whole time, so the answer is read rather than re-typed.

    FAIL DIRECTION. No git, no repository, or a git that errors → the empty set, which restores the
    OLD behaviour: junk is counted and the gate goes red. The fallback is never a pass that the
    full walk would have refused, and `SKIP_DIRS` still applies underneath it either way.
    """
    try:
        r = subprocess.run(["git", "-C", str(pkg), "ls-files", "--others", "--ignored",
                            "--exclude-standard", "-z"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    if r.returncode != 0:
        return frozenset()
    return frozenset(x for x in r.stdout.split("\0") if x)


def _skip(rel: Path, pkg: Path | None = None) -> bool:
    if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in rel.parts):
        return True
    return pkg is not None and rel.as_posix() in _ignored(pkg)


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
        if _skip(p.relative_to(pkg), pkg):
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
            # v6.0. The project's OWN `make install` writes `.gp/installed` -- the manifest says so
            # ("the project then COMMITS that one") -- while GP's copy of it stays GP-INTERNAL so
            # the export withholds it. M2 could not tell the two apart and flagged the project's
            # marker as a leak, so every `make check` after a successful install was red. Nobody
            # saw, because until the same cut no delivery had ever got past `make install`.
            # What this gives up, stated: a HAND copy of GP's tree carrying GP's marker is no
            # longer an M2 finding; the export never copies it, and it is the path GP ships.
            if decl == INSTALL_MARKER:
                continue
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
        wid, seen, status = cells[0], cells[2], cells[4].upper()
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
            # GROUPED BY CONTROL, not by provenance. `cells[1]` is the free-text "where this came
            # from" column -- "M8 independent security review, MAJOR-1" -- and it is unique on
            # every row by construction, so C2b could never reach three and never fired once.
            # Measured at M12-W1: 22 ACCEPTED rows, 22 distinct keys, zero triggers, **while two
            # records asserted that it had fired** and K.7 had been bypassed ten times.
            #
            # A counter that cannot count is worse than no counter, because records start citing
            # it. The key is now the CONTROL identifier taken from the context column -- `K.7`,
            # `V3C-78`, `V4C-13`, `INV-23`, the lettered seeds -- which is the thing V4C-13 is
            # actually about: not who accepted, but WHAT keeps being accepted.
            # Read the WHOLE row, not just the path column. Measured at M12-W5: of 22 ACCEPTED
            # rows, **19 name no control anywhere in the path column** -- because that column
            # holds a PATH. C2b was reading 3 rows out of 22 and calling the other 19 zero.
            # A row that cannot be keyed is not a row that was never accepted.
            controls = sorted(set(CONTROL_ID.findall(" ".join(cells))))
            for control in controls:
                accepted.setdefault(control, []).append((wid, why))
            # C2d -- coverage. An acceptance that does not say WHAT it accepts is uncountable, and
            # an uncountable acceptance is exactly the one that repeats. Required from W-087 on:
            # the 86 rows before it were written against a rule that did not ask (GPF-001 -- a
            # tool may not retroactively invalidate older records), and the blind spot is stated
            # here ONCE rather than as 19 findings (D-135).
            if not controls and wid >= "W-087":
                f.append(Finding(rel, i, "C2d",
                                 f"`{wid}` is ACCEPTED but names no control (`K.n`, `V3C-n`, "
                                 "`V4C-n`, `INV-n`) anywhere in the row — C2b counts acceptances "
                                 "per CONTROL, so an acceptance that names none is invisible to "
                                 "the trigger that exists to catch repetition"))
    # C2b — V4C-13's 3x trigger, finally countable by something
    for control, rows in sorted(accepted.items()):
        if len(rows) < ACCEPT_LIMIT:
            continue
        # **The trigger is SATISFIABLE, and that is deliberate.** V4C-13 says the third acceptance
        # sends the CONTROL for review rather than the people. A finding that cannot be discharged
        # is an alarm to be silenced; this one is discharged by DOING what it asks and pointing at
        # the result. K.7 reached three, the control was reviewed, and D-133 is the outcome -- so
        # the rows that cite it satisfy this and the ones that do not, do not.
        # The discharge must be EXPLICIT and it must be about THIS control. The previous form
        # accepted any `D-nnn` anywhere in any of the counted rows -- so W-020's incidental
        # mention of D-120 (the CLI exit-code contract, nothing to do with fresh eyes) silenced
        # K.7 permanently and silently. A trigger discharged by a coincidence is not a trigger.
        anchors = [int(m.group(1)) for _wid, why in rows if (m := C2B_REVIEWED.search(why))]
        if anchors and max(anchors) >= len(rows):
            continue
        ids = ", ".join(wid for wid, _why in rows)
        f.append(Finding(rel, 1, "C2b",
                         f"`{control}` has been ACCEPTED {len(rows)}x ({ids}) and no row names the "
                         f"decision that reviewed it — at {ACCEPT_LIMIT} the CONTROL goes under "
                         "review, not the people (V4C-13). Review the control, then write "
                         f"`C2b-reviewed: D-nnn @{len(rows)}` into one of those rows naming the "
                         "decision — or "
                         "refuse it; do not accept a fourth time"))
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
#: `.swift` ADDED at M12-W5 (Stage 4.0 MINOR-3). D-118 claims L1 *"now guards the whole product
#: surface instead of stopping at its edge"* — and the product surface is now half Swift, which L1
#: had never once read. So the wave that actually introduced Turkish into this repository was the
#: one wave L1 could not see, and the narrowing written to accommodate it was never needed.
#: A claim about coverage is worth exactly the suffix list underneath it.
LANG_SUFFIXES = {".md", ".py", ".sh", ".yml", ".yaml", ".json", ".html", ".txt", ".toml", ".swift"}
LANG_EXTENSIONLESS = {"Makefile", "Dockerfile", "CODEOWNERS", "LICENSE"}


def _strip_short_span(match: re.Match[str]) -> str:
    """Remove a code span from the prose — unless it is long enough to BE the prose."""
    span = match.group(0)
    return span if len(span) > INLINE_CODE_MAX else ""


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


PATH_REF_RE = re.compile(
    r"`([A-Za-z0-9_][\w./-]*\.(?:md|py|sh|yml|yaml|toml|json|html|txt|csv|pdf|xlsx))`")
ROOT_PATH_ALLOW = ".root-path-refs-allow"


def root_path_refs(root: Path) -> list[Finding]:
    """X4 — a path a ROOT document routes a reader to must resolve, or be declared absent.

    WHY (2026-09-22). `test-documented-paths.py` grades this inside the PACKAGE, on V4C-80's line:
    anything a reader is told to type is an interface, and a path is that promise in a different
    shape. The repo ROOT had no such control, and the gap was not hypothetical -- the spring
    cleaning removed fifteen frozen package directories and the root README went on handing a
    non-technical stakeholder `general_pipeline_v5.0/docs/executive-overview.pdf`. It was found by
    READING, which is the method the mutation census exists to replace.

    Three ways a reference resolves, and the middle one is the interesting one:
      * the path exists in the working tree, absolutely or beside the citing document
      * the path exists in the REPOSITORY -- `general_pipeline_vX.Y/...` is read out of the tag
        `vX.Y` when the directory is no longer checked out. The working tree is not the repository,
        and the decision trail cites 108 such paths that are all still true.
      * a glob in `.root-path-refs-allow`, each row carrying a written reason. A row without a
        reason is not a declaration.

    NOT graded: conformance fixtures, which name absent artifacts ON PURPOSE -- demanding that a
    fixture's missing file exist deletes the fixture's point. Packages are excluded because they
    carry their own control; grading them twice with different boundaries is how two authorities
    of different vintage end up disagreeing about the same subject.
    """
    # SCOPE. This validator ships inside the package and runs in every installation. There, the
    # same promise is graded by `conformance/test-documented-paths.py` against the project's own
    # tree -- and grading it twice with different boundaries is how two authorities of different
    # vintage end up disagreeing about one subject, which is the reason `pipeline-design.md` is
    # GP-INTERNAL in the first place. X4 is the DISTRIBUTION repository's rule: it runs where the
    # cut packages live, and nowhere else.
    if current_package(root) is None:
        return []

    allow: list = []
    af = root / ROOT_PATH_ALLOW
    if af.is_file():
        for ln in af.read_text(encoding="utf-8", errors="replace").splitlines():
            line = ln.strip()
            if not line or line.startswith("#"):
                continue
            pat, _, reason = line.partition("#")
            if reason.strip():
                allow.append(pat.strip())

    def _evidence(rel: str) -> bool:
        """Documents that QUOTE other repositories rather than route a reader inside this one.

        A field harvest says *the defect was at `src/app/config.py:42`* about a customer's tree, and
        the external research corpus quotes Kubernetes' `hack/verify-kep-metadata.sh`. Neither is a
        promise this repository can keep, and demanding it would turn the evidence into findings --
        617 of them on the first run, which is how a control teaches its reader to skip the report.
        """
        return (rel.startswith("research/") or rel.startswith("other_projects_exp/")
                or Path(rel).name.startswith("EXPERIENCE-HARVEST-"))

    docs = [q for q in sorted(root.rglob("*.md"))
            if not q.is_symlink()
            and not _skip(q.relative_to(root))
            and not q.relative_to(root).as_posix().startswith("general_pipeline_v")
            and not _evidence(q.relative_to(root).as_posix())
            and not re.match(r"^conformance/(fail|pass|wave)/",
                             q.relative_to(root).as_posix())]
    if not docs:
        return [Finding(Path(), 1, "X4",
                        "no root document found to grade. An empty derived set is a failure, "
                        "never a vacuous pass (G1)")]

    basenames = {q.name for q in root.rglob("*") if (q.is_file() or q.is_symlink())
                 and not _skip(q.relative_to(root))}
    cur = current_package(root)
    f: list[Finding] = []
    for doc in docs:
        rel = doc.relative_to(root)
        for n, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in PATH_REF_RE.finditer(line):
                target = m.group(1)
                if (root / target).exists() or (doc.parent / target).exists():
                    continue
                if "/" not in target and target in basenames:
                    continue
                # A root record naming `docs/closure-checklist.md` means the CURRENT package's
                # copy. The convention predates this rule -- `condition_closure` already resolves
                # `$CUT/` the same way -- and a record is not wrong for using the shorthand the
                # repository has always used.
                if cur is not None and (cur / target).exists():
                    continue
                # A template placeholder is not a path: `general_pipeline_vX/...` names every cut
                # and none of them. Same for `$CUT/` and angle-bracket slots.
                if re.search(r"general_pipeline_v[XN]\b|\$CUT|[<>{}*]", target):
                    continue
                # A version-pinned path also resolves against the CURRENT package -- the same
                # fallback C1b carries, for the same measured reason: 15-6's work shipped as
                # `general_pipeline_v5.2/scripts/coverage_floor.py` while the record names v5.1,
                # and a permanent false RED teaches the same blindness as a false GREEN.
                if target.startswith("general_pipeline_v") and cur is not None:
                    tail = target.split("/", 1)[1] if "/" in target else ""
                    if tail and (cur / tail).exists():
                        continue
                # The repository is larger than the checkout: a path this repo shipped at ANY cut
                # is a real path, whether or not it survives today. `pipeline-v2-design.md` was
                # real in v2.x and the record that names it is not wrong for saying so.
                hist = _historical_paths(root)
                base = target.rsplit("/", 1)[-1]
                if base in hist and (target in hist[base]
                                     or any(h.endswith("/" + target) for h in hist[base])):
                    continue
                if target.startswith("general_pipeline_v") and _git_blob(root, target) is not None:
                    continue
                if any(fnmatch.fnmatch(target, pat) for pat in allow):
                    continue
                f.append(Finding(rel, n, "X4",
                                 f"`{target}` resolves nowhere -- not in the tree, not in the tag "
                                 f"its path names, and no row in {ROOT_PATH_ALLOW} declares it"))
    return f


RULE_ID_RE = re.compile(r"\b(?:V[0-9]C-\d+|TB-\d+)\b")


def rule_id_refs(root: Path) -> list[Finding]:
    """X5 — a rule id the package cites must exist in the decision trail.

    WHY (2026-09-22, the owner's ruling two days into the provenance work). GP keeps its citations
    ON PURPOSE: *"when experience arrives from another project later, how else will we know which
    rule it matches?"* That mechanism is only as good as the citations. A dead `V4C-77` does not
    fail loudly -- it routes the next field harvest to a rule that was never written down, and the
    match comes back empty or, worse, lands on the wrong neighbour.

    Measured on first run: the package cites 144 distinct ids and **two of them exist nowhere in
    the trail** -- `V4C-76` in the install manifest's title and `V4C-77`, which is the stated
    authority for the warnings ledger AND for the `C2` rule inside this very validator. The v4
    register runs to V4C-90, so this is a hole in the middle of it, not an id assigned after a
    close.

    GROUND TRUTH is the trail itself -- every id mentioned by any root record. Not a definition
    PATTERN: the registers introduce ids as table rows, as `###` headings, as bold bullets, and as
    `## 13.12 OD-11 / V4C-79 —`, and chasing those shapes is the blacklist this repository keeps
    warning about. The weaker question answers the one that matters: does the decision trail know
    this id at all?

    SCOPE, like X4: this validator ships inside the package and runs in installations, where there
    is no trail to check against and a project's own ids are its own business. It returns early
    without a package directory.

    OUT OF SCOPE, with the reason: `OD-` (owner directives are announced in prose, not registered)
    and `GDF-` (the sister repository's register, which is not in this tree).
    """
    cur = current_package(root)
    if cur is None:
        return []
    trail: set = set()
    for q in sorted(root.glob("*.md")) + sorted(root.glob("other_projects_exp/*.md")):
        trail |= set(RULE_ID_RE.findall(q.read_text(encoding="utf-8", errors="replace")))
    if not trail:
        return [Finding(Path(), 1, "X5",
                        "no rule id found in any root record. An empty ground truth is a failure, "
                        "never a vacuous pass (G1)")]
    f: list[Finding] = []
    for doc in sorted(cur.rglob("*")):
        if not doc.is_file() or doc.is_symlink() or doc.suffix not in {".md", ".html", ".py"}:
            continue
        if any(part in {"__pycache__", ".venv"} for part in doc.parts):
            continue
        rel = doc.relative_to(root)
        for n, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for tok in RULE_ID_RE.findall(line):
                if tok not in trail:
                    f.append(Finding(rel, n, "X5",
                                     f"`{tok}` is cited here and appears in no record of the "
                                     f"decision trail -- a harvest matching a finding to this rule "
                                     f"would find nothing"))
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
        # **The rule is about PROSE, and inline code spans are not prose (GPF-005, -008; fourth
        # occurrence).** `L1` keeps the repository English, and it kept blocking the records that
        # DOCUMENT non-English behaviour: a security finding about Turkish case folding could not
        # explain itself without naming the letter that causes it, and a ledger row could not quote
        # the defective sentence it was reporting. Each time the workaround was to describe the text
        # instead of showing it, which makes the record measurably worse — a reader now has to
        # reconstruct the defect from a paraphrase.
        #
        # Same narrowing GPF-007 needed in `bootstrap-check.sh`, for the same reason: a rule that
        # reads code as prose fails on correct work, and a gate that fails correct work gets
        # switched off. A backticked span is a QUOTATION; bare Turkish in a sentence is still a
        # finding, and the self-test probe proves it.
        lines = text.splitlines()
        # **FAIL CLOSED on an unbalanced fence.** A running toggle is the wrong mechanism for a
        # linear scan: one unmatched ``` exempts everything after it, and that was LIVE — 26 lines
        # of a real review record went unchecked, and the M12 Stage 4.0 seat's own first draft
        # reproduced the bug in the report about it.
        #
        # When the fences do not pair, this scanner cannot tell code from prose, so it stops
        # claiming it can and reads the WHOLE file. Noisier, never quieter — which is the only
        # direction a language rule may fail in, and the direction GPF-007's narrowing also took.
        balanced = sum(1 for line in lines if line.lstrip().startswith("```")) % 2 == 0
        fenced = False
        for i, line in enumerate(lines, 1):
            if balanced and line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            prose = INLINE_CODE.sub(_strip_short_span, line)
            if TR_CHARS.search(prose):
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
    """Records under governance, DERIVED FROM CONTENT: any `.md` declaring `record_type:`.

    v5.2, condition 17-8. This function had failed the same way FIVE times and been repaired four
    times, each repair adding a pattern to a hand-kept list sitting beside the records it selects:

        v4.1  5 patterns                  baseline
        v4.2  +3  council-telemetry, friction-ledger, increment-*-packet
              -- the two instruments "the whole hearing ran on" were invisible
        v5.0  +1  CONTROL-SCREEN.md       (unrecorded at the time)
        v5.1  +1  EXPERIENCE-HARVEST-PROMPT.md   (unrecorded at the time)
        v5.2  increment-*.md              -- announced as "derived"; it was a ninth glob

    At the Increment 17 sitting, **nine records carrying `record_type:` were ungoverned — including
    the three field records the council was convened to judge.** The v4.2 sentence was true again,
    verbatim, inside the hearing called to adopt its repair.

    A filename cannot say whether a document is a governance record; its frontmatter already does.
    So selection is by content, recursively, and the hand-kept list inverts into an EXEMPTION list
    that carries a written reason per entry — which is what V5C-110 prescribes and what this
    function, of all functions, was not obeying.

    FAILS CLOSED (Security seat's ratified V5C-110 amendment #4, and it was unmet here until now):
    an empty derived set raises rather than returning quietly. A one-line edit to an in-tree
    `.governed-records` used to yield `(scanned 0 record(s)) PASS exit=0` — the whole governance
    validator switched off, green, by a file the change under evaluation could edit.
    """
    # Version packages carry their own records and are validated as installations, not as the
    # repo's decision trail. `.git`, caches and virtualenvs are not documents.
    # `conformance/` holds the validator's OWN fixtures -- records deliberately broken so the rules
    # can be watched failing (`--self-test`). Governing them would report every fixture as a finding
    # and drown the real ones, which is how a report teaches its reader to skip it.
    SKIP_DIRS = ("general_pipeline_v", "conformance", ".git", ".venv", "__pycache__", "node_modules")
    FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
    HAS_TYPE = re.compile(r"^record_type:\s*\S", re.M)

    exempt: list[str] = []
    exempt_file = root / ".governed-records-exempt"
    if exempt_file.is_file():
        for ln in exempt_file.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                # `path  # reason` -- the reason is required by V5C-110 and read by a human, not
                # by this code. An entry with no `#` reason is still honoured and still visible;
                # the rule is enforced at review, because a machine cannot grade a justification.
                exempt.append(ln.split("#")[0].strip())

    out: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(part.startswith(SKIP_DIRS) for part in rel.parts):
            continue
        # v5.3, TB-090 (Increment 18). This also matched by BASENAME, so the single exemption
        # entry -- written to hide a duplicate -- hid the CANONICAL copy too. Measured: the file
        # the exemption's own written reason calls "the canonical copy" was absent from the
        # governed set. **The exemption written to hide the duplicate hid the original**, four
        # hours after the repair that was supposed to end exactly this class. Exact path only; a
        # bare basename is an error, not a wildcard.
        if str(rel) in exempt:
            continue
        # A BROKEN SYMLINK is not a record. `CLAUDE.md -> AGENTS.md` ships in every installation,
        # and the `M1` falsification deletes `AGENTS.md` on purpose -- so the recursive walk found a
        # dangling link and `read_text` raised, aborting every later rule with a traceback.
        # `is_file()` is False for a dangling symlink, which is the whole check. Caught by
        # `falsify.py` scoring the recipe BAD-RECIPE rather than FALSIFIED: the crash-vs-fired
        # distinction earning its place the first time this walk touched a file it had never read.
        if not path.is_file():
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        head = FRONTMATTER.match(body)
        if head and HAS_TYPE.search(head.group(1)):
            out.append(path)

    # A repo with a `.governed-records` manifest ADDS to the derived set; it can no longer replace
    # it. GDF's reason for the manifest -- a different repo with a different record set -- is served
    # by addition. Replacement was a V4C-06 violation: the validator read its own scope from the
    # tree under evaluation, so the change being checked chose what got checked.
    manifest = root / ".governed-records"
    if manifest.is_file():
        for ln in manifest.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                out += [q for q in root.glob(ln) if q.is_file() and q not in out]

    # The empty case is a FAILURE, but it is not this function's to declare: `--install` runs
    # against trees that legitimately hold no governance records yet (a fresh Stage 0, or the
    # synthetic minimal tree `test-make-targets` builds to prove install-check accepts one).
    # Raising here made a correct installation fail. The caller that governs decides -- see G1 in
    # repo mode. **Fail-closed means the check that would have run reports its absence, not that
    # every caller inherits someone else's precondition.**
    return out


def duplicate_drift(root: Path) -> list[Finding]:
    """D1 — the shipped copy of this validator must match the one CI runs.

    v4.2 (Increment 12, Software seat): `scripts/check_records.py` and
    `general_pipeline_v<current>/scripts/check_records.py` were byte-identical at v4.1 and **nothing
    checked that they stayed that way** — an unmonitored drift between the live validator and the
    template projects copy. A divergence would mean projects ship a different governance contract
    from the one this repo enforces, silently.

    v6.0. A third pair joins them: `.claude/settings.json`. Until today GP shipped a harness --
    the destructive-command hook, the `.env` write block, the protected-branch guard, the
    post-edit gate -- and did not install it at the root where GP is authored, so every one of
    those guards was proven in a scratch copy and enforced nowhere on the repo that writes them.
    Installing it creates exactly the drift D1 exists for: a root copy someone loosens on a bad
    afternoon while the package keeps promising the strict version. A missing file still skips,
    so a project that has no `.claude/` is unaffected.
    """
    f: list[Finding] = []
    cur = current_package(root)
    if not cur:
        return f
    for rel in ("scripts/check_records.py", "schemas/record.schema.json",
                ".claude/settings.json"):
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
    # ── P2 reachability (v4.2 repair #1; P3 retired at v6.0) ─────────────────────────────────────────────
    # Build a deliberately broken throwaway package and assert package_invariants() reports P2.
    # Without this the self-test could pass while P2/P3 were no-ops, which is exactly what v4.1 did.
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        probe = Path(td)
        pkg = probe / "general_pipeline_v9.9"
        (pkg / "docs").mkdir(parents=True)
        (pkg / "pipeline-design.md").write_text("# design\n\nno changelog heading here\n")
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
            # The three ACCEPTED rows carry the SAME CONTROL in the path column, which is what C2b
            # now groups on. Updated at M12-W1 with the rule itself: the probe used to vary only
            # the provenance column, so it proved a version of C2b that could never fire in the
            # field. A self-test that passes against a fixture the real data cannot produce is the
            # same defect V4C-32 exists to catch, one level up.
            #
            # None of them names an ADR, so the trigger is NOT discharged and C2b must fire.
            "| W-3 | contract-suite | m2-w0 | K.7 / V3C-78 | ACCEPTED | no engine; owner runs it — milestone M2 |\n"
            "| W-4 | contract-suite | m2-w1 | K.7 / V3C-78 | ACCEPTED | no engine; owner runs it — milestone M2 |\n"
            "| W-5 | contract-suite | m2-w2 | K.7 / V3C-78 | ACCEPTED | no engine; owner runs it — milestone M2 |\n")
        got |= {x.rule for x in warning_ledger(probe)}                        # C2a/C2b/C2c
        (probe / "turkish.md").write_text("bu satir Turkce karakter tasiyor: \u015fey\n")
        # L1's own failure modes, probed. V4C-32/49: the narrowing shipped at M12-W4 with no test
        # for the way it could fail, and the way it could fail was the one that mattered — an
        # unbalanced fence exempting the rest of a file. The M12 Stage 4.0 seat found it live in a
        # real record, and its own first draft of the report reproduced the same bug.
        #
        # Three probes, because a narrowing needs BOTH directions and its edge:
        (probe / "tr-in-code.md").write_text(
            "A record quoting product output: `\u015fey` — this must NOT fire.\n")
        (probe / "tr-unbalanced.md").write_text(
            "```\n\nbu satir dengesiz bir fence sonrasinda: \u015fey\n")
        (probe / "tr-fenced.md").write_text(
            "```\nbir urun ciktisi: \u015fey\n```\n")
        # MINOR-2's two halves. The double-backtick form is the delimiter CommonMark REQUIRES when
        # the quoted text contains a backtick, and L1 used to scan its contents as prose.
        (probe / "tr-double-tick.md").write_text(
            "A record quoting output that contains a backtick: ``\u015fey `x` \u015fey`` "
            "— this must NOT fire.\n")
        # ...and the other direction: a code span long enough to be the record's substance is
        # prose wearing backticks, and the exemption was never meant to cover it.
        (probe / "tr-long-span.md").write_text(
            "`bu cok uzun bir metin ve tamamen Turkce yazilmis olup bir sembol degil bir "
            "paragraftir ve boyle bir sey L1 tarafindan okunmalidir cunku kaydin ozu budur "
            "\u015fey`\n")
        l1 = language_rule(probe)
        got |= {x.rule for x in l1}                                           # L1
        # L1's SCOPE, asserted per file — the half a "does the rule fire" probe cannot see.
        # A narrowing is only correct if it still catches the original defect, and the way this one
        # could fail was the way it did: silently, on a file it had decided not to read.
        flagged = {f.path.name for f in l1}
        for name, must_fire, why in (
            ("turkish.md", True, "bare Turkish in prose"),
            ("tr-in-code.md", False, "Turkish quoted inside a code span — evidence, not prose"),
            ("tr-fenced.md", False, "Turkish inside a balanced fenced block"),
            ("tr-unbalanced.md", True,
             "Turkish after an UNBALANCED fence — the scanner cannot tell code from prose here, "
             "so it must read everything"),
            ("tr-double-tick.md", False,
             "Turkish inside a DOUBLE-backtick span — the form CommonMark requires when the quote "
             "contains a backtick, and the one L1 used to read as prose"),
            ("tr-long-span.md", True,
             "Turkish inside a code span long enough to BE the record — an exemption without a "
             "bound lets a whole record's substance hide behind one pair of backticks"),
        ):
            if (name in flagged) == must_fire:
                print(f"self-test ok: probe/L1 {'fires' if must_fire else 'stays quiet'} on {why}")
            else:
                bad += 1
                print(f"self-test FAIL: L1 {'did NOT fire' if must_fire else 'FIRED'} on {why} "
                      f"({name}) — the language rule's scope is wrong in the "
                      f"{'quiet' if must_fire else 'noisy'} direction", file=sys.stderr)
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

        # v6.0, 2026-09-22. C1b now rescues a citation into a deleted package directory by reading
        # it out of that cut's TAG. The rescue must be BOUNDED: a package-shaped path that no tag
        # holds still evaporates. Without this probe the rescue could satisfy any citation that
        # merely LOOKS like one, which would be a false GREEN on the rule whose whole job is to
        # notice an artifact that never arrived.
        ctag = probe / "condition-probe-tagless.md"
        ctag.write_text("---\nrecord_type: ratification\nid: condition-probe-tagless\n"
                        "status: ratified\nprocess_version: v6.0\ndate: 2020-01-01\n---\n"
                        "# probe\n\n## Conditions\n\n| # | condition | owner | due | artifact |\n"
                        "|---|---|---|---|---|\n"
                        "| 1 | probe | chair | 2020-01-01 | `general_pipeline_v9.9/scripts/nothing.sh` |\n")
        _, tfields = validate_record(ctag, probe)
        tagless = {x.rule for x in condition_closure(probe, [(ctag, tfields)], scope="all")}
        if "C1b" in tagless:
            print("self-test ok: probe/C1b-tagless fires on a package path no tag holds — the git "
                  "rescue is bounded")
        else:
            bad += 1
            print("self-test FAIL: a condition naming a path inside a package NO TAG HOLDS did not "
                  "evaporate — the tag rescue is unbounded and C1b can no longer fail")

        # v6.0, 2026-09-22. X4 -- a root document routing a reader at a file that resolves nowhere.
        # The probe needs a package directory present, because X4 is the distribution repo's rule
        # and returns early without one; `pkg` above is exactly that.
        (probe / "ROOT-DOC.md").write_text("Read `docs/a-file-that-was-never-written.md` first.\n")
        got |= {x.rule for x in root_path_refs(probe)}                        # X4

        # X5 -- the package cites a rule id the trail has never heard of. The root record below is
        # the whole ground truth for the probe, so the citation in the package cannot resolve.
        (probe / "TRAIL.md").write_text("The council adopted V4C-01 and TB-001.\n")
        (pkg / "docs").mkdir(parents=True, exist_ok=True)
        # The id is ASSEMBLED at run time on purpose: written as a literal it would sit in this
        # file, and X5 scans the package's own sources -- the real finding that built this rule was
        # `V4C-77` cited inside `check_records.py` itself. A probe that trips its own control is a
        # false positive nobody can fix without weakening the control.
        fake = "V9C-" + "999"
        (pkg / "docs" / "cites.md").write_text(f"Enforced per `{fake}`, which nothing ratified.\n")
        got |= {x.rule for x in rule_id_refs(probe)}                          # X5

        for rule, why in (("P2", "missing §0 changelog heading"),
                          ("D1", "drifted shipped-vs-live validator copy"),
                          ("C1b", "a due condition whose named artifact is absent"),
                          ("M3", "an unclassified package path (manifest rot)"),
                          ("C2a", "a warning that outlived its close"),
                          ("C2b", "the same control ACCEPTED three times"),
                          ("C2c", "ACCEPTED with no reason and no owning milestone"),
                          ("L1", "Turkish text in an English-only repository"),
                          ("M1", "a PROJECT path missing from an install"),
                          ("M2", "a GP-INTERNAL path leaked into an install"),
                          ("X4", "a root document pointing at a file that resolves nowhere"),
                          ("X5", "a rule id the package cites that the decision trail never recorded")):
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
    findings += root_path_refs(root)                                  # X4
    findings += rule_id_refs(root)                                    # X5
    # G1 (v5.2, 17-8) -- FAIL CLOSED. The Security seat's ratified V5C-110 amendment #4: an empty
    # or errored derived set is a FAILURE, never a vacuous pass. It was unmet at this exact site
    # until Increment 17: a one-line edit to an in-tree `.governed-records` produced
    # `(scanned 0 record(s)) PASS exit=0` -- the entire governance validator switched off, green,
    # by a file the change under evaluation could write.
    # ...and only when this run is GOVERNING. `--install` shares this code path but asks a
    # different question -- "is this tree a complete installation?" -- of trees that may hold no
    # governance records at all. Conflating the two made a correct install fail, which is the
    # inverse of the defect G1 exists to catch and would have taught people to pass `--install`
    # to make the noise stop.
    if not records and not a.install:
        findings.append(Finding(Path(), 1, "G1",
                                "the governed-record set is EMPTY -- nothing under this root "
                                "carries `record_type:` frontmatter, or everything is exempted. A "
                                "validator that governs nothing reports PASS forever"))
    print(f"(scanned {len(records)} record(s) with frontmatter)")
    return report(findings, "repo")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
