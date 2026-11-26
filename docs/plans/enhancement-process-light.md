# Enhancement plan: a lighter process — reviews for user-facing code only, LOW findings in one file, short reports (#639)

**Golden Rules served:** 4 (no empty work): reviews, ADRs and issues that guard nothing a user sees are cut, so the
work goes to rules 1-3 and the v1 order (D-210). The owner's ruling of 2026-11-26, recorded as D-257.

## Goal

A review, a deploy delta, an ADR or an issue is owed only where it has caught, or can catch, a defect a user would
see. Each control the owner kept stays as it is.

## Scope

**In:** the deploy gate's change classes (`scripts/deploy_gate.py`), the brief's `Security-invariant tests:` line,
a `later` disposition in the findings grammar (`scripts/pr_check.py`, `scripts/wave_check.py`), the new later file (docs, phase 4),
the rule text in `AGENTS.md`, `.agents/rules/issues.md` and `.agents/rules/practices.md`, D-257 and its watch-list
rows.

**Out (untouched by the owner's ruling):** no direct push to main, and the PR plus merge-commit flow; the
`.github/workflows` and `.claude/` write ban, the permission matrix and the Bash guard; red-first tests for
user-facing code; the deploy gate itself and the secret-scan and dep-audit checks; the record of licence and
data-source decisions. The skill and agent texts under `.claude/` are the owner's: they follow as one bundle after
this PR merges.

## Decisions (resolved with the owner, 2026-11-26)

1. Tests do not re-open a deploy verdict, except the tests `docs/security-invariants.md` cites, which stay code.
   The list is derived from the register, never hand-kept, and an empty derivation fails closed (every test code).
   The register itself is code.
2. `src/` stays code as a whole: it all ships in the image (`Dockerfile`), and splitting it would be a hand-kept list.
3. A finding a user can see is at least MEDIUM; a LOW finding is a row in the new later file (docs, phase 4), not an issue.
4. D-257 carries a review clause: when 1.2 ships, report the reviews per PR and any defect that escaped.

## Phases

1. **D-257.** The ADR alone, before any code it governs.
   *Acceptance:* `make check-records` green.
2. **Deploy gate: tests and allow-lists are not code.** A red test first, then `change_class` and
   `policy_invariant_tests` read a register named on the brief's line; `.language-allow` and `.skill-refs-allow` are
   records; the brief names `docs/security-invariants.md`.
   *Acceptance:* the new tests green, every existing deploy-gate test and `conformance/test-deploy-classes.py`
   unchanged and green.
3. **`later` disposition.** A red test first, then `pr_check.py` and `wave_check.py` accept `later` for a row
   that the new later file (docs, phase 4) holds.
   *Acceptance:* the new tests green; `make findings-check` refuses `later` for an id the file does not hold.
4. **Rule text.** `AGENTS.md`, `.agents/rules/issues.md`, `.agents/rules/practices.md`, the new later file (docs, phase 4) with the
   open LOW issues (#619, #622, #629, #631), and the watch-list rows.
   *Acceptance:* `make check` green; the AGENTS.md cap holds.
5. **Reviews under the old rules.** The Security-Reviewer (a policy edit) and the Tester delta.
