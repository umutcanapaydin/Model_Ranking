---
record_type: register
id: gp-v5.0-field-experience
status: ratified
date: 2026-08-20
---
# GP v5.0 — Field experience report from **HCS MaaS Ranking**

> **Written for transport.** This report is meant to leave the project it was produced in, so it
> names no repository, no person and no tool vendor, and carries no absolute paths. Where a file is
> cited it is cited by its repository-relative path, which is the same in any adopting project.
> "The implementing agent" and "the reviewing seat" are roles, not products.
>
> **What it covers.** Eight milestones of continuous use, v4.3.1 for the first three and v5.0 from
> the migration onward. It is deliberately NOT a complaint list: the most useful half is which
> controls paid for themselves, because that is the half a pipeline gets talked out of.
>
> **Companion document.** Five specific defects in GP's own machinery are already filed separately
> as GPF-001..GPF-005. They are not repeated here.

## 0. The measurement base

Everything below is drawn from records that were written at the time, not reconstructed:

| | |
|---|---|
| Milestones completed | 8 |
| Automated tests at the last close | 578 (12 skipped) |
| Governed records under the validator | 43 |
| Project ADRs | 26 |
| Warning-ledger entries | 43 — **9 FIXED, 15 ACCEPTED with an owning milestone, 19 ESCALATED** |
| Reviewing seats used | code review, tester, security, explorer |

The ledger split is worth reading twice. **Only one warning in five was fixed in the milestone that
raised it.** That is not a failure of discipline — the ledger is doing exactly what it is for — but
it means an adopting project should expect the ledger, not the code, to be the place where the
milestone's real state lives. Any tooling GP adds should treat the ledger as a first-class
artifact, not a text file.

---

## Part A — Controls that paid for themselves, with the measurement

### A.1 Fault injection (V3C-72) is the highest-yield control in the pipeline, **but only when the mutants are designed by someone else**

This is the single most important finding in this report.

Across the whole project, fault injection found more real defects than every other technique
combined. Measured examples:

- One HIGH-tier wave: the author wrote 11 mutants; an independent tester wrote 52 across three
  rounds and **16 stayed green** on code whose gates were already passing.
- The last milestone: the implementing agent reported **23 mutants, 23 killed — 100%**. An
  independently designed set of 47 mutants over the same range was **12 killed, 35 survived: 25.5%**.

Both numbers were honestly produced. The difference is not diligence; it is that **a mutant set
written by the author of the code tests the author's model of the code.** A 100% kill rate against
your own mutants measures your imagination, and it reads in a record exactly like evidence.

**Proposal (P-1).** The wave-close checklist's fault-injection row should require the mutant set's
AUTHOR, and GP should state that a self-designed set is *supporting* evidence, never sufficient
evidence, on a HIGH-tier wave. One extra column; it changes what the row means.

**Proposal (P-2).** V3C-72's protocol is excellent and should be kept verbatim — mutate in place,
confirm RED, restore, **verify the restore with a checksum**, never `git checkout`. The checksum
step is not ceremony. In this project a tester's own restore logic corrupted two entries in a data
file by reverse-replacing the wrong occurrence, and the md5 assertion aborted the run within
seconds instead of leaving a silently wrong file for the next reader. **Add one sentence to the
protocol saying restore must reproduce the pre-injection BYTES held in memory, not re-derive them
by reversing the edit.** That is the specific mistake, and it is easy to make.

### A.2 Fresh eyes (K.7) — the value is now measured three separate times

Every occasion where a review was skipped or deferred produced findings when it eventually ran, and
none of them were found by the author:

| Occasion | What the independent seats returned |
|---|---|
| One wave that skipped its review and was held open | code review BLOCKING (2), security BLOCKING (1); three rounds before close |
| One HIGH-tier wave with all three seats | all three returned BLOCKING; 10 findings total |
| One production-entry-point wave | **30 BLOCKING across three rounds, none found by the author** |
| Three consecutive waves closed under an explicit bypass | all three seats BLOCKING, including a new module at 32% coverage with zero tests naming it |

The last row is the cleanest experiment the project ran, because the bypass was deliberate,
recorded, and then reversed. **The control's value is not theoretical and GP should say so with
these numbers rather than with an argument.**

