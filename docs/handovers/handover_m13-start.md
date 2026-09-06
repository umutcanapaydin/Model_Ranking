---
record_type: handover
id: handover-m13-start
status: draft
date: 2026-09-05
---
# HANDOVER — M13 start

**Written for the agent that picks this up next, human or otherwise.** It assumes you know nothing
about this project. It supersedes nothing: `handover_q4.txt` (M12 closure) is still the STATE
record for M1–M12 and `handover_rocky.txt` is still the best account of the DOCTRINE. This file
covers **what happened between 2026-08-30 and 2026-09-05** and what M13 opens with.

Written by: the lead agent (Claude Code, local lane, D-117), acting as council chair on the owner's
instruction. **Nothing in this window was committed.** The working tree is clean apart from
untracked notes; every finding below is a measurement, not a change.

---

## 0. Read this in this order

1. `note.txt` — the current-turn handoff. Still accurate for M12 and the settled decisions.
2. This file — what changed in this window.
3. `docs/second-opinion.md` — **every open question, written out for a stranger.** The owner asked
   for it so he could take the decisions elsewhere. It is the agenda for M13's plan.
4. `AGENTS.md` §3 and §5 — house rules. **§5: every committed file is English (V4C-79).** That is
   an owner directive enforced by `L1` in `scripts/check_records.py`; exemptions live in
   `.language-allow` and each one needs a written reason.
5. `docs/decisions.md` — D-104, D-115, D-124, D-125, D-126, D-127, D-128, D-134, D-135, D-136.

---

## 1. What the product is, in four sentences

`model_ranking` aggregates free-and-legal LLM benchmark and pricing data and serves deterministic,
budget-aware model recommendations. An iOS client renders them; the engine decides every number and
the client only chooses words (D-104). Twelve milestones are closed, M12 awaits the owner's
signature, nothing is deployed and nothing bills. **The purpose is an iOS AI-advisor app: a person
asks what they want an AI to do, and gets a defensible answer with the evidence attached.**

The doctrine that governs everything: **never present something unmeasured as measured.** If a fact
and a sentence disagree, the fact is right and the sentence is the defect.

---

## 2. Where things stand — measured 2026-08-30, not recalled

    ./runner  at HEAD 335d844, 2026-08-30 20:52
      tests    : 785 passed, 12 skipped
      coverage : 88.44%
      records  : wave-check-all PASS, 25 v5.0 records
      passed   : make-check secrets build surfaces engine swift-tests ios-build
      failed   : refresh-status          <-- the only red

**Before this window, `./runner` had never been run at the current HEAD.** The last full evidence
run was at `5fb5755`, 44 minutes before `335d844` landed — and `335d844` is the commit that
discharged Stage 4.0's three BLOCKING defects. That gap is now closed: the code currently in the
tree has been proven green except for the refresh.

Catalogue: **74 models** (OpenAI 20, Anthropic 13, Google 8, DeepSeek 6, Alibaba 6, xAI 5, Zhipu 5,
MiniMax 5, Moonshot 3, Mistral 2, ByteDance 1), **zero image/audio/video models**. Nine surfaces,
four incommensurable metrics, fourteen sources.

---

## 3. What is broken RIGHT NOW

### 3.1 The 12-hour refresh has two independent faults, and the first hid the second

**Fault A — launchd fires on schedule and cannot spawn the job.** Last successful publish
2026-08-27T03:38 UTC. The Mac rebooted 2026-08-27 15:04. By 2026-09-05: `runs = 10`,
`last exit code = 78 : EX_CONFIG`, and **neither `refresh.log` nor `refresh.err.log` has been
written a single byte since**. 78 is not in the plist's own documented set (0 published /
1 unchanged / 2 failed / 3 refused / 4 busy).

