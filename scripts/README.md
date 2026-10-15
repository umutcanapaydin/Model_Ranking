# scripts/

LLM-free, deterministic and fast (seed C.7). Run them through `make` — `make help` lists every
target — rather than by hand.

| Script | Run by | Purpose |
|---|---|---|
| `bootstrap-check.sh` | `make bootstrap-check` | the Stage-0 gate: placeholders (named exceptions in `.placeholder-allow`, `<path>: <text> -- <reason>`; a stale or unreasoned entry fails), `/health`, core docs, universal ADRs, brief, security baseline, something gating a push (it reports `core.hooksPath`, not what the hook runs); CI still starting a step (C12, a `[warn]` at most) |
| `check_fast.py` | `make check-fast` (the post-edit hook) | the legs of `make check`, read from its `check:` line, run side by side; `--plan` prints them. A project's own legs and forms: `CHECK_FAST_OWN_LEGS`, `CHECK_FAST_FORMS` in `stack.mk` (`make check-fast-config` prints both) |
| `ci_liveness.py` | `make ci-liveness`, `/start-session`, bootstrap-check C12 | ADVISORY, never a gate leg: whether the latest CI runs started any step (a billing or runner limit stops every job before its first); one line, always exit 0 |
| `secrets_scan.py` | `make secrets`, a leg of `make gate` | gitleaks over the files git tracks, as they stand in the working tree, every match redacted; outside a git work tree the whole tree |
| `session_check.py` | `make session-check`, a leg of `make check`; `/start-session` | inside Claude Code only: refuses a session whose SessionStart marker is missing -- started outside the repository root (no guard, profile, skill or hook loaded), or the session that installed the hook (start a new one after the merge; no skip row) -- a clone with no pre-push hook, and a directory git cannot read (fail closed). Its PASS line says what it checked: the marker and `core.hooksPath` |
| `brief_fields.py` | `make mode`; `review_need.py`, `deploy_gate.py` | reads the owner's setup answers a script acts on from `docs/project-brief.md`: working mode (unset: heavy), deploy commands, HIGH paths, QA verification |
| `review_need.py` | `make review-need`; `/close-wave`, `/fix-issue`, `wave_check.py` | which review a range needs, computed from the diff and the working mode: a Code-Reviewer above 130 product lines or on gate code (never in light mode -- the first reason line says why); security on declared HIGH paths, sensitive path names or a new parser of untrusted input, where test-only files are not a signal on their own. A stacked branch passes its own base: `make review-need RANGE=$(git merge-base <lower-branch> HEAD)..HEAD` |
| `check_records.py` | `make check-records`, `make install-check` | the governance-record validator and the install-completeness check; from `v7.1` also `V1` (the brief's `process_version:` against `.gp/installed`; no marker, not graded, and it says so) and `S1` (no `S<n>` session number used twice in `docs/process-log.md`) |
| `runner_verdict.sh` | sourced by `runner` | this project's: how a leg is recorded, skipped, and what the run is allowed to claim. Separate from `runner` so it can be tested without running `make check` (REQ-FIX-004) |
| `wave_check.py` | `make wave-check`, `make closes` | refuses a wave close that is not a filled checklist with the review verdicts its change needs, each declaring `**Independent:** yes`; counts `docs/control-events.csv` by the legend in `docs/warnings.ledger.template.md` -- a `review` row citing an ADR or a refusal restarts a control's three-skips count, a row of any other spelling, or a free-form wave, is a finding |
| `run_check.py` | `make run-check`, `make closes`; `/plan-run`, `/close-wave`, `/start-session` | refuses a run record (`docs/plans/run-<name>.md`, from `docs/run.template.md`) that is hollow or inconsistent: a mode, status or stop class outside its vocabulary, a ruling `docs/decisions.md` does not hold, a stacked wave with no close record, a closed milestone with a wave not stacked, a stopped wave with no stop row, an ended run with a wave still running |
| `closure_check.py` | `make closure-check`, `make closes` | refuses a milestone closure report that is not filled (Quality Gate on); from `v7.1` one with no milestone Tester verdict beside it, in both modes -- heavy `docs/reviews/m{N}-tester.md`, light `docs/reviews/release-tester.md` current by its `**Reviewed head:**` (the deploy gate's rule). `--release-records` (a leg of `make closes`, both modes, no report needed): once `docs/reviews/release-security.md` exists, the Tester verdict for that release must exist beside it -- the one leg that reaches a light project's release |
| `deploy_gate.py` | the Bash guard (`.claude/hooks/bash_guard.py`, `--judge`); `make deploy-check` (`--check`) | refuses a command the brief lists as a deploy unless the security verdict and the milestone Tester's verdict are current for the checkout the command runs in: `docs/reviews/release-security.md`, and `docs/reviews/release-tester.md` (light mode) or the latest `docs/reviews/m<N>-tester.md` (heavy), each naming a `**Reviewed head:**` with no code changed since it in the working tree (the Tester's declaring `**Independent:** yes` too). `make deploy-check` asks the same with no command, one line per verdict, for the deploys the guard never sees |
| `coverage_floor.py` | CI `test` job | the skip budget: a run that skipped more tests than accepted is not green |
| `slopsquat_check.py` | `make slopsquat` | seed F.8: declared dependencies exist on PyPI and are not brand new |
| `write_install_marker.py` | `make install` | writes `.gp/installed`: the version this tree installed, derived from the records |
| `create_labels.py` | `make labels` | creates the missing issue labels on the GitHub remote, once per repository |
| `shell_dialect_check.sh` | `make shell-dialect` | every shipped `.sh` parses and declares one dialect |
| `pin-actions.sh` | by hand, when a workflow action changes | pins every workflow `uses:` to a commit SHA |
| `gen_schema.py` | by hand, when the validator's record types change | regenerates `schemas/record.schema.json` |
| `standup.sh` | `make standup` | where are we: latest process-log entry, open ADRs, plans, reviews, git state |

A project adds its own scripts here under the same rule: no model calls, runnable in seconds, and
reached through a `make` target.

**The Bash guard** lives beside the hooks, in `.claude/hooks/bash_guard.py`, and `.claude/settings.json`
pins its sha256 (`make guard-pin` rewrites the pin; `.claude/hooks/guard_pin.py --check` reads it). It
reads every Bash tool call as the shell splits it — quoted text and here-document bodies are data,
rules look only at the words in command position — and hands the words in program position to
`deploy_gate.py --judge` in the repository it resolved from the call's own directory. A brief that
declares deploy commands with no `deploy_gate.py` beside it refuses every call; the guard never skips
the check. Everything under `.claude/`, `.githooks/`, `scripts/`, `conformance/`, `.github/` and the
`Makefile` is code to the gate whatever its extension; `docs/` and other Markdown are records.

**This project's own** (the engine service, D-170 and D-171). Each changes the owner's machine, so
the owner runs it, or the agent on his standing instruction:

| Script | Run by | Purpose |
|---|---|---|
| `install_engine_service.sh` | the owner, after each merge | deploys `origin/main` as a release and (re)starts the launchd service `com.ilgar.modelranking.engine`; `--lan` opens it to the home network, `--no-lan` closes it, and a reinstall keeps the mode it finds |
| `remove_engine_service.sh` | the owner | takes the service off, so it does not start again at login |
| `engine_service.sh` | launchd, through the installed wrapper; `ios/app.sh` | the launcher: refuses a development checkout as a service, checks the artifact and the startup config, then runs uvicorn on its one `--host`. The engine's nightly refresh (D-154) runs inside it |
| `simulator_session.sh` | by hand | REQ-RUN-001's first one-command session: engine, build, simulator, until Ctrl-C. Nothing calls it; `ios/app.sh` is the path the owner's steps use |

The nightly refresh runs inside the engine service (D-154, D-170); this repository installs no other
refresher (D-173 clause 7).