The uncomfortable half: every round after the first also found defects **the author had introduced
while fixing the previous round**. That is the strongest argument for the round cap that v5.0's
risk tiers introduced, and it should stay.

### A.3 The build stamp on `/health` (L.7) caught "restart is not rebuild" twice

Both times the symptom was identical and would have been unfalsifiable without it: the artifact on
disk had been rebuilt, the process was still serving the previous inode, and every health check,
every test and every gate was green. The **only** disagreeing evidence in the entire system was the
build stamp reporting an older commit than `HEAD`.

**Proposal (P-3).** L.7 currently says the deploy step must compare `/health`'s build to the
intended tag. Widen it: **any local run script that claims to "restart" must print the build stamp
it ended up with.** The failure is not specific to deploys; it happens on a developer's machine
every time a process outlives a file replacement, and that is where it costs the most time because
nobody suspects it.

### A.4 The record validator's narrowness rules are right, and unpopular for the right reason

Two v4.1 rules earned their keep repeatedly:

- **V4C-35 (a field may exist only if a check consumes it).** When the implementing agent added
  `ratified_by` and `ratified_date` to a ratification record's frontmatter, the validator rejected
  both within a minute. They looked obviously useful and nothing read them. The rule prevented a
  frontmatter schema from growing by accretion, which is how every metadata block in the world
  becomes unreadable.
- **V3C-69's evidence rule (an unevidenced PASS is an opinion).** The wave-check tool refused
  wave-close records **four times in a single session** for rows that carried a verdict and no
  `file:line`, path or date. Every refusal was correct.

**Keep both. Do not soften them.** They generate friction exactly proportional to how much someone
is about to assert without evidence.

### A.5 Default-deny publication (allowlists over denylists) is the one pattern that never failed

This project publishes an unauthenticated JSON payload. Its field set is an explicit allowlist, and
adding a field to it requires a human edit in two places, both gated. Across eight milestones **no
field ever escaped to a public surface by accident.**

Everything shaped the other way did fail, at least once. See Part C.1.

### A.6 The two-lane git authority rule (V4C-64) is correct and was needed

A prior agent in this project produced twelve commits carrying the OWNER's name with an unset-git
placeholder email. The rule that caught it is the one that says an agent commit must never be
mistakeable for the owner's. Without the attribution requirement there is no evidence base for any
of the other controls, because you cannot tell who did what.

**Proposal (P-4).** The rule exists; the CHECK is manual. A conformance test that reads the commit
range of the closing milestone and asserts that every commit carries either the owner's verified
identity or a machine identity plus the agent trailer is about fifteen lines, and it would have
caught this on the day rather than at closure.

---

## Part B — Controls that exist and do not fire

These are not missing rules. They are **written rules with no gate**, which is the failure mode
v4.2's own V4C-49 names ("ship the grep gate in the same change as the rule"). GP does not yet
apply that rule to itself.

### B.1 The coverage rule is the most expensive unenforced rule in the pipeline

The permission matrix lists "coverage drop on a touched module" as BLOCKING. Nothing computes it.
In this project the test runner produces a coverage report and there is **no failure threshold at
all**, so:

> A new module — the single reader behind six of the product's nine user-facing surfaces — reached
> the closing tree at **32% coverage with zero tests referencing it**, through a green gate, through
> a wave close, through a milestone closure report, and through a self-run security review. Three
> independent seats found it in the same pass. Fourteen of fourteen mutants placed in it survived,
> including a path-traversal guard whose own docstring cited a previously-reproduced incident: **the
> control had been carried forward as prose and the test had not been carried with it.**

This is the highest-leverage single change available to GP v5.1, and it outranks any individual
defect in this report.

**Proposal (P-5).** GP should ship a coverage floor in the template's test configuration — not a
number it dictates, but a *required, explicitly-set* value, with the bootstrap gate refusing a
project that leaves it unset. "Choose your floor" is enforceable; "coverage matters" is not.

**Proposal (P-6), stronger and cheaper.** A per-module rule beats a global one for exactly this
failure: a global 86% total hid a 32% module. Suggest: **fail when a file changed in this milestone
has coverage below the repository median.** It is computable from the same report and it targets
new code, which is where the risk is.

### B.2 Three named gates live outside the one command anybody runs

