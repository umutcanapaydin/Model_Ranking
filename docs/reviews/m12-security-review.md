---
record_type: review
id: m12-security-review
status: ratified
seat: independent
date: 2026-08-25
---
# M12 Stage 4.0 Security Review - the contract move, and the controls that moved with it

> **Independent seat.** I wrote none of this code. Policy was read from the protected base ref only
> (`git show HEAD:AGENTS.md`, `git show HEAD:.agents/rules/practices.md`,
> `git show HEAD:docs/security-baseline.md`) per V4C-06. Every claim below is measured; where a
> claim rests on running something, the command and its result are named.

## 0. Scope, verified rather than accepted

The range I was handed was `d13c810..HEAD`. I checked it, and **it moved during the review.** At the
start it was five commits ending at `c527d8e`; at the end it was seven, the two new ones being
`96f86cf` (capture) and `5fb5755` (closure report, `note.txt`, Q4 handover). `git diff --name-only
c527d8e..HEAD` returns only `docs/**` and `note.txt`, so **no code entered after `c527d8e`** and the
code surface I reviewed is complete. A second session was writing capture artefacts into the tree
while I read it: `docs/process-log.md`, `docs/EXPERIENCE.md`, `docs/retrospectives/m12-retrospective.md`
and `note.txt` all changed mtime between 18:40 and 18:47 on my clock. **All code evidence in this
record is pinned to `c527d8e`.**

One genuine scope gap, stated because it is not mine to close: **`D-135` itself is in the BASE
commit `d13c810`, not in the range.** W2 classified and deleted disclosures under that ruling, and
the ruling authorising the deletions was therefore outside what I was asked to review. The
deletions are in scope; the licence for them is not. I did not audit D-135's text.

I modified nothing. `md5 -q scripts/check_records.py docs/warnings.ledger.md Makefile` is
byte-identical before and after (`5dc359f14f1b43f6de64494c518bf9f3`,
`fa754e0baa07a07cf6c7f165c36267ae`, `9e02c74885065499d85fff6214da52bd`), and `git status --porcelain`
is clean of any path I touched. All probes ran in a scratch directory outside the repository, against
a **copy** of `advisor.db`.

---

## BLOCKING

### BLOCKING-1 - Three unconditional client crashes reachable from a `/v1` numeric value

`ios/ModelRanking/Engine/Language.swift:169` - `String(Int(double))`
`ios/ModelRanking/Engine/Language.swift:153` - `Int(blendedPerM.rounded())`
`ios/ModelRanking/Engine/Router.swift:511` - `Int(blendedPerM.rounded())`

Swift's `Int.init(_: Double)` **traps** - it is a `fatalError`, not a throw - when the value is
outside `Int64`, infinite, or NaN. `number(_:)` reaches it for any whole-valued `Double`, and every
number in a `why_fact` / `trade_off_fact` flows through it. Nothing between the socket and that line
bounds the range: `JSONValue` (`Models.swift:243-263`) accepts any `Double` the decoder produces, and
`dictionary` (`Models.swift:270-283`) hands it straight to the composition layer.

**Reproduced.** I built an isolated SwiftPM package over unmodified copies of the four Engine
sources and decoded a complete, well-formed `Pick` through the shipping `JSONDecoder` path:

| Input (verbatim JSON field) | Call site in the app | Result |
|---|---|---|
| `"why_fact":{"reason":"cheapest_above_floor","floor":1e19,"unit":"points"}` | `ContentView.swift:570` -> `whySentence` -> `number` | `Fatal error: Double value cannot be converted to Int because the result would be greater than Int.max`, `signal code 5` |
| `"blended_per_m":-1e19` | `ContentView.swift:584` -> `priceInPages` (`Router.swift:511`) | `Fatal error: ... less than Int.min`, `signal code 5` |
| `trade_off_fact` with `behind_by: 1e19` | `ContentView.swift:575` -> `tradeOffSentence` -> `number` | `Fatal error: ... greater than Int.max`, `signal code 5` |

`1e19` and `-1e19` are ordinary JSON numbers. No malformed document is needed, no oversized body, no
nesting. The negative-price path is the nastiest of the three because the guard that gates it,
`perPage < 0.01`, is **satisfied by every negative number**, so a negative `blended_per_m` walks into
the trap by design.

