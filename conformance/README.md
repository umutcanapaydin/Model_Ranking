# Conformance suite

Every control here is proven by the input it must refuse, and by the correct input it must accept.
A control nobody exercises is a control nobody has.

## What runs, and from where

| What | Run by | What it does |
|---|---|---|
| `run-all.py` | `make conformance`, a leg of `make gate` (pre-push, `/pre-merge`); CI's `install-and-governance` job | Runs every `test-*.py` in this directory and checks that every leg of `make gate` has a workflow that runs it |
| `test-*.py` | `run-all.py` | One control each. The suite is derived from the directory: add a file and it runs. Its docstring's first line is its description, and a test with no docstring fails |
| `lib_record.py` | the tests | Shared helpers: record or instruction surface, the delivered documents (`.md` and `.html`), the GP-internal set from `INSTALL-MANIFEST.md`, a git environment that cannot touch the graded repository |
| `pass/`, `fail/` | `scripts/check_records.py --self-test` (`make check-records-selftest`, a leg of `make check`) | Record fixtures for the governance validator |
| `wave/`, `reviews/`, `closure/`, `closure/reviews/` | `test-make-targets.py`, `test-milestone-tester.py`, `test-milestone-security.py`, `test-wave-unversioned.py` | Wave-close and closure-report fixtures for `scripts/wave_check.py` and `scripts/closure_check.py`, with the Tester verdicts they cite |
| `run/` | `test-run-check.py` | Run-record fixtures for `scripts/run_check.py`: one filled, one broken for its declared reasons, and the plan file the filled one names |

`python3 conformance/run-all.py` prints each test with its description. Each test's verdict is its
exit code: 0 PASS · 1 FAIL · 2 NOT-EVALUABLE. NOT-EVALUABLE means the test could not evaluate here
(for example, no git history to attest, or a tool it needs is missing: it then says
`<tool> not installed: cannot <what>`, or `bash not runnable here`). It is printed and does not fail
the suite. Any other exit code is a FAIL.

## Record fixtures

`pass/` holds the smallest records that MUST validate clean. `fail/` holds one fixture per blocking
record rule. Each declares its expected rule on an `<!-- expect: RULE -->` line, and the self-test
fails if the fixture does not produce that rule.

**A fail fixture may only declare a rule that a single record can trigger.** A fixture that declares
an expectation it cannot meet is a false claim inside the test corpus. Rules about a package or a
project tree (the install-manifest rules, the warnings ledger, the language rule, a due condition
checked against a synthetic table) are covered by probes instead: the self-test builds a broken
throwaway tree for each and prints `probe/<rule>` by name, so a probe cannot silently stop running.

Adding a blocking rule to `check_records.py` requires its fail fixture, or its probe, in the same
change.

## Close-record fixtures

Fixtures take milestone numbers no project reaches (`m901`, `m907`...): the checkers' filename rules
forbid a `fixture-` prefix, and a fixture named `m1-wave-2` was found in a project's own records
search and pointed `wave_check.py` at that project's real `docs/plans/m1-plan.md`.
`test-fixture-ids.py` refuses a fixture below `m900`, or one named like a record under `docs/`.

- `wave/m901-wave-2-close.md` is a filled copy of `docs/wave-checklist.template.md` and must pass.
  It declares `v7.0`, the version its rules are meant for (a close is graded by the version it
  declares); `wave_check.py` reads its Code-Reviewer verdict from `../reviews/`, which declares
  `**Independent:** yes`. The Tester verdict beside it is from the per-wave Tester of `v6`,
  which `v7` no longer requires; the checklist's rows still cite it as evidence.
- `wave/m901-wave-3-close.md` is hollow and must fail, and it must fail for the two reasons it declares.
- `wave/m905-wave-1-close.md` declares no `process_version`: history when it predates the
  installation (`.gp/installed`'s `installed_on`) or no marker exists, refused when it is dated on or
  after the installation, or undated beside a marker (`test-wave-unversioned.py`).
- `closure/closure-report-m907.md` is a filled copy of `docs/closure-report.template.md` and must pass
  (it declares `v6.3`, so the rules that came later do not apply to it).
- `closure/closure-report-m908.md` is missing §1b and its §6 prose, and must fail.
- `closure/closure-report-m910.md` is history in the shape of a field project's oldest reports --
  `record_type: ratification`, no `process_version`, none of today's sections -- and must pass:
  a history report is graded by its filename and id only.
- `closure/closure-report-m909.md` declares `v7.1` and must pass: its §1 citations name files this
  package ships, and the milestone Tester's verdict sits beside it in `closure/reviews/m909-tester.md`
  -- from `v7.1` `closure_check.py` requires that verdict in both working modes
  (`test-milestone-tester.py` proves the refusals, in both modes). It stays at `v7.1`: from `v7.1.2`
  heavy mode also asks for the milestone Security-Reviewer's `m{N}-security.md`, and
  `test-milestone-security.py` re-declares the fixture to prove that rule in both polarities.

When a template changes, its filled fixture changes in the same change.

## Not in an installation

The repository that authors this package also keeps a falsification registry, which breaks every
control on purpose and requires it to fire. It proves the controls before a package ships, so it is
not part of an installation. `make falsify` says so when it is absent.
