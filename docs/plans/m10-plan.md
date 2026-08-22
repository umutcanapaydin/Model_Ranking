# M10 Plan — What this system does when it is wrong and nobody is looking

**Status:** **DRAFT — awaiting the owner's signature.** No wave starts until it is signed.
**Date:** 2026-08-22 · **Risk tier:** **HIGH** (the guards that decide what reaches users)
**Mode:** A0.5 + D-117 · **Process baseline:** GP v5.0 · **Review depth:** D-122
**Quarterly obligation:** M10 is not `M % 3 == 0`. `note.txt` refresh still mandatory at 4.4.

---

## 0. Why this milestone exists

M9's retrospective carried this question forward, and it is this milestone's whole shape:

> **The refresh removes the last human from the loop, and the human was the error-detection
> mechanism for everything the gates do not cover.** A build that "fails loud" is loud to somebody
> reading. So: what does this system do when it is wrong and nobody is looking?

M9 answered part of it by accident. Its own Stage-4.0 review named the half that is missing, and
it is not a hypothetical:

**Every automated defence on served content is a SHRINKAGE detector.** The `minimum_rows` floors
catch a source going short. D-128 catches a surface going blind, losing a quarter of its models, or
pricing a budget out. Every one of them explicitly exempts gains and score movement, on the
reasoning — correct, as far as it goes — that a model getting worse is news rather than damage.

**The inverse has no guard at all.** An upstream that ADDS fabricated models with high ratings,
renames existing ones, or drops prices produces a larger, cheaper artifact. Every check reports
healthy. It ships to users twice a day. Five remote sources are fetched over TLS with no pinning,
no signature and no provenance, and the build report that a human used to read now goes to a log
nothing opens.

**That is the failure mode the refresh CREATED**, not one it exposed, and it is W-049.

### The trap this milestone must not walk into

**Adding guards until nothing publishes.** M9 established the shape of this risk and it applies
harder here: a guard tuned to catch a fabricated model will also catch a real new model, and a
product that refuses every genuine improvement freezes while reporting health. **The freeze remains
worse than the bad publish**, because a freeze is invisible and a bad publish is at least a wrong
answer somebody can see.

So every axis added in this milestone must state, in its ADR, what ORDINARY upstream movement looks
like on that axis and why the threshold does not catch it. A threshold without that sentence is a
guess wearing a number — which D-128 already had to correct once, when its worked arithmetic turned
out to be off by one in both examples.

---

## 1. Acceptance criteria (new REQ-IDs — into `docs/prd.md` AT W1, not at closure)

| # | REQ-ID | Criterion | Verified by |
|---|---|---|---|
| 1 | **REQ-GRD-001** | A refresh refuses a candidate whose evidence moved UPWARD in a way ordinary upstream movement does not produce: a surface gaining more than a stated share of previously-unseen model names, or a surface's median published price moving more than a stated share. | A candidate built with fabricated high-rated models is refused and NAMES the surface; a candidate with one genuine new model publishes |
| 2 | **REQ-GRD-002** | No single refresh can be made to allocate without bound by an upstream. Every paginating client caps total accumulated rows and bytes, not only its request count. | A hostile fixture serving full pages to the page cap is refused loudly rather than accumulated |
| 3 | **REQ-GRD-003** | The refresh states its environment assumptions as CHECKS. The directory it locks and publishes in is verified not group- or world-writable at startup, and a timestamp it reads is verified finite and not in the future. | Each assumption violated in a fixture produces a refusal, not a silent pass |
| 4 | **REQ-GRD-004** | Nothing a refresh writes can make `runner` lie or crash: every value it prints is bounded, sanitized, and defined for the hostile case. | A record containing `NaN`, a future timestamp, ANSI escapes and an oversized reason is handled and reported honestly |
| 5 | **REQ-EVI-001** | A surface whose primary benchmark can no longer separate its top models SAYS so, on the surface, in the payload. | The two saturated boards produce the disclosure; a healthy board does not (W-035) |
| 6 | **REQ-EVI-002** | The population the engine actually ranks — reconciled AND priced — has a NAME in the code, and calibration work is required to call it. | A citing test that fails if a threshold is derived from any other population (W-037) |

**Criterion-to-wave map:** W1 owns 1. W2 owns 2, 3, 4. W3 owns 5 and 6. W4 closure.

---

## 2. Waves

### W1 — The upward-anomaly axis (risk: **HIGH**, and this is the wave that matters)

