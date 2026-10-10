# Refusals — decisions NOT to build

> **Purpose:** a refusal is a decision, and a decision that is not written down gets re-litigated
> every time the proposal comes back. Each row names what was refused, why, who ruled, and the
> trigger that re-opens it. **A refusal is not "not yet" — it is "no, until the trigger fires."**
> Do not re-open a row from prose: bring the trigger's evidence.

## When a row belongs here

- **A gate you will not wire.** `make smoke-deps`, `make cold-start` and `make journey` fail loudly
  until wired; refusing one is a legal answer, recorded here with the reason.
- **A repository you will not govern.** `docs/project-brief.md` §2.1 lists every repository that
  ships something a customer can reach; one that does not run DevFlow names its row id here, and
  `make bootstrap-check` refuses a `no` without one.
- **A control you retire.** When `make wave-check` reports the same control skipped or bypassed three
  times (`docs/control-events.csv`), fix it, re-scope it, or refuse it here. A retired control also
  gets a row in `docs/watchlist.md`, so it can come back on evidence.
- **A tool, service or practice you decided against**, so the next proposal starts from the reason.

## Format

`R-<n>`, monotonic, never reused. A refusal is reversed by a new row that names the old one, never by
editing it.

| id | Refused | Why (the failure mode or cost that decided it) | Ruled by (name, date) | Re-open trigger |
|---|---|---|---|---|
| R-1 | `make check-fast` in full before every commit: the `commit-after-check-fast` control as first written, which reached its third row at the M20 closure (`docs/control-events.csv`). Re-scoped, not retired. `.githooks/commit-msg` runs `HEAD`'s copy of `scripts/commit_gate.py` on the staged paths (both sides of a rename) and the subject: `make check-fast` for any commit, a merge, and one with nothing staged (a reworded amend); `make check-red` for a declared red test commit (a `test:` subject, read as git records it, that says `red` as a word of its own, with a test staged; it may carry code beside the test), which leaves out the legs that run tests (`test`, `swift-test`, `conformance`, `client-decls`) and builds instead (`swift-build-tests` compiles the Swift package and its tests, `pytest-collect` collects the Python tests), while lint, types and the records must pass; and `make check-docs` for a docs-only commit (every staged path a Markdown file outside the code directories), which leaves out the Swift tests and the compiled gate. Held by `tests/unit/test_commit_gate.py` and `tests/unit/test_check_fast.py`; the hook runs once `make hooks` is run, on `git commit` and `git merge` (git runs no `commit-msg` on `cherry-pick` or `rebase`). | A red test commit fails its own tests by design (the red-to-green rule; `/fix-issue` step 3), so a gate that runs the tests refuses every one, and an agent may not use `--no-verify`. Who checks a red commit's failures: `/fix-issue`'s Tester confirms the red test fails on the pre-fix commit and passes after (`.claude/skills/fix-issue/SKILL.md` step 6); the M21 Tester seats also built each red commit from `git archive` and checked that it fails only on its own tests (row 2 of the M21 closes), a check no role definition requires. A docs-only commit waited about 100 s on the Swift tests and the compiled gate, which read no Markdown; the Python legs do read it (AGENTS.md's cap, INSTALL.md's version, the register, the PRD and the plans' globs), so `check-docs` keeps them. | The owner, 2026-10-10 ("fix and narrow", translated from Turkish). The red-commit scope and `check-docs` are the agent's application of that ruling at the M21 closure (the fixes review's B1 and M2), which the owner may overrule. | A docs-only commit, gated by `make check-docs`, that leaves the Swift tests or the compiled gate red at the next code commit; or a declared red commit whose failures are not all in its own tests |