In this project `make check` runs lint, typecheck, tests and the record validator. The secret scan
is a separate target. The wave-record validator is a separate target. Coverage has no target at
all. **A gate that is not in the command people actually type does not run**, and this was measured:
the wave-record validator failed all four of one milestone's wave records on the same three lines,
and nobody knew until someone ran it by hand at closure.

**Proposal (P-7).** GP's template `check` target should be the single door, and anything a project
declares as a gate should be reachable from it. If a gate is expensive, gate it behind a flag —
but its absence from the default path should be a deliberate, recorded choice, not an accident of
Makefile layout.

### B.3 V3C-02 has no exemption class, so it cannot express a process criterion

"EVERY acceptance criterion has a citing test" is the right default. But this project produced a
criterion of the form *"any contract gap the client finds is recorded as a finding before any
workaround"* — a process obligation whose evidence is the ledger and the ADR trail, not an
assertion about running code. There is no honest citing test for it.

The two available behaviours are both bad: mark it MET and lie, or leave it out and let the
checklist quietly shrink. This project ledgered it instead, which is a third option only because
someone noticed.

**Proposal (P-8).** Add an explicit `process` criterion class to V3C-02 whose evidence is a named
record rather than a test, and require the class to be declared on the criterion. The rule stays
absolute for behavioural criteria, which is where it earns its keep.

### B.4 The bypass counter (V4C-13 / `C2b`) is prose, so it does not count

The rule is excellent: a control skipped under pressure is recorded, never hidden, and **the same
control bypassed three times sends the CONTROL for review rather than the seat.** In this project
that threshold was reached — three consecutive waves closed with no fresh-eyes review, each under
an explicit owner ruling, each recorded honestly.

It worked only because the implementing agent wrote "this is the second" and "this is the third"
into the wave records by hand. **Nothing counted.** A project with a less scrupulous author, or
simply a different author per wave, would have hit the threshold invisibly.

**Proposal (P-9).** Make the bypass ledger a small structured file (`control`, `wave`, `reason`,
`date`) that the wave-check tool appends to and reads. Three lines with the same `control` value
turns the next wave's checklist row red automatically. This is perhaps forty lines of tooling and
it converts the pipeline's best self-correcting rule from an honour system into a gate.

### B.5 The record system cannot tell a comparison table from a checklist table

A minor but recurring friction: the wave-record validator identifies checklist rows structurally,
so any OTHER table in the same record — for example a two-column "claimed versus independently
measured" comparison — is parsed as unevidenced checklist rows and fails the file. The author's
only recourse is to rewrite legitimate content as a bullet list.

**Proposal (P-10).** The validator already locates and validates the checklist's HEADER row. Anchor
row parsing to the table that follows that header, and ignore other tables. Small fix; it stops the
tool from teaching authors to put less structure in records.

---

## Part C — The recurring defect taxonomy

This is the part most worth carrying into GP's own documentation, because these classes recurred
across unrelated subsystems, different authors and both pipeline versions. Each is stated in the
form that made it recognisable.

### C.1 "An enumeration that is typed out is a denylist wearing better clothes"

Proven four separate times in one milestone alone. Every hand-maintained list of names — fields to
redact, sources to attribute, disclosures to render, clients to check — eventually disagreed with
the thing it was supposed to describe, silently.

**The fix that works is derivation**: read the set from the source of truth (the dataclass, the
directory, the registry, the AST) rather than restating it. Where an exemption is genuinely needed,
it must be a NAMED entry carrying a written reason, and the exemption set must itself be validated
against reality — an exemption that outlives the thing it exempts silently widens.

### C.2 "A control that is cited but does not run"

The classic form. v5.0's conformance suite catches some of these. The variants that got through:

- a control cited in a docstring, with the code deleted
- a control whose only reachable path was through a branch nothing entered
- a control that ran on every request and **should not have existed at all** — deleting the write
  that forced it removed the control, its budget, its tests and the entire class of finding

### C.3 **NEW: "A control whose SCOPE is narrower than the rule it cites"**

This class is not in GP's vocabulary and it should be. It is more dangerous than C.2 because the
control genuinely runs, genuinely fails on some inputs, and looks like a gate in every record.

