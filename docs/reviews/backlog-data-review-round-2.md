---
record_type: review
id: backlog-data-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-13
---
# Independent review, round 2: the backlog data wave (#232, #234, #235, #262, #264, #266)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-13
**Commit range:** `0d5bc8b..7bdc928` (8 commits). It also re-checks round 1
(`docs/reviews/backlog-data-review.md`) and the author's dispositions of it.
**Risk tier:** MEDIUM

## Verdict
BLOCKING

The fix for round 1's B1 brings K2.7 Code's price back to 0.95/4.0, but it goes too far on the score
side. The same registry rule also refuses Arena's only spelling of Kimi K2 Thinking. As a result, 33
Arena score rows link to no model, and K2 Thinking drops off four surfaces. D-195 records these rows as
moving to new ids. The other fixes hold.

How the review was done:
- **Artifact.** I worked on copies of the worktree's `advisor.db` (sha256 `bc5435b0…`, unchanged at the
  end). I set every `model_id` to NULL, then ran `reconcile`, `access.link`, `reconcile_plans` and
  `build_price_medians` with three trees (`git archive`): `origin/main`, `0d5bc8b` and `7bdc928`.
  - Rebuilding with `origin/main` reproduces the served links exactly: 0 price rows and 0 score rows
    differ.
  - `origin/main` against `7bdc928`: `degradations` = [] and `upward_anomalies` = [].
    `largest_board_change` = `board arena_text_polish`, 6 of 232.
- **Regex audit.** I ran all 4,503 distinct `raw_name` and `alias` values through `0d5bc8b`'s registry
  and `7bdc928`'s registry. Exactly 10 change: the 7 speed-tier names leave, and the 3 K2 dated previews
  join K2.
  - `_NOT_A_SPEED_TIER` is used only by the five Kimi rules. `grok-4-fast*`, `gemini-*-flash`,
    `grok-code-fast-1` and every effort suffix (`kimi-k2.5_none`, `Kimi K2.5 (high)`) read as before.
