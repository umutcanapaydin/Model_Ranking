---
record_type: register
id: gp-field-findings
status: ratified
date: 2026-08-16
---
# Field findings handed BACK to General Pipeline

> **Direction of travel.** V4C-71 governs what a GP harvest does with a finding about a project.
> This register is the reverse: findings this project made **about GP itself**, recorded here so the
> owner can carry them to the pipeline repository. Nothing here is a change to model_ranking.
>
> **Context:** both findings were produced by GP v5.0's own `conformance/` suite and validator on the
> first run after this project migrated from v4.3.1 to v5.0 (D-113, 2026-08-16). Neither was found
> by reading prose. That is the point: v5.0's new machinery worked, and what it caught first was v5.0.

---

## GPF-001 — Removing a Make target retroactively invalidates every adopting project's records

**Severity:** MED. It does not break a build's correctness; it breaks a build's *honesty gate*, which
in this lineage is the same thing.

**What happened.** v5.0 removed the `pin-check` Make target and moved action pinning into
`conformance/test-action-pins.py`. The conformance leg passes here (16 action references, 0
unpinned), so the control itself is intact and strictly better.

But `conformance/test-documented-commands.py` now fails against three of this project's records:

| File | Line | What it says |
|---|---|---|
| `docs/closure-report-m3.md` | 69 | names the removed target as a gate the milestone ran |
| `docs/reviews/m4-security-review.md` | 80 | same, in the tooling-output section |
| `docs/reviews/m5-security-review.md` | 101 | same |

**Why it cannot be fixed locally.** All three are historical governance records under the
append-only rule (B.2), and `closure-report-*.md` is inside this project's `.governed-records`
globs. Editing them would rewrite the record of what a milestone actually ran, to match a tool that
changed afterwards. The record is not wrong: the target existed, the milestone ran it, and the
statement was true on the day it was written.

**The general shape, which is the part GP should care about.** `test-documented-commands.py` asserts
that every command a document names still exists. That is exactly right for *live* documentation and
exactly wrong for *records*. A methodology that is simultaneously append-only and command-verified
will fail on its own history the first time it removes any target — and the failure grows with the
project's age, not with its defect count.

**Proposed remedies, in the order this project would rank them:**

1. **Make the check record-aware.** Skip files matched by `.governed-records`, or any file carrying a
   `record_type` frontmatter block. A record is a statement about the past; a document is an
   instruction for the present. The checker currently cannot tell them apart.
2. **Keep removed targets as documented tombstones.** A `pin-check` target that prints "moved to
   `conformance/test-action-pins.py` at v5.0" and exits non-zero. Cheap, but it grows forever.
3. **Do nothing and let adopters allowlist.** Rejected here: it pushes a GP decision into every
   project's exemption file, which is how allowlists become the place findings go to die.

**Recorded locally as:** W-013 in `docs/warnings.ledger.md`, ESCALATED, owning milestone M6.

---

## GPF-002 — `schemas/record.schema.json` contradicts the validator and is read by nothing

**Severity:** MED. It is inert today, which is precisely what makes it dangerous: it looks like the
contract and is not.

**Measured, on the v5.0 package and on this installation — the two files are byte-identical:**

- `schemas/record.schema.json` declares `record_type` as an enum of **seven** values:
  `ratification, register, adr, experience, handover, design, council`.
- `scripts/check_records.py:66` enforces **fourteen**: those seven plus
  `closure, wave, fixpack, brief, status, license-review, warnings`.

**The contradiction is inside v5.0's own shipped files.** `docs/wave-checklist.template.md` ships
`record_type: wave`, and `conformance/wave/m1-wave-2-close.md` — a conformance fixture — does too.
Both are values the schema forbids. If the schema were ever wired to a validator, GP's own template
and its own fixture would fail it.

**Nothing consumes the schema.** The only reference to the filename anywhere in the tree is
`scripts/check_records.py:869`, inside `D1`, which compares the file byte-for-byte against the
package copy to detect drift. It checks that the two copies are *the same*, never that either is
*correct*. So the schema has been carried, copied and drift-checked for several cuts without once
being asked whether it describes the thing it is named after.

**Why this is worth GP's attention rather than a shrug.** The comment three lines above the
validator's own `RECORD_TYPES` set is this lineage naming the exact failure, in its own words: *"a
governance model that cannot name the artefacts of the thing it governs is not installed, it is on
display."* That comment was written when `closure` was added. The JSON schema was not updated in the
same change — so the sentence describes the file sitting next to it.

