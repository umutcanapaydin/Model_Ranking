---
record_type: review
id: m11-council-senior-swe
status: ratified
seat: independent
date: 2026-08-24
---
# M11 Council — Senior Software Developer seat

> **Not a correctness review.** Eleven milestones of review seats have covered whether this is right,
> and they have covered it unusually well. This seat answers a different question: **what will this
> codebase be like to work in six months, and what is being accumulated that nobody is counting?**
>
> Policy read from the protected base ref (`git show HEAD:AGENTS.md`) per V4C-06. Everything below was
> measured by running something, not by reading a record. Where I mutated a file to measure it, the
> restoration is verified by md5 and the command is shown.

**Methodology note, stated because it affected one measurement.** This council's seats share one
working tree. At 18:19 my `make gate` run went red on `test_categories.py` against a
`src/app/workflows/categories.py` that another seat was mid-mutation on (`value_window` 100.0 → 1.0,
restored by 18:20:30, `git diff --stat` empty). That is a session artefact, not a repository property,
and I re-ran every affected measurement on a clean tree. My own mutation
(`src/app/workflows/recommend.py`) restored to md5 `4c17631e454a08004b0a4d138bd5069d`; the ledger I
experimented against restored to `93a3388391dc926cc6360cadfa8776f4`. Nothing in the repository was
left changed by me except this file.

**The headline.** The engine is in good shape. Median function length is 22 lines across 205
functions; only 12 exceed 80. Cross-module duplication is 23 eight-line windows in six file pairs.
Tests import exactly two private symbols. Coverage is 88% with a per-module floor. `make check` runs
in 18 seconds, which is the single best thing about this repository — a gate that costs 18 seconds
gets typed, and that is why it works. **What is accumulating is not in `src/`.** It is in the
records, in the gates about the records, and in one specific place: the half of the product the next
milestone is entirely about is the half nothing executes.

---

## 1. The next milestone lands on the only part of the system nothing tests, through a contract that is frozen

**What it is.** `docs/plans/m12-inputs.md` records five requirements from the first real users, four
of which are one finding: the product explains what it measured in the language of the measurement.
The owner's decision on item 1 (`docs/plans/m12-inputs.md:29-30`) is *"the ENGINE returns structured
facts and the CLIENT composes the sentence."* That inverts the engine/client boundary the last five
milestones were built on. Three things stand in its path, and none of them is visible from a green
gate.

**The evidence.**

*(a) Every user-facing sentence in the product is unpinned.* I replaced all three `why=` strings in
`src/app/workflows/recommend.py:333,340,356` with `MUTANT-A/B/C` and ran the suite:

```
$ python3 - <<< "…replace 3 why-strings…"   # mutated 3 why-strings
$ .venv/bin/python -m pytest -q
714 passed, 12 skipped, 151 warnings in 6.39s
$ md5 -q src/app/workflows/recommend.py     # 4c17631e454a08004b0a4d138bd5069d — restored, verified
```

**714 of 714 stayed green with every explanation the product gives a human replaced by garbage.**
Corroborating counts: `grep -rn "\.why\b" tests/` → 9 hits; assertions containing an English sentence
across all of `tests/unit/` → 6. The suite pins the *pipeline* thoroughly and the *meaning* not at
all. That cuts both ways and the second way is the dangerous one: rewriting these strings costs
nothing in test churn, and nothing will tell you when the rewrite makes them wrong.

*(b) The file that will absorb the work has no executed tests.* `ios/ModelRanking/ContentView.swift`
is 551 lines. `ios/Package.swift:45` scopes the test target to `ModelRanking/Engine`, and
`ios/Package.swift:12-16` says so honestly: *"`ContentView.swift` and `ModelRankingApp.swift` are
SwiftUI and stay unexecuted."* That was a defensible call for M11, whose subject was the Engine. It
is the wrong shape for M12, whose subject is the screen. The only thing standing over ContentView is
`tests/unit/test_ios_client_contract.py` — **416 lines of Python regular expressions run over Swift
source text.** Sample assertions: `:156` `re.search(rf"\.{field}\s*[-+*/]\s*[\w(.]", code)`,
`:190` an ordering check, `:107` `re.findall(r"func\s+disclosures\s*\(", view)`, `:413`
`re.search(r"eligibleCount\s*<\s*\w+\.ranking\.count", code)`. These encode Trap 1/2/3 — the client
may not compute, reorder, or drop a disclosure — under the *old* architecture where the engine
composes prose. Move composition to the client and every one of these regexes either fights the edit
or silently stops matching. A regex that stops matching is a test that stops testing.