*Corrected 2026-09-05: an earlier reading of this file said `runs = 1` and inferred launchd had
stopped triggering. It has not — the counter has climbed to 10 on the 12-hour interval. The job is
attempted on time and dies before the interpreter starts, which is why both logs stay empty. That
makes a spawn-time restriction (TCC on `~/Desktop`, where the program, working directory and both
log paths all live) the stronger hypothesis, not a weaker one.*

The Python side is **proven healthy**: it was run under launchd's exact minimal environment
(`env -i`, same PATH, same PYTHONPATH) against a *copy* of `advisor.db` and completed normally.
So the fault is in launchd's spawn. The program, the working directory and both log paths are all
under `~/Desktop`; the most likely cause is that the background item lost Desktop access (TCC) after
the reboot. **Unverified** — TCC.db is unreadable.

Loading and unloading this job is the owner's action by the plist's own instruction. The command to
give him:

    launchctl kickstart -p gui/$(id -u)/com.hcs.modelranking.refresh

If it still returns 78, add `.venv/bin/python3.14` to Full Disk Access.

**Fault B — even alive, it would refuse to publish.** The probe run produced:

> `refused: computer-use's median price would move up 33% ($2.58 to $3.44), over the 25% limit;
> one provider changing a price does not move a surface's median`

Pricing rows moved 2676 → 2818. D-128's guard is working correctly and protecting the artifact, but
the consequence is that fixing Fault A alone will not refresh anything — `consecutive_refusals`
will climb to escalation. Somebody has to look upstream and decide whether the 25% threshold is
right.

**Why this matters beyond a cron job:** `launchctl list` shows the label loaded and `note.txt` says
"Loaded", while nothing has refreshed for over a week. That is the W-023/W-058 shape this project
has already paid for twice — healthy to every existence check, answering nothing.

### 3.2 Two layout defects in the iOS app

1. **The bottom docked search bar overlaps content.** `ContentView.swift:186` compensates with
   `.padding(.bottom, 88)`; a screenshot shows the bar sitting translucently over the BEST VALUE
   card's last line and ghosting the BUDGET PICK badge. Fix with `.safeAreaPadding(.bottom)`, not a
   magic number.
2. **The question box has no submit affordance.** `ask()` fires only from `.onSubmit`
   (`ContentView.swift:116`). With a hardware keyboard attached and window focus lost there is no
   way at all to submit a question.

### 3.3 The keyboard — TWO app defects, reproduced 2026-09-05

The owner's symptom was **both**: no software keyboard appeared, and his Mac keyboard did not type
either. Both were reproduced. `ConnectHardwareKeyboard` has been left at `false`, which matches the
state he reported it in.

**Correct two things this project's record briefly believed:**

1. **Synthetic taps DO reach the Simulator.** An earlier note in this window said they did not. The
   coordinates were wrong: the device screen is the Simulator window's `AXGroup 1` at `(619, 117)`,
   size `356 × 775` — **not** the window origin `(595, 39)` size `405 × 869`. Scale is
   `1206 / 356 = 3.388`. Everything missed by ~78 points. Read the geometry with:

       osascript -e 'tell application "System Events" to tell process "Simulator" \
         to get {position, size} of group 1 of window 1'

   Synthetic **keystrokes** are a different matter — System Events `keystroke` has no effect here,
   so the typing path cannot be exercised from this environment. Mouse works, keyboard does not.

2. **"Simulator configuration only" is overturned for the question field.** The Mobile seat read the
   code and was right about everything it checked — no `@FocusState`, no `.disabled`, no
   `allowsHitTesting`, `Card` intercepts nothing, the two `.searchable` modifiers sit on different
   screens of one stack and do not conflict. It simply could not tap the field, and nobody had.

**Measured, with the hardware keyboard disconnected:**

| Target | Result |
|---|---|
| Language flag | works — UI switches to Turkish |
| Budget button | works — selection and results change |
| Bottom `.searchable` filter | **gains focus** — caret, clear button, nav collapse |
| **Question `TextField`** (`ContentView.swift:114`) | **no visible change at all** |
| **Software keyboard, on the focused field** | **never appears** |

