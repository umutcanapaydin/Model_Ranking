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
| `wave/`, `reviews/`, `closure/` | `test-make-targets.py` | Wave-close and closure-report fixtures for `scripts/wave_check.py` and `scripts/closure_check.py` |

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

- `wave/m1-wave-2-close.md` is a filled copy of `docs/wave-checklist.template.md` and must pass.
  `wave_check.py` reads its two verdict files from `../reviews/`.
- `wave/m1-wave-3-close.md` is hollow and must fail, and it must fail for the two reasons it declares.
- `closure/closure-report-m7.md` is a filled copy of `docs/closure-report.template.md` and must pass.
- `closure/closure-report-m8.md` is missing §1b and its §6 prose, and must fail.

When a template changes, its filled fixture changes in the same change.

## Not in an installation

The repository that authors this package also keeps a falsification registry, which breaks every
control on purpose and requires it to fire. It proves the controls before a package ships, so it is
not part of an installation. `make falsify` says so when it is absent.
