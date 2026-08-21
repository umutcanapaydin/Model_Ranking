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

**New evidence, 2026-08-17 (M6 closure) — the check has a second mode of failure and it is worse.**
The owner's out-of-sandbox run surfaced a fourth dangling command that was NOT this finding: an M6
review record cited a `serve` target that never existed (the target is `make run`). That one was a
genuine defect and was corrected. **But writing the correction note re-broke the check**: both
amendment notes had to name the bad target in order to say what was wrong with it, and
`test-documented-commands.py` counted those citations as instructions — dangling went 4 → 5, and the
repair looked identical to the disease.

The workaround was to write the target's name without its invocation prefix, which is a formatting
trick, not a fix. The point for GP is structural: **a project cannot document having fixed a broken
command, because the fix record must quote the broken command.** This is the same records-versus-
instructions blind spot as GPF-004 (`test-git-authority` reading an attestation as an order) and
GPF-005 (`L1` having no negation escape hatch) — **now confirmed in a third check of seven.** Three
of seven conformance tests share one design gap; that is a property of the suite, not a coincidence
among its files. Whatever mechanism GP adopts for GPF-004/005 — a negation list, a quoted-citation
form, a `record_type`-aware mode — must cover this check in the same change.

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

## GPF-004 — `test-git-authority.py` cannot tell a compliance ATTESTATION from an instruction (this section instructs nobody: it must not be read as a command)

**Severity:** MED. It produces a false BLOCKING on exactly the artifact that proves compliance,
which teaches a reviewer to stop writing the attestation.

**How it surfaced.** A fresh-eyes reviewer, operating under the rule that agents do not run git in
the local lane (D-114 here, `AGENTS.md` §3 in v5.0), ended its verdict with the sentence stating
that no git state-changing command had been run, followed by its `git status --short` evidence.
`conformance/test-git-authority.py` flagged that sentence as a local-lane git violation.

**Cause, precisely.** The check's `NEGATION` regex exempts a line that *forbids* a command —
`never`, `do not`, `must not`, `shall not`, `refuse`, `forbid`, `DENY`, `bypass`, and the
owner-performs constructions. It does not recognise the past-tense negative attestation
**"no `git commit` … was run"**. The check is section-aware and carefully written — its own comments
record two earlier rounds of exactly this false-positive class being fixed — but every exemption so
far is phrased as a PROHIBITION. A record of non-action is a third grammatical mood and the list has
no entry for it.

**Why it matters more than a wording nit.** The rule this check enforces is one an agent demonstrates
compliance with by *writing the attestation down*. Under the current pattern, writing it down is what
fails the build. The available responses are all bad: reshape the sentence to include a magic word
(prose written to satisfy a grep), delete the attestation (lose the evidence), or ledger a permanent
red leg (a gate nobody can pass stops being read). This is the same records-versus-instructions
confusion as **GPF-001**, in a different check — which is the actual signal: two of the seven
conformance tests share a blind spot, so it is a design gap in the suite rather than a bug in one file.

**Proposed remedies:**

1. **Exempt by artifact class, not by wording** — skip files carrying a `record_type` frontmatter
   block, and files under `docs/reviews/`. A verdict is a record of what happened; only live
   instructions can instruct. One rule would close GPF-001 and this together.
2. **Add the attestation mood to `NEGATION`** — `\bno\b[^.]{0,40}\bwas run\b`, `\bdid not run\b`,
   `\bnever ran\b`. Cheaper, and it keeps the same enumeration problem one round further out.
3. **Ship the fixture with the rule (V4C-49):** a `pass/` fixture containing a compliance
   attestation that must NOT fire, alongside the existing violation fixtures. The check has fixtures
   for what it must reject and none for what it must accept, which is why two rounds of false
   positives were found by users rather than by the suite.

**Recorded locally as:** no warning row. Nothing in this project is defective; the finding is
entirely about the package. The affected line is left as the reviewer wrote it or restated by the
reviewer — not edited by the lead agent, because it is that reviewer's record.

---

## GPF-005 — `L1` has no negation escape hatch, so no record can state what it detects (this section describes, never instructs)

**Severity:** MED, and it is the same defect as GPF-004 in a second rule — which is the finding.

**How it surfaced, twice in one session.** A fresh-eyes reviewer's verdict failed `check-records`
because it quoted the characters `L1` looks for, in order to explain a finding about `L1`. Then the
ADR correcting that finding failed for the same reason. Both documents were *about* the rule; neither
instructed anything.