**Defect A — the question field gives no feedback when tapped.** The control the owner wants to
build the product around does nothing visible, while a field 700 points below it responds correctly.

**Defect B — no software keyboard for a focused field.** **A real iPhone has no hardware keyboard**,
so if this reproduces on device the app cannot be typed into at all. Do not file this as a simulator
detail.

**Open, and stated as a boundary rather than a guess:** whether the question field silently gains
focus and only the keyboard is missing, or never gains focus. From outside the two are identical.
**The settling measurement is one build** — add `@FocusState` to the field and log its transitions,
or put a `print` behind the tap, then read `xcrun simctl spawn booted log stream`.

**Do not mistake ⇧⌘K for a fix.** Connecting the hardware keyboard restores Mac typing and
*suppresses* the software keyboard by design. It is a workaround for the developer, not a repair.

---

### 3.4 Four engine defects the council missed, reproduced by the chair 2026-09-05

A second-opinion review (`docs/sec_op_answers_turn_1.md`) read the handover first, inspected the
code independently, and returned findings **no council seat had found**. The chair reproduced the
four below against the shipping functions rather than accepting them. All four are real.

**D1 — Pareto dominance is wrong in both engines.** `recommend.py:229` and `subscribe.py:274` both
test `o.score > r.score and o.price < r.price` — strict on *both* axes. Correct dominance allows
equality on one axis when the other is strictly better. Reproduced through the shipping function:

    equal score, different price -> ['A-cheap', 'B-dear']    B should be dominated
    equal price, different score -> ['C-better', 'D-worse']  D should be dominated
    strictly dominated (control) -> ['E-best']               correct

**Measured blast radius, against `advisor.db`: 9 of 27 (surface, budget) combinations return a
frontier that is too large** — `coding` (all three budgets, extra row *Gemini 3 Flash*),
`agentic-coding` (medium/unlimited, *GPT-5.6 Terra*), `mathematics` (unlimited, *Claude Fable 5* and
*GPT-5.5*), `computer-use` (all three, *Gemini 3 Pro*, *MiniMax M2.5*).

**But narrow the severity honestly: the picks do not change on today's data.** `best_quality` and
`best_value` were identical under both predicates for every case checked, because a wrongly-retained
row is never strictly cheaper than the row that should have dominated it. What *is* wrong today is
`frontier_size`, which is a published `/v1` field decoded by the client at `Models.swift:73`. Fix
the predicate; do not describe it as having changed a recommendation, because it has not.

**D2 — startup validation approves a database the serving path cannot read.**
`main.py:314 _database_unusable` checks `{"scores", "pricing"}`, a `scores.effort` column and a
non-empty `px_median`. It does **not** check `models`, which `rank.py:297` joins on every ranking.
Reproduced: a SQLite file with the checked objects and no `models` table returns `None` — "usable".
The process would boot green and answer every surface with nothing.

**D3 — the refresh fingerprint ignores an attribution change.**
`refresh.py:231 UNHASHED_ROW_FIELDS` excludes `evidence_source`. But `rank.py:87 attributions_for`
derives every payload's citation list from exactly those evidence sources. So a change of evidence
source alone produces an identical `_row_digest`, D-128 sees no change, and the artifact is not
published — **while the citation the reader sees goes stale.** Under REQ-LIC-001 attribution is a
licence obligation, not a display detail, so this is more than the cosmetic P2 it was filed as.

**D4 — `runner` can report an unrun leg as a pass.** When the Epoch bundle is absent it prints
`SKIPPED` and calls `record "build" 0` (`runner:87-88`); the same shape at `:173-174` (engine not
listening) and `:291-292` (no `xcodebuild`). A full-green `runner` can therefore mean major legs did
not execute. **The 2026-08-30 run recorded in §2 is not affected** — its log contains no leg-level
`SKIPPED`, only the 12 documented conditional pytest skips. But the mechanism must gain an explicit
`SKIPPED` state that cannot be counted as a pass.

