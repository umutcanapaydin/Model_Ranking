---
record_type: review
id: m10-security-review
status: ratified
date: 2026-08-22
---
# Stage 4.0 Security Review — M10 (the router, the anomaly axis, the bounds)

> **VERDICT AS RETURNED: BLOCKING — 1 blocking, 0 medium, 3 minor.** Walked against
> `97e77a0..HEAD`, risk tier HIGH (a new on-device model in front of the catalogue, plus a
> refusal path that decides whether a publish happens).
>
> **K.7 is NOT satisfied on this pass and the record says so rather than implying otherwise:** the
> lead agent authored the code under review. The finding below was reached by executing the
> suspect construction rather than by reading it, which is the only reason a self-review found
> anything — every claim here cites a measurement, and the ones that could not be measured are
> marked as unverified rather than passed.

## BLOCKING-1 — `f"file:{path}?mode=ro"` does not open a database read-only

`src/app/workflows/refresh.py:376` (as written), `scripts/arena_calibration.py:66`.

The string form opens whatever URI the PATH spells. Measured, each against a fresh artifact:

| path suffix | result |
|---|---|
| `a.db?mode=rwc&z=` | connection WRITABLE; `CREATE TABLE injected` landed in the real artifact |
| `a.db#` | fragment stripped, no mode parameter survives, default `rw`; wrote |
| `a.db?` | empty query taken over; wrote |
| `a.db?vfs=unix&mode=rwc&j=` | wrote |

**Why this is blocking rather than theoretical.** `refresh.py` opens the LIVE artifact this way to
fingerprint what it currently serves. Read-only is the contract on that path, not a precaution:
the refresh's entire promise (D-129) is that it never leaves the artifact worse than it found it,
including under SIGKILL, and it keeps that promise by never holding a writable handle to the live
file while a candidate is being built. A `--db` path that defeats the mode gives the compare step
a writable handle to the artifact the app is serving.

**The part worth the record.** This fix already existed. `adapter/main.py::open_readonly` has
carried the derived construction since M6 with a docstring naming this exact defect — *"a `?` in
the path silently dropped the mode and created a database when this was string-built elsewhere"* —
and `workflows/refresh.py`, written three milestones later, string-built it anyway, under a
comment arguing that doing so was **"not a second definition of any project behaviour."** It was,
and it was the broken one. The comment's premise was sound (REQ-REF-007: the refresh must not
import the adapter) and its conclusion did not follow: the rule needed was *do not import the
ADAPTER*, not *do not share code*.

**Fixed:** the construction moved to `app/workflows/schema.py::open_readonly` — a workflows module,
so the D-116 boundary is untouched — and the adapter, the refresh and the calibration script all
call it. `tests/unit/test_readonly_uri.py` carries a case per measured shape, a fixture-blindness
guard so the parametrised cases cannot pass by everything raising, and an `ast` gate that fails any
`file:`-prefixed f-string anywhere in `src/` or `scripts/`. Three mutants, three killed — including
one that restores the exact defect.

## What was walked and held

| Surface | Question asked | Evidence | Verdict |
|---|---|---|---|
| `ios/.../Router.swift` | Can the on-device model put an arbitrary value into a request? | `Router.swift:227` re-checks `known.contains(id)` AFTER `GenerationSchema(anyOf: known)` already constrains it; the similarity tier only ever returns an id it took FROM `known`; `RoutingOutcome` has no free-text field | PASS |
| `ios/.../ContentView.swift` | Does the typed question leave the device? | `ContentView.swift:261-279` — `ask()` passes the text only to the local router; `EngineClient.swift:144-145` sends `task` and `budget` and nothing else | PASS |
| D-104 boundary | Does any model output reach the scoring path? | The router selects WHICH of nine surfaces is asked; ordering, thresholds and picks are unchanged (`REQ-RTR-004`) | PASS |
| `refresh.py` anomaly axis | Can an upstream cause a publish that a refusal should have stopped? | `upward_anomalies()` bounds gain and median-price movement at 0.25 either way; the blind-return exemption is the only bypass and is scoped to a surface coming back from zero | PASS |
| `arena.py` bounds | Unbounded allocation from a hostile upstream? | `_MAX_MERGED_ROWS = 2_000` reachable and tested; `MAX_RESPONSE_BYTES` per page unchanged | PASS |
| Secrets | Anything new committed? | `make secrets` clean at the closing tree | PASS |

## MINOR, recorded and not fixed

- **N1** — `arena_calibration.py` takes `--db` and `--category` with hand-rolled argument parsing
  rather than `argparse`. It is a developer script; the failure mode is a confusing message, not a
  wrong number. Ledgered rather than fixed to keep this wave's delta to the finding.
- **N2** — `open_readonly` resolves symlinks via `Path.resolve()`. That is correct for this use
  (the artifact is named by an operator, and following the link is the intent) but it means the
  function cannot be reused unchanged in a context where a symlink is untrusted input. Stated here
  so the next caller reads it as a property rather than discovering it.
- **N3** — **The refresh is still not scheduled**, so no finding on this path has ever been
  exercised by an unattended run. Every verdict above describes code, not operation. This is the
  same class as W-030/W-031 and is not closed by this review.

---

Reviewed by: the lead agent (Claude, Claude Code CLI) — **self-review, K.7 NOT satisfied**
Date: 2026-08-22 · Range: `97e77a0..HEAD`
