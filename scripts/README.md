# scripts/

LLM-free, deterministic and fast (seed C.7). Run them through `make` — `make help` lists every
target — rather than by hand.

| Script | Run by | Purpose |
|---|---|---|
| `bootstrap-check.sh` | `make bootstrap-check` | the Stage-0 gate: placeholders, `/health`, core docs, universal ADRs, brief, security baseline, something gating a push; CI still starting a step (C12, a `[warn]` at most) |
| `check_fast.py` | `make check-fast` (the post-edit hook) | the legs of `make check`, read from its `check:` line, run side by side; `--plan` prints them. A project's own legs and forms: `CHECK_FAST_OWN_LEGS`, `CHECK_FAST_FORMS` in `stack.mk` (`make check-fast-config` prints both) |
| `ci_liveness.py` | `make ci-liveness`, `/start-session`, bootstrap-check C12 | ADVISORY, never a gate leg: whether the latest CI runs started any step (a billing or runner limit stops every job before its first); one line, always exit 0 |
| `check_records.py` | `make check-records`, `make install-check` | the governance-record validator and the install-completeness check |
| `runner_verdict.sh` | sourced by `runner` | this project's: how a leg is recorded, skipped, and what the run is allowed to claim. Separate from `runner` so it can be tested without running `make check` (REQ-FIX-004) |
| `wave_check.py` | `make wave-check`, `make closes` | refuses a wave close that is not a filled checklist with both review verdicts, each declaring `**Independent:** yes` |
| `closure_check.py` | `make closure-check`, `make closes` | refuses a milestone closure report that is not filled (Quality Gate on) |
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
