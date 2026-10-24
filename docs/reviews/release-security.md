---
record_type: review
id: release-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-23
---
# Security Review — deploy delta for release v0.1.0 (Stage 5.1, light mode: #415 / PR #416)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`, read from `main`), Stage 5.1, light mode, dispatched by `/going-live` for the delta before the v0.1.0 hosted deploy
**Independent:** yes. I wrote none of this range's code, tests, records or earlier reviews.
**Date:** 2026-10-23
**Release range:** `660af4b9b46dce2d769101da7ae4f80b6e6d3132..9208fd8d86c2cb0fc7b95011337fad642768a27f` (11 commits). `660af4b` is the reviewed head of the verdict this one extends. The range holds #414's release record (`5d729c7`, `08655e2`, merge `da65e96`), #415's ADR D-220 (`9bdce37`), red tests (`520520c`) and fix (`bf278b0`), merged as `55cf42e` (#416), and the release Tester's two test commits (`91eff48`, `9d3cf0e`) and verdict (`9208fd8`).
**Reviewed head:** 9208fd8d86c2cb0fc7b95011337fad642768a27f
**Risk tier:** MEDIUM. The delta relaxes a data-safety guard (D-164 / INV-54) and changes how untrusted upstream names are read (`registry.py`). The brief declares no HIGH path, and no auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-415` at `9208fd8`, plus a detached worktree at `660af4b` for base comparisons, both under `$TMPDIR`. The permission system refused `make install` in my worktree. So I ran the tests and probes with the main clone's interpreter, read-only, with `PYTHONPATH` set to my worktree's `src` (checked: `app.__file__` resolves into the worktree). I wrote no bytecode, made no edit or commit in the main checkout, and made no network call. I sent nothing to the launchd service, Fly or GitHub. The data probes ran on copies of the served artifact and the 2026-10-23 candidate, kept in my scratch directory.

> **This record extends** the release verdict of 2026-10-23 (`958458d..660af4b`, PASS WITH FINDINGS, BLOCKING 0, MINOR 3, reviewed head `660af4b`). That verdict covers everything up to `660af4b`, and its text stays in git: `git show 660af4b:docs/reviews/release-security.md`. Its MINORs (#410, and the parser findings filed with it) and its queued risks R1-R3 are carried unchanged. The delta touches none of their files.

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 4 · NIT 0 · risks queued 3.

Nothing in the delta is exploitable from outside, and nothing blocks the deploy.

**The relaxation is close to as narrow as D-220 says, with one gap.** The cut:
- applies only to declared boards (`refresh.py:300`, `:307`), and only to the D-164 loss count (`refresh.py:374`);
- is looked up board by board (`refresh.py:545`);
- never touches a surface's own boards, the new-rows guard or the upward anomalies.

The gap is M2. For a linked model, the cut excuses lost rows by model, not by name. A probe confirmed that a cut naming the rows that were *kept* excused the unnamed rows that were lost.

**The cuts file fails closed:**
- every schema bend raises `AcceptedCutError`;
- through `refresh()`, that error records `EXIT_FAILED` and leaves the live artifact byte-identical;
- a missing file excuses nothing.

**An attacker cannot widen the cut beyond its 94 named rows on `epoch_chess`.** An upstream name can only:
- match a cut entry's spelling key;
- be a row the live board already held.

On the served copy, the 94 names give 94 distinct keys. No other served name, and no 2026-10-23 candidate name, shares a key with them. So after the first publish, the cut excuses nothing unless Epoch publishes a named row again (M3).

**One hostile-input cost is new.** The bracket fallback makes `canonicalize_with_reason` quadratic on a long run of whitespace, and it triples `derive_identity`'s existing cost (M1). The effect stays fail-safe: the night is killed, and nothing is published.

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR
- **M1** `src/app/workflows/registry.py:380`, `:394`, `:400-402`, `:671`. The bracket fallback runs two regexes that are quadratic on hostile names, and it runs them on every name, eagerly.
  - **The regexes.** `_TEXT_BRACKET = r"\s*\(([^()]*)\)"` and the existing `_PAREN_EFFORT` both start with `\s*`. On a run of whitespace with no `(` after it, every start position re-scans the run.
  - **Why it is new cost.** `_unbracketed` is computed before the first lookup has missed. `canonicalize_with_reason` was linear before.
  - **Measured on `"x (" + " " * 20000 + "y"`:**

    | Function | at `660af4b` | at the head |
    |---|---|---|
    | `canonicalize_with_reason` | 8 ms | 1006 ms |
    | `derive_identity` | 500 ms | 1505 ms |

    At 100k characters, one `_TEXT_BRACKET.sub` alone takes 25 s.
  - **Reach.** LMArena caps a value at 256 characters (`clients/arena_slices.py:68`). An Epoch board name is bounded only by csv's 131,072-character field limit (`clients/epoch_board.py:163` strips it and nothing more). So a few names in one hostile upstream file now stall the night until the cycle is killed. Before, it took about five times as many.
  - **Why it is only MINOR.** It fails safe: nothing is published and the served data ages. It is the class of the 660af4b verdict's M3 (SimpleBench).
  - **Remedy:**
    - compute `_unbracketed` only after the first lookup or derive returns nothing;
    - drop the leading `\s*` from `_TEXT_BRACKET`, since the substitution already strips the result;
    - cap a raw name at the score-row boundary (256 characters, as `arena_slices` does). The cap also bounds the existing `_PAREN_EFFORT`.
  - Add a timing-bounded test with a name of 100k spaces after `(`.
- **M2** `src/app/workflows/refresh.py:329-337` (`_excused`, its linked-row branch). For a linked model, the cut excuses lost copies up to `len(live spellings & named)`, whether or not the named spelling is the one that left. D-220 clause 3 says the guard "stops counting only those rows as lost".
  - **Probe.** Sixteen rows. Four models each have a second, linked spelling `Probe NN alt`. The candidate keeps every `alt` row and drops the four `Probe NN` rows.
    - With no cut, it is refused: "would lose 4 of 16 rows".
    - With a cut that names only the four `alt` rows, which stayed, it publishes.
    - The Tester's `test_accepted_cuts.py:150` covers both spellings going, not a named one staying.
  - **Bound.** It applies only while the live board still holds a named spelling, which in practice means the next night. Six served models mix named and unnamed spellings (`gpt-5.5`, `claude-4.6-opus`, `claude-4.6-sonnet`, `claude-5-opus`, `gemini-3-flash`, `gemini-3.1-pro`), so up to about nine unnamed rows could be excused.
  - **Remedy:** excuse a model's lost copies only up to `len((live_spellings & named) - candidate_spellings)`, using `candidate.spellings` for the same board. Add the probe above as a test.
- **M3** `data/accepted-cuts.yaml`, `src/app/workflows/refresh.py:542` (the release Tester's M1, from the security side). Nothing retires the cut. Once the first refresh publishes, it is inert on today's data: I found no served or candidate name that shares a key with an entry. It comes alive again if Epoch publishes a named row again, or an unlinked row whose spelling key matches one, and later drops it. The guard then excuses that loss with no new ruling.
  - **The bound.** Up to 94 rows on one board, all chosen by the upstream. The 154-row board's 25% limit is 38 rows, so the whole guard could be bypassed on that board.
  - **Why it is only MINOR.** Only the publisher of the board can trigger it, by dropping its own rows. The loss is what that publisher publishes.
  - **Remedy (either):**
    - remove the entry in the PR after the first published night;
    - make a cut one-shot. For example, `load_accepted_cuts` or a unit test fails when no named row is left in the served board. Or add an `until:` date the parser enforces.
- **M4** `data/accepted-cuts.yaml` (who can write it). The file relaxes INV-54, but nothing routes a change to it to the security seat, and its ADR field is checked for shape only.
  - `make review-need` reports `no security signal` for it, and the brief declares no security glob.
  - `parse_accepted_cuts` checks `decision` against `D-\d{3}` (`refresh.py:308`), not against an ADR that exists and names the board.
  - The pin test `tests/unit/test_accepted_cuts.py:80` checks the board set and a count of 94, not the names. A same-count swap passes it, and the test can be edited in the same PR.
  - **Who can write it today.** Any branch an agent works on. It takes effect when the owner merges it.
    - **The hosted deploy commands.** The deploy gate counts the file as code (`scripts/deploy_gate.py:136`), so every brief `Deploy commands:` entry, the nightly one included, needs a security delta review first.
    - **The local service.** `scripts/install_engine_service.sh`, which is not a brief deploy command, takes the file into the next launchd release with no security review.
  - **Remedy:**
    - the owner adds `data/accepted-cuts.yaml` to the brief's security globs, so a change routes to the Security-Reviewer;
    - a check (records or unit) asserts that each cut's `decision` is an ADR in `docs/decisions.md` naming that board;
    - the pin test asserts a digest of the names.

### PASS: what I checked and found sound
- **The cuts file fails closed.**
  - Every schema deviation raises `AcceptedCutError` (`refresh.py:292-315`): unknown or missing keys, a non-list, a board that is not declared or is named twice, a decision that is not an ADR id, a blank reason, an empty or non-string row. Broken YAML and an unreadable path raise it too (`refresh.py:296-297`, `:323-325`).
  - Through `refresh()`, a malformed file records `EXIT_FAILED` and leaves the live artifact byte-identical (`tests/unit/test_accepted_cuts.py:197-214`).
  - A missing file returns `{}`, which excuses nothing, so the night is refused (`:188-194`, the `no-file` case asserts `EXIT_REFUSED`).
- **The YAML loader.** The file goes through `yaml_guard.safe_load_bounded`, with its 1 MiB size cap and expanded-node budget (`refresh.py:295`). No new loader exists.
- **Mutants.** I ran three mutants of the cut logic on `test_accepted_cuts.py`, each restored byte for byte from a copy. All three were killed:

  | Mutant | Result |
  |---|---|
  | key excusal without `min` | 1 failed |
  | cuts of every board applied to each board | 1 failed |
  | the file never read | 5 failed |

- **Spelling-key collisions on real data.** The served copy holds 4,649 unlinked rows across all boards. None of them has an empty key, and no two distinct unlinked spellings on one board share a key. The 94 cut names give 94 distinct keys. No served name outside the cut, and no candidate name, collides with any of them.
- **`UnlinkedRow` is a dataclass, not a tuple.** So `UnlinkedRow("x", 0) != LinkedRow("x", 0)`, and a row that loses its link no longer reads as kept (`refresh.py:237-249`).
- **Two spellings with one key stay two rows.** The flood guard still fires on re-spellings beside their old names (`tests/unit/test_refresh_board_ids.py:180`).
- **The bracket fallback runs only on a clean miss.**
  - It runs only when the first reading returned `(None, None)` (`registry.py:381`) or nothing (`:672`). So a modality refusal or a fine-tune refusal is never retried.
  - Read as dash tokens, a modality token in brackets still trips the modality guard: `Some Lab (vision)` gives `Some Lab-vision` and derives `None`, and `claude-3-5-sonnet (audio)` derives `None`.
  - Media names are never re-read (`:671`).
  - An upstream that controls a name could already have published the slug itself, so the fallback gives an attacker no new link.
- **Secrets.** `gitleaks git --log-opts=660af4b..HEAD`: `no leaks found` (8 commits scanned). The arena fixture holds public LMArena rows only.
- **Dependencies.** The delta has no new third-party import. `yaml` is already declared (`pyproject.toml:21`, `pyyaml>=6.0`; `requirements/ingest.lock:379`). `re`, `Counter` and `yaml_guard` are the standard library or the project's own.
- **SAST.** `ruff check --select S` on `refresh.py` and `registry.py`: all checks passed. bandit is not installed in the interpreter I could use, so I did not run it.
- **Destructive operations.** None in the delta's code or commits. `.claude/`, `.githooks/` and `.github/` are untouched.
- **Security invariant.** INV-54 is amended in `docs/security-invariants.md`, citing D-220 clause 4, the owner's 2026-10-23 ruling on #415. No citing test was removed.
  - `test_an_unlinked_row_is_still_compared_by_its_name` still asserts that a renamed row (a changed letter) is refused (`test_refresh_board_ids.py:166-177`).
  - Five tests were added to the row.
- **Tests.** The delta's suites pass at the head: `test_accepted_cuts`, `test_arena_respelling`, `test_refresh_board_ids`, `test_refresh_boards`, `test_uncovered_boards` and `test_floor_served`, 225 passed.

## Gates passed
- [x] Secret scan green: `make secrets` `no leaks found` on `bf278b0` (dispatcher), and my own gitleaks run over the range at `9208fd8`
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found` on `bf278b0`; the delta changes no lock
- [x] `make slopsquat` green: PASS on `bf278b0`; the delta adds no third-party import
- [x] Default-deny preserved for new external surfaces: the delta adds no route, endpoint or network call
- [x] Permission matrix not violated: no destructive operation, no guarded tree touched
- [x] Prompt-injection hygiene: names are data, matched by regexes and never interpreted; no LLM reads them in this path
- [ ] Auth/PII checks + human review trigger: not applicable, no HIGH path and no auth, PII, payment or migration code
- [x] SAST: `ruff --select S` clean on both changed modules; bandit unavailable to this seat

## Acceptance criteria evidence (#415, D-220)
- D-220 cl. 1 (spelling key; two spellings with one key are two rows; `+` kept) → `tests/unit/test_refresh_board_ids.py:154`, `:166`, `:180`, `:195`
- D-220 cl. 2 (a bracketed name read as its slug; a moving alias derives nothing; an effort is never part of the id) → `tests/unit/test_arena_respelling.py:40`, `:50`, `:55`, `:76`, `:86`
- D-220 cl. 3 (a named cut is not a loss; any other row counts; one board's cut excuses nothing on another; the file fails closed) → `tests/unit/test_accepted_cuts.py:57`, `:61`, `:67`, `:73`, `:95`, `:120`, `:150`, `:188`, `:197`, `:217`. M2 is the one case not covered.
- D-220 cl. 4 (INV-54 reworded, its tests kept) → `docs/security-invariants.md` INV-54; `tests/unit/test_refresh_board_ids.py:166`

## Risks queued
- **R1** `src/app/workflows/refresh.py:280` (`spelling_key`). The key keeps ASCII letters, digits and `+` only.
  - Two kinds of name collide:
    - a name with none of those characters (any non-Latin name) gets the empty key, so every such name on a board shares one key;
    - two models that differ only in punctuation share a key, for example `Llama 3.1 8B` and `Llama 3 18B`.
  - A lost row and a new row with one key then read as kept. No gate watches for this: D-220's revisit trigger covers only what a person notices.
  - On the served data there are no such collisions today (see PASS).
  - Suggested:
    - the night record counts keys shared by distinct spellings;
    - `parse_accepted_cuts` refuses a cut name whose key is empty or shared within the cut.
- **R2** `src/app/workflows/registry.py:334`, existing and unchanged by the delta (the same at `660af4b`). A modality token inside a parenthesis escapes the curated-rule modality guard.
  - `_MODALITY_RX` needs `^` or `[-_/. ]` before the token, so `GPT-4o (image)` and `GPT-4o (vision)` canonicalize to the text model `gpt-4o`. A media price or score could then attach to a text model.
  - The delta's fallback does not widen this, since it runs only on `(None, None)`.
  - This is a correctness bug for an issue, not a security finding.
- **R3** Carried from the `660af4b` verdict, unchanged:
  - its M1-M3: #410, and the parser findings filed beside it;
  - R1: the `Fly-Client-IP` check after the first deploy;
  - R2: confirm the `fly-production` environment allows `main` only before the first scheduled night;
  - R3: #401, #403, #396, #371, #323, #309.

**New issues needed:**
- M1;
- M2, M3 and M4 together, as one issue on the accepted-cuts controls; it also covers the release Tester's M1;
- R2, as a `bug`.