Measured instance: a guard asserting that every ingested evidence source can be attributed asked
only about each *category's primary source*. A source used as secondary evidence was outside that
population — so deleting its attribution walked straight through a control specifically written to
prevent that. Rebasing the guard onto the source registry then made it too WIDE, demanding
citations from pricing sources that are never cited, which is the same error mirrored.

**The diagnostic question**, which GP could add to the reviewer profile: *"name the exact population
this control examines, then name the population the rule covers. Are they the same set?"*

### C.4 **NEW: "A test cannot fail if its fixture cannot reach what it asserts"**

Three instances in a single wave, all in tests written to close review findings:

- a rounding assertion whose fixture values were already round
- the same fixture carrying no rows of the secondary kind at all, so a mutant was *equivalent there*
  and live in production
- a report assertion where the two counts being compared were both `2`, so swapping them was
  invisible

Each produced a test that read as a gate and was a decoration, and each was written *by someone who
had just been told the code was untested*. This is C.3 one level down — in the DATA rather than the
code.

**Proposal (P-11).** The V3C-02 row should not ask "is there a citing test" but "**has the citing
test been observed RED**", with the mutation recorded. This project adopted that practice
informally and it caught every one of the three above within minutes. It is a one-column change to
the checklist and it is the highest-value process change in this report after P-5.

### C.5 "A seam is only a seam if it reaches the caller"

Three instances, each a different half of the same mistake:

1. an injection parameter bound as a **default argument**, so it bound at definition time and a test
   that believed it used fakes reached the real network
2. the identical bug written into a neighbouring function **twenty minutes after fixing the first**
3. a function that took an injection parameter and read it correctly at call time, while its own
   CALLER exposed no way to pass one — so eight tests believed they controlled the input set and
   silently ran the real one

The third is the one nobody looks for. **The injection point is not the parameter; it is the path
from the caller to it**, and the test that proves it must drive the real entry point.

### C.6 "A record that states the opposite of the code" — and its worse relative

Records drifting from code is a known class. The variant this project produced is worse and GP
should name it:

> A closure report, two wave records and a **retrospective** all stated that a one-time contract
> revision window was unspent. An ADR in the same repository recorded spending it. The retrospective
> then drew a CONCLUSION from the false premise — a general lesson about contract design — and that
> conclusion travelled into a closure report awaiting signature.

**A retrospective is the easiest place in the pipeline to launder an unverified premise into a
finding, because nothing downstream re-derives it.** Everything else gets checked against code
eventually; the lessons file does not.

**Proposal (P-12).** The retrospective template should require every factual claim underpinning a
lesson to cite the record or `file:line` it was re-derived from **at retrospective time**, not
inherited from the closure report. Cheap, and it protects the one document whose whole purpose is
to be believed later.

### C.7 "Calibrating against the wrong population"

Domain-flavoured but general: three times, thresholds that decide user-visible behaviour were
derived from a data set that was not the one the system actually operates on (raw input rows, then
parsed rows, then the full candidate set instead of the filtered subset the engine can actually
serve). Each was caught by measuring, never by reading, and each produced materially different
numbers.

The root cause is worth generalising: **the operative population had no name in the codebase.**
There was no function to call and no term to look up, so the question was answered from whatever
data was nearest. GP's guidance on calibration should say: if a number is derived from a
population, that population gets a named accessor in the code, and the calibration work is required
to call it.

### C.8 "Restart is not rebuild"

See A.3. Twice.

---

## Part D — What actually made the work SLOW

Requested explicitly, so stated plainly. The pipeline's overhead was not the problem; three
specific things were.

### D.1 Review rounds that find defects introduced by the previous round

Measured: findings across three rounds on one wave went 14 → 8, and **every round after the first
found defects the author had introduced while fixing the earlier ones.** The round cap is the right
answer and v5.0 has it. What v5.0 lacks is the cheap counter-measure:

**Proposal (P-13).** After a fix round, **re-run the PREVIOUS round's mutant set against the fix**
before re-review. It costs one command and it catches the regression class that causes the extra
round. Add it to V3C-72 as the "fix verification" step.

### D.2 Depth applied uniformly to work with wildly different blast radius

Before this was ruled on, plumbing and the scoring path received the same review depth, and the
cost was visible: the owner asked, in as many words, whether the methodology was being applied
because it fit or because it was there. The project answered with a local ADR — review depth
follows blast radius, full depth on the scoring path and the public contract, single pass on
plumbing, round cap of two.

