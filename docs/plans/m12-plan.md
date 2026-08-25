---
record_type: plan
id: m12-plan
status: draft
process_version: v5.0
date: 2026-08-25
---
# M12 Plan — the 60-year-old CFO can use it

> **AWAITING SIGNATURE.** Five waves. No money is spent and nothing deploys.

## 0. The four rulings this plan is built on

Taken 2026-08-25, after the council:

1. **The app gets a budget picker.** The product's own description is "budget-aware" and
   `ContentView.swift:29` hardcodes `unlimited`. Everything M11 built for W-044 — `/v1/budgets`,
   `eligible_count`, the "25 fit your budget" line — currently serves a control that does not exist.
2. **`subscribe.py` is PARKED, deliberately, and revisited at M13.** 599 lines that answer the
   CFO's literal question are on no HTTP route. The council said route it or decide out loud that
   it is not part of the product; this is the third answer — *not yet* — and it is recorded so it
   stops being an accident.
3. **A structural absence is stated once, not per surface** (D-135). Not a reduction in disclosure;
   a reduction in repetition.
4. **`C2b` is wired to something it can count.** It groups on a free-text column where all 22 rows
   are unique, so it cannot fire — while two records assert that it did.

**`shellcheck` was offered and NOT chosen.** W-074 stays open. Recorded here rather than treated as
an oversight: the owner declined a gate, which is his to decline, and the next person should not
find it quietly added.

## 1. Why this milestone exists

Eleven milestones specified this product, and every requirement written before 2026-08-23 came from
someone who already knew what a benchmark was. Then the owner gave the app to a 60-year-old CFO,
who produced five requirements in twenty minutes, four of which are one finding:

> **the product explains what it measured in the language of the measurement.**

`161.7 ECI`. `$1.03/1M`. `Abstract reasoning`. All correct. None usable.

The council then found the same shape one layer down and a dozen times over — a thing asserted
somewhere and exercised nowhere — including a product that calls itself budget-aware and has no
budget control. **M12 is where this product stops being right and starts being usable**, and the
two are not the same achievement.

### The two traps

**Trap 1 — making it simpler by making it vaguer.** Every number on that screen is defensible and
several are load-bearing. "83.5% resolved" must not become "very good". The work is to say what the
number MEANS beside it, never to replace it.

**Trap 2 — a disclosure pass that quietly becomes a disclosure cut.** D-135 exists to stop that and
states its own test: after any change, can a reader still learn every limitation that applies to
the answer in front of them? If not, D-121 governs and the change is wrong.

## 2. Acceptance criteria (new REQ-IDs — into `docs/prd.md` AT THE WAVE)

| REQ-ID | Criterion |
|---|---|
| REQ-CMP-001 | Every number a reader meets carries, beside it, something that says what it means without domain knowledge — including a RANK where the scale is arbitrary (`ECI`, `elo`). |
| REQ-CMP-002 | Price is expressed in a unit a person outside this industry uses, without removing the exact figure. |
| REQ-CMP-003 | Every surface name says what the surface measures, in words a non-specialist would choose. No two surfaces begin with the same word. |
| REQ-DSC-001 | A limitation that is a property of a SOURCE is stated once per source; a limitation that is a STATE of the data keeps its warning treatment (D-135). Every fact remains reachable. |
| REQ-BGT-001 | A reader can choose a budget in the app, and the answer changes when they do. |
| REQ-LOC-001 | `/v1` returns the FACTS behind each sentence; the client composes the sentence, in English or Turkish, from those facts alone. |
| REQ-LOC-002 | Text matching in the client is correct under a Turkish locale, pinned by a test that SETS the locale rather than inheriting it. |
| REQ-GOV-001 | Every ADR cited anywhere in this repository exists; `C2b` counts something it can actually reach. |

## 3. Waves

### W1 — Foundations that are currently false (risk: **MED**)
First, because everything after it is written on top of these and they are cheap now.

- **D-119 and D-120 do not exist** and are cited in 27 files as a K.8 frozen contract — including
  `build.py`, three tests, and the M10 and M11 plans. Write them, **dated today**, describing a
  contract in force since M6. Not backdated: backdating would commit the defect a second time.