**Cause.** `conformance/test-git-authority.py` ships a `NEGATION` list precisely so a rule may name
the command it forbids — its own comments record two rounds of that false-positive class being
repaired. `L1` in `scripts/check_records.py` has no equivalent. There is therefore **no way to
document the rule inside the repository the rule governs**: any accurate description of it is a
violation of it.

**The pattern across GPF-001, GPF-004 and now this.** Three of the suite's checks cannot distinguish
a document that DESCRIBES a thing from one that DOES it — a removed command named in a historical
record, a compliance attestation about git, and now the alphabet an English-only rule detects. One
check solved it (section-aware negation) and the solution was not generalised. **That is a
suite-level design gap, not three bugs.**

**Additional finding about the rule's reach, measured here:** `L1` detects an ALPHABET, not a
language. Turkish written in pure ASCII passes it silently — this project shipped four such strings
after declaring an English-only migration complete, with the gate green (recorded locally as W-019).
A project reading `L1`'s name would reasonably believe it enforces the policy V4C-79 states, and it
enforces a proper subset.

**Proposed remedies:**

1. **Generalise the artifact-class exemption** proposed in GPF-001 across every conformance rule and
   `L1` — a file carrying a `record_type` frontmatter block, or living under `docs/reviews/`, is a
   record. One rule, three findings closed.
2. **Give `L1` the negation mechanism `test-git-authority.py` already has**, so a heading that says
   "describes, does not instruct" exempts its section.
3. **Rename or re-document `L1`** so its stated scope matches its reach: it is a non-ASCII-letter
   detector, and the gap between that and "English-only" is where a migration will stop.

**RECURRENCE COUNT, updated 2026-08-17: FOUR in one project, one milestone.** A W1 reviewer's
verdict, the ADR that documented the finding, a W3 Tester's verdict, and the Stage-4.0 closure
review — every one of them a record
of non-action, every one flagged as an instruction. The count matters because this lineage's own rule
is that the same control tripping three times sends the CONTROL for review, not the people. Two
different checks (`test-git-authority` and `L1`) are producing it, so the review is of the suite's
records-versus-instructions model rather than of either file.

**Recorded locally as:** W-019 for the reach gap; no local warning for the escape-hatch gap, which is
entirely GP's.

---

## What this project did NOT do

It did not write these findings into the GP package tree. v5.0's `M3` rule fails the build on any
package path that appears in neither manifest class, so dropping a file into
`general_pipeline_v5.0/docs/` would break GP's own gate unless `INSTALL-MANIFEST.md` were edited in
the same change — and editing another repository's manifest is not this project's call to make.
The owner carries these across.

---

## GPF-006 — `L1` detects an ALPHABET, not a language, and a project can pass it while shipping the language

**Rule:** `check_records.py` rule `L1`, which enforces V4C-79 (an adopting project's committed files
are English).

**What GP ships:** `L1` flags the six letters that exist in Turkish and not in English. That is a
reasonable first approximation and it is what makes the rule cheap. It is also, precisely, an
alphabet check wearing a language check's name — and the gap is not theoretical.

**Measured in the field.** After this project's English-only migration was declared complete and
its full gate was green, **four fragments of Turkish written in pure ASCII were still shipping in
live user-facing strings**, one of them rendering a single sentence in two languages. The migration
had followed the gate's signal and stopped exactly where the gate stops. Three tests had also been
left pinning the survivors, so the suite was asserting the defect.

**Why the adopting project cannot simply fix this.** It can mitigate — this one now parses its own
string literals and matches a conservative list of ASCII spellings that have no English meaning —
but that list is language-specific, and the next project adopting v5.0 will be shipping a different
language with a different ASCII footprint. The rule belongs where the rule is.

**Two remedies, ranked.**

1. **Make the rule's SCOPE honest in its own message.** One sentence in the failure text — that
   `L1` detects the alphabet and not the language, so a clean run is not evidence of a completed
   migration — costs nothing and stops the reading that produced the defect here. A gate whose
   limits are stated is a gate people calibrate against.
2. **Let a project declare its non-English source language** in `.language-allow` or beside it, and
   ship a small per-language ASCII marker list that `L1` consults. Optional, opt-in, and it turns a
   letter check into a language check for the one language each project actually risks.

**Related, and found while writing this up:** the mitigation test above **failed `L1` on its first
run**, because its docstring wrote out the six letters in order to explain what the rule detects.
That is **GPF-005 reproducing itself in a new file** — no record can state what the rule catches.
The workaround was to name the letters in prose instead. Two findings that look separate are one:
`L1` has no way to distinguish text that IS the thing from text ABOUT the thing.