**That ruling roughly halved the process cost with no measurable loss** — with one important
caveat found later: when the tiering allows a bypass, the bypass compounds silently unless
something counts it (see B.4). **Recommend v5.1 adopt blast-radius tiering as a first-class concept
alongside V3C-78's risk tiers, and ship P-9 with it.** The two are safe together and unsafe apart.

### D.3 Records the tooling makes expensive to write correctly

Between the placeholder-repair check, the English-only rule with no negation escape hatch
(GPF-005), the checklist parser (B.5), and the frontmatter narrowness rule, a substantial amount of
time went into making correct records *pass*, rather than into making them correct. The rules are
individually right. The aggregate friction is real, and it is highest for exactly the documents
that matter most — closure reports and wave records.

**Proposal (P-14).** Ship a record-scaffolding target — "make record-new TYPE", named here
without backticks on purpose, because the pipeline's own `test-documented-commands` check
reads a backticked `make` target as an INSTRUCTION and fails the build for naming a command
that does not exist yet. A proposal cannot be written in the notation the checker demands.
That is a small instance of GPF-001's shape and it happened while writing this report. The
scaffold would emit a skeleton already
satisfying every structural rule. The rules are machine-checkable, therefore machine-satisfiable.
Every minute an author spends discovering a structural rule by failing it is a minute not spent on
the content the rule exists to protect.

---

## Part E — Smaller observations, kept short

1. **The bootstrap gate (FB-1/FB-4) was worth it.** A single early command that refuses stray
   placeholders and an unfilled requirements document prevented the whole class of "we will fill
   that in later".
2. **`make smoke-deps` (L.8) found a genuinely dead dependency**, and more usefully proved the
   difference between *configured* and *working* on a source that had been assumed healthy for days.
3. **The spike lane (V3C-87) was never used** in eight milestones. Either it is unnecessary for
   projects of this shape or its existence needs surfacing at plan time; currently it is discovered
   by reading.
4. **The explorer profile (V3C-85) meaningfully reduced context pressure** and should be promoted
   from a note to a default: repository exploration goes to a read-only seat that returns a bounded
   summary.
5. **The security review's position at closure (v5.0 moved it there) is correct**, with one caveat:
   when nothing deploys, the review has no gate to block and quietly becomes advisory. GP should
   say what a Stage 4.0 PASS means for a milestone that does not deploy.
6. **A self-run security review should not be allowed to record a verdict.** In this project one
   returned PASS / 0 BLOCKING and an independent seat subsequently returned BLOCKING and found a
   factual error in it. The self-review was written honestly and labelled as a self-review; that
   was not enough, because the label does not travel with the verdict into the closure report.
   Suggest: a self-run security pass records FINDINGS but is not permitted to record a PASS.

---

## Part F — The five changes with the best ratio

If GP v5.1 adopts nothing else:

| # | Change | Why this one |
|---|---|---|
| **P-5 / P-6** | A required, explicitly-set coverage floor; per-module rather than global | The single control that would have caught the worst defect in the last milestone. A global figure hid a 32% module. |
| **P-11** | The citing-test row asks for the RED observation, not the test's existence | Converts V3C-02 from "a test exists" to "a test can fail", which is what it always meant. Caught three fixture-blind tests in minutes. |
| **P-9** | Make the bypass counter mechanical | Turns the pipeline's best self-correcting rule from an honour system into a gate. ~40 lines. |
| **P-1** | Record who designed the mutant set; self-designed is supporting evidence only | 100% against your own mutants was 25.5% against someone else's. One column. |
| **P-13** | Re-run the previous round's mutants against the fix | Directly attacks the "extra round" that costs the most wall-clock in this pipeline. |

---

## Closing note

The uncomfortable summary of eight milestones is that **almost every serious defect was found by
something mechanical or by someone who had not written the code, and almost none by careful
reading — including careful reading by the person who had just been told what to look for.**

That is not an argument for more process. It is an argument for putting the process budget into
the two things that demonstrably work: independent eyes, and controls that fail loudly when the
thing they protect is removed. Most of the proposals above are attempts to move a rule from the
first category into the second.
