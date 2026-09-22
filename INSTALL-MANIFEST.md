# INSTALL MANIFEST — what an installation IS 

> **Why this file exists, and it is the first thing in the package that admits a mistake.**
>
> For twelve cuts nobody declared which files constitute an installation. The consequence was
> measured in the field on 2026-08-12, and it was **wrong in both directions at once**:
>
> - A **correct** install copied GP's own history into a customer's delivery tree — 11 handover
> records from five earlier cuts, 2 internal presentations, 3 design documents, 3 manager-facing
> overview files. **Nineteen files a project has no use for.** The owner's words:
> *"What is a project supposed to do with OUR presentations?"* (owner, translated from Turkish)
> - The **actual** install silently dropped `.agents/rules/`, `.claude/` and
> `docs/closure-checklist.md` — the house rules, the hooks, and the checklist Stage 4 opens by
> walking. Two milestones closed without them. Seven `AGENTS.md` citations pointed at a directory
> that was never there.
>
> **One root cause: no manifest.** A copy step with no declared contract cannot be wrong, because
> nothing said what right was. This file is that contract, and `check_records.py` reads it.

## How to read this

Every path in the package belongs to exactly one class. There is no third option and no unlisted
file — an unclassified path is itself a finding (rule `M3`).

| Class | Meaning | Absent from a project | Present in a project |
|---|---|---|---|
| **PROJECT** | The installation. Copy it, fill it, keep it. | **FAIL** — the install is incomplete | correct |
| **GP-INTERNAL** | GP's own records and artefacts. **Never copied.** | correct | **FINDING** — internal history leaked into a delivery tree |

---

## PROJECT — this is the installation

### Control surface — the files that make the rules real
```
scripts/gen_schema.py
conformance/lib_record.py
conformance/test-commit-identity.py
conformance/test-schema-sync.py
docs/control-events.csv
conformance/test-action-pins.py
scripts/pin-actions.sh
docs/branch-protection.md
conformance/test-documented-commands.py
docs/watchlist.md
scripts/slopsquat_check.py
scripts/write_install_marker.py
scripts/coverage_floor.py
docs/skip-budget.txt
scripts/shell_dialect_check.sh
scripts/wave_check.py
scripts/closure_check.py
scripts/runner_verdict.sh          (project control, carried from the v5.0 install)
.governed-records
AGENTS.md
CLAUDE.md                      (symlink → AGENTS.md)
permission-matrix.md
.agents/rules/README.md
.agents/rules/issues.md
.agents/rules/practices.md
.agents/rules/playbook-seeds.md
.agents/rules/environment.md.template
.claude/settings.json
.claude/skills/
subagent-profiles/
```
**These are the ones the field install dropped.** Everything else in this list is recoverable by
reading a document; these are the ones whose absence means a rule was never read.

### Gates and checks
```
Makefile
scripts/bootstrap-check.sh
scripts/check_records.py
scripts/standup.sh
scripts/README.md
schemas/record.schema.json
conformance/
.github/workflows/ci.yml
.github/workflows/governance-contract.yml
.github/workflows/issue-agent.yml
.github/CODEOWNERS
.pre-commit-config.yaml
.gitleaks.toml
.gitignore
.mcp.json
.language-allow
.skill-refs-allow
.path-refs-allow
```

### Project scaffolding
```
README.md
METHODOLOGY.md
Project_Implementation_Prompt.md
pyproject.toml
note.txt
src/
tests/
```

### Working documents and templates — filled by the project
```
docs/architecture.md
docs/prd.md
docs/decisions.md
docs/deliverables-plan.md
docs/feature-catalog.md
docs/process-log.md
docs/security-baseline.md
docs/closure-checklist.md
docs/autonomy-protocol.md
docs/refusals.md
docs/tool-suitability.md
docs/codex-audit.md
docs/EXPERIENCE.template.md
docs/wave-checklist.template.md
docs/warnings.ledger.template.md
docs/warnings.ledger.md
docs/closure-report.template.md
docs/fixpack.template.md
docs/license-review.template.md
docs/project-brief.template.md
docs/plans/
docs/reviews/
docs/retrospectives/
docs/handovers/
INSTALL-MANIFEST.md
```

