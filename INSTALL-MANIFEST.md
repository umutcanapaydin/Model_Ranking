# INSTALL MANIFEST — what an installation IS (V4C-72/V4C-76, v4.3)

> **Why this file exists, and it is the first thing in the package that admits a mistake.**
>
> For twelve cuts nobody declared which files constitute an installation. The consequence was
> measured in the field on 2026-08-12, and it was **wrong in both directions at once**:
>
> - A **correct** install copied GP's own history into a customer's delivery tree — 11 handover
>   records from v2.1 to v4.2, 2 internal presentations, 3 design documents, 3 manager-facing
>   overview files. **Nineteen files a project has no use for.** The owner's words:
>   *"What is a project supposed to do with OUR presentations?"* (owner, translated from Turkish)
> - The **actual** install silently dropped `.agents/rules/`, `.claude/` and
>   `docs/closure-checklist.md` — the house rules, the hooks, and the checklist Stage 4 opens by
>   walking. Two milestones closed without them. Seven `AGENTS.md` citations pointed at a directory
>   that was never there.
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
.governed-records
AGENTS.md
CLAUDE.md                      (symlink → AGENTS.md)
permission-matrix.md
.agents/rules/README.md
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
scripts/journey.py
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
```

### Project scaffolding
```
README.md
START_HERE.md
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
docs/onboarding.md
docs/process-log.md
docs/security-baseline.md
docs/closure-checklist.md
docs/autonomy-protocol.md
docs/refusals.md
docs/tool-suitability.md
docs/codex-audit.md
docs/claude-harness-config.md
docs/claude-skills-content.md
docs/external-skills/
docs/EXPERIENCE.template.md
docs/wave-checklist.template.md
docs/warnings.ledger.template.md
docs/warnings.ledger.md
docs/closure-report.template.md
docs/fixpack.template.md
docs/license-review.template.md
docs/pm-status.template.md
docs/project-brief.template.md
docs/plans/
docs/reviews/
docs/retrospectives/
docs/handovers/
INSTALL-MANIFEST.md
```

---

### The schema — PROJECT by owner ruling OD-12 (2026-08-12)
```
pipeline-schema.html
```
*The chair proposed moving the whole manual — design, architecture and schema — into PROJECT, because
ten PROJECT files cite them and `START_HERE.md` lists the design doc as item 5 of "files to read in
order". **The owner took the schema and refused the rest**, translated: "the schema can be copied to the
customer, no problem. The rest — the presentations and so on — makes no sense to me."*

***A project needs the map of the pipeline it is running. It does not need the document explaining why
we built the pipeline that way.*** *The schema is the map; the design doc and the architecture doc are
our reasoning, and our reasoning is not a deliverable.*

*This leaves the citation problem real and unsolved by classification — so the remedy this manifest
**promised in v4.3 and never implemented** is now actually implemented: every PROJECT-file reference to
a GP-INTERNAL document is a **pinned URL** at tag `v4.3`, not a relative path. A pinned link cannot go
stale silently. A relative path to a file `M2` deletes is simply a lie.*

## GP-INTERNAL — never copied into a project

### GP's own version history
```
docs/HANDOVER-v4.3.1-material.md
pipeline-design.md
pipeline-architecture.html
docs/HANDOVER-v2.1-material.md
docs/HANDOVER-v2.2-material.md
docs/HANDOVER-v3-material.md
docs/HANDOVER-v3.1-material.md
docs/HANDOVER-v3.2-material.md
docs/HANDOVER-v3.3-material.md
docs/HANDOVER-v3.4-material.md
docs/HANDOVER-v3.5-material.md
docs/HANDOVER-v4.0-material.md
docs/HANDOVER-v4.1-material.md
docs/HANDOVER-v4.2-material.md
docs/HANDOVER-v4.3-material.md
```
*Eleven of these shipped into every install for twelve cuts. They are the record of how GP was built.
A project does not need to know how GP was built; it needs GP to work.*

### GP's own presentation and explanatory material

**Language rule (V4C-79, owner directive 2026-08-12): every file in this repository is written in
ENGLISH.** The Turkish edition of the deck (`GP-v4.1-presentation-TR.html`) was **removed from v4.3**
under that rule. It is preserved unchanged in the frozen `general_pipeline_v4.2/` package and can be
regenerated on request. **If a translated artefact is ever needed again it must:** carry its language
in the filename (`-TR`), be classified **GP-INTERNAL**, and **never be the master** — the English file
is the source of truth and the translation follows it, never the reverse.
```
GP-v4.1-presentation.html
docs/executive-overview.md
docs/executive-overview.pdf
docs/executive-overview.gen.py
```

**A judgement call, stated openly:** `pipeline-design.md` and `pipeline-architecture.html` are
**reference material an agent may legitimately want** — `AGENTS.md` cites the architecture document
for the enforcement-tier model. But they are GP's documents, they go stale relative to the project
independently, and shipping them makes a project's tree carry two authorities of different vintage
for the same subject. **Resolution: they stay GP-INTERNAL, and `AGENTS.md` links them by URL at a
pinned SHA rather than by relative path.** A pinned link cannot go stale silently; a copied file can.

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

## Cost line (V4C-13)

~60 lines of stdlib list-comparison, <0.1 s. **New failure mode:** a legitimately new file fails
`M3` until classified — deliberate.

**How `M3` is proven to fire.** Not by a record fixture: `M3` is a fact about a *package*, and no
single record can trigger it. `--self-test` builds a throwaway package with an unclassified file and
asserts `M3` fires by name (`self-test ok: probe/M3 …`). The first attempt at covering it **was** a
marker fixture declaring `<!-- expect: M3 -->` — a rule that file could not possibly produce. That is
a false claim inside the test corpus, which is the exact class `conformance/` exists to catch. Deleted
in the same session it was written; see `conformance/README.md` for the rule that followed.
