---
record_type: review
id: integration-run-queue-1021-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-22
---
# Security Review — integration/run-queue-1021 (PR #394), the stack's delta review

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`), light mode, run queue-1021. This is `/pre-merge` §1a's one delta review of the whole stack. `make review-need` routed it to `security` for four reasons: gate and control code changed, the sensitive path `scripts/deploy_hosted_engine.sh`, new parsers and fetches of untrusted input (csv, json, zipfile), and a policy edit to the brief's `Deploy commands:`.
**Independent:** yes. I wrote none of this range's code, tests or records.
**Date:** 2026-10-22
**Release range:** `3eb4189a6ac04474b15a7743781367f63f5e0a0b..fc02b04cf6f62f27002eab304a045302b26ba865`, from the merge-base with `origin/main` to the integration head: 56 commits and 105 files. The stack, in merge order:
- #388 (#387)
- #395 (#389)
- #397 (#391)
- #398 (#371)
- #399 (#378)
- #402 (#379)

**Reviewed head:** fc02b04cf6f62f27002eab304a045302b26ba865
**Risk tier:** MEDIUM. The range holds deploy and gate code beside a deploy credential, and new parsers of fetched input. The brief declares no HIGH paths (`docs/project-brief.md:110`), and no auth, PII, payment or migration path is touched, so no senior review is triggered.

I reviewed in a detached worktree at `fc02b04` under `$TMPDIR`, with its own venv (`make install` from the locks).
- **The stacked PRs' own verdicts stand and were not re-run:** `docs/reviews/fix-issue-387-security.md` and `docs/reviews/fix-issue-389-security.md`.
- **Tests:** these ten files gave 460 passed: `test_osworld`, `test_livebench`, `test_metr`, `test_simplebench`, `test_media_surfaces`, `test_arena_media_boards`, `test_nightly_hosted`, `test_deploy_hosted`, `test_client_decl_gate` and `test_sources`.
- **Mutants:** five on `src/app/clients/osworld.py`, each restored byte-identically (sha256 checked). `git status` was clean afterwards.
- **Probes:**
  - crafted workbooks, CSV, JSON and YAML fed to the new parsers;
  - a fake optional source handed to `build._ingest_sources`;
  - `deploy_gate.deploy_in` on another clone's script path;
  - a Swift probe file compiled beside a copy of the gate's fixture, which `client_decl_gate.dump_ast` read.
- **Network:** nothing contacted Fly.io or GitHub, no workflow ran, and nothing was fetched from the boards' hosts.

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MINOR 4 · risks queued 3. Nothing in the combination is exploitable as shipped.
- Two of the MINORs are robustness defects in the new parsers, and an upstream host can trigger both: M1 is an amplification past the workbook caps, and M2 is an exception class that aborts the whole night.
- One is a security refusal with no test that can fail (M3).
- One is the path form of the redirect that #391 closed only in its environment-variable form (M4).

**What the combination does not break:**
- **#391 against #387 and #389's workflow and stamp.**
  - `scripts/nightly_hosted.sh` derives `REPO` from its own path (`:24`) and calls `scripts/deploy_hosted_engine.sh` by a relative path after `cd "$REPO"` (`:33`, `:45`, `:87`), so the night's internal `deploy_gate.py --check` (`:77`) judges the tree that ships.
  - #389's M1 fix holds after #391. `HEAD_SHORT` is cut to 7 at `scripts/deploy_hosted_engine.sh:67` and used at `:85` and `:147`, and `tests/unit/test_nightly_hosted.py:219` holds it with `core.abbrev 12`.
  - Since #389's reviewed head (`93d9ee2`), the only deploy-path change is that script's `REPO` and `HEAD_SHORT` lines and #389's M2 header wording (`:26-28`). `scripts/ci/nightly-hosted.yml`, `scripts/nightly_hosted.sh`, `Dockerfile`, `.dockerignore` and `fly.toml` are unchanged since then.
- **#378 and #379 together in sources, the registry, `/v1` and the router.**
  - Every new score reaches SQL through parameters: `_store_scores` uses `executemany`. The quality-only source lists reach SQL as `json_each(?)` of a list derived from code (`src/app/workflows/registry.py:997-1001`, `src/app/workflows/standings.py:52-55`).
  - Media names become ids only through `[a-z0-9][a-z0-9.+\-]*` (`registry.py:672`), and become displays only through `_DISPLAY` (`registry.py:695`), so no fetched text reaches a display outside that charset.
  - The text pass runs before `_reconcile_media` (`registry.py:1121`), and the media pass only `INSERT OR IGNORE`s, so a media name cannot take over a text model's display.
  - Nothing fetched reaches a shell, a filesystem path or `eval`. SimpleBench's JS file is matched by three regexes and never run (`src/app/clients/simplebench.py:29-33`), and none of those regexes backtracks badly: a 100,000-brace probe returned at once.
- **The `/v1` changes stay read-only and leak nothing.**
  - `priced` (`src/app/adapter/main.py:1515`) is a boolean that the code declares.
  - `unpriced_models` (`standings.py:141-172`) carries id, display, vendor and accessibility, the same public fields `models` carries, minus the price.
  - The `unknown_task` error no longer reflects the surface list, so the reflected body stays bounded (`main.py:1640-1642`).
  - D-218 clause 1 is the ADR for the nullable price fields.
  - No route, method or write was added.
- **The new HTTP clients.**
  - Each client pins one host: `osworld-v1.xlang.ai`, `metr.org`, `livebench.ai`, `simple-bench.com`.
  - Each fetches through the existing `fetch_bounded(_bytes)`, which refuses any hop that is not `https` to an allowed host and caps redirects at 5, the body at 32 MB and the cycle's deadline (`src/app/clients/protocols.py:105-185`, unchanged in the range).
  - OSWorld's old host, which redirects over plain HTTP, is never asked. A mutant adding it to `hosts` fails `tests/unit/test_osworld.py:154`.
  - METR's YAML goes through `safe_load_bounded`, which caps the size at 1 MB and bounds alias expansion; its `YamlGuardError` is a `yaml.YAMLError`, so `parse_metr` catches it.
  - Every new source is `required=False` (`src/app/workflows/sources.py:286-346`).
- **The OSWorld workbook reader.**
  - Its member reads are by fixed name only: `xl/sharedStrings.xml` and the first `xl/worksheets/sheet\d+.xml`. Nothing is extracted to disk, so member paths cannot traverse; a probe with `../../xl/...` and `/etc/x` members got "holds no sheet".
  - A `<!DOCTYPE>` or an entity is refused: a probe with an internal entity and one with an external `SYSTEM` id each got `SourceError` (but see M3).
  - A member past `MAX_MEMBER_BYTES` is refused before it is read. A mutant removing that check fails `tests/unit/test_osworld.py:125`.
  - A member that lies about its size is truncated by `zipfile` at the declared size and fails its CRC check (see M2 for how that failure surfaces).
- **The brief's `Deploy commands:` edit** (`docs/project-brief.md:107`) adds `scripts/nightly_hosted.sh` and `gh workflow run nightly-hosted.yml`. It only widens what the gate judges, so it fails closed.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `src/app/clients/osworld.py:151-173` with `:64`: the shared-string table amplifies past every cap. Each cell `t="s"` copies a reference to one shared string, and `fetch_raw` then `json.dumps` every copy. `MAX_MEMBER_BYTES` bounds each member's size, not the output.
  - **Probe.** A 2,186-byte workbook gave `json.dumps` 0.3 GB. It held one 1 MB shared string and 300 cells referencing it, about 137,000 times the download. At the caps, a 16 MB sheet holds about 500,000 such cells and a 16 MB shared string, so the output reaches terabytes from a download of a few hundred KB.
  - **Who can trigger it.** The upstream host, or anyone who controls it.
  - **The effect.** The refresh process exhausts memory. On the owner's Mac that is the engine's refresh child (`src/app/adapter/nightly.py:227-292`), which has no rlimit, so the whole machine comes under memory pressure until the kernel kills the child. On the runner the night fails and nothing deploys.
  - **Why it is minor.** Serving and the data's integrity are untouched, and the failure is closed.
  - **Remedy.** Bound what the reader produces, not only what it reads. Either cap the total characters of the resolved cell values (for example at `MAX_RESPONSE_BYTES`) and the number of cells, raising `SourceError` past either cap, or check `len()` of the JSON before returning it. Add a test with the probe's shape.
- **M2** `src/app/workflows/build.py:669`: only `SourceError` and `BuildError` are caught, and the new parsers let other exception classes out. So an OPTIONAL source's bad file aborts the whole night's build, every other source included. That breaks D-121's "an optional source that fails does not stop the build".
  - **Probed:**
    - `parse_livebench` gives `_csv.Error: field larger than field limit (131072)` (`src/app/clients/livebench.py:95-103`).
    - `LiveBenchClient.fetch_raw`'s `json.loads` (`livebench.py:51`) gives `RecursionError` on deep JSON.
    - `workbook_rows` gives `zipfile.BadZipFile: Bad CRC-32` on a lying size (`osworld.py:131`; only the `ZipFile()` constructor's `BadZipFile` is caught, at `:142`).
    - `workbook_rows` also gives `RecursionError` on deeply nested XML, from `_Node.iter` (`osworld.py:76-80`).
    - `parse_metr` gives `RecursionError` on deeply nested YAML (`yaml.compose` in `src/app/workflows/yaml_guard.py:122`).
  - **Through the build.** I handed `build._ingest_sources` a fake LiveBench source (`required=False`) carrying the oversized field, followed by a SimpleBench source. It printed `build aborted: Error field larger than field limit | next optional source reached: False`.
  - **Precedent.** The project has already ruled that this class is a bad input, not a builder bug (`src/app/clients/epoch_board.py:147-156`, `deepswe.py:50`), and the top-level handler deliberately refuses to widen its catch (`build.py:956-964`).
  - **Remedy.** Turn these exceptions into `SourceError` at each new parser and in `LiveBenchClient.fetch_raw`:
    - `csv.Error` in `parse_livebench`;
    - `zipfile.BadZipFile`, `NotImplementedError` and `RuntimeError` (an unsupported compression or an encrypted member) around `archive.read`;
    - `RecursionError` around `json.loads` and around the `_Node` walk (or make `iter` iterative).

    Add one test per class asserting `SourceError`. The METR depth case is the shared YAML guard's, and pre-existing for Aider too. Either fix it there or record it.
- **M3** `src/app/clients/osworld.py:111-112`, the DTD and entity refusal, has no test that can fail. Deleting both `StartDoctypeDeclHandler = _refuse` and `EntityDeclHandler = _refuse` leaves `tests/unit/test_osworld.py` at 24 passed.
  - **Why the test cannot fail.** Its DTD case (`:113`) is a `<worksheet/>` in no namespace, which fails as "holds no rows" either way.
  - **What the mutant does.** A probe applied it to a namespaced sheet whose cell is `&a;`, with `<!ENTITY a "Injected">`. As shipped, that sheet gets `SourceError: ... declares a document type or an entity`. Under the mutant it returns `[{'Model': 'Injected'}]`.
  - **The residual.** It is small: CPython's expat limits entity amplification and fetches no external entity without a handler. But the module's docstring claims this property (`:14-16`), and it is the reader's only XML hardening. This is the class "a fault that stays green with no test".
  - **Remedy.** Use a namespaced sheet that would otherwise parse, and assert the refusal's own words, once for a `<!DOCTYPE>` alone and once for an entity declaration.
- **M4** `scripts/deploy_hosted_engine.sh:36,51` with `scripts/deploy_gate.py:328`: the deploy still ships whichever checkout the script's PATH names, while the gate judges the call's directory. #391 removed the `MODEL_RANKING_REPO` form of the #387 review's R1 but not this form.
  - **Matched by basename.** The gate matches a declared command's program by its basename. So `deploy_gate.deploy_in([["/tmp/elsewhere/scripts/deploy_hosted_engine.sh"]], <judged tree>)` answers `scripts/deploy_hosted_engine.sh`, which the guard judges in the CALL's tree (`.claude/hooks/bash_guard.py:3250-3276`, from the cwd).
  - **The other checkout ships.** The script then `cd`s to its own checkout (`:36`, `:51`) and builds and deploys that one.
  - **#391's own test shows it.** `_deploy` (`tests/unit/test_deploy_hosted.py:69-72`) runs the scratch clone's copy with no `cwd=`, so from the project's own tree, and the test asserts that the scratch checkout shipped (`:83`).
  - **The exposure.** A clean checkout at a reviewed head can stand as the call's directory while a clone at a newer, unreviewed `main` tip ships.
  - **Not affected.** `scripts/nightly_hosted.sh` runs its own `deploy_gate.py --check` in its own tree (`:77`), and CI calls everything by relative path.
  - **Why it is minor.** It needs a deliberate call by path, and D-185 clause 5 bars an agent from deploying at all.
  - **Remedy.** Before its `cd`, the script refuses unless the caller's tree is its own checkout: `[ "$(git rev-parse --show-toplevel 2>/dev/null)" = "$REPO" ]`, both sides resolved with `pwd -P`. Add a test that runs the scratch copy with `cwd=` another clone and expects no `fly` call.

## Gates passed
- [x] Secret scan green: `make secrets` on `fc02b04` (the coordinator's `make gate` PASS line: check conformance falsify secrets deps slopsquat). The new fixtures are the publishers' own public files. The OSWorld workbook's `docProps` carries only the publisher's tool name and a pseudonym, and no credential.
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found` (the coordinator's line).
- [x] `make slopsquat` green (the coordinator's line). No new third-party import: the workbook reader uses `zipfile` and `xml.parsers.expat` from the standard library, and METR's `yaml` is already declared.
- [x] Default-deny preserved for new external surfaces. `/v1` adds one read-only field and one read-only list, and no route. Each new client pins its host, accepts `https` only and bounds its size and time.
- [x] Permission-matrix not violated. There is no `.github/`, `.claude/` or `.githooks/` edit; the workflow is the proposal under `scripts/ci/`. There is no destructive operation in the range.
- [x] Prompt-injection hygiene. Fetched text is data: it never reaches an LLM prompt, a shell, `eval`, a path or unparameterised SQL. Router changes act on the user's own question on the device.
- [ ] Auth/PII checks + human review trigger: n/a (not HIGH; no auth, PII, payment or migration path).
- [x] SAST: conformance green in the coordinator's `make gate`. Bandit and shellcheck were not run here. The deploy shell adds no unquoted expansion.

## Acceptance criteria evidence
- #391 "the deploy ships its own checkout whatever `MODEL_RANKING_REPO` names" → `tests/unit/test_deploy_hosted.py:75-84`. M4 is the path form it does not cover.
- #389 M1 "the jobs name the commit alike" → `tests/unit/test_nightly_hosted.py:219-227`, at `scripts/deploy_hosted_engine.sh:67,85,147`.
- #371 "a served number into a numeric generic is refused" → `tests/unit/test_client_decl_gate.py:1485-1500`, seven twins, with `FIXTURE_REFUSALS` at `scripts/client_decl_gate.py:794`.
- #371 "a served number met inside a closure that counts or searches is refused" → `tests/unit/test_client_decl_gate.py:1517-1532`, seventeen twins.
- #371 "the admitted list fails closed" → `tests/unit/test_client_decl_gate.py:1543-1571` (a place with one more meeting is refused, and an unseen entry fails the gate). Also `:551` and `:581`: the new table, emptied, is caught as stale permissions.
- OSWorld member cap → `tests/unit/test_osworld.py:125` (a mutant removing the cap fails it).
- OSWorld host pinned → `tests/unit/test_osworld.py:154` (a mutant adding the old host fails it).
- OSWorld DTD and entity refusal → no failing test (M3).
- Every new board is optional → `tests/unit/test_osworld.py:171` and the matching tests in `test_livebench.py`, `test_metr.py` and `test_simplebench.py`. M2 shows the property does not hold for every bad input.

## Risks queued
- **R1** `scripts/client_decl_gate.py:2405` (`COUNTS_OR_SEARCHES`): D-218 clause 4 refuses only the methods it names, so a served number can still be rebuilt by methods it does not. My probe compiled these beside the fixture:
  - `(1...100).map { $0 <= s.position ? 1 : 0 }.reduce(0, +)` passes;
  - `(1...100).compactMap { $0 <= s.position ? $0 : nil }.count` passes;
  - `.split { $0 == s.position }` passes;
  - `.lazy.filter { ... }` is refused.

  G-2 (`docs/security-invariants.md`) already says forms outside the ruling are not held, but it does not list `map`/`compactMap` followed by `reduce` or `.count`, which are as short as the refused shapes. Either add them to G-2's examples, or ask the owner to widen clause 4.

  Separately, #371's refusals are not in the D-214 pin (`tests/unit/data/client_decl_refusals_before_242.txt`, unchanged). The self-test needs only one refusal per phrase per file, so a later loosening of a single #371 shape is held only by the pytest twins on the snapshot.
- **R2** `src/app/workflows/registry.py:1004-1050`: a media board's name whose derived id equals a priced text model's id links to that model. `board_standings` then lists it under `models`, with that model's per-token price (`standings.py:145-156`), beside its image or video standing, against clause 1's "no price". This is not a security issue. I did not measure whether today's boards produce such a collision. A test that no quality-only board's model carries a price, or that they are kept apart, would settle it.
- **R3** The #387 review's R5 still stands. Nothing on the runner is verified until the owner applies `scripts/ci/nightly-hosted.yml`, and that includes the four new hosts answering an anonymous runner. #390 (the guard's other spellings of a dispatch) and #392 remain open owner bundles.