- **`make gate` exits 2 on a clean tree** and is the only thing the post-edit hook runs. One line.
- **`C2b` grouped by control name**, so the ten K.7 bypasses it never counted become visible. Fix
  the two records that assert it fired.
- **The Turkish case-folding defect** (`Router.swift`, `localizedCaseInsensitiveContains`), with a
  test that sets the locale. **This must land before Turkish ships**, and it is here rather than in
  W4 for exactly that reason.
- A gate that fails any citation to an ADR that does not exist. Ship the gate with the rule
  (V4C-49) — the phantom-ADR class is now a known shape and must not recur.

### W2 — The comprehension pass (risk: **MED**)
REQ-CMP-001/002/003, REQ-DSC-001. The CFO's items 3, 4, 5 and ruling 3.

- Category names from the council's table; no two beginning with the same word.
- `≈ $1 per 1,500 pages of text` beside the exact `$1.03/1M`.
- A rank beside every score, and one sentence saying what the scale is. Rank comes from the
  engine's own ordering — reading a position, not computing one (Trap 1 of the M11 plan stands).
- Disclosures under D-135, with the reader-can-still-learn-everything test applied and recorded.
- **The full 28-row inventory** in `docs/reviews/m11-council-product.md` is the work list, not the
  CFO's five. He found the ones he happened to hit.

### W3 — The budget picker (risk: **LOW**)
REQ-BGT-001. Small, and it makes a milestone of existing work live.

- Three choices under the category strip. `/v1/budgets` already publishes the caps.
- The `eligible_count` line stops being a dead branch.
- Fix `scripts/simulator_session.sh`, which instructs the owner to use a control that does not exist.

### W4 — Turkish (risk: **HIGH**)
REQ-LOC-001, REQ-LOC-002. The contract move, and the largest piece.

- `/v1` returns structured facts where it now returns prose: `pick.why`, `trade_off`,
  `ordering_note`, the notices, `unavailable_reason`. **This is a payload change and needs its own
  ADR**, because D-115 froze the payload and D-124's one window was spent by D-125.
- The client composes both languages from those facts. A flag switch in the top-right.
- Category titles and every product sentence move client-side with it.
- **Risk is HIGH for a measured reason:** `ContentView.swift` is 551 unexecuted lines, and the M11
  council found that the Python guard over it (416 lines of regex) was written for the architecture
  this wave inverts. The mitigation is in the plan, not in the wave: move composition into an
  `@Observable` model inside `ios/ModelRanking/Engine/`, where the Swift test target already
  reaches — the Senior Mobile seat's recommendation, and it needs no project-file edit.

### W5 — Closure (risk: **LOW**)
Stage 4.0 under D-133 with an independent seat, then 4.1, 4.2, 4.4. **4.3 does not run.**

## 4. Shared contracts (K.8)

**MOVED, deliberately, once:** the `/v1` answer payload at W4, under a new ADR. Everything else
frozen: D-104 (no LLM in the scoring path — the composition is a CLIENT concern and the engine
still decides every number), D-105, D-109, D-118, D-128..D-135, INV-23.

**Touched:** `ios/` throughout, `src/app/adapter/main.py`, `src/app/workflows/serialize.py`,
`src/app/workflows/recommend.py`, `scripts/check_records.py`, `scripts/wave_check.py`,
`Makefile`, `docs/decisions.md`.

## 5. What this milestone is NOT

- **Not a deploy.** D-123, W-030, W-031 stay open for a fifth milestone, by the owner's sequencing:
  finish locally, then his phone, then the App Store.
- **Not the phone.** The Senior Mobile seat found the device build has never once succeeded
  (`DEVELOPMENT_TEAM` appears zero times) — that is real, and it needs an Apple account. It is the
  next milestone's opening, not this one's.
- **Not `subscribe.py`.** Ruling 2. Parked with a date.
- **Not `shellcheck`.** Offered, declined, W-074 stays open.
- **Not a redesign.** The card direction is set and the owner has used it.

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25
