# INSTALL MANIFEST — what an installation is

This file is the contract for what a project receives. `make export-project` copies the PROJECT set
and nothing else, and `scripts/check_records.py` reads the fenced lists below to check a tree
against them. A copy step with no declared contract cannot be wrong, because nothing says what right
is — so the lists are exact, and the check refuses a tree that disagrees with them.

## How to read this

Every path in the package belongs to one class. A directory entry (ending in `/`) covers everything
under it, and **the most specific entry wins**: a file listed as GP-INTERNAL inside a PROJECT
directory (`conformance/falsify.py` inside `conformance/`) is still withheld from an installation.

| Class | Meaning | Absent from a project | Present in a project |
|---|---|---|---|
| **PROJECT** | The installation. Copy it, fill it, keep it. | **FAIL** — the install is incomplete | correct |
| **GP-INTERNAL** | The distribution's own build, export and proof tooling. **Never copied.** | correct | **FAIL** — it does not belong in a delivery |

---

## PROJECT — this is the installation

### Control surface — the files that make the rules real
```
conformance/lib_record.py
conformance/test-commit-identity.py
conformance/test-agents-cap.py
docs/control-events.csv
conformance/test-action-pins.py
scripts/pin-actions.sh
docs/branch-protection.md
conformance/test-documented-commands.py
conformance/test-claude-md.py
conformance/test-text-encoding.py
conformance/test-check-fast.py
docs/watchlist.md
scripts/slopsquat_check.py
scripts/write_install_marker.py
scripts/create_labels.py
scripts/coverage_floor.py
docs/skip-budget.txt
scripts/shell_dialect_check.sh
scripts/wave_check.py
scripts/closure_check.py
scripts/runner_verdict.sh          (project control, carried from the v5.0 install)
.governed-records
AGENTS.md
CLAUDE.md                      (one line, @AGENTS.md; a symlink to AGENTS.md also passes)
permission-matrix.md
.agents/rules/README.md
.agents/rules/issues.md
.agents/rules/issues-qa.md
.agents/rules/practices.md
.agents/rules/playbook-seeds.md
.agents/rules/two-tools.md
.agents/rules/ci-traps.md
.agents/rules/environment.md.template
.claude/settings.json
.claude/hooks/bash_guard.py     (the Bash guard; settings.json pins its sha256)
.claude/hooks/guard_pin.py      (rewrites that pin: `make guard-pin`)
.claude/statusline.py           (the statusLine settings.json runs: DevFlow's segment after the owner's own)
.codex/hooks.json               (Codex runs the same pinned guard; .agents/rules/two-tools.md)
.githooks/pre-push
.claude/skills/
.claude/agents/
```
Without these a rule is never read or never enforced; everything else can be recovered from a
document.

### Gates and checks
```
Makefile
.devflow-stack
scripts/check_fast.py
scripts/ci_liveness.py
scripts/secrets_scan.py
scripts/brief_fields.py
scripts/review_need.py
scripts/deploy_gate.py
scripts/session_check.py
scripts/git_hooks.py
scripts/leak_scan.py
scripts/bootstrap-check.sh
scripts/check_records.py
scripts/run_check.py
scripts/gate_stamp.py
scripts/post_edit_scope.py
scripts/net_cache.py
scripts/deps_accept.py
scripts/ci_diff.py
scripts/next_adr.py
scripts/owner_bundle.py
scripts/doctor.py
scripts/cost_ledger.py
scripts/pr_check.py
scripts/prune_merged.py
scripts/standup.sh
scripts/README.md
conformance/
.github/workflows/ci.yml
.github/workflows/issue-agent.yml
.github/CODEOWNERS
.gitleaks.toml
.gitignore
.gitattributes
.language-allow
.placeholder-allow
.deps-accept
.skill-refs-allow
.path-refs-allow
```

### Project scaffolding
```
README.md
INSTALL.md
UPGRADING.md
Project_Implementation_Prompt.md
pipeline-schema.html
pyproject.toml
src/
tests/
```

### Working documents and templates — filled by the project
```
docs/architecture.md
docs/prd.md
docs/decisions.md
docs/deliverables-plan.md
docs/release.template.md
docs/owner-actions.md
docs/security-invariants.md
docs/process-log.md
docs/security-baseline.md
docs/closure-checklist.md
docs/autonomy-protocol.md
docs/refusals.md
docs/tool-suitability.md
docs/subagents.md
docs/adoption-audit.template.md
docs/EXPERIENCE.md
docs/wave-checklist.template.md
docs/warnings.ledger.md
docs/closure-report.template.md
docs/fixpack.template.md
docs/license-review.template.md
docs/project-brief.template.md
docs/run.template.md
docs/plan.template.md
docs/plans/
docs/reviews/
INSTALL-MANIFEST.md
```

### Ships empty — directories that legitimately contain only `.gitkeep`
```
docs/plans
docs/reviews
```
An emptied directory and a deliberately empty one look the same, so emptiness is declared here.
Every other PROJECT directory must hold at least as many files as it shipped with.

## GP-INTERNAL — never copied into a project

```
conformance/falsify.py
conformance/falsifications.py
conformance/test-falsify-scratch.py
conformance/test-falsify-budget.py
conformance/test-fixture-copy.py
conformance/test-no-customer-names.py
conformance/test-delivered-tree.py
conformance/test-no-gp-provenance.py
conformance/nonzero-budget.txt
scripts/export_project.py
scripts/provenance_check.py
docs/project-aliases.md
.gp/installed
.gp-distribution
pipeline-design.md
```
These build, export and prove the distribution before it ships, and none of them can run inside an
installation (`make falsify` says so and skips). `.gp/installed` is listed so the distribution's own
marker never travels: a project's `make install` writes the project's marker, and the project
commits it — `check_records.py` M2 exempts that one path in an installation for this reason, and
it is the only GP-INTERNAL path that may be present there.

One file is generated and declared in neither list: `.install-lock`, written into the delivery by
`make export-project`. It records how many files each directory carried, and `M1` compares against
it, so a directory cut down to one placeholder file still fails. A project that binds another stack
writes `stack.mk` (`INSTALL.md`); it is the project's own, never shipped, and in neither list.

## What the check does (rules `M0`–`M4`)

| Rule | Fires when |
|---|---|
| **M0** | `make install-check` is run in the distribution package itself (it carries `.gp-distribution`). That tree is not an installation; run `make export-project DEST=…` and check the result. |
| **M1** | A **PROJECT** path is missing from a project tree, or a PROJECT directory holds fewer files than `.install-lock` recorded → **FAIL.** |
| **M2** | A **GP-INTERNAL** path is present in a project tree → **FAIL.** |
| **M3** | A file in the package appears in **neither** list → **FAIL.** It runs wherever the validated root carries `.gp-distribution`, so the package's own `make check` refuses a file nobody classified. |
| **M4** | A project tree has no `.install-lock`: it was copied by hand, and nothing records what it shipped with → **FAIL.** |

`M1`, `M2` and `M4` run against a project tree through `make install-check`, a leg of `make check`.
