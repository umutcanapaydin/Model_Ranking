---
record_type: review
id: fix-issue-477-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-28
---
# Security Review — fix-issue-477

**Reviewer:** Security-Reviewer subagent (light mode; routed to security because the range edits the policy file `data/accepted-cuts.yaml`, #283)
**Independent:** yes. I wrote none of the red tests, the fix or the process-log entry. M6 and M7 of `c845e94:docs/reviews/release-security.md` are mine, and they became #478 and #479.
**Date:** 2026-10-28
**Release range:** `3d29975..c9d6584` (`2911dda` red tests, `a78eb15` the fix, `c9d6584` the process log; branch `fix/issue-477-respelling-expiry`). `3d29975` merged #481, an iOS-only change, which is out of scope.
**Reviewed head:** c9d65846d5e0adfab5d293e34064f1ba12a5edef
**Risk tier:** MEDIUM. The file holds exceptions to a product safety guard (the night's board-loss guards). The brief declares no HIGH paths (`docs/project-brief.md:110`). Nothing here touches auth, PII, payment or a migration, so no senior-review line is owed.

## Verdict
MINOR

BLOCKING 0 · MINOR 4 · risks queued 2.

All three issues are fixed for the shapes they name, and each fix fails closed. The entry's removal is safe tonight: the hosted engine serves the new ids. The four MINORs are residues of the classes #478 and #479 target:
- a YAML merge key still overrides silently;
- the repeated-key walk is quadratic;
- #479's second clause was not done;
- a model moves when only one of its pairs is a re-spelling.

None of the four can act while the file holds no `respellings` entry.

## Method

- Policy read from the base ref: this profile, `AGENTS.md` and `permission-matrix.md` as the session loaded them. Nothing in the range edits policy.
- I read the range diff of `src`, `tests` and `data`, the M6/M7 text at `c845e94`, and #479.
- I worked in my own worktree at `c9d6584`, with its own venv from the hash-checked locks (`make install`).
- `pytest tests/unit/test_accepted_respellings.py tests/unit/test_accepted_cuts.py`: 100 passed.
- Red→green: I ran the final tests against `2911dda`'s `src` (exported with `git archive`, `-o pythonpath=`). 3 failed: `a-name-the-pairs-do-not-list` and both `test_a_key_written_twice_fails_closed` cases. 39 passed.
- I probed `safe_load_bounded(..., unique_keys=True)`, `_accepted_doc`, the parsers and `_respelled_ids` with hand-built inputs. I timed `_refuse_repeated_keys` alone on composed nodes.
- I fetched `https://model-ranking.fly.dev/v1/boards` (GET, read-only). `arena_text_to_image` has 82 standings, `observed_at 2026-10-28`, `evidence_date 2026-10-26`. 6 ids are `flux.2-*` and none is `flux-2-*`.

## Answers to the dispatcher's questions

**Does the autouse fixture hide a real failure the night would hit?** No, and no committed-policy test now passes vacuously.
- **What the fixture changes.** `tests/conftest.py:313-320` rebinds only the two loaders' default path. The night's own callers use that default (`src/app/workflows/refresh.py:739`, `:1789`), so in-process night tests read an empty policy.
- **Night tests that bring their own policy are unaffected.** They override the fixture's binding with a policy of their own (`tests/unit/test_accepted_respellings.py:161-166`, `tests/unit/test_accepted_cuts.py:169-177`). They still run the real entry with a real file, the malformed-list night included (`test_accepted_respellings.py:202`).
- **The committed file is still read under the real date.** `test_the_committed_file_parses` (`test_accepted_respellings.py:208-211`) reads it through `ACCEPTED_CUTS_FILE`, under the real `today` and the real decision log. So a future entry past its `until:` turns exactly that test red, not the whole suite.
- **Only one test changed its reading.** That is `test_accepted_cuts.py:88`, which moved from the default path to the explicit file, so it still reads the committed file.
- **Import-isolation tests are unaffected.** They run in a fresh interpreter (`tests/unit/test_nightly_refresh.py:486-500`, `tests/unit/test_arena_slices.py:696`), so the fixture's import of `refresh` leaves them alone.
- Residue: R1.

**Is the repeated-key walk sound?** For plain keys, yes; with merge keys, no (M1); its cost is quadratic (M2).
- **Plain keys:** equality is on the composed scalar text after escapes and folding. Refused: a quoted key against a plain one, `"P\x200"` against `"P 0"`, an alias used as a repeated key (`&k foo` / `*k`), and two `<<` keys in one mapping.
- **Aliases:** they compose to shared nodes. The `id()` set visits each node once, so an alias cycle or a fan-out cannot loop.
- **Constructor-equal but text-different scalars** (`yes`/`true`, `~`/`null`, `1`/`0x1`) are not caught. They cannot reach a valid policy: `pairs` must have `str` keys, and the entry and top-level key sets are fixed (`refresh.py:328-329`, `:334`, `:384`).
- **Non-scalar keys** are skipped by the walk. PyYAML then refuses them as unhashable (`ConstructorError`, which `_accepted_doc` turns into `AcceptedCutError`).
- **Bound:** the walk is bounded by the 1 MiB and 500,000-node limits, which run before it (`yaml_guard.py:118`, `:141`).

**Can the #478 condition be bypassed?**
- **The shapes #478 named are closed.** I probed an unlisted old name, a split into two new models, a merge of two old models into one, and an extra unlisted new name. Each returns `{}`.
- **One residue (M4):** the condition is checked per model. A model moves if one of its pairs passes the per-pair re-spelling test. Its sibling pairs need not pass it.

**Does removing the entry risk the next night?** No.
- **The hosted board already serves the new ids.** The night compares against that served artifact. On it the 27 old names are absent, so every pair failed `old in was` (`refresh.py:452`) and the entry was inert.
- **Keeping it would have failed nights.** On 2026-11-10 the entry would have failed every night closed (`refresh.py:369-371`, through `:1789`). Removing it is the fix.
- **A rollback stays closed.** If the hosted artifact were rolled back to a pre-2026-10-26 release, the next night would meet the re-spelling again and refuse it. That is closed, not open (R2).

## Findings

### BLOCKING
- none

### MINOR
- **M1** `src/app/workflows/yaml_guard.py:157-170` (`_refuse_repeated_keys`), used by `src/app/workflows/refresh.py:324`. **A YAML merge key still lets one policy entry silently replace another, the class #479 closes for plain keys.**
  - The walk compares the keys written in one mapping. `<<` merges the keys of another mapping, and an explicit key then overrides a merged one without error. In `<<: [*a, *b]`, the first mapping wins.
  - Probe through `_accepted_doc`, a schema-valid file. Entry 1 (`board: coding`) has `pairs: &p {"Probe 00": "PROBE.00"}`. Entry 2 (`board: assistant`) has `pairs: {<<: *p, "Probe 00": "PROBE.09"}`. It is accepted as `{'Probe 00': 'PROBE.09'}`, and no error names the override.
  - Why MINOR: it needs an anchor and a `<<` in the policy diff, which this seat reads (#283). The overridden value still passes the schema, the ADR and the 30-day cap.
  - Remedy: under `unique_keys`, refuse a key node tagged `tag:yaml.org,2002:merge`. Or refuse aliases altogether in policy mode, since no policy entry needs one. Add the probe as a third `test_a_key_written_twice_fails_closed` case.
- **M2** `src/app/workflows/yaml_guard.py:166-167`. **The walk costs O(n²) in the keys of one mapping (`keys.count(key)` for every key).**
  - I timed the walk alone on flat mappings, on the loaded machine: 5,000 keys took 1.9 s, 10,000 took 8.3 s and 40,000 took 115 s.
  - The 1 MiB and 500,000-node limits allow well over 100,000 keys in one mapping. That is on the order of 10¹⁰ comparisons, which would stall the night inside the guard meant to bound it. The docstring's "the expansion is bounded already" bounds the node count, not this walk.
  - Why MINOR: it needs a committed policy file of that size, and this seat reads every policy edit.
  - Remedy: count with `collections.Counter(keys)` (linear). Optionally add a timing test with about 50,000 keys.
- **M3** `src/app/workflows/refresh.py:338` and `:390`. **#479's second clause was not done: a non-scalar `board:` still raises `TypeError`, not the schema error.**
  - Probe: `board: [text_to_image]` in a re-spelling, and `board: {x: 1}` in a cut. Each raises `TypeError: cannot use 'list'/'dict' as a set element` at `board not in known`.
  - #479's remedy says: "check `isinstance(board, str)` before the `known` lookup". The commit names #479 as fixed.
  - Why MINOR: the night still fails closed (`main` records `crashed: TypeError` and exits `EXIT_FAILED`). Only the message is wrong.
  - Remedy: add the `isinstance(board, str)` check in both checkers, with one test per checker. Or say in the PR that #479 stays open for this clause, so the merge does not close it.
- **M4** `src/app/workflows/refresh.py:450-455` (`_respelled_ids`). **A model moves when one of its pairs is a re-spelling, even if its sibling pairs are not.**
  - The new conditions require every old name of the model to be listed (`:454`), and the new model's names to be exactly the mapped names (`:455`). The per-pair re-spelling tests at `:452-453` apply only to the pair being iterated.
  - Probe 1: served `A{a1, a2}` and `X{b2, x}`; candidate `B{b1, b2}` and `X{x}`; pairs `a1→b1`, `a2→b2`. The result is `{'B': 'A'}`. The pair `a2→b2` is itself the `the-new-name-was-served` shape (`tests/unit/test_accepted_respellings.py:258`), which on its own changes nothing. Yet row `b2`, served under `X`, now reads as `A`'s.
  - Probe 2: the same, with `a2` still served in the candidate under `X`. It also moves.
  - Effect: the board's total loss stays visible, but it is charged to `X`, and `a2`'s own loss is masked.
  - Why MINOR: it needs an owner-listed pair of that shape, the file now holds no `respellings`, and the guards still see a loss.
  - Remedy: accept `(n, o)` only when every pair over `before[o]` passes the per-pair conditions. Add the two probes as `_NOT_A_RE_SPELLING` shapes.

### PASS
- **#477:** the entry is removed, and the file keeps a dated retirement note naming the commit where the entry lives (`747b63c`). `load_accepted_respellings(ACCEPTED_CUTS_FILE) == {}` is held by a test.
- **#478:** the remedy M6 asked for is implemented as written (`refresh.py:454-455`). The red shape fails before the fix and passes after. The control (`test_a_model_with_two_names_moves_when_the_pairs_list_both`) proves the condition does not refuse the legitimate two-name move.
- **#479:** the check is opt-in, and only the policy loader passes it (`refresh.py:324`), so other curated inputs are unchanged. It runs on the composed node, after the size and expansion bounds. It raises `YamlGuardError`, a `yaml.YAMLError` (`yaml_guard.py:44`), which `_accepted_doc` already turns into `AcceptedCutError`, so the refusal is closed and nothing new can escape.
- **Fail direction:** if the fixture's rebinding ever leaked into production, it would be fail-closed. The loaders' missing-file branch accepts nothing (`refresh.py:405-406`, `:516-517`).
- No secret, no new import, no new dependency, no endpoint, no logging, no destructive operation in the range.

## Gates passed
- [x] Secret scan green (`make secrets` at `c9d6584` in this worktree: gitleaks "no leaks found")
- [x] `make deps` (pip-audit): not run. The range changes neither `pyproject.toml` nor any lock under `requirements/`.
- [x] `make slopsquat`: not applicable. The range adds no import; `yaml` was already imported in both files.
- [x] Default-deny preserved for new external surfaces: none is added.
- [x] Permission-matrix not violated
- [x] Prompt-injection hygiene: not applicable. The range consumes no external text; the policy file is committed and reviewed.
- [x] Auth/PII checks: not applicable. There are no HIGH paths (`docs/project-brief.md:110`).
- [ ] SAST: `bandit` is not in the dev lock, and the Makefile has no SAST target. I read the changed code by hand: `yaml.compose`/`yaml.safe_load` only, no `eval`, no subprocess.

## Acceptance criteria evidence
- **#477 (1)**, the D-228 entry is removed:
  - change: `data/accepted-cuts.yaml:13-19`
  - test: `tests/unit/test_accepted_respellings.py:325-328`
- **#477 (2)**, the suite reads no committed policy by default:
  - change: `tests/conftest.py:313-320`
  - test: `tests/unit/test_accepted_respellings.py:331-337`
  - the committed file is still read under the real date: `tests/unit/test_accepted_respellings.py:208-211`
- **#478**, a pair names rows, not models:
  - change: `src/app/workflows/refresh.py:454-455`
  - tests: `tests/unit/test_accepted_respellings.py:263-267` (red shape), `:298-310` (control)
- **#479**, a key written twice is refused:
  - change: `src/app/workflows/yaml_guard.py:148-149`, `:157-170`, `src/app/workflows/refresh.py:324`
  - test: `tests/unit/test_accepted_respellings.py:313-323`
  - not yet done: the clause on a non-scalar `board:` (M3)

## Risks queued
- **R1** `tests/conftest.py:313-320`. The fixture rebinds the defaults in-process only.
  - A child-process refresh in a test still reads the committed file. Today none reaches the policy loaders: `tests/unit/test_nightly_refresh.py:349` is killed mid-build.
  - With the defaults rebound suite-wide, no test holds that the production default of `load_accepted_cuts`/`load_accepted_respellings` is `ACCEPTED_CUTS_PATH`. A wrong default would fail closed, accepting nothing.
- **R2** `data/accepted-cuts.yaml:17-19`. If the hosted artifact is rolled back to a release from before 2026-10-26, the next night meets LMArena's re-spelling again and refuses `text_to_image`. That is fail-closed. Restoring the pairs from `747b63c` needs a new entry under D-228's terms, with a fresh `until:`.