---

### The schema — PROJECT by owner ruling (2026-08-12)
```
pipeline-schema.html
```
*The chair proposed moving the whole manual — design, architecture and schema — into PROJECT, because
ten PROJECT files cite them and the orientation file listed the design doc as item 5 of "files to
read in order". **The owner took the schema and refused the rest**, translated: "the schema can be copied to the
customer, no problem. The rest — the presentations and so on — makes no sense to me."*

***A project needs the map of the pipeline it is running. It does not need the document explaining why
we built the pipeline that way.*** *The schema is the map; the design doc and the architecture doc are
our reasoning, and our reasoning is not a deliverable.*

*This leaves the citation problem real and unsolved by classification — so the remedy this manifest
**promised in an earlier cut and never implemented** is now actually implemented: every PROJECT-file reference to
a GP-INTERNAL document is a **pinned URL** at tag ``, not a relative path. A pinned link cannot go
stale silently. A relative path to a file `M2` deletes is simply a lie.*

### Distribution-side only — reclassified 2026-08-12 by council ruling
`conformance/falsify.py` and `conformance/falsifications.py` prove GP's controls **before** a package
ships. They were classified PROJECT while `scripts/export_project.py`, which `falsify.py` invokes, is
GP-INTERNAL — so `make gate` called a file the manifest guarantees is absent from every install.

**Three seats found this independently, and PM found the part that settles it: the two states are
mutually unsatisfiable.** Ship `export_project.py` to fix `falsify` and `install-check` fails with `M2`;
withhold it and `falsify` fails. *There was no state of a customer tree in which `make gate` could be
green.* That is 's class — one gate requiring a file another gate requires absent — on the
canonical gate, one increment after the telemetry catalogued it.

A project does not maintain GP's control set and has no reason to falsify it. **The gate belongs where
the controls are authored.**

`HARVEST-CONTEXT.md` and `scripts/gen_harvest_context.py` join them (condition). The context is
generated from the control roster at packet-assembly time and travels **with the harvest prompt**,
not with an installation — a project has no use for GP's roster of its own controls, and shipping it
would put the list an audit grades GP against inside the tree being audited. Policy is read from the protected base only:
read from the protected base ref, never from the material under evaluation; that is the whole
argument for generating and hashing it here rather than pasting it into a prompt.

### Generated at export — declared in neither list, deliberately
`.install-lock` is written by `export_project.py` into the delivery, not shipped from the package. It
records how many files each directory carried at the moment of export, and `M1` compares against it.
It is the only test three separate audits could not defeat with a placeholder file, because a count
does not care what the file contains.

### Generated at install — declared in neither list, deliberately
`.gp/installed` is written by `make install` (condition, closing GPF-B03). It carries the GP
version derived from the records plus the SHA-256 of this manifest, so a later harvest can read what
the install step actually did instead of believing a document's claim about its own version — the
guess that came back wrong in the 2026-08-19 field harvest.

**It is GP-INTERNAL, and that classification is the whole point.** A marker is a MEASUREMENT of the
tree that wrote it. Shipping GP's marker into a delivery would hand the next harvest GP's own commit
SHA and install date as though they were the project's — a copied measurement, which is precisely
the class of claim this file exists to replace. The project's `make install` writes its own. The
project then COMMITS that one, because a marker only the installing machine can see answers nobody's
question.

### Ships empty — directories that legitimately contain only `.gitkeep`
```
docs/plans
docs/reviews
docs/retrospectives
```
*Emptiness has to be DECLARED, not inferred. An emptied directory and a deliberately empty one are
indistinguishable in the tree — and an auditor proved it twice: first by reducing a 105-file install to
68 (`M1` accepted `.exists`), then by reducing 118 to 42 after the repair exempted any directory
holding a `.gitkeep`. Every directory NOT in this list must carry real content or `M1` fails.*

## GP-INTERNAL — never copied into a project