**What it lets through.** A deterministic, unrecoverable kill of the app from a value on the wire.
The engine is unauthenticated and reached over cleartext today (`EngineClient.localDefault` is
`http://127.0.0.1:8080`, D-123), and D-116 puts it on a real host next. Anything that can answer for
the engine - a compromised or misconfigured server, a MITM on a cleartext hop, another process on
the simulator host - has a one-field, one-request denial of the product.

**Why this is BLOCKING and not a robustness nit.** The client already declares a graceful path for
a payload it cannot use: `EngineError.undecodable` says *"The engine's answer was not in a shape this
app understands"*, and `Language.swift:47-49` states the fallback contract explicitly - *"Showing the
English is not a failure; inventing a Turkish sentence for a reason we do not understand would be."*
A trap bypasses both. The code promises degradation and delivers a process abort. `number(_:)`
returning `""` for an out-of-range value - which is exactly what it already does for every other type
it does not recognise - closes all three.

**No test can see this today.** `tests/unit/test_why_facts.py` has six tests, all of them derivation
and presence; `ios/EngineTests/LanguageTests.swift` has none with a hostile value. V3C-74 asks for a
negative test per security invariant, and the invariant "a payload value cannot abort the app" has
none.

### BLOCKING-2 - `L1` fails OPEN on an unbalanced fence, and it is already failing open in this repository

`scripts/check_records.py:881-885`

```
if line.lstrip().startswith("```"):
    fenced = not fenced
    continue
if fenced:
    continue
