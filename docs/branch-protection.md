---
record_type: design
id: branch-protection
status: ratified
process_version: v6.4
date: 2026-09-23
---
# Required status checks — the one list

This file is the single list of the checks a project's default branch requires. Anything naming
required checks elsewhere points here. Two failure modes it exists for: three documents once named
required checks and no two agreed, so a PR could fail the install and governance gates and still
merge; and one of them required a check named `lint`, which is a step inside `test`, not a job —
**a required check by a name that never reports blocks nothing while looking like protection.**

## Protect the default branch

Require these **job names** — not step names, not workflow names:

| required check | workflow | what it means if you drop it |
|---|---|---|
| `test` | `ci.yml` | lint, typecheck and the test suite. Lint and typecheck are STEPS inside this job; do not list them separately |
| `secret-scan` | `ci.yml` | gitleaks. Dropping it means a credential can reach the default branch through a green PR |
| `dep-audit` | `ci.yml` | `pip-audit --strict .` against the project's declared dependencies |
| **`install-and-governance`** | `ci.yml` | install completeness (`M0`–`M4`), the governance records, the validator's not-a-no-op proof, and the conformance suite |

Also enable: **require a pull request with at least one human approval**, **require branches to be up
to date before merging** (otherwise a check can pass against a stale base), and **include
administrators** — a rule the owner can wave through is a rule that will be waved through under
deadline.

**Where GitHub Actions do not run** (a private repository on a free plan may have no minutes), the
required checks never report. Protection still blocks direct pushes and unreviewed merges; the checks
themselves run on each developer's machine through the pre-push gate (`make hooks` → `make gate`).
Record that in `docs/project-brief.md` (§2, question 7): `make bootstrap-check` reads it, and
unless both answers are yes, a clone without `make hooks` fails Stage 0.

## What this file does not do

It cannot enforce itself. Branch protection is configured in GitHub's UI or API and lives outside every
tree, so `conformance/test-ci-yaml.py` asserts only that **every job named here exists in a workflow**
and that **every job in `ci.yml` is named here.** Drift between this list and the repository's actual
settings is invisible to any shipped check; the honest mitigation is that the list is one list, in
one place, and short enough to compare by eye against the settings page.
