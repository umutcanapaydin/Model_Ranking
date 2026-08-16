---
record_type: wave
id: m5-wave-4-close
status: ratified
date: 2026-08-16
---
# Wave-Close Checklist — M5 Wave 4 (attribution, migrate command, carried warnings; v4.1 template)

> Wave scope: `docs/plans/m5-wave-4-implementation.md` (REQ-LIC-001 + W-003/W-004/W-006/W-007 +
> Epoch cadence). **This wave was implemented by one agent and closed by another** — the implementing
> agent ran out of budget at the `wip(m5-w4): checkpoint — NOT reviewed` commit with four files still
> uncommitted, and no review of any kind had run. The closing agent authored none of the reviewed
> code, so K.7 fresh eyes is satisfied structurally rather than by assignment.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier: **HIGH**, self-declared by the wave's own plan (schema migration → auto-escalates under P-005), not inherited from the milestone's LOW-MED default | m5-wave-4-implementation.md "Risk: HIGH" | ✅ |
| 2 | Full `make check` green on the CLOSING tree (not the checkpoint): ruff, black, mypy (27 files), **266 passed + 12 gated**, check-records, selftest, install-check, pin-check | run log 2026-08-16, /tmp/m5c.log | ✅ |
| 3 | HIGH → fresh-eyes **Code Reviewer** on the whole W4 delta (`5eb3e15..HEAD` + the 4 uncommitted files reviewed together as one unfinished wave). Verdict **FAIL: 3 BLOCKING + 9 MINOR**. The reviewer independently fault-injected five behaviours (all RED) before finding the three that ship defects | review transcript; §Findings below | ✅ |
| 4 | Tester duty: fault-injection protocol run on every FIX, in place, md5-verified byte-identical restore, never `git checkout`. **6 mutants, 6 RED** — one initially STAYED GREEN and the mutant itself was wrong (first-match-wins meant reverting the base rule alone could not reproduce the bug); re-injected by deleting the variant rules and it went RED | /tmp/fi_m5.py, /tmp/fi_m5b.py run logs | ✅ |
| 5 | Security-on-slice for the migration path: `migrate` opens `mode=rw`, refuses a missing file (exit 2), refuses a database it cannot repair (exit 2, **new**), is atomic (`BEGIN IMMEDIATE` + rollback), idempotent, and both read CLIs stay migration-free (`recommend` plain connect, `coverage` `mode=ro`) | schema.py:337-370; reviewer §4; whole-milestone security review at closure | ✅ |
| 6 | Criteria → citing tests: REQ-LIC-001 (`test_req_lic_001_epoch_citation_ships_where_epoch_data_is_served`, `test_payload_never_claims_a_source_it_did_not_read`, e2e CLI), W-007 (3 tests asserting `/rows` is never called), W-003 (`test_selected_stale_roster_clock_is_disclosed_through_cli` + boundary), W-004 (`test_explicit_migrate_cli_refuses_a_legacy_table_it_cannot_repair`, `test_migration_validator_requirements_are_derived_from_the_shipped_ddl`, idempotence, rollback), W-006/REQ-REC-013 (`test_budget_notice_counts_only_scoreable_plans_excluded_by_price`, `test_budget_that_prices_out_everything_still_says_how_many` **through the CLI**), Epoch cadence (`test_ingest_stamp_and_committed_clock_are_one_value`, boundary, unparseable-date) | tests/unit/*, tests/integration/test_cli_e2e.py | ✅ |
| 7 | No `git checkout`/`restore` on uncommitted work — every revert was a byte-comparison restore | rows 4 | ✅ |
| 9c | Invariant hardening: the migration validator now **derives its requirement from the shipped DDL** instead of a hand-written list, so a column added tomorrow is covered tomorrow. That is the structural form of the defect it fixes — a hand-maintained copy of the schema drifts from the schema | schema.py `_ddl_columns` + its citing test | ✅ |
| 9b | Scope row: PLANNED = the six W4 behaviours. DELIVERED = all six, **plus three BLOCKING fixes and four MINOR fixes found by the review that never ran**, plus one live-data defect found while closing (see §Findings). NOT DELIVERED: MINOR-4 (two migration entry points), MINOR-6 (roster `last_verified` invariant enforced at read time), MINOR-2 (roster staleness window borrowed from the plan table), effort-telemetry under-count — all ledgered with owning milestones rather than patched at close | §Findings; docs/warnings.ledger.md | ✅ |
| 9a | Economy: 12 files touched by the fix pass, ~470 net lines on top of the inherited checkpoint. The wave itself was inherited, so its implementation cost is not attributable here | git diff --stat | ✅ |
| 9 | RUN LINE — gates run: ruff · black · mypy · pytest(266+12 gated) · check-records · selftest · install-check · pin-check · live Epoch bundle probes (ingest + reconcile against the owner's fetched CSVs) · outcome: **shipped**. SKIPPED: 12 network/`EPOCH_DATA_DIR`-gated tests (standing rule; the owner's bundle is not in CI) | this row | ✅ |

## Findings closed in this wave

**BLOCKING-1 — `schema migrate` reported success on a database it had not made usable.** The
validator checked two tables by hand, so a pre-M3 `plans` missing `observed_at` migrated with exit 0
and a JSON success payload, and the next `recommend --subscription` died with `no such column` —
the precise symptom W-004 exists to remove, now hidden behind a success message. Fixed by deriving
the requirement from the DDL; exit 2 with the missing column named.

**BLOCKING-2 — `sources` claimed sources the answer never read.** Both payloads stamped the full
attribution catalogue, so an `assistant` answer ranked purely on Arena Elo also claimed SWE-bench,
Aider and Epoch. `sources` is a provenance claim in a machine contract. Fixed: attributions are
derived from the evidence rows actually used (`attributions_for`), an unattributed source raises
rather than silently dropping a CC-BY obligation, and the subscription engine no longer claims the
per-token pricing feeds it never reads.

**BLOCKING-3 — the Epoch acquisition clock existed twice.** CI checked `data/epoch-source.yaml`
while the only production path that constructs an `EpochClient` carried a hardcoded
`--last-verified` default. Re-acquire the bundle, update the file, and CI goes green while the data
keeps the old stamp. Fixed: one clock, read from the committed record, with a test that fails if the
default becomes a literal again.

**MINOR-1 — the budget notice was silent in the case that needed it most.** `excluded_by_budget` was
computed *after* the early return, so when the cap excluded every scoreable plan the CLI printed a
bare error. W-006's complaint was unfixed at its sharpest point while the ledger already read FIXED.
Fixed via `budget_shutout`, asserted through the real CLI.

**MINOR-5 / MINOR-7 / MINOR-8** — the DDL splitter died on a trailing comment (a comment could take
the whole application down); a docstring in the file this wave rewrote still described the
pre-M2 Arena category; the licence token appeared twice in two spellings so a test could
substring-match it. All three fixed, the first with a citing test.

**Found while closing, not by the review — a live registry swallow.** Running the real Epoch
SWE-bench board through ingest + reconcile showed `kimi-k2.5` (73.8) and `kimi-k2.6` (76.7) both
folding into `kimi-k2`, so `MAX()` published the newer model's score under the older model's name.
This is the M4-W1 swallow class recurring on a new source, and the rule table's own property tests
could not see it because the live-name corpus had never met these names. Fixed with guarded variant
rules and five new corpus entries. **Lesson: a new SOURCE is a new corpus — replay the live-name
expectations against every board the milestone adds.**

**Escaped-blocker tripwire:** one, and it is the wave itself — W4 was committed as a checkpoint
labelled NOT reviewed and would have entered milestone closure unreviewed if the owner had not
handed it over. Three BLOCKING defects were sitting in it.

Filled by: Claude (Cowork lead agent, D-106) · Date: 2026-08-16 · Wave commit range: `5eb3e15..HEAD`