**Proposed remedies:**

1. **Generate the schema from `RECORD_TYPES` / `REQUIRED` / `OPTIONAL`,** so drift is impossible
   rather than merely detected. This is V4C-49's own rule applied to GP: ship the gate in the same
   change as the rule.
2. **Or delete the file.** A schema nothing validates against is a claim, and this lineage's
   position on unexercised claims is already written down.

Option 3 — hand-editing the enum to fourteen — closes today's gap and leaves the mechanism that
produced it, so it would be the third choice, not the first.

**Recorded locally as:** no local warning. Nothing in this project is broken by it; it is entirely a
finding about the package.

---

## GPF-003 — v5.0's placeholder repair cannot tell a placeholder from notation, and no project can pass it

**Severity:** HIGH for adopters. `make bootstrap-check` is the Stage-0 gate; under v5.0 a correctly
completed project cannot make it green without editing files GP forbids it to edit.

**Isolated by differential test, not by reading.** The v4.3.1 and v5.0 versions of
`scripts/bootstrap-check.sh` were run against **the same unchanged tree** — this project at the M6
boundary, every real placeholder filled five milestones ago:

| Checker | Result on the identical tree |
|---|---|
| v4.3.1 `bootstrap-check.sh` | `RESULT: PASS -- Stage 0 gate clear` |
| v5.0 `bootstrap-check.sh` | `RESULT: BLOCKING`, 5 fail / 1 warn |

No file the checker reads was modified between the two runs. **The regression is in the checker.**

**All five findings are notation inside prose, not unfilled slots:**

| Where | The match | What it actually is |
|---|---|---|
| `docs/decisions.md:29` | `src/<pkg>/clients/` | the body of **D-001**, a UNIVERSAL ADR **GP itself ships** and AGENTS.md forbids editing without an ADR |
| `src/app/adapter/main.py:12` | `src/<pkg>/adapter/` | GP's own seed docstring explaining the K.1 boundary |
| `src/app/adapter/main.py:7` | `APP_BUILD=<tag>` | a docstring example of the L.7 build stamp |
| `README.md:71` | `src/<pkg>/` | a directory-tree diagram of the layout convention |
| `pyproject.toml:69` | `"src/<pkg>/schemas/**"` | a **commented-out** example lint rule |

A sixth finding — *"`docs/decisions.md` still looks like a template"* — is derived from the same
match, so one false positive is reported twice, which reads as corroboration.

**The trap, stated plainly.** Two of the five live in files GP ships and marks do-not-edit. A project
that "fixes" them edits a UNIVERSAL ADR to satisfy a grep; a project that does not stays BLOCKING at
Stage 0 forever. The v4.3 changelog describes the repair as *"`bootstrap-check` reads lowercase
placeholders"* — making the match case-insensitive is what pulled documentation prose into scope,
and the seed files that document the convention are the first things it catches.

**Proposed remedies:**

1. **Match a placeholder by position, not by pattern** — an unfilled slot is a whole field value
   (`name = <pkg>`), never a fragment inside a sentence, a fenced block, a comment or a path
   example. This is the same distinction GPF-001 needs between a record and an instruction.
2. **Exempt the files GP ships and forbids editing** — at minimum the UNIVERSAL ADRs in
   `docs/decisions.md` and the `src/**/adapter/main.py` seed. A gate that can only be passed by
   violating another rule is not a gate.
3. **Ship the falsification with the repair (V4C-49):** a fixture containing `<pkg>` in prose that
   must PASS, alongside one containing an unfilled field that must FAIL. The repair shipped with
   neither, which is why a case-insensitivity change reached the field as a Stage-0 blocker.

**Recorded locally as:** W-015 in `docs/warnings.ledger.md`. Not blocking this project — Stage 0
closed at M1 and `bootstrap-check` is in neither `make check` nor `make gate` — but it would block
any new project bootstrapping on v5.0 today.

---

## What this project did NOT do

It did not write these findings into the GP package tree. v5.0's `M3` rule fails the build on any
package path that appears in neither manifest class, so dropping a file into
`general_pipeline_v5.0/docs/` would break GP's own gate unless `INSTALL-MANIFEST.md` were edited in
the same change — and editing another repository's manifest is not this project's call to make.
The owner carries these across.
