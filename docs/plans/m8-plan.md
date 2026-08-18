# M8 Plan — The iOS app: the engine gets its first real reader

**Status:** DRAFT — awaiting the owner's signature. No wave dispatches until it is SIGNED.
**Date:** 2026-08-18 · **Risk tier:** MED (a new client codebase; the engine's frozen surface is
touched only if the owner rules it may be)
**Mode:** A0.5 + **D-117** · **Process baseline:** GP v5.0 (D-113) · **Review depth:** **D-122**
**Quarterly obligation:** M8 is not `M % 3 == 0`. `note.txt` refresh still mandatory at 4.4.

---

## 0. Why this milestone exists

The engine has answered questions correctly since M3 and over HTTP since M6, and **nothing has ever
consumed it except its own tests.** `/v1` was designed, frozen (D-115) and reviewed by people
imagining a client. M8 writes the client.

That ordering is the milestone's whole risk and its whole value. M6 demonstrated four separate times
that an enumeration written by someone imagining the cases misses the one that matters; a payload
designed without a reader is the same bet at a larger scale. **The first real consumer is the first
honest test of the contract.**

**Nothing is deployed and nothing needs to be** (D-123). The app runs in the iOS Simulator, which is
free, and reaches the engine at `http://127.0.0.1:8080` via `make run` on the owner's Mac. Money
enters the project at exactly two later moments, both the owner's: an Apple Developer membership to
put the app on someone else's device, and Fly.io when something off this machine must call the
engine.

### The traps this milestone must not walk into

**Trap 1 — Re-implementing the engine in Swift.** The app renders answers; it does not compute them.
No ranking, no budget arithmetic, no median, no "just this one sort" on the client. D-104 (no LLM in
the scoring path) and D-105 (no cross-scale averaging) are engine invariants, and the fastest way to
break them is a client that quietly re-derives a number the API already sent. **If a screen needs a
value the API does not serve, that is a finding against the API, not a licence to compute it.**

**Trap 2 — Letting the client silently fix the server's honesty.** `/v1` deliberately returns
answers with zero picks plus an `unavailable_reason`, and surfaces that disclose stale or missing
evidence. A client that hides an empty answer, or renders a `source_health.stale` notice as nothing,
undoes the exact property three security rounds were spent building. **Every disclosure the API
sends must be visible to the user**, and where it is not, that is a deliberate design decision the
owner makes rather than a rendering convenience.

**Trap 3 — Deciding the frozen contract is negotiable one field at a time.** M8 will find fields it
wishes were shaped differently. The carried question (§5) exists so that "may the contract move" is
answered once, in the abstract, BEFORE a specific field makes it tempting. Until it is answered,
`/v1` is frozen.

**Trap 4 — A simulator that talks to a server that is not this one.** The engine must be running,
built from a current artifact, or the app shows plausible nonsense. `advisor.db` is gitignored and
the process refuses to boot on an unbuilt one — but a stale artifact boots fine and answers with
old prices. **The app must display the build stamp and evidence dates the API already sends**, so
the owner can always see what he is looking at.

---

## 1. Acceptance criteria (REQ-IDs)

New REQ-IDs are proposed here and must be copied into `docs/prd.md` at W1, not at closure.

| # | REQ-ID | Criterion | Verified by |
|---|---|---|---|
| 1 | **REQ-APP-001** (new) | A SwiftUI app runs in the iOS Simulator, asks the engine for a recommendation, and renders the real answer — no mock data anywhere in the shipping target | A run against a live `make run`, and a build that has no fixture JSON compiled in |
| 2 | **REQ-APP-002** (new) | **Ruling A survives the client.** A coding request shows BOTH coding surfaces with neither presented as the winner — no default tab, no first-position emphasis, no sort that ranks them | A UI test asserting both surfaces are present and equally prominent |
| 3 | **REQ-APP-003** (new) | Every disclosure the API sends is visible: `unavailable_reason`, `source_health` staleness notices, undated-evidence notices, and the ordering note | A test per disclosure type, driven by a canned payload that carries it |
| 4 | **REQ-APP-004** (new) | The app degrades honestly: engine unreachable, 503, an empty answer and a slow response each produce a stated condition, never a blank screen or a spinner that never ends | Each condition forced against a real or stubbed endpoint |
| 5 | **REQ-APP-005** (new) | The app computes no ranking value of its own. Scores, prices and orderings are rendered as received | Review + a grep-style check that the client has no arithmetic on served numbers |
| 6 | **REQ-API-010** (new) | Any contract gap the client finds is recorded as a finding against `/v1` before any client-side workaround | The ledger, and the carried question's ruling |

