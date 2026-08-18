---
record_type: wave
id: m7-wave-4-close
status: draft
process_version: v5.0
date: 2026-08-18
---
# Wave-Close Checklist — M7 Wave 4 (deploy readiness, without the deploy)

> **STATUS: CLOSED 2026-08-18, with go-live moved to M8 by the owner (D-123).** Everything W4 owned
> except the deploy itself was built, run and measured. The deploy stopped on a Fly.io payment
> method, and the owner ruled that a hosted endpoint buys nothing until the iOS client needs one —
> the simulator reaches the engine on `localhost`, and Xcode is free.

## What the wave delivered

`scripts/journey.py` had shipped as a template since v4.1 with three TODO stubs. It is wired for
this product now, and — the part that matters in a project that keeps finding controls which never
ran — it was **executed**, in three configurations:

| Target | Result |
|---|---|
| local `uvicorn` | 4/4 PASS |
| the real container, artifact **mounted** not baked (D-116) | 4/4 PASS, `/health build=m7w4-local` |
| no server listening | **exit 1** — the journey can fail |
| a `file://` base URL | **all four fail** — the scheme is checked, not the linter suppressed |

Step 2 is **declared N/A rather than left stubbed**, and the distinction is the wave's small lesson:
this is a public read-only API with no credential surface (D-115), so the step ASSERTS that no
authenticated route exists. An unwired step exits 2 forever; a bare claim of N/A would exit 0
forever. If anyone adds authentication, the step starts failing and they inherit the job of wiring
it.

Step 3 asserts **content**, not status — both coding surfaces present, every pick carrying a
populated label/model/score/price/why, a numeric score, and no precedence field. Status alone would
have blessed the artifact W-023 shipped, which answered 200 with zero picks while `/health` reported
a healthy build.

**The container fails closed, proven in the deploy shape rather than asserted:**

- unbuilt database → exits 1, naming `app.workflows.build`
- pre-M5 database → exits 1, naming `schema migrate`

| # | Check | Evidence | ✅ |
|---|---|---|---|
| 1 | Risk tier — D-122 | Plumbing ⇒ single pass. The Stage-4.0 closure review covers this surface and is separate from the wave tier | ✅ |
| 2 | REQ-API-009 citing evidence | `scripts/journey.py` exit 0 against a container; falsified two ways | **PARTIAL — W-030** |
| 3 | L.7 build stamp | `/health` returns `{"status":"ok","version":"0.1.0","build":"m7w4-local"}` from inside the image | ✅ |
| 4 | Stage 4.0 security PASS before deploy | PASS, 0 BLOCKING, 8 MINOR — six fixed, two accepted as unverified-without-a-deploy | ✅ |
| 5 | `make smoke-deps` exit 0 | **NO** — arena's upstream 500 (W-024). Handled by D-121: the artifact ships without assistant evidence and the surface discloses it | **WAIVED — W-024** |
| 6 | Deploy executed | **NO — deferred to M8 by D-123.** Nothing was created on Fly.io; there is no half-provisioned state | **DEFERRED** |
| 7 | Gates green | `make check` exit 0 · 511 passed / 12 skipped · gitleaks clean | ✅ |

## What is NOT verified, and must not be read as covered

The Stage-4.0 seat marked two things unverified *because no deployment existed*, and deferring the
deploy leaves them exactly there. They are ledgered as **W-030** (REQ-API-009's over-the-network
half — TLS, DNS, Fly's proxy, real latency) and **W-031** (volume permissions against a non-root
uid, machine OOM and restart behaviour, `force_https`). A local container is a good proxy for a
platform and is not the platform.