W-049. The guard that does not exist. Its whole difficulty is the trap in §0: the axis must
distinguish "an upstream published twelve models that do not exist" from "an upstream published a
new model", and those look identical to a row count.

The likely shape, to be decided at the wave and not assumed here: compare the SET of model names, not
the count, and treat a large fraction of previously-unseen names as the signal — a real board adds
models one or two at a time, and a fabricated one arrives all at once. Price movement is the second
axis and needs its own threshold with its own ordinary-movement sentence.

**Full depth under D-122**: this is the supply line of the scoring path, and an independent seat is
required on this wave. M9 closed two of three waves without one and the seats that ran found six
BLOCKING between them.

### W2 — Bounds and the environment assumptions (risk: **MED**)

W-050 and W-051 together, because they are the same sentence: **things this code assumes about the
world and does not check.** Aggregate allocation, directory permissions, timestamp sanity, and the
values `runner` prints to the person deciding whether the product is healthy.

### W3 — Two surfaces that are quietly becoming wrong (risk: **MED**)

W-035 and W-037, and this is the product half of the same question.

`expert` and `mathematics` rank on boards that have stopped separating their top models: on GPQA the
twelve highest-scoring priced models span 1.8 points against a 2.52 standard error, and on AIME
three models tie at exactly 100.0. The engine handles it honestly per-answer — `close_call` fires —
but **nothing says the SURFACE is saturated**, and a board at its ceiling cannot record next
quarter's improvement. It gets less informative on its own, with every gate green. That is the
milestone's question in the data rather than in the machinery.

W-037 rides along because it is one named accessor and it prevents a fourth wrong calibration.

### W4 — Closure (risk: **LOW**)

---

## 3. Shared contracts (K.8)

**FROZEN, and this milestone must not move it without a new ADR:** the `/v1` payload. D-115 froze
it, D-124 permitted ONE revision during M8, and D-125 spent that revision. **There is no unspent
window.** REQ-EVI-001 needs a saturation disclosure on a surface, which is a payload field — so it
requires an ADR opening a new window, and that ADR is §5's first question rather than something a
wave decides on the way past.

Also frozen: D-104, D-105, D-109, D-118, D-120, D-128 (amendable, with its ordinary-movement
sentence), D-130.

---

## 4. Definition of done

`make check` exit 0 — now nine gates including conformance · every criterion with a citing test
**proven RED** · fault injection with an INDEPENDENT mutant set on W1 (M9 measured the difference:
40 mutants and 8 survivors against a self-designed 24 with none) · fresh-eyes review, **mandatory on
W1** · ADRs for every §5 question · retrospective · dated EXPERIENCE entry · `note.txt` ·
`docs/closure-report-m10.md`.

**Carried in and NOT blocking W1:** W-030, W-031 (unverifiable without a deploy), W-036, W-038,
W-039, W-044, GPF-001..006.

---

## 5. Three questions to answer before W1 writes a threshold

**1. Does `/v1` get a new revision window?** REQ-EVI-001 cannot ship without a payload field, and
there is no unspent window. Either a new ADR opens one — with the same one-shot discipline D-124
had — or the saturation disclosure waits and W3 ships only W-037. **Decide this before W3 makes a
specific field tempting**, which is exactly why D-124 was written in the abstract.

**2. What does ordinary upstream movement look like?** Every threshold in W1 needs this measured,
not estimated. The project has the data: nine boards, and a build history. **A threshold set without
measuring the normal case is the mistake D-128 made and had to correct.**

**3. What is the refresh allowed to do on its own, ever?** Today it can replace what every user
reads, unattended, on a timer. It cannot yet refuse permanently, alert anybody, or stop itself. As
the guards get better at catching bad candidates, the product gets closer to a state where it
refuses everything and reports health. **Is there a point at which the refresh should stop trying
and demand a human?** M9 added an escalation counter and nobody has said what it escalates TO.

---

## 6. What this milestone is NOT

- **Not the deploy.** D-123 is undischarged for a third milestone and W-030/W-031 stay unverifiable.
  If the owner deploys, that is its own milestone.
- **Not the iOS test target** (W-038). It is real, it has been open since M8, and it is a
  `project.pbxproj` edit plus a test suite — a milestone's worth of work in the wrong subject.
- **Not new categories or new sources.** Nine surfaces is settled (D-127).
- **Not the design.** The owner has said the interface gets its attention after the coding.