*(c) The payload is frozen and the window is spent.* D-115 (`docs/decisions.md:587`) froze `/v1`;
D-124 (`:921`) granted exactly one revision during M8; D-125 (`:957`) spent it and says so at
`:993-994`. D-124's own *Revisit-when* at `:953` is *"M8 closes. At that point this ADR expires by
its own terms"* — M8, M9, M10 and M11 have all closed and D-124's status line still reads `accepted`.
`tests/unit/test_contract_change_provenance.py` turns red on a payload field no ADR accounts for.
D-134 (`:1350`) established the cheap path — a sibling resource is not a payload revision — and it is
carefully argued. **That is exactly why it is the risk.** With the freeze intact and a blessed
workaround on the shelf, the path of least resistance for M12 is four more sibling resources and a
client that reassembles the answer from them. That is a frozen contract bent around rather than
revised, and six months from now the shape of `/v1` will be an archaeology problem rather than a
design.

**What it costs today.** Nothing. Everything is green.

**What it costs in six months.** This is the product's entire next phase. Working blind on 551 lines
of UI, fighting regexes written for the previous architecture, while routing every payload change
around a freeze whose justification (D-124: *"a contract frozen before anyone read it is a guess with
a lock on it"*) has now been answered by real readers.

**Smallest change that alters the trajectory.** Three things, all before M12-W1 opens:
1. **One owner ADR that decides whether `/v1` may move.** Not four sibling resources decided one wave
   at a time. D-124's precedent is the right shape: a bounded window, tied to the first
   comprehensibility client, expiring by its own terms.
2. **Add `ModelRanking` (the SwiftUI target) to `ios/Package.swift` and write three tests** that
   render an `Answer` and assert on the strings the user sees. Then delete the regex tests they
   replace. The count floor at `Makefile:118` (`SWIFT_TEST_FLOOR = 59`) already exists to make this
   stick.
3. **Pin the sentences.** One test per surface asserting the composed sentence for a fixed fixture.
   Not the wording — the *shape*: that a number is accompanied by a unit a reader knows, that a rank
   appears where a raw index does. That is the instrument M11's own carried question asks for
   (`note.txt:66`: *"A correctness culture measures whether a number is right and has no instrument
   for whether it is understood."*).

---

## 2. `make gate` — the declared canonical gate, and the only thing the post-edit hook runs — is RED on a clean tree

**What it is.** `Makefile:44-46` states plainly: *"`gate` is now the ONE name that means 'everything
this pipeline claims to enforce'. The hook calls it, CI calls it, and the design doc points at it. If
a control is not reachable from here, we do not claim it."*

**The evidence.** Measured twice, second time on a verified-clean tree:

```
$ ( time make gate )
714 passed, 12 skipped, 151 warnings in 6.64s
coverage-floor PASS · check_records PASS · self-test PASS: 0 problem(s)
wave-check-all PASS · conformance-gate PASS: 6 finding(s), all exempted · swift-test PASS: 59
  [FAIL] test-git-authority.py       FAIL: 2 violation(s)
  [FAIL] test-documented-commands.py FAIL: 373 documented command(s), 4 dangling
conformance FAIL: 7 test(s), 2 failing
make: *** [conformance] Error 1
make gate  15.08s user 3.72s system 87% cpu 21.607 total
EXIT=2
```

The cause is one word in one line. `Makefile:154` — `check: … conformance-gate …` — runs the
conformance suite through `scripts/conformance_gate.py`, which knows about the six exemptions handed
back to the pipeline (GPF-001, GPF-004) and passes. `Makefile:48` — `gate: check conformance falsify
secrets deps slopsquat` — then runs the **raw** suite a second time, which does not know about the
exemptions and fails. `make gate` runs the whole conformance suite twice and the second run
overrides the first.

**And nothing consumes the failure.** `.claude/settings.json:58` wires `make gate` as a `PostToolUse`
hook on `Write|Edit|MultiEdit` with `exit 1` on non-zero — i.e. a hard block after every file edit.
That hook `tee -a`s into `.claude/last-check.log`. **That file does not exist** (`ls -la .claude/`:
`RESUME.md`, `settings.json`, `skills/` only). CI does not run it either: `grep -rn "make " 
.github/workflows/*.yml` returns two comment lines and no invocation — every workflow calls `ruff`,
`mypy`, `pytest`, `check_records.py` and `conformance/run-all.py` directly. `runner:64` runs
`make check`, not `make gate`, while `note.txt:9` describes `./runner` as *"gate + secrets + …"*.
`conformance/test-hook-claims.py` — whose docstring is literally *"Every control the documentation
claims is enforced must be reachable from `make gate`"* — checks that each target **exists** and that
its recipe **contains a string**. It never runs `make gate`.

So there are two gates called canonical. The one everybody types (`make check`) is green and is
cited by `note.txt`, the closure reports and `runner`. The one the Makefile, the hook and the design
doc call canonical is red, and has been since `conformance-gate` was introduced without amending
`gate`.

This repository's own doctrine, written in `scripts/conformance_gate.py:6`: *"A permanently red CI
teaches everyone to stop reading it, and that is what happened."* The lesson was written and then
reproduced one Make target over.

**What it costs today.** Either the post-edit hook is not firing at all (no log, ever), or it is
firing and being overridden. Both are worse than not having it. And a control the documentation names
as the complete set is a control nobody can trust the boundary of.

**What it costs in six months.** Every future "is X enforced?" question gets answered from
`Makefile:44-46`, which is false. New controls will be added to `check` (where they run) or `gate`
(where the docs say they belong) with no rule deciding which, and the two will drift further.

**Smallest change.** One line: `gate: check falsify secrets deps slopsquat` — drop the raw
`conformance` leg, which `check` already runs exemption-aware. Then either delete the "CI calls it"
clause from `Makefile:45` or add `make gate` to `ci.yml`. Total: two lines, and the suite stops
running twice.

---

## 3. C2b — the counter that decides when a discipline goes under review — cannot fire on this ledger

**What it is.** V4C-13 says a control bypassed three times sends the **control** for review, not the
people. `scripts/check_records.py:728-734` implements it as `C2b`. It is the single most important
governance rule in the repository, because it is the only one that can criticise a discipline from
inside — and my profile's brief is that a discipline which cannot be criticised from inside becomes a
ritual.

**The evidence.** `C2b` groups by `cells[1]` — the ledger's *"rule that warned"* column
(`check_records.py:721`, `accepted.setdefault(rule, []).append(wid)`). That column is filled with
free-text provenance, not with a rule identifier:

```
$ grep "^| W-" docs/warnings.ledger.md | awk -F'|' '{if($6=="ACCEPTED") print $3}' | sort | uniq -c
   1 `docs/plans/m6-wave-3-close.md` rows 3 and 4
   1 M9-W2 independent review, MAJOR-6
   1 M8 independent tester, V3C-02 audit
   … all 22 distinct, every count == 1
```

**All 22 ACCEPTED rows have a unique key, so `C2b` is arithmetically unable to fire.** I proved the
rule itself works and only the key is wrong, by copying the ledger into a synthetic root and
rewriting *nothing but column 2* on the three K.7 rows:

```
REAL ledger  -> C2 findings: NONE
SAME ledger, column 2 = the CONTROL's name instead of provenance:  C2b
--- ledger untouched? --- now: 93a3388391dc926cc6360cadfa8776f4  was: 93a3388391dc926cc6360cadfa8776f4
```

`C2a` — *"a warning may not survive the close it was raised in"* — is likewise unreachable: it fires
only on `status == "OPEN"` (`check_records.py:711`) and the ledger contains **zero** OPEN rows (47
FIXED / 22 ACCEPTED / 6 ESCALATED). `C2c` requires an ACCEPTED row's reason to match
`[mM]\d|milestone`, which any incidental `m8-plan.md` in a 1,379-character prose cell satisfies —
`W-011` is ACCEPTED with no owning milestone line at all and passes.

**Meanwhile the thing it exists to count has happened ten times.** K.7 / V3C-78 (fresh eyes) carries
5 ledger rows (W-016, W-018, W-020, W-055, W-056) plus 5 more bypasses recorded only in wave-close
records with no ledger row at all (`docs/plans/m8-wave-1-close.md:30`, `m8-wave-2-close.md:25`,
`m8-wave-3-close.md:23`, `m9-wave-1-close.md:27`, `m9-wave-2-close.md:29`, each tagged *"WAIVED under
PRESSURE … `control-bypass` under V4C-13"*). And two records assert the counter fired —
`docs/reviews/m8-security-review.md:15` (*"`C2b` has fired and the CONTROL goes to M9"*) and
`docs/retrospectives/m8-retrospective.md:87`. **It cannot have.** That assertion was made by hand, in
prose, about a rule that returns nothing on this data. W-055 itself says the quiet part:
*"The telemetry worked exactly as designed and nothing consumed it."* It did not work as designed. It
did not run.

This is the highest-value finding in this review for the *process*, because it is the project's own
signature defect — a record asserting a control that is not there — occurring inside the mechanism
built to catch exactly that.

**What it costs today.** The only self-correcting loop in the governance system is off, and two
records claim it is on.

**What it costs in six months.** Every future repeat-bypass is invisible, and the ledger keeps
growing (20 rows in M11 alone) with a counter that can never reach 3.

**Smallest change.** Two edits, roughly ten lines total: (1) add a seventh column `control` to the
ledger schema holding a stable token (`K.7`, `V3C-02`, `L.8`) and key `C2b` on it; (2) backfill the
five M8/M9 wave-close bypasses as ledger rows so the count is true. The conformance fixture at
`probe/C2b` already proves the rule — it was written against a synthetic row whose column 2 was a
rule name, which is why the gate was proven and the artefact was not. Worth noting in its own right:
**the falsification suite validated this rule against a fixture that does not resemble the file.**

---

## 4. Two ADRs cited as frozen contracts in 25 files do not exist

**What it is.** D-119 and D-120 are cited across the repository as ratified decisions. Neither has
ever been written.

**The evidence.**

```
$ grep -rn "^## D-119\|^## D-120" docs/          # (no output)
$ comm -13 <(defined ADR ids) <(cited ADR ids)
D-008 D-013 D-019 D-021 D-025 D-026 D-027 D-028 D-029 D-038 D-043 D-044 D-099 D-119 D-120 P-002 P-003
$ # D-120 cited in 25 files; D-119 in 3; P-002 in 7; P-003 in 5
```

D-120 is not a passing mention. It is load-bearing:

- `docs/architecture.md:55` — *"**Exit codes (D-120, K.8 frozen contract):** `0` migrated and
  servable · `2` could not migrate · `3` migrated and NOT yet servable"*
- `src/app/workflows/build.py:25` — *"Exit codes mirror `schema.py`'s frozen D-120 contract"*;
  also `src/app/clients/epoch_board.py:162`
- `tests/unit/test_roster_window.py:416` — *"D-120: CLI exit codes are a K.8 frozen contract, so the
  SET is pinned"*; also `test_build.py:264`, `test_epoch_board.py:270`
- `docs/plans/m7-wave-1-close.md:82` and `m8-wave-1-close.md:66` — *"Frozen surfaces untouched: …
  `schema migrate` exit codes (D-120)"*, i.e. a wave-close gate citing a nonexistent ADR
- `docs/plans/m9-plan.md:115`, `m10-plan.md:130`, `m11-plan.md:144` — named as an invariant to protect
- `docs/closure-report-m6.md:189`, `docs/EXPERIENCE.md:279` and
  `docs/retrospectives/m6-retrospective.md:64` all state *"7 ADRs (D-113..D-120) ratified"*. Five
  exist. **Three closure-grade records carry a false count.**

D-119's intended text is still sitting in `docs/plans/m6-plan.md:201` — *"D-119 — `equivalent_plans`
carries labelled groups … written at CLOSURE alongside D-116"* — and closure came and went.

Nothing checks this. `check_records.py` validates frontmatter, refs between *record files*,
supersession cycles and propagation — it has no rule that resolves a `D-NNN` citation to a heading.
`make check` and `make gate`'s conformance legs both pass.

**A second-order consequence worth naming.** Because D-120 does not exist, the exit-code convention
it supposedly freezes has no single definition, and it has already diverged. `schema.py`/`build.py`
use `3 = built but not servable`; `src/app/workflows/refresh.py:77` uses `EXIT_REFUSED = 3` for
*"the candidate is WORSE than what is being served"*, and `refresh.py:67` uses `1 = unchanged,
success` where `recommend` uses `1 = no model fits`. Nine `__main__` modules hand-roll the contract;
only `refresh.py` has named constants, and they are the ones that differ. `build.py:25`'s claim that
an operator *"learns one convention rather than two"* is already false. The M7 review saw the shape
coming — `docs/reviews/m7-wave-1-review.md:323`: *"D-120 exit-code mirror (0/2/3) — met in the
module, broken at the caller."*

**What it costs today.** The documented reversal mechanism ("mark old `superseded by D-NNN`") is
unavailable for a contract three tests treat as frozen.

**What it costs in six months.** Every milestone adds citations. `m11-plan.md` already names D-120 as
an invariant. The longer it is cited, the more expensive it is to discover that the thing everyone
was protecting was never written down.

**Smallest change.** (1) Write D-119 and D-120 from the shipped behaviour — D-119's text exists at
`m6-plan.md:201`, D-120's at `architecture.md:55` — and mark both *"recorded retroactively at M12
from shipped behaviour; the decision was made at M6-W3 and the record was not."* (2) Add one rule to
`check_records.py`: every `D-NNN`/`P-NNN` cited in a governed record resolves to a heading in
`docs/decisions.md`. That is roughly fifteen lines and it would have caught this at M6 closure. The
other 15 phantom ids are almost certainly inherited pipeline references and the same rule will
classify them.

---

## 5. The warning ledger's format has outgrown its content

**What it is.** 75 rows, and it is the right instrument. The problem is that it is a GFM table
holding essays.

**The evidence.**

```
$ wc -l -c docs/warnings.ledger.md       121   126816
$ awk '{print length}' … | sort -rn | head -3     4753  4708  4667
```

- **121 lines, 126,816 bytes.** Mean 1,676 characters per row; the largest cell is 4,753 characters.
- **87.7% of the file (111 KB) is the single `reason` column.** Nothing machine-readable lives there.
- Three rows (W-017, W-023, W-026) contain raw newlines, which terminates a GFM table. Line 80 is
  blank, which **splits the file into two tables** — rows W-035..W-075 (41 rows, 55% of the ledger)
  render header-less in any markdown viewer. `check_records.py:696` matches line-by-line on a leading
  `|` and never sees it.
- Row order is neither id-sorted nor date-sorted.
- **18 of the 28 non-FIXED rows carry a status cell that contradicts their own body** — e.g. W-040 at
  `:86` is `ESCALATED` and its text says `**RESOLVED 2026-08-20`. W-013, W-016, W-020, W-028, W-029,
  W-019, W-018, W-002, W-005, W-008, W-009, W-010, W-011, W-042, W-043, W-044, W-048 likewise.
- **Of the 10 genuinely open rows, 6 have an owning milestone that has already closed.** W-030 and
  W-031 (`:31-32`) are assigned *"M8 go-live"* and M8, M9, M10 and M11 have all closed — four
  milestones overdue. W-058 (`:104`) says of itself *"it must not survive this close the way W-037
  survived M9's."* It survived M11's.
- 51 of 75 rows have zero inbound references. Six rows share ~500 characters of identical copy-pasted
  boilerplate. Three clusters describe one underlying fact each (W-016/W-018/W-020 are one control
  failing three times; W-030/W-031/W-054 are all *"nothing has ever been deployed off 127.0.0.1"*).

**What it costs today.** The ledger is an excellent historical record and an unusable worklist. The
ten open rows cannot be found without reading 126 KB, and six of them are overdue with nothing saying
so.

**What it costs in six months.** M11 added 20 rows. At that rate this is a 250 KB single-column
document by M15, and the six-overdue-of-ten ratio is the leading indicator: rows are being written
faster than they can be dispositioned, and no gate measures the gap.

**Smallest change.** Do not restructure it. Add **one column** — `due` (an owning milestone as a bare
token) — and **one gate rule**: a non-FIXED row whose `due` milestone has closed is a finding. That
plus the `control` column from §3 makes both `C2a` and `C2b` reachable and turns 126 KB of prose into
a ten-row worklist. Fix the blank line at `:80` while you are there.

---

## 6. The governance corpus is 2.4× the product, and 39% of `src/` is prose

**What it is.** Not a criticism of any single document. A measurement of what a new engineer inherits.

**The evidence.**

| | lines |
|---|---|
| `src/` (Python engine) | 8,896 |
| `ios/` shipping + test Swift | 2,166 |
| `tests/` (Python) | 16,270 |
| `scripts/` + `conformance/` (governance tooling) | 4,216 |
| **`docs/*.md`** | **26,081** |
| root `*.md` | 1,133 |

Within `docs/`: `docs/reviews/` is 12,143 lines across 47 files — **larger than the entire engine**.
`docs/plans/` is 4,326 across 53 files. Within `src/`, measured by AST:

```
TOTAL src lines 8896  code 5450 (61%)  docstring 1401 (16%)  comment 948 (11%)
src/app/adapter/main.py     1132 lines, 41% prose
src/app/workflows/refresh.py 865 lines, 40% prose
```

And the mandatory read before any change, per `AGENTS.md` §3.1 plus the files it points at:

```
permission-matrix.md 2,136 w · decisions.md 13,917 w · prd.md 6,645 w
practices.md 3,782 w · AGENTS.md 2,458 w · START_HERE.md 2,770 w · note.txt 947 w
TOTAL 32,655 words ≈ 148 minutes at 220 wpm
plus warnings.ledger 19,994 w + playbook-seeds 18,790 w + EXPERIENCE 6,676 w
```

**≈78,000 words, roughly six hours, before the first line of code.** `AGENTS.md` is 156 lines against
its own stated cap of *"≤80 target, ≤150 hard cap"*.

I want to be careful here, because **most of this prose is genuinely load-bearing and I would not
delete it.** `src/app/workflows/serialize.py` is 68 lines of which 62% is a docstring, and that
docstring is why nobody will ever re-introduce the hand-written mirror it replaced. That is prose
doing work. But it is also unverified: the sentences in `main.py` and `refresh.py` that describe
invariants ("it RESOLVES SYMLINKS, and that is a property to read rather than discover",
`schema.py:400`) are boundaries enforced by prose. §4 above is what happens when prose is the only
enforcement.

The navigability cost is concrete and I measured it: `docs/decisions.md` is 1,389 lines with **no
index**, and its own *"Append new ADRs in sequence"* footer sits mid-file at `:1115` with seven ADRs
appended after it. Asked which ADRs govern `src/app/workflows/recommend.py`, grepping the filename
returns three governing ADRs, one active false positive (D-102 at `:279`, which refers to the
*spike's* `recommend.py` and says the opposite of what a skimmer concludes), and misses eight — the
real set is D-104, D-105, D-109, D-110, D-111, D-112, D-115, D-118, D-122, D-125, D-134, plus the
missing D-119. The module's own docstring names two of them.

**What it costs today.** One-off onboarding cost, paid by an owner who already knows everything.

**What it costs in six months.** It grows monotonically — every milestone adds a closure report, a
retrospective, 4-5 wave records, 3-6 reviews and ~15 ADR/ledger entries, and nothing is ever removed
(correctly — they are append-only). The risk is not the volume, it is that **the read order in
`AGENTS.md` §3.1 will stop being followed**, and when it stops being followed the prose-enforced
boundaries stop being enforced, silently, because no gate reads prose.

**Smallest change.** Two cheap things. (1) A **module → ADR map** at the top of `docs/decisions.md`,
generated rather than written — thirty lines of script over the `D-NNN` citations already in each
module's docstring, run in `make check` so it cannot rot. That turns a six-hour read into a targeted
one and it is the single highest-leverage document this repository does not have. (2) At the next
closure, run the AGENTS.md diet honestly against its own 150-line cap; being 6 lines over is trivial,
but the cap exists because the file stops being read when it is long, and it is the file every seat
starts from.

---

## 7. `board_measurement.py` — 616 lines the project's own gate says to delete, wired into the REQ trace

**What it is.** The largest coverage hole and the clearest piece of dead weight.

**The evidence.** From `coverage.json`:

```
  40.9%  stmts=304 missing=165  src/app/workflows/board_measurement.py
  63.1%  stmts=129 missing= 32  src/app/workflows/rank.py
  (next lowest is 76.8%)
```

`scripts/coverage_floor.py:33-38` exempts it, and the exemption text says: *"A replayable one-off
comparison … Nothing in the serving or build path imports it. **It is a candidate for deletion under
the schema-narrowness rule rather than a candidate for tests.**"* That is correct and it has been
true since M5. Nothing imports it outside `tests/unit/test_m5_board_measurement.py` and one
`inspect.getsource` call at `tests/unit/test_epoch_staleness.py:108`.

But it cannot simply be deleted, because `docs/prd.md:334` and `:336` cite
`test_m5_board_measurement.py` as the citing test for **REQ-SUB-007** and **REQ-REC-012**. A one-off
measurement script became load-bearing on the requirement trace. It is also 616 lines at **3% prose**
— the lowest documentation density in `src/` by a factor of five, in a repository averaging 39% — and
it holds the longest single function outside `subscribe.py`. If there is one module here only its
author could safely change, this is it.

Also worth noting: the exemption removes it from the floor, so it can grow without limit and no gate
will notice.

**What it costs today.** 7% of the engine's line count, a permanently exempted gate, and a false
impression of the coverage number.

**What it costs in six months.** It will still be there, still exempt, still cited by two REQ rows,
and the person who could safely delete it will have less context than they have now.

**Smallest change.** Delete the module; re-point REQ-SUB-007 and REQ-REC-012 at the evidence the
board measurement produced (`docs/reviews/m5-w1-board-measurement.md`, which is the artefact the
requirement actually needs) plus `test_deepswe_workflow.py`, which already co-cites REQ-SUB-007; drop
the exemption from `coverage_floor.py`. One wave, well under 200 net lines, and it removes a
permanent exemption rather than adding one.

---

## 8. Three cheaper items, grouped

**(a) 154 unclosed SQLite connections in the test run.** `grep -c "unclosed database"` on the
`make check` log returns **154**, across 24 test files (top: `test_recommend_assistant.py` 18,
`test_subscribe.py` 14, `test_schema.py` 14). The production code closes properly — every
`sqlite3.connect` in `src/` has a matching `close()` in a `finally`. The leak is at the seam:
`src/app/workflows/schema.py:412` (`open_readonly`) and `:417` (`connect`) return bare connections
with no context-manager form, so every caller must remember. Tests mostly do not.
*Cost today:* 151 warnings of noise that make a real new warning invisible. *In six months:* the
warning count keeps climbing and nobody reads it — the same shape as the red CI in §2. *Smallest
change:* give `schema.connect`/`open_readonly` a `@contextlib.contextmanager` sibling and use it in
new tests; do not retrofit 24 files.

**(b) 806 lines of shell and a 14 KB `runner`, with no linter.** Already ledgered as W-074 and
escalated to M12 as a gate-definition change (owner's call under AGENTS.md §3), so I only add the
measurement: `grep -rn shellcheck Makefile scripts/ .github/ .pre-commit-config.yaml` returns nothing,
and `runner` is the command `note.txt:9` tells every developer to use. M11 shipped three shell
defects; `Makefile:124-136` documents a `swift test | tail -3` pipe that made a gate unable to fail.
`brew install shellcheck` plus one Make target is the whole fix.

**(c) The product's actual data lives on one laptop's Desktop.** `note.txt:89-91` names
`/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/epoch_data` — 1.9 MB of CSVs, outside
the repo, outside git, outside CI — as *"required by `--epoch-dir` for seven of the nine surfaces to
have any evidence at all."* `advisor.db` is gitignored (`.gitignore:50`). Seven tests skip without
the bundle (`test_epoch_ingest.py:139`, `test_epoch_workflow.py:132`, `test_effort.py:395`,
`test_deepswe_workflow.py:160`, `test_m5_board_measurement.py:30,169`), and five contract tests skip
without network (`RUN_CONTRACT_TESTS=1`). So of the twelve skips in a green `make check`, **all
twelve are the tests that touch the real world** — V3C-44's "contract test vs the real API" is
present and never executed locally. *Smallest change:* commit a small redacted fixture bundle (a
dozen rows per board) so the seven skips become real tests, and leave the network five as they are.

---

## 9. The process itself — what is earning its keep, and what is sediment

The brief asks me to say this plainly, so I will.

### Earning its keep, and I would not touch any of these

- **`make check` at 18.4 seconds.** This is the reason the discipline works at all. A gate that
  costs 18 seconds gets typed a hundred times a day. Protect this number above almost anything else
  in this section.
- **`check_records.py --self-test`.** 18 rejection fixtures plus 11 live probes, every one naming the
  rule it must fire (`probe/D1 fires on a drifted shipped-vs-live validator copy`). This is the best
  piece of engineering in the repository, and it is a *test of a test*. It is why I trust the
  frontmatter contract and do not trust the ledger rules — §3 exists because the fixture did not
  resemble the artefact, not because the harness is weak.
- **Per-FINDING exemptions, never per-leg** (`scripts/conformance_gate.py:14-16`, and the same
  pattern in `coverage_floor.py:14-15`). Including the inverse rule — *an exemption that stops firing
  is also a failure*. This is a genuinely good idea and I have not seen it done this well elsewhere.
- **The per-module coverage floor.** A global 88% concealed a module at 32%. The absolute-rather-
  than-relative floor is the right call for the stated reason (`coverage_floor.py:10-12`).
- **`wave_check.py::review_seat_problems`.** The two-pass, label-independent design is correct, and
  the docstring at `:46-57` is exemplary because it states narrowly what the gate does *not* prove:
  *"It does NOT verify that a review ran in a separate session; no file can show that."* A gate that
  is honest about its ceiling is worth ten that overclaim.
- **`serialize.py`.** One serializer, `asdict`-derived, importing no engine module to avoid a cycle.
  The right answer, and the 501-line parity test derives its expectations from the dataclass rather
  than a hand-written list — a mirror one level up would have had the same defect.
- **`docs/plans/m12-inputs.md` itself.** Written the day the requirements arrived, *"so it cannot be
  remembered selectively later."* That is the discipline paying off in the single place it matters
  most.

### Sediment

- **`make falsify` as a leg of `gate`.** It prints `falsify SKIPPED: this is an installation, not the
  distribution package` and returns 0, every time, forever. The message is well-written and the leg
  is decoration. It costs nothing but it dilutes the meaning of `gate` — and §2 shows that meaning is
  already unreliable.
- **`wave-check-all`: 20 of 40 wave records permanently out of scope.** `make check` reports
  *"20 v5.0 record(s) validated; 20 pre-migration record(s) out of scope (GPF-001)."* GPF-001 is
  correct — a tool may not retroactively invalidate records written before it existed — but the
  *reporting* is not: half the corpus is unchecked and the line reads like a pass. It will read like
  a pass at 20-of-60 too. Say "20 unvalidated by design" rather than "out of scope", or the number
  stops being read.
- **`scripts/journey.py`, 271 lines, called by nothing.** Its only live reference is
  `docs/coverage-by-req.md:33`, where REQ-API-009 is **PARTIAL** because journey.py *"never [ran] over
  a network. W-030."* A verification script for a deploy that has not happened, four milestones after
  it was written. Not wrong to keep; wrong to keep unlabelled. It belongs on `docs/watchlist.md` with
  the other two controls that were removed for exactly this reason (`Makefile:38-46`).
- **The prose density of the wave-close checklist.** 13 rows × ~4 waves × 11 milestones, and
  `docs/plans/` is 4,326 lines. The gate on it is good (§9 above). The *filling* is where the
  friction is, and it is the mechanism that produced ten "WAIVED under PRESSURE" bypasses of K.7 —
  which is the ceremony telling you something, through a counter that cannot hear it (§3).
- **`make smoke-deps` is in neither `check` nor `gate`.** It exists, it works, it is well-argued
  (`Makefile:210-220`), and it runs only at a Stage 4.3 that has never happened. Fine — but it means
  L.8's "configured != working" has been asserted at eleven closures and executed at zero.

### The one process observation I would not have found by reading

`AGENTS.md` §3 (protected base ref) describes operating mode A0.5: *"the OWNER … makes the commits at
EVERY MILESTONE."* Measured:

```
$ git log --format='%an <%ae>' | sort | uniq -c
 105 Claude <noreply@anthropic.com>
  20 GP Agent (Claude Code) <gp-agent@localhost>
  16 Codex <noreply@openai.com>
   1 Umut Can Apaydin <the address you want on commits>     [surname ASCII-folded here for L1]
```

**One commit of 142 has the owner as author, and its email address is an unfilled placeholder.** The
project caught the related problem itself — W-011 escalated twelve M5 commits authored under the
owner's name, and D-117 (`docs/decisions.md:683`) and the owner's 2026-08-22 standing permission moved
agent work onto the distinct `GP Agent` identity, which the last 20 commits use correctly. So the
*practice* has been repaired. What has not been repaired is the **protected base ref**, which still
describes a mode nobody runs, and which every review seat in this council is required by V4C-06 to
read policy from. A seat reading `AGENTS.md` §3 today would conclude the owner commits at milestones.
He does not, by his own ruling, correctly.

Also: `git config --global user.email` is still literally `<the address you want on commits>`. The
owner currently cannot make a correctly-attributed commit without setting it, and V4C-64's whole
argument rests on attribution being real.

*Smallest change:* one paragraph in `AGENTS.md` §3 replacing the A0.5 commit clause with what D-117 +
the 2026-08-22 permission actually establish, and `git config --global user.email <real address>`.

---

## What I did NOT look at

Stated plainly so nobody mistakes this record for a sweep.

- **Correctness of the ranking, pricing, effort or category logic.** Not read for defects. Eleven
  milestones of seats have. Where I touched `recommend.py` it was to mutate strings, not to judge
  arithmetic.
- **Security.** No threat modelling, no review of `validate_startup_config`, CORS, the read-only URI
  construction, the YAML guard, or the redirect/transport handling in `EngineClient.swift`. I read
  `docs/reviews/m11-security-review.md`'s frontmatter only.
- **The nine surfaces' data quality**, the Epoch/Arena/OpenRouter/LiteLLM/SWE-bench/Aider/DeepSWE
  client parsers, and every ingestion path. I measured their coverage and did not read them.
- **The refresh machinery** (`refresh.py`, 865 lines, D-128/D-129/D-130/D-132, `launchd`). I measured
  it and read its exit constants. I did not assess whether the refusal thresholds are right, and
  REQ-RUN-002's two-firings-on-schedule gap is the owner's open item, not mine.
- **Swift beyond structure.** I did not read `Router.swift` (400 lines), `EngineClient.swift` or
  `Models.swift` for correctness — only for what is and is not executed. `ContentView.swift` I
  measured (551 lines) and did not read.
- **The iOS app running.** I did not launch the simulator, run `./runner`, or run
  `scripts/simulator_session.sh` — which `note.txt:14-16` says *"found six defects that eleven
  milestones of gates did not."* That is a gap in this review and the owner should weight it: the
  most productive instrument in this repository is the one I did not use.
- **`make secrets` / `make deps` / `make slopsquat` results.** They ran inside `make gate`; I read the
  exit path, not the findings.
- **CI as it behaves on GitHub.** I read the four workflow files. I did not check which are required
  status checks, and `governance-contract.yml:12` says that is an owner action *"once, outside this
  file"* whose completion I cannot verify locally.
- **`docs/EXPERIENCE.md`, the retrospectives, the handovers, `gp-field-findings.md` and
  `gp-v5.0-field-experience.md`** — 4,000+ lines read only for the specific claims I cite.
- **The 15 phantom ADR ids other than D-119/D-120** (D-008, D-013, D-019, D-021, D-025..D-029, D-038,
  D-043, D-044, D-099, P-002, P-003). I counted them and did not trace them; they are probably
  inherited pipeline references, and the gate proposed in §4 will classify them without anyone
  reading them.
- **Whether the `PostToolUse` hook actually fires.** I established that `make gate` exits 2, that the
  hook is declared, and that its log file has never been written. I did not instrument the harness to
  observe a hook invocation.

---

**Files changed by this review:** this file only. **Tests run:** `make check` (exit 0, 714 passed,
18.4 s), `make gate` (exit 2, 21.6 s, `conformance FAIL: 7 test(s), 2 failing`), `pytest` under a
3-string mutation of `recommend.py` (714 passed — the finding), `make wave-check FILE=README.md`
(correctly FAILS, 4 reasons), `check_records.warning_ledger` against the real ledger (no findings) and
against a synthetic-root copy with column 2 renormalised (C2b fires). **Restorations verified:**
`recommend.py` md5 `4c17631e454a08004b0a4d138bd5069d`; `warnings.ledger.md` md5
`93a3388391dc926cc6360cadfa8776f4`; `git diff --stat` empty. **New ADRs:** none — this seat does not
propose them. **Risks queued:** items 1–4 above, in that order.