**Also reported and not yet reproduced by the chair** (read as plausible, verify before acting):
an iOS load-ordering race in `ContentView.load()` with no cancellation or generation counter; a
manual-tier contradiction where `TieredRouter` returns the assistant category with `tier = manual`
and `unmeasured = false` while the explanation says *"Pick a surface below."* and the view loads it
anyway; CORS origin validation accepting full URLs; `_hold_lock` reporting any `OSError` as `busy`
when only `EAGAIN`/`EWOULDBLOCK` means contention; `write_status` calling `.get()` on JSON that may
not be an object; parsers accepting non-finite values; `SameHostOnly` comparing host without scheme
or port.

---

## 4. The single most consequential measurement of this window

**Apple Intelligence had never once run.**

`SystemLanguageModel.default.availability` returned `.unavailable(.appleIntelligenceNotEnabled)` on
the owner's Mac (M3, macOS 26.5.2 — fully eligible hardware). Therefore `ModelRouter.route()`
returned `nil` at its first guard (`Router.swift:238`) on every question ever asked, and every
routing in twelve milestones came from `SimilarityRouter` — sentence-embedding similarity against
hand-written hints.

The owner's complaint, in his own words (translated from Turkish): *"it felt like a search bar, not
an AI"* — he found that a sentence containing the word "mathematics" matched and a sentence meaning
mathematics without saying it did not. **That is exactly the signature of the similarity tier.** The
product was not broken; the intelligent tier was simply never running.

He has since enabled Apple Intelligence. Measured on the host afterwards: **1.33 s cold, 0.17 s
warm.** The simulator runtime does ship a real `FoundationModels.framework` (not a stub), so the
tier should now fire in the simulator — **but nobody has confirmed that inside the simulator yet.**
Treat it as probable, not measured. The settling command: a probe target that prints
`SystemLanguageModel.default.availability`, or a temporary `print` behind `Router.swift:238` read
via `xcrun simctl spawn booted log stream`.

**And the framing this overturns.** `IPHONEOS_DEPLOYMENT_TARGET = 18.0` while Apple Intelligence
requires iPhone 15 Pro or newer. Every iPhone 14 and below is **permanently ineligible**. For most
of the addressable device base, `SimilarityRouter` *is* the product. The Mobile seat's conclusion,
which the chair endorses: **make the similarity tier good enough to ship alone and treat Apple
Intelligence as a quiet upgrade.**

**Cheap and overdue:** `ModelRouter.unavailableReason` produces "Apple Intelligence is turned off"
at `Router.swift:222`, is read once as a guard at `:238`, and is **rendered nowhere**. The app knew
why it had degraded and told nobody for twelve milestones.

---

## 5. The M13 research, and what happened to it

The owner asked for research on a real question: *what do we do when someone asks about something
no benchmark measures?* His example — *"which model best enhances a profile photo"*.

**Finding 1 — his example is a coverage gap, not a measurement gap.** Image editing is benchmarked
publicly with Elo (Artificial Analysis Image Editing Arena, LMArena Single-Image Edit, ImgEdit-Bench
NeurIPS 2025, GEditBench v2). The two kinds of gap have completely different remedies and conflating
them is the central risk in M13.

**Finding 2 — the literature offers a defensible method for genuine gaps.** Observational Scaling
Laws (Ruan, Maddison, Hashimoto, NeurIPS 2024 Spotlight, arXiv 2405.10938): the benchmark × model
matrix is low-dimensional, the top three components explain ~97% of variance, and downstream
unmeasured behaviour is predictable from them. It is pure PCA — deterministic, **no LLM anywhere,
D-104 untouched.**

**Finding 3 — the honest boundary.** These methods predict unseen *questions*, not unmeasured
*capability domains*. You can predict MATH from GSM8K. You cannot predict image editing from
SWE-bench.

