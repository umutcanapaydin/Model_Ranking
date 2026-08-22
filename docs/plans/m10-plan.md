# M10 Plan — The router, and the guard that is missing on the way up

**Status:** **DRAFT — awaiting the owner's signature.** No wave starts until it is signed.
**Date:** 2026-08-22 · **Risk tier:** **HIGH** (a free model in front of the catalogue; the guards
that decide what reaches users) · **Mode:** A0.5 + D-117 · **Process baseline:** GP v5.0 ·
**Review depth:** D-122 · M10 is not `M % 3 == 0`.

---

## 0. Three owner rulings this plan is built on

Given 2026-08-22, and each one narrows the milestone rather than widening it:

**1. Finish with what exists; revisions come later.** So `/v1` gets **no new revision window**.
D-124 permitted one and D-125 spent it, and nothing here asks for another. Anything needing a new
payload field is out of M10 by construction — which removes the saturation disclosure (W-035) from
this milestone and leaves it stated in the ledger where it already is.

**2. Do not let M9's refresh make decisions on its own.** The cycle may prepare, compare and
REFUSE. It may not acquire new judgement. Practically: every axis added here errs toward refusing
and telling somebody, never toward "this looks fabricated but I will publish it anyway", and no
wave in this milestone adds autonomy the refresh does not already have.

**3. The free routing model goes on the home screen, in place of the first block of text.** D-126
ruled this at M8 — *"the router picks the QUESTION; the engine answers it"* — and **it has never
been given a REQ-ID or a wave.** It is the product's front door and it does not exist. That is
this milestone's first wave.

---

## 1. Why this milestone exists

Two things are missing, one from the product and one from the machinery, and they are the same
milestone because both are about what happens at the edges of what this engine can vouch for.

**The product has no front door.** Nine categories are reachable only by tapping a chip whose
wording the user has to map onto their own question. D-126 settled the answer — a free model reads
the question and picks the surface — and settled its boundary in the same breath: **it may never
say a model is good.** Not "I recommend", not "this one is best for you". It picks the question;
the engine answers it. That line is what keeps this product a dashboard over measurements rather
than one more assistant with opinions.

**The machinery has no guard on the way up.** M9's Stage-4.0 review named it: every automated
defence on served content is a SHRINKAGE detector. The `minimum_rows` floors catch a source going
short; D-128 catches a surface going blind, losing a quarter of its models, or pricing a budget
out. Every one exempts gains. **An upstream that ADDS fabricated high-rated models, renames
existing ones, or drops prices produces a larger, cheaper artifact that every check calls healthy
and that ships twice a day.** Five sources, TLS only, no pinning, no signature, no provenance —
and the build report a human used to read now goes to a log nobody opens. That is W-049, and it is
the failure the refresh CREATED rather than one it exposed.

### The two traps

**Trap 1 — the router acquiring an opinion.** It will be asked to. A user will type "which is
best", and the honest answer is to route that to a surface and let the engine answer with its
disclosures. The boundary must be STRUCTURAL, not a prompt instruction: **the router returns one id
from a closed set of nine, and anything else is discarded.** A model cannot be talked into
recommending if the only thing the product can read from it is a category id — and a user typing
"ignore your instructions" then gets the manual chips, which is a worse experience and not a wrong
answer.

**Trap 2 — adding guards until nothing publishes.** A threshold tuned to catch a fabricated model
also catches a real new one, and a product that refuses every genuine improvement freezes while
reporting health. **The freeze is worse than the bad publish**, because a freeze is invisible.
Every axis added here must state, in its ADR, what ORDINARY upstream movement looks like on that
axis and why the threshold does not catch it — the sentence D-128 lacked and had to be corrected
for.

---

## 2. Acceptance criteria (new REQ-IDs — into `docs/prd.md` AT W1, not at closure)