```

The fenced-block state is a **toggle with no balance check and no reset**. A file containing an odd
number of lines that begin with three backticks leaves `fenced` true for everything after the last
one, and every remaining line is skipped without being read. The rule that keeps this repository
English (V4C-79, an owner directive, AGENTS.md section 5) simply stops.

**Measured against the real tree, not a fixture.** `docs/reviews/m11-wave-1-review.md` has 27
fence-opening lines - an odd count - and **85 of its 347 lines are currently never checked by L1**.
Repository-wide, 1,871 of 67,789 scanned lines (2.8%) are exempted by the fence rule today. That is a
live instance, not a hypothetical.

**Reproduced, seven smuggles, six of them silent.** I ran `check_records.language_rule` over probe
files in a temporary directory:

| Probe | L1 |
|---|---|
| Bare Turkish in prose (control) | **FIRED** |
| Turkish inside an inline code span | SILENT (by design) |
| One unmatched fence, Turkish 3 lines later | **SILENT** |
| Turkish in a fence's info string (the toggle line is `continue`d, so it is never read) | **SILENT** |
| Fence indented inside a list item (`line.lstrip()`), Turkish after | **SILENT** |
| Turkish heading wrapped in backticks | **SILENT** |
| **A `.py` source file: a fence inside a docstring, then a live product string** | **SILENT** |

The last one is the finding. `LANG_SUFFIXES` includes `.py`, and this project's Python files carry
long prose docstrings that routinely contain fenced examples. A module whose docstrings hold an odd
number of fence lines is **exempt from L1 for the remainder of the file**, including its string
literals. My probe file was (shown indented rather than fenced, so that this record does not commit
the very defect it reports - see the note at the end of this section):

    x = 1
    """
    doc
    <three backticks>
    sample
    """
    NOTICE = "<a Turkish product sentence>"

L1 said nothing. D-118's own Mitigation paragraph names L1 as *"the remaining guard"* on product
language and lists `recommend.py`, `subscribe.py`, `categories.py` and their tests as what it covers.
This change silently removes that cover from any of them that acquires an unmatched fence.

**A note on this record's own fences.** The first draft of this section illustrated the probe with a
fenced block containing a nested fence, and the result was that **this record exempted 359 of its own
480 lines from L1** - odd parity, everything after the last toggle unread. I noticed it only because
I ran the parity measurement over the tree with this file in it. That is how cheap the defect is to
commit: a security review reporting the bug reproduced it while writing the report. The block above
is indented instead, and this file's fence count is now even.

**What it lets through.** Non-English user-facing product text committed to `src/`, past the only
mechanical control V4C-79 has, with a green `make check`.

**The process half.** This is a **weakened validation shipped without a probe for its own failure
mode.** `practices.md` names weakened/removed validation as an explicit item of the agent security
pass; V4C-32 requires the self-test to prove the validator is not a no-op; V4C-49 requires the gate
to ship with the rule. The self-test change in this commit (`check_records.py:1064-1073`) updates the
**C2b** fixture and adds nothing for L1 - the L1 probe is still the pre-existing bare-Turkish file,
which proves only the case that was never at risk. There is no probe asserting that a closed fence
re-enables scanning, and none asserting that an unbalanced fence is a finding.

### BLOCKING-3 - All four M12 waves closed K.7 green citing reviews written before the code existed

`docs/plans/m12-wave-1-close.md:34` · `m12-wave-2-close.md:34` · `m12-wave-3-close.md:33` ·
`m12-wave-4-close.md:36`

Every one of the four "Review per tier - V3C-78 / K.7" rows is marked `✅` and cites an **M11 council
record**:

- W1 -> `docs/reviews/m11-council-senior-swe.md`, `m11-council-senior-mobile.md`
- W2 -> `docs/reviews/m11-council-product.md`
- W3 -> `docs/reviews/m11-council-product.md`
- W4 -> `docs/reviews/m11-council-senior-mobile.md`

All of those records carry `date: 2026-08-24`. Every M12 code commit is dated `2026-08-25`
(`git log --format="%h %ad" --date=short d13c810..c527d8e`). The records say so themselves - W1's
row reads *"this wave implements THEIR findings, so the review preceded the code"* and W4's reads
*"its recommendation shaped where the composition lives."*

A review that predates the code did not review the code. K.7 requires fresh eyes on **the wave's
code**; a record naming the defect a wave was built to fix is an input to the wave, not a review of
it. `scripts/wave_check.py::review_seat_problems` passes because it checks exactly two things - the
cited file exists and declares `seat: independent` - and its own docstring is honest that it proves
nothing more. **The gate is working as designed; the rows are using it as designed to certify
something it does not check.**

**What it lets through.** 2,828 inserted lines across a contract move, a new composition layer and
551 previously unexecuted SwiftUI lines, closed across four waves with **no independent read of the
code**. This Stage 4.0 pass is the first one, and it found BLOCKING-1 and BLOCKING-2 by reading and
running that code.

**And the bypass is not ledgered.** V4C-13 requires a control skipped under pressure to be recorded
- the row goes WAIVED, which forces it to name a ledger id, which puts it in front of the owner. All
four rows are `✅`. Compounding it, C2b's only countable group is `K.7`, and it is discharged (see
MAJOR-1), so the 3x trigger cannot fire on these four either.

---

## MAJOR

### MAJOR-1 - The C2b rekey did not make the counter able to count

`scripts/check_records.py:746` (grouping key) and `:757` (discharge)

Two independent holes, both measured against the real `docs/warnings.ledger.md`:

**(a) 19 of 22 ACCEPTED rows are invisible to the counter.** The group key is
`CONTROL_ID.findall(cells[3])` - the free-text **path** column. Nothing requires a control identifier
there, and 19 rows name a file or a symbol instead (`W-002` -> `src/app/workflows/subscribe.py:286`,
`W-019` -> `` `scripts/check_records.py` rule `L1` ``, `W-028`, `W-029`, `W-035`, `W-036`, ...). Those
rows are counted **for nothing**. The counter sees three rows in total, and they are the same three
in both of its two groups (`K.7` and `V3C-78`: `W-016`, `W-018`, `W-020`). W-078's own text says K.7
*"had been bypassed ten times"* - the rekeyed counter can see three of them.

**(b) Any `D-nnn` or `P-nnn` anywhere in any one row's reason discharges the whole control,
permanently.** Reproduced with fixtures:

| Fixture | C2b |
|---|---|
| 3x `K.7`, no ADR named (control) | **FIRES** |
| 3x `K.7`, one row's prose merely mentions an **unrelated** `D-104` | SILENT |
| 13x `K.7`, one old row cites `D-133`, twelve later bypasses | SILENT |
| 3x the same bypass, path column names a file rather than a control | SILENT |
| 3x `K.7` spelled `K.7` / `k.7` / `K7` | SILENT |

`re.search(r"\b[DP]-\d{3}\b", why)` cannot tell "the decision that reviewed this control" from "an
ADR this row happens to mention", and ledger reasons in this repository cite ADRs constantly. There
is no re-arm: once one row discharges a control, the fourth, tenth and twentieth acceptance are
silent forever, which is the opposite of what V4C-13 asks for.

**Is it a hole or an acceptable cost?** The discharge design is defensible and I would keep it. The
implementation is not: it should require the ADR to be named on **the row being counted** (or in a
dedicated column), and it should re-arm at every subsequent `ACCEPT_LIMIT`. Hole (a) is not a design
question at all - a counter whose input is an unschema'd free-text column is the same defect W-078
was written to fix, one column to the left. `tests/unit/test_c2b_counter.py` has eight tests and none
of them covers (a), the unrelated-ADR discharge, or the missing re-arm.

**What it lets through.** V4C-13's 3x control-review trigger, still unable to fire on 86% of the
ledger it reads.

### MAJOR-2 - `/v1` prose changed on 116 sites; the records say it did not

Measured by extracting `d13c810` with `git archive` into a scratch tree, pointing both trees at the
**same copy** of `advisor.db`, and calling every endpoint through `fastapi.testclient`: 40 task/budget
combinations plus `/v1/categories`, `/v1/budgets`, `/v1/sources`, `/health`.

**The shape moved exactly once and additively, and that part is clean:**

| Level | Keys added | Keys removed |
|---|---|---|
| envelope | none | none |
| answer | none | none |
| **pick** | `why_fact`, `trade_off_fact` | none |
| ranking row | none | none |
| `/v1/budgets`, `/v1/sources`, `/health` | byte-identical | - |

All status codes identical. **D-115 / D-125 / D-136 hold on shape.**

**The values did not hold.** 116 existing-field differences: `ordering_note` x40, `title` x25,
`trade_off` x27, `why` x24. The titles and the ordering note are deliberate, recorded W2 product
changes (W-080, and the `categories.py` comment block). The trade-off changes are not recorded
anywhere I can find:

- **26 of the 27 `trade_off` changes are `best_value` picks**, and they changed **shape**, not
  precision. Before: `1.5 points below the leader, and 73% cheaper.` After: `1.5 points below the
  leader, but 4x cheaper.` The old `best_value` sentence was hardcoded to a percentage; routing it
  through `trade_off_sentence` re-decides percentage-vs-multiple by ratio, so almost every
  `best_value` sentence in the product is now a different sentence.
- D-136 says *"The English prose stays and is derived from the same values ... so there is one source
  of truth and no consumer breaks"*, and `docs/plans/m12-wave-4-close.md:18-19` says the prose is
  *"DERIVED, not parallel."* Both are true of the mechanism and false of the outcome: the prose did
  not stay.

**What it lets through.** A recorded contract move whose record understates what it moved. D-115
exists so a consumer is not broken for the server's convenience; a consumer keying on `"% cheaper"`
in `best_value` is broken by this milestone, and no ADR or ledger row says so. The fix is a paragraph
in D-136, not a code change - but the paragraph is load-bearing, because the next reader will use
this ADR as the precedent for what "additive" permits.

### MAJOR-3 - The frozen key set that enforces D-115 stops at the answer level

`tests/unit/test_api_v1.py:187-189`, allowlists at `:41-69`

The comment above those allowlists (`:33-37`) says: *"The payload's key set is FROZEN. A new key is a
test failure whatever it is called."* It is not. `ENVELOPE_KEYS` and `ANSWER_KEYS` are asserted;
**pick keys (24 of them) and ranking-row keys (11) are not asserted anywhere.**

**Reproduced.** I took a real `/v1/recommendations?task=coding` body, injected `"primary": true`,
`"display_order": 0` and `"internal_debug_sql": "SELECT * FROM scores"` into **every pick** and
`"authoritative": true` into **every ranking row**, then ran the two frozen-set assertions verbatim.
Both passed.

Those are not arbitrary names - `primary`, `display_order` and `authoritative` are three of the four
literal keys the comment's own history says killed versions 1 and 2 of this control. Ruling A's Trap
2 ("both silently becomes both, but one first") is unguarded at exactly the level where a pick lives.

This is the same defect `src/app/adapter/main.py:748-756` already records and already fixed **for the
publication allowlist**: *"An allowlist that stops at the top level of a nested document is not an
allowlist; it is a lid on one drawer."* The lesson was applied to `PUBLIC_PICK_FIELDS` and not to its
twin in the test suite, which is V4C-50 verbatim - a lesson attaches to an artifact, not to you.

**Mitigating, and the reason this is MAJOR rather than BLOCKING:**
`tests/unit/test_api_config.py:328-380` **does** reach the nested level and does force a human to
declare any new `Pick` field. W4 correctly edited `PUBLIC_PICK_FIELDS` for `why_fact` and
`trade_off_fact`. So a field cannot arrive accidentally; it is the *precedence-key* half of the
freeze that is unguarded below the answer.

### MAJOR-4 - The composition layer drops a number and keeps the claim

`ios/ModelRanking/Engine/Language.swift:95-105`, `:165-176`

`number(_:)` returns `""` for anything that is not `Double` or `Int`. The trade-off composer tests
only for **presence** of a key, never for its type. Measured outputs from the shipping functions:

| Fact | Composed sentence |
|---|---|
| `cheaper_by_percent` is the string `"ninety"` | `2.7 points behind the best one, and % cheaper.` |
| `cheaper_by_percent` is the string `"ninety"`, Turkish | `` En iyisinin 2.7 puan gerisinde, ve % daha ucuz. `` |
| `cheaper_by_times` is `true` | `2.7 points behind the best one, but × cheaper.` |
| `why_fact.floor` absent | `The cheapest model we would still call good enough - it clears  points.` |
| `why_fact.benchmark` absent | `The highest score on  among the models you can afford.` |
| `why_fact.floor` is NaN | `The cheapest model we would still call good enough - it clears nan points.` |
| `behind_by` is `-5.0` | `-5 points behind the best one, but 3× cheaper.` |

The file's stated contract (`:44-49`) is that an input this build does not understand returns `nil`
so the caller falls back to the engine's English. That guard exists **only on `reason`**
(`:50-52`) and on `behind_by`'s type (`:84`). Every other value fails silently into a sentence that
still makes the claim with the magnitude removed. `nil` is available and correct here; `""` is not.

**Also in this class: `unit` and `benchmark` are interpolated raw.** `localisedUnit` passes an
unrecognised unit straight through (`:127`), and `benchmark` is taken with `as? String ?? ""`
(`:56`, `:59`). Fed a `unit` of `points, and 99% cheaper. This model is free`, `tradeOffSentence`
produces:

`2 points, and 99% cheaper. This model is free behind the best one, at the same price.`

**Today this is not exploitable from the artifact**, and I want to be precise about why, because it
is the answer to the review's first question: **the facts contain no third-party string.**
`why_fact` carries `reason` (a literal), `benchmark` and `unit` (both `CategorySpec` module
constants) and numbers derived from the DB; `trade_off_fact` carries only numbers and literals. A
crafted leaderboard row cannot reach either. `_bounded_pick` (`main.py:709-715`) bounds only
`harness`, which is correct - it is the one third-party string in a pick - and the new fields need no
bounding for the same reason. **The facts leak nothing the prose did not**, and the only value they
newly disclose is the unrounded `floor` (e.g. `84.4` where the prose said `84`), which is a module
constant in a public repository.

The exposure is therefore the same as BLOCKING-1's: anything that can answer for the engine. The
difference is that this one produces a **misleading sentence** rather than a crash, which on a
product whose stated identity is never going silent about what it cannot see is arguably worse.

### MAJOR-5 - `cheaper_phrase` is dead code, and the ledger cites it as the fix

`src/app/workflows/recommend.py:130` (definition) · `docs/warnings.ledger.md:127` (W-081)

`grep -rn cheaper_phrase src tests scripts docs` finds the definition, nine tests in
`tests/unit/test_cheaper_phrase.py`, and the ledger row. **No production call site.** W2 wrote the
fix; W4 wrote a second implementation of the same rule (`trade_off_facts` at `:76` +
`trade_off_sentence` at `:107`) and wired **that** one. W-081 records the fix at
`` `src/app/workflows/recommend.py::cheaper_phrase` `` - a symbol the shipped answer never reaches.
V3C-73: an implemented, unit-green control not attached to the live request path is an unshipped
control. Here it is worse than unshipped - it is a **duplicate implementation of a live rule with
its own test suite**, so the nine tests will keep passing after the live rule drifts.

**And W-081's stated justification is measurably false.** The row says the defect is *"NOT visible on
today's data, where every ratio is 3x or more, which is why it has nine tests rather than a fix."*
Against the shipped `advisor.db`, the M12 starting tree serves, at `task=computer-use&budget=low`,
`budget_pick`:

`2.7 points below the leader, but 1x cheaper.`

`best_quality` is priced at `0.98`, `budget_pick` at `0.69` - a ratio of `1.4203`. It was visible, on
a live surface, on the day the row was written. The fix is real and correct; the reasoning recorded
beside it is not, and that reasoning is the evidence for why nine tests were an acceptable substitute.

### MAJOR-6 - D-118 is not superseded, and M12 shipped the thing its Revisit-when names

`docs/decisions.md:725` (D-118) · `:1485` (D-136) · `ios/ModelRanking/Engine/Language.swift`

D-118 is `Status: ratified` and says *"every user-facing string the product emits ... is English."*
Its Revisit-when reads: *"the product acquires a real localization layer, at which point this ADR is
superseded rather than amended."* M12-W4 shipped exactly that - a localisation layer, a language
switch, and a Turkish rendering of titles, surfaces, budgets, pick badges, placeholders, scales,
prices and units.

`grep -n superseded docs/decisions.md` shows **no supersession marker on D-118**, and D-136 does not
mention D-118 anywhere in its body. AGENTS.md section 3.4 and practices.md seed B.2 both require the
old ADR to be marked. As the records stand, a ratified, unsuperseded ADR forbids the product surface
this milestone shipped, and the ADR that authorised it does not acknowledge it. This is the
record-contradicts-code class, in the decision log itself.

(D-118's Payload-strings clause is separately still true and still enforced - `/v1` is English, and
D-136's architecture is precisely what keeps it that way. It is the "product emits" clause that has
been overtaken.)

### MAJOR-7 - The Turkish placeholder invites a question the router cannot read

`ios/ModelRanking/Engine/Router.swift:119` · `ios/ModelRanking/Engine/Language.swift:189-191`

`UIText.askPlaceholder(.turkish)` now asks, in Turkish, `Yapay zekânın ne yapmasını istiyorsun?`
The router that classifies the answer is hard-pinned:

`guard let embedding = NLContextualEmbedding(language: .english)`

and every vector is built with `embeddingResult(for: string, language: .english)`. A Turkish question
is embedded as English. The outcome is either `nil` - which is safe, the reader drops to the chips -
or a centred cosine above `SimilarityRouter.defaultFloor` (`0.15`) that is noise, in which case the
app routes the reader to a surface on no evidence and, per `ContentView.swift:129`, does **not** mark
it `unmeasured`.

REQ-RTR-005 and the `defaultFloor` docstring exist specifically so that *"routing an unmeasured
question to `assistant` silently"* cannot happen. No test in `ios/EngineTests/` puts a Turkish
question through `route(_:within:)` - `LanguageTests.swift` covers composition and chrome only. D-136
carefully records what it does **not** localise (the notices); the router is not in that list, and
it should be, or the Turkish placeholder should not invite free text until it is.

---

## MINOR

- **MINOR-1 - `subscribe.py` still rounds the claim.** `src/app/workflows/subscribe.py:547,563,566`
  print `{spec.min_quality:.0f}` and `{spec.value_window:.0f}`. W-084's finding - *"printing `84`
  states a bar the engine does not apply"* - was applied to `recommend.py` (`:g`) and not here. On
  the same `CategorySpec` constants, the CLI now says `84` where the API says `84.4`, on **6 of 9
  surfaces** (`everyday` 149.9->`150`, `expert` 83.6->`84`, `mathematics` 84.4->`84`, `computer-use`
  53.4->`53`, `abstract` 72.8->`73`, `web-dev` 1478.9->`1479`). One product, two bars.

- **MINOR-2 - L1's inline-code exemption has no scope limit.** `check_records.py:83,886` strips every
  `` `...` `` span before checking, on every line of every scanned file - including headings and the
  Evidence cells of wave-close records, where this project habitually puts everything in backticks. A
  whole record's substance can be non-English and pass. The narrowing's stated motive (quoting a
  defect verbatim) is sound; the implementation grants it everywhere rather than in the records that
  need it. **It is also inconsistent in the other direction:** the regex only understands a
  single-backtick span, so CommonMark's double-backtick delimiter - the form you must use when the
  quoted text itself contains a backtick - is stripped as two empty spans and the content between
  them is scanned as prose. I hit this while writing MAJOR-7 of this record: a correctly-formed
  double-backtick quotation of a Turkish product string produced an L1 finding on line 394. So the
  rule under-enforces on an unbalanced fence and over-enforces on a legitimate quotation, which is
  the pairing that gets a gate switched off.

- **MINOR-3 - `.swift` is not in `LANG_SUFFIXES`.** `check_records.py:789`. L1 never scanned the
  client, so the wave that actually introduced Turkish into the repository was never at risk from L1
  and did not need the narrowing at all. Worth stating because D-118 claims L1 *"now guards the whole
  product surface instead of stopping at its edge"*, and the product surface is now half Swift.

- **MINOR-4 - `TR_CHARS` is a diacritic detector, not a language detector.**
  `check_records.py:787`. ASCII-only Turkish is invisible. D-118's corrected Mitigation paragraph
  already records this honestly (W-019); it is listed here only because MINOR-2 and BLOCKING-2 widen
  the same blind spot rather than narrow it.

- **MINOR-5 - `number(_:)` renders NaN as `nan` and negatives as written.** Same site as
  BLOCKING-1 (`Language.swift:165-176`). `it clears nan points` and `-5 points behind the best one`
  are both reachable. Fixing BLOCKING-1 with a range-and-finiteness guard closes these in the same
  line.

- **MINOR-6 - The review range is a moving target.** See section 0. Two commits landed during this
  review. Both were documentation, so nothing was missed - but a Stage 4.0 pass cannot certify a tree
  another session is still writing to, and the previous milestone's seat raised the same class of
  problem.

---

## What checks out, with the evidence I ran

| Invariant / control | How I checked | Verdict |
|---|---|---|
| **D-104** - no LLM in the scoring path | `git diff d13c810..c527d8e` grepped for `openai\|anthropic\|llm\|prompt\|completion\|FoundationModels\|SystemLanguageModel` on added lines: every hit is a model NAME in test data or the agent identity in a governance record. The new composition layer is a `switch` over four `PickReason` cases and a static string table - deterministic code, no model. D-136's rationale for moving translation to the client is itself a D-104 argument. | **HOLDS** |
| **D-115 / D-125 / D-136** - the payload moved ONCE, additively | Old tree extracted with `git archive d13c810`, both trees run against the same copy of `advisor.db` through `fastapi.testclient`, 44 responses compared key-by-key. Exactly two keys added, both at `pick`, both named in `PUBLIC_PICK_FIELDS` and in D-136. Envelope, answer, ranking-row and `/v1/budgets` key sets and values byte-identical; all status codes identical. | **HOLDS on shape** (see MAJOR-2 for values) |
| **D-116** - engine ships as a service | `docs/decisions.md:632`. `fly.toml` and `Dockerfile` untouched by this range (`git diff --stat d13c810..HEAD` lists neither). `EngineClient.swift:6-10` keeps the base URL as configuration and documents D-123's localhost hold. | **HOLDS** |
| **D-127** - the ids did not move while the titles did | `/v1/categories` diffed old vs new: 9 ids, **identical, in order**; 5 titles changed (`assistant`, `everyday`, `expert`, `computer-use`, `abstract`); no non-title field changed on any category. `UIText.surface(id:engineTitle:)` (`Language.swift:246-262`) keys the Turkish names on the **id**, with an English fallback for an unknown id, which is the right way round. | **HOLDS** |
| **INV-23** - read-only URIs derived, never concatenated | `src/app/workflows/schema.py:392` and `src/app/adapter/main.py:302` are untouched by this range (`git diff --stat` lists neither `schema.py` nor any change to `open_readonly`). The client half is derived too: `EngineClient.swift:193-197` builds every request with `URLComponents` + `URLQueryItem`. | **HOLDS** |
| **`recovery` vs `diagnostic` (W2 split)** | Read `EngineClient.swift:41-113` line by line and traced the render site. `recovery` returns generic sentences for `unreachable`, `timedOut`, `insecureTransport`, `offline` and `undecodable`, and `nil` for `refused`. Every host, path, `make run` instruction, `NSAllowsArbitraryLoads` warning and `/v1` contract reference is in `diagnostic`. `ContentView.swift:322-324` renders **only** `errorDescription` and `recovery`; `diagnostic` has no view. The one detail that still reaches a user string is `refused`'s `message`, which is the **engine's** words - and the engine's `_error` (`main.py:562-564`) emits four fixed messages plus two that echo the caller's own `task`/`budget` through `_echo`, bounded at 40 chars (`main.py:557-559`), with an explicit comment at `main.py:1124` refusing to name the database path. **No host, path or internal detail reaches an end-user string.** | **CLEAN** |
| **Third-party text into the new fields** | Enumerated every key the engine puts in `why_fact` / `trade_off_fact`: `reason` (literal), `benchmark` and `unit` (`CategorySpec` constants), `score`/`floor`/`window`/`behind_by`/`cheaper_by_*` (numbers). No DB-derived string. A crafted leaderboard row cannot reach either field. | **CLEAN** |
| **Mutating routes / CORS** | `grep -n "@app.post\|@app.put\|@app.patch\|@app.delete"` on `main.py`: none. `allow_methods=["GET"]` at `main.py:513`; the CORS block is untouched by this range and still refuses a wildcard outright. V3C-12 is vacuous here and V3C-13 holds. | **HOLDS** |
| **V3C-51** - fail the process on bad security config | Observed, not read: my first payload run aborted with `ConfigError: APP_BUILD is unset - /health cannot say which code is live`. The startup validator fires. | **HOLDS** |
| **W1's `make gate` repair** | `make gate` -> **exit 0** on a clean tree, twice. `gate PASS: lint typecheck test records install secrets deps slopsquat`. `gitleaks`: `no leaks found` over 57 MB. `pip_audit`: no known vulnerabilities. `slopsquat`: 15 deps, 0 suspect. | **FIXED** |
| **W1's Turkish case-folding repair** | `Router.swift:425-434`: `matchesFilter` pins `Locale(identifier: "en_US_POSIX")` and passes it to `range(of:options:range:locale:)`. I swept the Engine and `ContentView` for every other locale-sensitive call: `lowercased()` at `Router.swift:117` and `:463`, `uppercased()` at `Language.swift:225`, `capitalized` at `Router.swift:608`. **All four are correct** - Swift's no-argument `lowercased()`/`uppercased()`/`capitalized` use the Unicode default mapping and are not locale-dependent; only the `(with: Locale)` overloads are. The comment at `Router.swift:422-424` claiming those sites were checked and deliberately left is accurate. | **FIXED, and the claim beside it is true** |
| **W1's phantom-ADR repair** | `tests/unit/test_adr_citations.py` ships three tests: cited-ADR existence with **word-boundary** matching (which is what stopped W-077's false positive on `P-002` inside `REQ-APP-002`), reserved-band integrity, and no silent gaps in the project band. D-119 and D-120 exist and are dated honestly rather than backdated. | **FIXED** |
| **W3's budget picker** | `/v1/budgets` payload is byte-identical old vs new, so W3 changed the client only. The cap is enforced **server-side** - `eligible_count` and the exclusions are computed by the engine from `BUDGETS`, and the client sends an id, not a number. The picker is a filter, not an authorization boundary, so V3C-12 does not apply; there is nothing here a hostile client could bypass that it could not simply ask for. `BudgetOption.blendedCapPerM` is `Double?` and `Models.swift:229-232` documents that `unlimited` is the **absence** of a cap rather than a large one. | **CLEAN** |
| **Whole suite, pinned to this tree** | `make check` -> exit 0. `python -m pytest -q` -> **781 passed, 12 skipped**. `cd ios && swift test` -> **121 tests**, all passing. `scripts/check_records.py` -> PASS. `wave_check_all` -> PASS, 24 v5.0 records. `conformance_gate` -> PASS, 6 findings, all exempted and all still firing. | **GREEN** |

**On the deliberate design choices I was asked to judge:** the fallback architecture in
`Language.swift` is right - composing from a fact and falling back to the engine's English on an
unknown `reason`, rather than inventing a sentence, is the correct direction, and
`testAnUnknownReasonComposesNothingRatherThanGuessing` proves it. Keying the Turkish surface names on
the **id** rather than the title (D-127) is right, and it is what makes W2's five renames safe.
Leaving `elo` and `ECI` untranslated, and pinning the number format to POSIX in both languages, are
both correct and both defended in the record. Refusing to localise the notices, **and saying so in
D-136's scope paragraph rather than letting a Turkish reader discover it**, is the behaviour this
project is good at. None of my findings is an argument against the contract move; BLOCKING-1 and
MAJOR-4 are arguments that the client half of it does not yet defend itself against the wire.

---

**VERDICT: FAIL - three BLOCKING findings (a remote-triggerable client crash on three code paths, an
English-only gate that fails open on real repository content, and four wave closures certifying a
K.7 review that predates the code); the `/v1` contract move itself is sound, additive and clean of
any new leak.**
