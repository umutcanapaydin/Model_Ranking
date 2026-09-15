# M13 Plan — The question is the front door, and the numbers stop overstating

**Status:** **SIGNED** by the owner on 2026-09-06. Wave dispatch is authorized.
**Date:** 2026-09-05 · **Risk tier:** **HIGH** overall (the scoring path's frontier predicate is
wrong, and the milestone rewrites the product's primary input) · **Mode:** A0.5 + D-117 ·
**Process baseline:** GP v5.0 · **Review depth:** D-122 · **K.7:** every wave review is a separate
session and a file (D-133), dated after the code it reviews (D-137).
**Quarterly obligation:** 13 % 3 ≠ 0 — no handover is due at this closure.

**Prerequisite:** M12's closure report is still unsigned (`docs/closure-report-m12.md` §0). M13 must
not open over an unsigned milestone. **Sign M12 first, or explicitly waive it here.**

---

## 0. Why this milestone exists

Two things happened in the window before this plan, and each one inverts something the project
believed.

**The intelligent tier had never run.** `SystemLanguageModel.default.availability` returned
`.unavailable(.appleIntelligenceNotEnabled)`, so `ModelRouter` returned `nil` at its first guard on
every question ever asked. Twelve milestones of routing came from `SimilarityRouter`. The owner's
report — *"it felt like a search bar, not an AI"* (owner, translated from Turkish) — was an accurate
description of what was running. And the deployment target admits devices that can never run Apple
Intelligence at all, so for most of the addressable base **the similarity tier is the product, not
the fallback.** M13 is planned accordingly: make the front door good on the tier everyone has.

**The frontier predicate is wrong.** `pareto_frontier` tests strict inequality on both axes, so a
model that is equal on quality and dearer is not dominated. Measured against `advisor.db`: **9 of 27
(surface, budget) combinations publish a `frontier_size` that is too large.** The picks do not
change on today's data — that is stated precisely so nobody oversells the fix — but this is the
scoring path, and it has been wrong in every milestone that shipped it.

Around those, a council of five blind seats and one independent second-opinion review converged, from
different directions, on the same product answer: **remove the controls, keep the numbers.** The
owner's six directives were right in direction and wrong in their literal cuts, and this plan takes
the direction.

### What is already true, measured rather than assumed

- `./runner` at `335d844`: 785 Python tests, 88.44% coverage, 25 records, 132 Swift tests. The only
  red leg is `refresh-status`.
- 74 models, 9 surfaces, 4 incommensurable metrics, 14 sources. Zero image/audio/video models.
- The 12-hour refresh fires on schedule and dies at spawn: `runs = 10`, `last exit 78 : EX_CONFIG`,
  both logs untouched since 2026-08-27. Independently, D-128 would refuse today's candidate
  (computer-use median price +33%, over the 25% limit).
- Six of twelve score sources carry **no `run_date` at all**; `aider` is 332 days stale and is the
  secondary that stamps **High confidence** on every coding pick.
- On `expert`, 25 of 50 models are inside the project's own `close_call` threshold of the leader.

### The trap this milestone exists to avoid

**Simplifying the display into a claim the evidence does not support.** The owner asked for one
"Score" and no price control. Taken literally that prints `Score 161.7` beside `Score 83.5`, and
deletes the quality-versus-cost trade-off that is the product's only real differentiator. Every
seat, independently, refused the literal form and endorsed the intent. **This plan removes controls
and keeps every number, and where a number cannot be made honest it shows rank instead.**

---

## 1. Acceptance criteria (new REQ-IDs — copied into `docs/prd.md` AT THE WAVE THAT OWNS THEM)

| # | REQ-ID | Criterion | Verified by |
|---|---|---|---|
| 1 | **REQ-FIX-001** | Pareto dominance admits equality on one axis: a row is dominated when another is at least as good on both and strictly better on one. Both engines agree | Table-driven test over equal-score, equal-price, strictly-dominated and incomparable pairs, run through the shipping functions; plus a test asserting `frontier_size` for a fixture where the two predicates differ |
| 2 | **REQ-FIX-002** | Startup refuses a database the serving path cannot read. Every table and column a ranking touches is validated, or a representative read is performed per advertised surface | A DB carrying `scores`, `pricing`, `px_median` and no `models` is REFUSED at startup. Today it is accepted |
| 3 | **REQ-FIX-003** | A change that alters published attribution changes the refresh fingerprint | A candidate differing only in `evidence_source` produces a different `_row_digest` and publishes |
| 4 | **REQ-FIX-004** | `runner` cannot report an unrun leg as a pass. Absent environment is `SKIPPED`, and any skip prevents the all-green claim | Run with the Epoch bundle path unset and assert the summary neither says the leg passed nor claims all-green |
| 5 | **REQ-UNC-001** | Where the project's own `close_call` threshold says two models are indistinguishable, the screen does not present them as ordered | A citing test per surface: models within `close_call` of each other render a shared band, and `#N of M` is not printed as if it were a strict order inside that band |
| 6 | **REQ-UNC-002** | Nothing on screen calls a coverage count a confidence. The reader is told how many independent benchmarks measured the pick, and how old the oldest of them is | The rendered string is asserted; a pick whose secondary is >180 days old carries that age |
| 7 | **REQ-UNC-003** | Every score source carries a date, or the product says it does not have one | `select count(*) from scores where run_date is null` is 0, or the undated sources are named on screen |
| 8 | **REQ-ASK-001** | The question field is reliably focusable, raises a keyboard, and can be submitted without one | A UI test that taps, focuses, types and submits via the button; and manual device/simulator verification of both keyboard paths recorded in the wave close |
| 9 | **REQ-ASK-002** | The screen shows what it understood, and it can be corrected in one tap | `"prove a theorem" → Mathematics` renders with the reader's own words, and a correction affordance reaches every one of the nine surfaces |
| 10 | **REQ-ASK-003** | A question the catalogue does not measure returns a ranking AND a statement, above it, of what that ranking cannot tell the reader. It is never silently answered as if measured | Two citing tests — wrong modality and wrong axis — asserting both the list and the sentence. `tier = manual` may not carry `unmeasured = false` |
| 11 | **REQ-ASK-004** | A slower response for a previous selection can never overwrite the current one | A test that resolves two loads out of order and asserts the newer selection survives |
| 12 | **REQ-CMP-004** | A score is shown with its ceiling where one exists (`Score 83.5 / 100`), with its scale NAME where the scale is unbounded but published (`Score 1504 Elo`), and as a rank alone where neither exists (ECI). No two surfaces' scores are presented as comparable | Rendered-string tests per metric family: bounded percentage, elo, ECI |
| 13 | **REQ-DTL-001** | Tapping a model opens a detail screen carrying the evidence the payload already sends and the client currently discards | The screen renders `harness`, `effort`, `higher_effort_score`, `evidence_date`, `input_per_m`/`output_per_m`, and the source attribution |
| 14 | **REQ-DTL-002** | An outbound link is presented only when its origin is on a versioned, hand-maintained vendor allowlist checked on the client | A link whose origin is not on the allowlist is not presented; INV-23 (derived, never concatenated) holds |

**Criterion-to-wave map:** W1 owns 1–4. W2 owns 5–7. W3 owns 8–11. W4 owns 12–14. W5 is closure.

---

## 2. Waves

### W1 — The instrument (risk: **HIGH**)

**Nothing new is measured until the thing that measures is right.** Four defects, all reproduced
against the shipping code, plus the refresh.

1. **The Pareto predicate**, in `recommend.py:229` and `subscribe.py:274`. One-line change each,
   and it is HIGH because it is the scoring path. Fault injection must include the case the current
   code gets right (strict dominance) so the fix is not a regression in disguise.
2. **`_database_unusable`** (`main.py:314`) — validate the full serving schema, or perform one
   representative read per advertised surface. The second is preferable: it validates what the code
   actually does rather than a list somebody must remember to update.
3. **`UNHASHED_ROW_FIELDS`** (`refresh.py:231`) — remove `evidence_source`. Under REQ-LIC-001
   attribution is a licence obligation, so a stale citation is not a display detail.
4. **`runner`'s skip accounting** (`:87`, `:173`, `:291`) — an explicit `SKIPPED` state that cannot
   be counted as a pass, and a summary that will not claim all-green when a leg did not run.

**Owner actions inside this wave, which no agent may take:**
- `launchctl kickstart -p gui/$(id -u)/com.hcs.modelranking.refresh`, and if it still returns 78,
  grant Full Disk Access to `.venv/bin/python3.14`.
- Rule on D-128: is the computer-use median moving 33% a real upstream event, or is the 25% limit
  too tight? **Nothing publishes until this is answered.**
- Sign M12, or waive it.

### W2 — Say only what we know (risk: **HIGH**)

The wave that makes the display honest before the display is redesigned. Order matters: W3 removes
the cues that currently stop a reader over-reading a number, so the honesty must land first.

- **Tie bands.** Use the calibrated `close_call` values already in `categories.py`. This is HIGH
  because it changes what the product asserts about every ranking, and because getting it wrong in
  the loose direction re-creates the problem it exists to solve.
- **Coverage, not confidence.** `confidence_of` (`recommend.py:207`) returns "High" when a second
  benchmark exists. The payload fields stay (D-115 is frozen and D-124's window is spent) — **the
  client stops rendering the word "confidence"** and renders the fact instead, with the age of the
  oldest contributing benchmark.
- **`run_date` for the six undated Epoch feeds.** If a feed genuinely has no date upstream, the
  product says so rather than implying freshness.
- **`aider`** — the owner's decision (see §5).

### W3 — The question is the front door (risk: **HIGH**)

The wave the owner asked for, and it is HIGH because it deletes the reader's current controls and
replaces them with a router whose shipping tier is sentence similarity.

- **Fix the field first.** Explicit `FocusState`, a visible send button, submit from both Return and
  the button, progress in place of the send icon, no duplicate submissions. Then verify the software
  and hardware keyboard paths on the simulator **and** record what was seen.
- **Remove both top strips.** The nine surfaces move into a `Change` bottom sheet reached from a
  matched-surface row — **the correction affordance D-126 requires survives the deletion**, which is
  the condition the council's C1 rejection turned on.
- **Echo the question.** `"prove a theorem" → Mathematics` with one-tap alternatives. The echo is
  what shows a stranger that the words did not have to match.
- **Move the model-name filter off the home screen** to the full-ranking screen. Two text inputs is
  why the AI bar reads as the weaker of two search boxes.
- **Fix the manual-tier contradiction:** `tier = manual` with `unmeasured = false` while the view
  loads the assistant surface and the text says "Pick a surface below."
- **Fix the load-ordering race** in `ContentView.load()` — cancellation or request identity.
- **Surface `unavailableReason`** as quiet help, never as an error. The similarity route still works.
- **Fix the bottom-bar overlap** with `.safeAreaPadding(.bottom)`, not the magic `88`.

### W4 — The card, and what a tap opens (risk: **MED**)

- **`Score 83.5 / 100`** where a real ceiling exists; the scale name or rank for elo; **rank only,
  no invented maximum, for ECI**. Keep the plain-language gloss — it is the part that works.
- **Rename `BUDGET PICK`.** With no budget control, a label implying the reader set a budget is
  false. `Affordable pick` or equivalent.
- **The model detail screen** — the evidence the payload already sends and the client throws away.
- **Official links** behind an eleven-entry vendor-origin allowlist, versioned in the repo, checked
  on the client. 44 of 74 URLs derive free from data already fetched; ~30 are hand-entered.

### W5 — Closure (risk: **LOW**)

Stage 4.0 security review (BLOCKING), 4.1 quality gate, 4.2 capture, 4.4 `note.txt`. No deploy.

---

## 3. Shared contracts (K.8)

**FROZEN — no field may be added or renamed in `/v1` during M13:**

```
$ grep -n "PUBLIC_ANSWER_FIELDS\|PUBLIC_PICK_FIELDS\|PUBLIC_RANKING_FIELDS" src/app/adapter/main.py
735:PUBLIC_ANSWER_FIELDS = frozenset(
758:PUBLIC_PICK_FIELDS = frozenset(
796:PUBLIC_RANKING_FIELDS = frozenset(
```

D-115 froze the payload; D-124's single revision window was spent by D-125; D-136 was the second
move and was additive. **Every display change in W2 and W4 is therefore a CLIENT change.** If a wave
finds it cannot deliver a criterion without a payload move, that is an escalation, not a decision.

Also frozen: **D-104** (no LLM in the scoring path — the engine decides every number), **D-105**,
**D-109**, **D-126** (the router picks the question; the engine answers it), **INV-23**.

---

## 4. Definition of done

- Every criterion in §1 has a citing test able to fail (V3C-02, BLOCKING).
- `make check` and `make gate` exit 0 at the closing tree; `./runner` green with **no leg SKIPPED**.
- Each wave-close checklist committed, its K.7 review a file dated after the code (D-133, D-137).
- The four W1 defects each carry a regression test that fails against the pre-fix predicate.
- **The keyboard paths are verified by a human on the simulator**, and the result recorded — this
  milestone's front door cannot close on a gate that never touched it.

---

## 5. Decisions this milestone needs from the owner BEFORE W2 dispatches

1. **`aider`.** Drop it and let every coding pick fall from "two benchmarks" to one — arguably the
   honest outcome — or keep it and print its 332-day age beside the claim.
2. **D-128's 25% threshold.** Real upstream event, or a limit too tight? Nothing refreshes until
   this is answered.
3. **`Score X / 100` versus rank-only for ECI.** The plan assumes the split. Confirm or overrule.
4. **The ~30 hand-entered vendor URLs.** Willing to maintain them, or does W4 ship covering only the
   44 that come free?

Each answer becomes an ADR **written at the wave that consumes it**, with its number allocated then.
This plan deliberately does not name those numbers: `tests/unit/test_adr_citations.py` fails the
build when a record cites an ADR nobody has written, and M12 paid for that lesson thirty files at a
time — *a contract nobody can read is a contract nobody agreed to.* The draft of this plan cited two
such numbers and the gate rejected it, which is the control working.

---

## 6. What this milestone is NOT

**It does not add the image-editing surface**, and that is a deliberate cut the owner should
challenge if he disagrees. The data is reachable — `lmarena-ai/leaderboard-dataset` config
`image_edit`, 93 rows, CC BY 4.0, on a client whose `config` is already a constructor parameter. The
blocker is not licensing: `pricing` declares `input_per_m`/`output_per_m` with `CHECK (> 0)` and
image models are priced per image. Shipping it needs a typed, modality-aware pricing model plus the
UI work to suppress value comparisons on an unpriced surface — a milestone's work, not a wave's, and
this milestone is already at five waves and rewriting the primary input. **It is M14's opening.**

It does not deploy (D-123, W-030, W-031 remain open), does not build for a device
(`DEVELOPMENT_TEAM` is still zero occurrences), and does not close the fact that
`EngineClient.localDefault` points at `127.0.0.1` — which on a phone is the phone. Those three are
one problem and they are M14's or M15's, with an Apple account.

It does not build demand logging. The mechanism that would make coverage requests countable
conflicts with `Router.swift:13` — *nothing typed here leaves the device* — and the app has no
privacy manifest. The on-device-counter design is written up in `docs/second-opinion.md` Q8 and
needs the owner's ruling before anyone writes it.

---

## 7. Council rulings, 2026-09-06 — these ARE the owner's decisions

The owner went to sleep mid-milestone and delegated the §5 questions in his own words: *"if you
need to ask something, stand up a blind council of 3 core members — their joint decision is my
decision"* (owner, translated from Turkish). Three seats ruled blind, in parallel, each on the
questions matching its lens. Recorded here rather than in a side document because work was built on
them the same night.

**Two of the six rulings were overturned by measurement afterwards, and both overturns are recorded
below rather than quietly applied. A ruling this project acts on has to survive the same evidence
rule as everything else.**

| # | Question | Ruling | State |
|---|---|---|---|
| 1 | `aider` | **A3** — a secondary older than `STALE_NOTICE_DAYS` (90), or carrying no date, does not upgrade the coverage claim. Threshold REUSED, not invented | **IMPLEMENTED** (W2) |
| 2 | D-128's 25% limit | **B3** — make the limit population/step-aware rather than flat | **NOT IMPLEMENTED — see below** |
| 3 | Score display | **C1** — `Score 83.5 / 100` for bounded metrics, `Score 1504 Elo` for elo, **rank only** for ECI | Ruled; W4 |
| 4 | Tie bands | **D1** — greedy bands anchored at the top, `=1 of 50`, band size stated once per ranking | Ruled; W2/W4 |
| 5 | Vendor URLs | **E4** — derive the 44 that come free, fall back to the VENDOR ORIGIN for the other 30. No per-model table; the only maintained artifact is the origin allowlist | Ruled; deferred with W4's second half |
| 6 | Scope | **F2** — split W4: keep the card-honesty half, move the detail screen and links to M14 | **ADOPTED** |

### Where a ruling was overturned by measurement

**Ruling 2 (D-128) is not implemented, and the seat's own condition is why.** It reasoned the
refusal was composition arithmetic — new models entering above the median — and named the settling
measurement itself: *"if a large share of shared models were repriced, B1 is right instead and my
ruling should be overturned."* That measurement was run. A candidate was built to a scratch path and
diffed against the live artifact:

```
computer-use: added 0, removed 0, shared 33, repriced 5 (15%)
              GPT-5 Codex 2.58 -> 3.44  (the model sitting exactly AT the median)
all nine surfaces: 0 breach the 25% limit today (largest, web-dev +17.5%)
```

The roster did not move at all, so it is not composition arithmetic — it is a genuine reprice of the
model that happened to be the median. **And no surface breaches the limit against today's upstream,
so the guard is not firing.** Restructuring the one module that must not be wrong, at night, on a
hypothesis, against a guard that is not currently refusing anything, is not a trade this milestone
should take. The 2026-08-27 refusal has cleared on its own; only the launchd spawn fault remains.

**Ruling 1's second clause is not implemented, and the seat missed a shipped disclosure.** It also
required `_stale_notice` to emit a notice for an UNDATED primary, on the finding that
`recommend.py`'s `latest_run is None → return None` leaves five surfaces unable to report staleness.
The branch reads exactly as the seat described. But `_evidence_dating` already publishes
`evidence_dating: "undated"` plus *"This answer's benchmark publishes no evaluation dates, only
model release dates. Its scores cannot be aged, so freshness is unknown rather than recent."* —
verified live on `everyday`, `abstract`, `web-dev` and `agentic-coding`, every surface with an
undated primary. Adding a second notice saying the same thing is the duplication D-135 exists to
prevent and that M12 spent a milestone removing. **The seat read one function; the disclosure lives
in another.**

### Corrections the council made to this plan

- **REQ-CMP-004 contradicted W4.** The criterion said "as a rank where none does", mandating
  rank-only for elo; W4's prose said "the scale name or rank". The criterion has been rewritten to
  C1's ruling. Caught before a citing test encoded the wrong one.
- **"Six of nine surfaces have every adjacent top-ten pair inside `close_call`" is wrong; it is
  three of nine.** The leader-band counts reproduce exactly (expert 25/50, mathematics 28/51); the
  adjacent-pair figure does not. Recorded because it appears in §0 of the handover.
- **There is no iOS test target at all.** `ios/ModelRankingTests/` is empty and `Package.swift`
  scopes its target to `ModelRanking/Engine`, whose own header states `ContentView.swift` stays
  unexecuted. **Nine of the fourteen criteria in §1 are client-rendering criteria**, and V3C-02
  requires each to have a citing test able to fail. The Definition of Done in §4 cannot be met as
  written for those nine. **Consequence adopted for W2–W4: display LOGIC goes into
  `ModelRanking/Engine/`, which the 132 Swift tests already cover, and `ContentView` stays a thin
  renderer.** That is how these criteria get citing tests without first building an XCUITest target.
- **REQ-ASK-001 offers a device/simulator disjunction where the device branch is physically
  unavailable** (`DEVELOPMENT_TEAM` appears zero times; `ios/app.sh` builds with
  `CODE_SIGNING_ALLOWED=NO`). It must read "simulator", and no closure sentence may say the front
  door was verified on a device.
- **The vendor-origin allowlist is twelve entries, not eleven** — 20 of the free 44 URLs derive from
  `hugging_face_id` to a HuggingFace card, and `huggingface.co` is not a vendor. Either it goes on
  the list as a third-party host, stated as one, or those 20 drop to their vendor origin.

---

## 8. Owner rulings, 2026-09-15 — in session, answering the lead agent directly

Appended rather than edited into §7, because §7 records what the council ruled and this records
where the owner changed it.

| # | Question | Ruling | Consequence |
|---|---|---|---|
| 1 | M12 is unsigned and M13 is open over it | **Signed** | `docs/closure-report-m12.md` records it; the §0 prerequisite is discharged nine days late, ledgered in the W2 close |
| 2 | The margin and the second board's age are published nowhere; §3 freezes `/v1` | **Add them to `/v1/categories`** | D-138. The answer payload's field sets do not move |
| 3 | Wave commits under D-117 | **Commit and push** | Each wave lands as its own agent-identity commit; the milestone-closing commit stays the owner's |
| 4 | §7 ruling 4 (D1, greedy tie bands) orders 47 within-margin pairs on today's data (45 on raw scores) | **Rank ranges** (`#1–27 of 50`) | Ruling 4 is SUPERSEDED. REQ-UNC-001's verification reads "overlapping ranges" where it read "a shared band" |