| # | REQ-ID | Criterion | Verified by |
|---|---|---|---|
| 1 | **REQ-RTR-001** | A user types a question in their own words and the app opens the surface that answers it. The router's choice is SHOWN and can be changed with one tap (D-126). | A question per surface routes correctly; the chosen surface is visible and overridable |
| 2 | **REQ-RTR-002** | **The router can only ever return one of the nine category ids.** Any other output — a recommendation, a model name, prose, an injected instruction — is discarded and the user gets the manual chips. | Adversarial inputs, including explicit attempts to make it name a model, produce either a valid id or the fallback, never a recommendation |
| 3 | **REQ-RTR-003** | The router is never required. If it is unreachable, slow, rate-limited or wrong, the product still works by tapping a chip, and says which happened. | Each condition forced; the app remains usable and states the condition |
| 4 | **REQ-RTR-004** | Nothing the user types reaches the ENGINE, and nothing the engine serves is influenced by the router beyond which surface is opened. The scoring path is untouched (D-104). | A test that the routing call and the recommendation call share no data but the category id |
| 5 | **REQ-GRD-001** | A refresh REFUSES a candidate whose evidence moved upward in a way ordinary upstream movement does not produce: a surface gaining more than a stated share of previously-unseen model names, or its median published price moving more than a stated share. **It refuses; it never judges and publishes.** | A candidate with fabricated high-rated models is refused and NAMES the surface; a candidate with one genuine new model publishes |
| 6 | **REQ-GRD-002** | No refresh can be made to allocate without bound by an upstream: every paginating client caps total accumulated rows and bytes, not only its request count. | A hostile fixture serving full pages to the cap is refused loudly |
| 7 | **REQ-GRD-003** | The refresh states its environment assumptions as CHECKS — the directory it locks and publishes in is not group- or world-writable, and a timestamp it reads is finite and not in the future. | Each assumption violated in a fixture produces a refusal, not a silent pass |
| 8 | **REQ-EVI-002** | The population the engine actually ranks — reconciled AND priced — has a NAME in the code, and calibration is required to call it. | A citing test that fails if a threshold is derived from any other population (W-037) |

**Criterion-to-wave map:** W1 owns 1–4. W2 owns 5. W3 owns 6, 7, 8. W4 closure.

---

## 3. Waves

### W1 — The router (risk: **HIGH**, and it is the wave the owner wants to see)

A free model in front of the catalogue, on the home screen, in place of the first block of text.

The whole wave is the boundary. The model reads a question and returns a category id; the app
validates that id against the nine it already fetches from `/v1/categories` and discards anything
else. **The engine is not touched** — no new route, no payload change, no LLM anywhere near the
scoring path (D-104). The router picks which existing question to ask.

Three things to settle at the wave and NOT assume here: which free model and on whose terms (§5.1),
what the app does with a question that fits no surface, and whether the typed text leaves the
device at all before the owner has said it may.

### W2 — The upward-anomaly axis (risk: **HIGH**)

W-049. Set names, not counts: a real board adds models one or two at a time and a fabricated set
arrives at once. Price movement is the second axis with its own threshold and its own
ordinary-movement sentence.

Under ruling 2 the outcome is always **refuse**, never a judgement call that publishes anyway. An
independent seat is required on this wave — M9 closed two of three waves without one and the seats
that ran found six BLOCKING between them.

### W3 — Bounds, environment, and a name for the ranked population (risk: **MED**)

W-050, W-051 and W-037. Three small things sharing one sentence: **assumptions this code makes
about the world and does not check.**

### W4 — Closure (risk: **LOW**)

---

## 4. Shared contracts (K.8)

**FROZEN and not moved by this milestone:** the `/v1` payload — no unspent revision window exists
and ruling 1 forbids opening one. Also D-104 (no LLM in the scoring path — **the router is in front
of the catalogue, not inside it**, and REQ-RTR-004 is what proves that), D-105, D-109, D-118,
D-120, D-128 (amendable, with its ordinary-movement sentence), D-130.

**Touched:** the iOS client, and `app.workflows.refresh`.

---

## 5. Three questions to answer before W1 writes any code

**1. Which free model, and does the user's typed question leave the device?** A routing call sends
what somebody typed to a third party. That is a privacy decision and it is the owner's, not a
default. If the answer is "not yet", W1 ships the boundary and the fallback with an on-device or
keyword router and the model arrives later — the structure is the same either way.

**2. What happens to a question that fits no surface?** "Which AI should I use to do my taxes" maps
to nothing this product measures. Saying so plainly is the honest answer and it is also a product
decision about how often the front door says no.

**3. What does the escalation counter escalate TO?** M9 added it and nobody has said. Under ruling
2 the refresh refuses more often, so this stops being theoretical: a refusal that reaches nobody is
a product that quietly stops updating. Today the only channel is `runner`, which only speaks when
the owner runs it.

---

## 6. What this milestone is NOT

- **Not a `/v1` revision.** Ruling 1. The saturation disclosure (W-035) waits.
- **Not more refresh autonomy.** Ruling 2.
- **Not the deploy.** D-123 undischarged for a third milestone; W-030/W-031 stay unverifiable.
- **Not the iOS test target** (W-038), and it is worth naming that this milestone puts real logic in
  the client while no Swift is executed by any gate. The router's boundary is therefore enforced
  where it CAN be tested — in the validation of the returned id, which is data the Python side can
  see — rather than in the client alone.
- **Not the design pass.** The owner has said the interface gets its attention after the coding.