**Finding 4 — more sources does not mean more quality.** A systematic review of 445 LLM benchmarks
by 29 expert reviewers (arXiv 2511.04703): only 16% use uncertainty estimates, 27% use convenience
sampling. A bad benchmark is worse than no benchmark because it contaminates every aggregate.

**Finding 5 — a licensing trap.** Artificial Analysis's Data API grants attribution on all tiers and
points elsewhere for redistribution rights; their base terms URL returns HTTP 404. **The absence of
a grant is operationally a prohibition** under the project's free-and-legal rule. LMArena by
contrast is `cc-by-4.0` and clean.

**The chair proposed a three-layer rule** — measured / derived-from-latent-axis / out-of-scope —
and put it to a council. **The council destroyed the middle layer.** See §6.

---

## 6. The council of 2026-08-31 — what it was and what it decided

Five seats, blind, in parallel, no shared context: **Measurement & Psychometrics, Product &
Delivery, Data Sources & Licensing, Senior Mobile Developer, the Stranger.** Each read one brief and
returned a ballot plus reasoning. Precedent: `docs/council-m11-assessment.md`.

*(A first attempt was lost entirely when the machine slept mid-run. If you convene one, run
`caffeinate -dimsu` first.)*

### Tally

| Seat | A (score) | B (unmeasured) | C (UI) | D (extend) | E (budget) |
|---|---|---|---|---|---|
| Measurement | A5 | B2 | C4 | D5 | E3 |
| Product | A5 | B4 | C2 | D1 | E5 |
| Data & Licensing | A3 | B2 | C4 | D1 | E2 |
| Senior Mobile | A5 | B2 | C2 | D5 | E3 |
| Stranger | A5 | B4 | C4 | D3 | E3 |

**On three of five ballots, no seat chose the owner's directive as literally worded — and on all
three, every seat agreed with its direction.** The pattern repeated: *remove the control, keep the
number.*

- A1, A2, A4 — zero votes. A bare "Score" label is refused 4–1.
- **B1, the chair's own proposal — zero votes. The derived layer died 5–0.**
- C1 (bar only, chips deleted) — zero votes.
- E1 (price becomes a hidden attribute) — zero votes; **removing the strip — unanimous.**

### What killed the derived layer, in numbers

The Measurement seat ran PCA on the real matrix (on a copy; `advisor.db` untouched):

- **73 models × 12 columns, 50.2% filled. Exactly one model has all twelve.**
- On the largest complete block (49 × 4): **PC1 = 0.806**, and **0 of 2000 column permutations came
  near it**. A single general-capability axis is real in our data.
- **The "top 3 ≈ 97%" figure cannot be tested here** — a permutation null already yields cum-3 =
  0.83 from pure noise at four columns. The literature figure is largely a column-count artifact.
- **PC2 is Arena** (loading −0.87 to −0.92, everything else near zero). Human preference is a
  separate axis; any single score that folds it in destroys the one thing the app measures most
  credibly.
- Leave-one-out prediction of a held-out board from the latent axis: ARC-AGI 0.813, TerminalBench
  0.560, WebDev 0.398, SWE-bench Verified 0.334, **DeepSWE −0.104** — *worse than printing the
  mean*, in the easy case.

**Conclusion the chair accepts: one score per surface is supported. An invented surface is not.**

### What each seat saw that no other could

- **Data & Licensing — the owner's own example is already solved.** `lmarena-ai/leaderboard-dataset`
  (which we already ingest, CC BY 4.0) has an **`image_edit` config**: 93 rows, publish date
  2026-08-18. And `ArenaClient.__init__(config="text")` **already takes `config` as a parameter**
  (`src/app/clients/arena.py:76`). The real blocker is the `pricing` schema — `CHECK (> 0)` on
  per-token columns, while image models are priced per image. It ships **unpriced** or not at all.