### GP's own version history
```
conformance/falsify.py
conformance/falsifications.py
scripts/export_project.py
scripts/strip_provenance.py
scripts/gen_harvest_context.py
scripts/gen_methodology.py
docs/project-aliases.md
docs/practices-cut.md
docs/control-screen.template.md
docs/pm-status.template.md
conformance/test-no-customer-names.py
HARVEST-CONTEXT.md
.gp/installed
.gp-distribution
pipeline-design.md
pipeline-architecture.html
```
*Eleven of these shipped into every install for twelve cuts. They are the record of how GP was built.
A project does not need to know how GP was built; it needs GP to work.*

### GP's own presentation and explanatory material

**Language rule (owner directive 2026-08-12): every file in this repository is written in
ENGLISH.** The Turkish edition of the deck (`GP-v4.1-presentation-TR.html`) was **removed**
under that rule. It is preserved unchanged in the frozen `general_pipeline_v4.2/` package and can be
regenerated on request. **If a translated artefact is ever needed again it must:** carry its language
in the filename (`-TR`), be classified **GP-INTERNAL**, and **never be the master** — the English file
is the source of truth and the translation follows it, never the reverse.

*Nothing is listed here any more.* The last entry, a manager-facing overview that recounted GP's
version history, was retired: that is the record of how GP was built, which the section above
already says a project does not need.

**A judgement call, stated openly:** `pipeline-design.md` and `pipeline-architecture.html` are
**reference material an agent may legitimately want** — `AGENTS.md` cites the architecture document
for the enforcement-tier model. But they are GP's documents, they go stale relative to the project
independently, and shipping them makes a project's tree carry two authorities of different vintage
for the same subject. **Resolution: they stay GP-INTERNAL, and the method itself is DERIVED into a
delivered file.** `scripts/gen_methodology.py` generates `METHODOLOGY.md` from `pipeline-design.md`
§1–§17 — dropping §0 (GP's council changelog), substituting the project aliases, and rewriting the
links. One source, one generator, a staleness check: rather than a second hand-written copy.

**This replaces the previous resolution, and the reason is worth recording.** Until the split
the answer was *"`AGENTS.md` links them by URL at a pinned SHA"* — 22 such links existed, and **every
one of them pointed at a GP-INTERNAL file in a PRIVATE repository.** That was survivable while a
delivery was a private handover. The moment the distribution became the public `DevFlow` repository
it stopped being survivable: each link is a dead end for the reader, or a pointer at something they
cannot open. A pinned link cannot go stale silently, but it can point somewhere nobody can follow.

---

## What the check does (rules `M1`/`M2`/`M3`)

| Rule | Fires when |
|---|---|
| **M1** | A **PROJECT** path is absent from a project tree → **FAIL.** This is the rule whose absence let two milestones close without house rules. |
| **M2** | A **GP-INTERNAL** path is present in a project tree → **FAIL.** GP's history does not belong in a delivery. |
| **M3** | A path exists in the package but appears in **neither** list → **FAIL.** Without this, the manifest rots the moment someone adds a file, and a manifest that rots is worse than none because it looks authoritative. |

**M3 is the one that keeps this file honest**, and it is deliberately the strictest: adding a file to
the package without classifying it breaks the build. That is the intended cost.

`M1` runs against a project tree (`--install <path>`). `M2` and `M3` run against the package itself,
in the standard validator run, so a manifest drift is caught at the GP repo before any project sees it.

## Cost line 

~60 lines of stdlib list-comparison, <0.1 s. **New failure mode:** a legitimately new file fails
`M3` until classified — deliberate.

**How `M3` is proven to fire.** Not by a record fixture: `M3` is a fact about a *package*, and no
single record can trigger it. `--self-test` builds a throwaway package with an unclassified file and
asserts `M3` fires by name (`self-test ok: probe/M3 …`). The first attempt at covering it **was** a
marker fixture declaring `<!-- expect: M3 -->` — a rule that file could not possibly produce. That is
a false claim inside the test corpus, which is the exact class `conformance/` exists to catch. Deleted
in the same session it was written; see `conformance/README.md` for the rule that followed.