- **Credits (#262).** I ran FastAPI `TestClient` with `APP_ENV=test` and `MODEL_RANKING_DB` on the
  rebuilt copy, over all 14 tasks × 3 budgets.
  - Cited sources ⊆ `/v1/boards` attributions (9 against 10).
  - The one credit nothing cites is Epoch's WebDev Arena board, which `/v1/boards` serves. No secondary
    is credited without being served.
- **Faults.** I planted 11 faults, each restored from its bytes and checked by sha256. Six were caught
  and five survived (M4). `git status` was clean afterwards.
- **Tests.** The five touched test files pass: 303 passed.

**Round 1, re-judged.**
- **B1 fixed for prices.** K2.7 Code's median is 0.95/4.0, and K2.6's is 0.95/4.0. The over-reach is
  the new B1 below.
- **K1 fixed.** 55 Arena rows link to K2.
- **M1 fixed.** `largest_board_change` now judges boards as the two guards do:
  - losses are measured against `baseline` (`degradations(baseline, fresh)` at `refresh.py:1083`);
  - gains are measured over `live`'s boards, falling back to the baseline's rows (`upward_anomalies`);
  - a board that was empty, or that `live` does not serve, is skipped by both.
- **M2 partly fixed.** Two of the new call paths are still untested (M4).
- **M3.** D-195 exists, but parts of it are false (M1).
- **Dispositions.**
  - K2: honest. D-195 clause 3 and #267's closing comment both rule a Pro run `unspecified`.
  - K3: honest. #269 is open.
  - R1: an honest acceptance. The 30-day `CARRY_MAX_AGE` still bounds it.
- **#266.** The ruling holds, and D-195 clause 3 records it as round 1 asked.
- **#262.** No over-credit and no missed route. `/v1` serves only `/health`, `categories`, `budgets`,
  `boards` and `recommendations`, and `subscribe.py` is CLI-only.

## Findings

### BLOCKING
- **B1** `src/app/workflows/registry.py:224` (and `:67`, with the pin at `tests/unit/test_registry.py:928`):
  the speed-tier rule drops Kimi K2 Thinking's Arena scores, not only the prices B1 was about.
  - **The cause.** `kimi-k2-thinking-turbo` matches no rule now, and it is Arena's only spelling of
    K2 Thinking. It is a score name only: the artifact has no price alias of that name. B1's reason,
    "a speed tier priced at double", therefore does not apply to it.
  - **Measured on the rebuilt copy.**
    - 33 Arena rows (`arena`, `arena_factuality`, `arena_text_*`) have `model_id` NULL.
    - Under `0d5bc8b` they were K2 Thinking's; under `origin/main` they were K2's.
    - They derive nothing. `reconcile` links a derived id only when it has both a price and a score
      (`registry.py:926-927`, used at `:1030`).
  - **Effect.** Against `0d5bc8b`, Kimi K2 Thinking leaves `assistant`, `expert`, `factuality` and
    `mathematics`. Its only rows left are `epoch_eci` and `swebench`.
  - **Wider risk.** The artifact's score names use `-turbo` and `-fast` widely: `glm-5v-turbo` (39 rows),
    `grok-4-1-fast-reasoning` (39), `gpt-4-turbo-2024-04-09` (35). Generalising this lookahead would
    drop them the same way.
  - **Fix.**
    - Refuse a speed tier only on the price path: in `reconcile`'s `pricing` loop, or with a
      price-only check. A score name with a tier keeps linking to the model it ran, which is the same
      weights at a different speed.
    - Add a test: a score `raw_name` of `kimi-k2-thinking-turbo` links to `kimi-k2-thinking`, while the
      price alias still never prices it.
    - Correct D-195 (M1).

### MINOR
- **M1** `docs/decisions.md:4948` and `:4950-4953`: D-195's clause 4 and its *Consequence* paragraph
  state things the artifact does not show.
  - **"they derive models of their own".** None does. The two `-highspeed` aliases and the four
    Fireworks `-fast` routers have `model_id` NULL, because a derived id needs a score too.
  - **The score rows.** It says "138 score rows … leave Kimi K2, Qwen3-Coder and DeepSeek V3, V3.1 and
    V3.2 for six new ids". Measured against the served artifact: 102 go to the six new ids, 3 to
    K2.5, and 33 to no model (B1).
  - **The price aliases.** It says "59 price aliases". I count 55: 43 to the new ids, 8 to
    K2.5/K2.6/K2.7 Code/V3.1/V3.2, and 4 to none.
  - **The MiniMax example.** It cites MiniMax M2.5's `lightning` as the precedent, but MiniMax's own
    `-highspeed` tiers still price M2.5 and M2.7 (K1).
  - **Fix.** Restate clause 4 to match B1's fix, and restate the counts from a reconcile of the served
    artifact.
- **M2** `scripts/venv_owner.py:36` and `:45`: on Windows, and on a macOS path typed in a different
  case, the check refuses a venv the tree owns.
  - **Windows.** `Path(unquote(urlparse(url).path))` reads pip's `file:///C:/Users/...` as
    `\C:\Users\...`, with no drive (checked with `PureWindowsPath`). It never equals `tree.resolve()`.
    So on Windows, the first `make install` after a `pyproject.toml` or lock change refuses, and tells
    the user to delete their venv. INSTALL.md supports Windows, and no CI runner is Windows.
  - **macOS case.** `resolve()` does not fold case on APFS. Run read-only against the owner's clone:
    - `venv_owner.py …/Desktop/ILGAR/model_ranking/.venv --tree …/Desktop/ILGAR/model_ranking`
      exits 0;
    - the same tree as `…/desktop/ilgar/MODEL_RANKING` (a valid `cd` on a case-insensitive disk)
      exits 1, with "Remove it".
  - **Fix.**
    - Use `urllib.request.url2pathname(parsed.path)`.
    - Compare with `os.path.samefile` when both paths exist, falling back to `os.path.normcase` on the
      resolved paths.
    - Add a test with a `file:///C:/…` URL through `PureWindowsPath`. Removing the `Lib/site-packages`
      glob survives today (F9).
- **M3** `scripts/deploy_hosted_engine.sh:97` and `src/app/workflows/refresh.py:827`: #235 R2 is not met,
  and the new test's docstring (`tests/unit/test_data_release_stamp.py:190-192`) overstates what it pins.
  - **What happens.** `_builds` records `served_built_by: "unknown"` for any refresh run without
    `APP_BUILD`, dev code included. The deploy's own message at `:90` says so.
  - **Failure.** Such data deploys under `DEPLOY_ACCEPT_DATA_FROM=unknown`. It is announced as "a record
    from before #198" and stamped `-from-unknown`, so `/health` still cannot tell it from a pre-#198
    record. That is the sign #235 names.
  - **Fix.**
    - Have `_builds` record a distinct value when `APP_BUILD` is unset (`unset-<sha>`, or `dev-<sha>`
      from git), so `unknown` comes only from a missing key.
    - Or reword `:97` and the docstring, and keep #235 open for R2.
- **M4** `tests/unit/test_refresh_board_ids.py:306-350` and `tests/unit/test_registry.py:928`: three
  planted faults in the round-1 fixes survive (303 passed each time).
  - **F3** `was_by.get(name) or rows` replaced by `was_by.get(name, frozenset())` (`refresh.py:319`):
    a board an expiry empties is skipped instead of judged against its live rows.
  - **F4** the refused call at `refresh.py:1402` without `baseline`: the expiry case is tested only
    through a direct call.
  - **F6** `_NOT_A_SPEED_TIER` removed from the bare K2 rule: no test name is a K2 speed tier, though
    Moonshot sells `kimi-k2-turbo-preview`.

  Caught: F1 (baseline ignored), F2 (board-appearing excuse removed), F5 (`turbo` dropped), F7 (#235's
  `qwen` clause), F8 (#262's secondaries), F11 (K1 reverted).
  - **Fix.** Add:
    - a refused expiry night through `refresh`;
    - an expiry that empties a board;
    - `kimi-k2-turbo-preview` among the never-the-base names.

## K.9 candidates spotted outside this wave's scope
- **K1** `src/app/workflows/registry.py:264-265`: MiniMax's own `-highspeed` tiers still price their base
  models. This is B1's class, and D-195 clause 4 now rules it out.
  - **What joins.** `minimax/MiniMax-M2.7-highspeed`, `novita/minimax/minimax-m2.7-highspeed` and their
    M2.5 twins, all at 0.6/2.4, join M2.7 and M2.5 (base 0.3/1.2).
  - **Measured.** Served medians are M2.7 0.375/1.5 and M2.5 0.385/1.54. Without the tiers they are
    0.3/1.2 and 0.305/1.22: +25% and +26%.
  - **Fix.** Refuse `highspeed` on the price path, as B1's fix should. This is a bug.

## Risks queued to next M
- **R1** `Makefile:83`: `venv_owner.py` runs only inside the `$(VENV)/.installed` recipe, so it guards
  pip and nothing else.
  - **The risk.** A worktree whose `.venv` links to the main clone's still runs `make test` and
    `make check` on the main clone's code, the second harm #264 names.
  - **How it hides.** `make install` itself skips the check when the linked `.installed` is newer than
    the worktree's `pyproject.toml` and locks.
  - **What would show it is real.** A worktree run whose `app.__file__` resolves outside the worktree.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| B1 | Fixed. The regex guard is gone; a speed tier is refused on the price path only (`registry.price_refusal`, `SPEED_TIERED`), so Arena's `kimi-k2-thinking-turbo` and `kimi-k2-turbo-preview` link to their models while their prices are refused. | `0ecc9c8` red, `4bf45d0` fix |
| M1 | Fixed. D-195 clauses 4 and 5 and its Consequence are rewritten from a measurement with every link made again: 135 score rows and 46 aliases to seven new ids, 55 preview rows and an alias to K2, 11 speed-tier and 3 Cyber aliases refused, and the medians named. | this commit |
| M2 | Fixed. `editable_path` keeps a Windows drive, and trees are compared with `Path.samefile`; a tree reached by another spelling owns its venv. | `0ecc9c8` red, `4bf45d0` fix |
| M3 | Fixed. A cycle run without APP_BUILD records `unstamped`, which no `DEPLOY_ACCEPT_DATA_FROM` accepts; `unknown` names only a record from before #198. | `0ecc9c8` red, `4bf45d0` fix |
| M4 | Fixed. The emptied-baseline fallback has a test; the figure is computed once, so the refused path cannot drop the baseline; `kimi-k2-turbo-preview` is a test name. | `0ecc9c8`, `4bf45d0` |
| K1 | Fixed in this wave: MiniMax's speed tiers are in `SPEED_TIERED` (`c035b78`, then the price path in `4bf45d0`). | `4bf45d0` |
| R1 | Fixed. `make install` checks the venv on every run, so `make test` does too. | `0ecc9c8` red, `4bf45d0` fix |