- **Senior Mobile — the app cannot work on a phone.** `EngineClient.localDefault` is
  `http://127.0.0.1:8080` (`EngineClient.swift:144`); on a phone that is the phone. Combined with
  `DEVELOPMENT_TEAM` appearing zero times, **every M13 UI decision is being taken about a screen
  that has never rendered real data on real hardware.**
- **Measurement — the ranked gaps are not real.** Using the project's own `close_call` thresholds:
  on `expert`, **25 of 50 models are statistically tied with the leader**; on `mathematics`, 28 of
  51. On six of nine surfaces every adjacent pair in the top ten is inside the noise threshold.
  Collapsing to one "Score" makes this worse, because differing units were the last cue.
- **Stranger — the tier upgrade is invisible.** The entire observable difference between the
  intelligent and the fallback tier is one footnote string in the same font, colour and position —
  and *the fallback string is the more informative of the two*. Today's design rewards a successful
  route with less information. Its proposal: echo the input, *"prove a theorem" → Mathematics*, with
  two alternates beneath. The echo is the proof.
- **Product — the chair's layer 3 was a regression.** The app already does not decline:
  `Router.swift:206-210` routes an unmeasured question to the chat surface with `unmeasured: true`
  and renders an orange caveat above a full ranking. The chair proposed to take the ranking away and
  return nothing.

### The collision the chair had to adjudicate

Two blind seats contradicted each other and **one was wrong.** Data recommended dropping `aider`
because *"no surface reads it — `grep aider categories.py` is empty."* Measurement said `aider` is
what stamps **High confidence** on every coding pick. The chair checked: **Measurement is right**;
the grep missed it because the field reads `secondary_benchmark="Aider polyglot"`
(`categories.py:74`), and `confidence_of` (`recommend.py:207`) returns "High" purely because a
secondary score exists.

> **"High confidence — two independent benchmarks (SWE-bench Verified + Aider polyglot)" is printed
> on the strength of a benchmark last run 2025-10-03 — 332 days ago — covering 15 of 74 models.**

And `confidence_of` is not a confidence measure at all: it counts *how many boards we hold*. For
`everyday`, the secondary that mints "High" is `epoch_mmlu` — **3 models of 74.**

### The thing two seats found independently without being asked

Product and Senior Mobile both discovered that the coverage-request log — the mechanism that makes a
decline temporary and demand-driven coverage possible — **cannot be built without breaking the
product's stated privacy property.** `Router.swift:13` says nothing typed leaves the device;
`ask()` sends only a surface id; there is no request logging; there is **no `PrivacyInfo.xcprivacy`
file at all**. Both independently proposed the same fix: count on-device, submit only the surface id
and the `unmeasured` flag, never the text.

---

## 7. What must not be undone

Carried forward from `note.txt`, still binding:

- **D-104** — no LLM in the scoring path. The client chooses words; the engine decides every number.
- **`/v1`'s prose is DERIVED from `why_fact` / `trade_off_fact`, never computed beside it.** If the
  fact and the sentence disagree, the fact is right. `tests/unit/test_why_facts.py` asserts it.
- **`whySentence` / `tradeOffSentence` return `nil` for anything they cannot render**, and the
  caller falls back to the engine's English. Do not "fix" this with a default — the function once
  rendered an unreadable value as `""` and shipped `and % cheaper.`, the claim intact and the
  magnitude deleted.
- **D-127** ids are the contract, titles are the product. **D-133** K.7 means a separate session and
  the review is a file. **D-137** a review has a date. **INV-23** read-only URIs are derived, never
  concatenated.
- **Agents never commit in the local lane.** They may stage and write a commit message. Never commit
  as the owner.

Added by this window:

- **The derived-score layer is refused on evidence, not taste.** If a future agent proposes
  predicting an unmeasured surface from a latent axis, the answer is the leave-one-out table in §6.
- **Artificial Analysis must not be ingested under the free tier.**

---

