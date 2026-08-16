---
record_type: design
id: branch-protection
status: ratified
process_version: v5.0
date: 2026-08-16
---
# Required status checks — the one list, and why there was none

**DevOps seat, Increment 14 (D-3):** three documents named required checks, no two agreed, and **not one
of them named the job that runs the install and governance gates.** A pull request could fail
`install-and-governance` and merge.

There was a fourth problem underneath: `pipeline-design.md` required a check named `lint`, which is not
a job — it is a step inside `test`. **A required check by that name never reports at all**, and a
required check that never reports blocks nothing while looking like protection.

This file is the single list. Anything naming required checks elsewhere is wrong by construction.

## For a project using this package

Protect `main`. Require these **job names** — not step names, not workflow names:

| required check | workflow | what it means if you drop it |
|---|---|---|
| `test` | `ci.yml` | lint, typecheck and the test suite. Lint and typecheck are STEPS inside this job; do not list them separately |
| `secret-scan` | `ci.yml` | gitleaks. Dropping it means a credential can reach `main` through a green PR |
| `dep-audit` | `ci.yml` | `pip-audit --strict` against the installed dependency set |
| **`install-and-governance`** | `ci.yml` | **the one that was missing.** Install completeness (`M0`–`M4`), the governance records, the validator's not-a-no-op proof, and the conformance suite |

Also enable: **require branches to be up to date before merging** (otherwise a check can pass against a
stale base), and **include administrators** — a rule the owner can wave through is a rule that will be
waved through under deadline.

## For the GP repository itself

| required check | workflow |
|---|---|
| `governance-contract` | `.github/workflows/governance-contract.yml` |

One job, deliberately: it is an aggregate, unconditional, and it now runs the conformance suite and the
falsification registry as well as the validator. **A single required name cannot be satisfied by a
skipped job**, which is the failure this lineage was founded on.

## What this file does not do

It cannot enforce itself. Branch protection is configured in GitHub's UI or API and lives outside every
tree, so `conformance/test-ci-yaml.py` asserts only that **every job named here exists in a workflow**
and that **every job in `ci.yml` is named here.** Drift between this list and the repository's actual
settings is invisible to any check we can ship.

**That gap is real and it is Tier 4.** The honest mitigation is that the list is now one list, in one
place, and short enough to compare by eye against the settings page.