**Criterion-to-wave map:** W1 owns 1. W2 owns 2 and 3. W3 owns 4 and 5. W4 owns 6 and closure.

---

## 2. Waves

### W1 — One screen, real data (risk: **MED**)

A single screen that calls `/v1/recommendations?task=coding&budget=unlimited` and shows what comes
back. No design work, no navigation. The point is the seam: Swift's decoder against the real
payload, on the simulator's network stack, against a running engine.

Expected to surface contract friction immediately — that is the wave's product. Every piece goes to
the ledger as a finding against `/v1`, not into a client-side patch (Trap 3).

### W2 — Ruling A and the disclosures (risk: **MED**, and this is the wave that matters)

Both coding answers, neither leading, and every disclosure the API sends made visible. This is where
a client most easily undoes server-side honesty: a tab bar makes one answer primary, a card layout
buries `unavailable_reason`, a "clean" design drops the staleness notice.

Deliberate design decision required from the owner: **how do you show two equal answers to one
question on a phone screen?** There is no neutral default — a list has a first item, tabs have a
selected one. This is Ruling A's real cost, arriving three milestones after the ruling.

### W3 — Failure states (risk: **MED**)

Engine down, 503 unbuilt artifact, empty answer, slow response, no network. Each gets a stated
screen. The engine already produces an honest sentence for most of these; the app's job is to show
it rather than replace it with "Something went wrong".

### W4 — Owner review, closure, and the deploy decision (risk: **LOW**)

The owner uses the app and gives feedback; fixes land as normal waves. Closure then names, plainly,
what has to happen for the app to reach anyone else: an Apple Developer membership, a deployed
engine (D-123's trigger), and the two rows that remain unverified without one — **W-030** and
**W-031**.

---

## 3. Shared contracts (K.8)

**FROZEN and out of scope unless the carried question is answered otherwise:** the `/v1` payload
(**D-115**), English query values (**D-118**), and every engine invariant — D-104 (no LLM in
scoring), D-105 (no cross-scale averaging), D-109 (rounding at the output boundary only).

The client reads `/v1/categories` and `/v1/recommendations`. It writes nothing; there is no mutating
route to write to (REQ-API-001).

**To be grep-verified at W1 dispatch, not now:** the exact field set of a `Pick` and an answer, taken
from `PUBLIC_PICK_FIELDS` and `PUBLIC_ANSWER_FIELDS` in `src/app/adapter/main.py` rather than from a
sample response, because a sample shows only the fields that happened to be populated.

---

## 4. Definition of done

`make check` exit 0 in the engine repo, unchanged by M8 unless a contract finding is ruled in · the
app builds and runs in the Simulator against a live engine · every criterion in §1 has a citing test
able to fail · fault injection on the client's failure states · fresh-eyes review per D-122 (the
client is not the scoring path: single pass, round cap of two, escalate-now unchanged) · ADRs for
every contract question the client raises · retrospective answering M7's carried question and posing
the next · dated `docs/EXPERIENCE.md` entry · `note.txt` refreshed · `docs/closure-report-m8.md`.

**Open questions carried in, and none of them blocks W1:** W-019, W-024 (arena's upstream 500),
W-025, W-027, W-028, W-029, W-030, W-031, W-032, and GPF-001..005.

---

## 5. The question that must be answered before W2

M7's retrospective poses it and M8 cannot get far without a ruling:

> **`/v1` was frozen by D-115 with no consumer in existence. Now that a real client is being written
> against it, does "frozen" mean frozen before or after the first real reader?**

**Holding it:** a contract that moves when its first consumer complains is not a contract, and D-115
exists because Ruling A was trivial to state and took three review rounds to enforce.

**One revision:** every field in that payload was designed by someone imagining a client, and M6
proved four times over that imagined enumerations miss the member that matters.

**Answer it in the abstract, now** — not in the moment a specific field turns out to be
inconvenient, which is when the answer stops being a principle and becomes a rationalisation.

---

## 6. Signature

The owner signs by changing **Status** at the top of this file to SIGNED with a date. Until then no
wave dispatches, per the standing rule that no wave starts without a signed plan.