## 8. How to run everything

    cd /Users/umutcanapaydin/Desktop/ILGAR/model_ranking

    ./runner                        Everything. Gate + secrets + build + surfaces + engine +
                                    refresh record + Swift tests + iOS build. Writes nothing into
                                    the repo; advisor.db is never touched. Output lands in
                                    ~/Desktop/terminal_output/model_ranking/runner/latest.log
    ./ios/app.sh up                 Engine + simulator + build + install + launch, then returns.
                                    `restart` after a change, `status`, `logs`, `down`.
    ./scripts/simulator_session.sh  Same, but stays in the foreground until Ctrl-C.
    make run                        Engine only, on :8080.
    make check                      The merge gate.
    make gate                       check + falsify + secrets + deps + slopsquat.
    make standup                    LLM-free project-state dump.

**Before any long unattended run, prevent sleep:** `caffeinate -dimsu -t 5400 &`. A council of five
agents was lost to a sleeping machine in this window.

Simulator note: synthetic mouse and keyboard events (CGEvent, System Events) **do not reach the
Simulator** from this environment — the cursor moves and nothing is delivered. UI interaction must
be done by a human. Screenshots (`xcrun simctl io booted screenshot`) do work.

---

## 9. What M13 opens with

**The plan does not exist yet, deliberately.** The owner's instruction was to write M13 with the
outstanding debt as W1 and the six directives after it, and the directives cannot be planned until
he answers `docs/second-opinion.md`. Six questions there block the plan: Q1 (what replaces the
metric name), Q2 (one score per surface or across surfaces), Q3 (show-always versus decline), Q4
(what survives the budget strip), Q5 (detail screen versus external URL), Q6 (what gets extended
first).

**Proposed shape, for the agent that writes it:**

- **W1 — the debt.** The refresh's two faults; M12's signature; `./runner` green at the closing
  tree. Nothing new until the instrument works.
- **W2 — measurement honesty.** `close_call` banding so `#1 of 50` stops meaning "one of twenty-five
  co-leaders"; rename or repair `confidence_of`; decide `aider`; fix `run_date` on the six undated
  sources.
- **W3 — the screen.** Q1's score form, the budget strip removal, the two layout defects, the echo,
  and `unavailableReason` finally rendered.
- **W4 — coverage.** `image_edit` as a config string, unpriced, behind the date fix.

**And the thing the council said that the plan should be built around**, because it inverts the
brief the owner gave: `SimilarityRouter` is the product for most of the device base, permanently.
Making it good is worth more than making the on-device model tier fire.

---

## 10. Ledger of what this window changed on disk

**No source file was modified. No commit was made.** For completeness:

- Created `docs/second-opinion.md` and this file.
- Set the booted simulator's `ConnectHardwareKeyboard` to `1` in
  `~/Library/Preferences/com.apple.iphonesimulator.plist`, then **reverted it to `false`** once the
  owner confirmed the symptom. Outside the repo; the current value matches the state he reported in.
- Drove the booted simulator with synthetic taps to reproduce §3.3 — read-only interaction, no
  build change.
- Ran `./runner` (writes only to `~/Desktop/terminal_output/`), `./ios/app.sh up`, and one refresh
  probe against a scratch copy of `advisor.db`.
- The untracked file `model_ranking_suggestions_coku` in the repo root is the owner's own note, not
  an agent artifact.

**Suggested commit message** (the owner runs it; agents do not commit):

    M13 opening: the council's findings, and every question that blocks the plan

    Five blind seats read one brief and voted. On three of five ballots no seat chose the
    owner's directive as literally worded, and on all three every seat agreed with its
    direction. The derived-score layer this agent proposed died 5-0 on a leave-one-out
    table it had not run before proposing it.

    Also records what a week of measurement found: Apple Intelligence had never once run,
    so twelve milestones of routing came from the fallback tier; the refresh has two
    independent faults and the first hid the second; and the owner's own example was
    already solved by a config string on a client shipped in M2.
