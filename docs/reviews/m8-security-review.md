---
record_type: review
id: m8-security-review
status: ratified
date: 2026-08-19
---
# Stage 4.0 Security Review — M8 (the client, and the six categories behind it)

> **VERDICT: PASS, 0 BLOCKING.** One positive finding worth protecting, two notes carried.
>
> **This pass was run by the agent that wrote the code.** K.7 fresh eyes were not available and the
> owner ruled on 2026-08-18 that the methodology be lightened and waves not stop for review. That
> makes this a self-review, and a self-review's PASS is worth exactly what M6-W1 measured it at:
> the reviews that found the most there were run by seats that had not written the code. Recorded
> as the third `control-bypass` under V4C-13; `C2b` has fired and the CONTROL goes to M9.
>
> **Nothing is deployed** (D-123 unspent; see §4). This pass therefore gates no deploy.

## 1. What M8 actually exposed

The milestone added one genuinely new trust boundary: **a client process that speaks to the engine
over the network.** Everything else is data — six `CategorySpec` entries, seven Epoch board
declarations — read from a bundle the owner places by hand under the M5 data-boundary invariant.

| Surface | Change | Assessment |
|---|---|---|
| `ios/ModelRanking/Engine/EngineClient.swift` | New HTTP client, GET only | No mutating route exists to call (REQ-API-001). The client writes nothing, stores nothing, and holds no credential |
| App Transport Security | **No key set at all** | See §2 — this is the finding |
| `src/app/clients/epoch_board.py` | Reads owner-placed CSVs | Local file read inside the declared bundle; no runtime fetch, so D-101's acquisition boundary holds. A missing declared column raises `SourceError` loudly rather than yielding a silent empty board |
| `src/app/workflows/build.py` | `boards` parameter | Build-time only. Not reachable from the serving process |
| `/v1/categories` | Gains its first consumer | Read-only, derives from `CATEGORIES`, leaks no path and no configuration |

## 2. The finding: ATS is correct, and correct BY ABSENCE

`ios/ModelRanking.xcodeproj` declares **no `NSAppTransportSecurity` key**, so App Transport Security
is at its default. The app reaches `http://127.0.0.1:8080` today only because iOS exempts loopback
from the cleartext ban without configuration.

**That is the safe state and it is safe by accident of good defaults, not by decision.** The
consequence is the part to protect: **the day `baseURL` points at a deployed engine (D-116), iOS
will REFUSE the connection unless it is HTTPS.** The app will appear broken, and the fastest way to
"fix" it is `NSAllowsArbitraryLoads = true`, which permits cleartext to *every* host and would ship
this product's first real network call unencrypted.

**Recorded so that the refusal is read as the control working.** No change is made now: adding an
exception for a host that does not exist would be adding the hole in advance.

## 3. Verified, not assumed

- `gitleaks` — **no leaks found**, 32.99 MB scanned, 2026-08-19. Note that `make check` does NOT run
  it; `make secrets` is a separate target and was invoked explicitly for this pass.
- No credential, token or key literal anywhere in the Swift client (grep over all four sources).
- `ios/.build/` is gitignored and untracked; no build product entered the tree.
- The client can only reach the host in `baseURL`; there is no path where a served value becomes a
  URL, so nothing in a response can redirect the app at another host.
- The engine's database handle remains read-only (REQ-API-006, unchanged by M8).

## 4. What this pass does NOT cover, stated rather than implied

- **W-030 / W-031 remain UNVERIFIED.** REQ-API-009's network half and the whole Fly platform
  surface cannot be tested because nothing is deployed. A local container is a good proxy and is not
  the platform. M8 does not deploy — the owner's ruling is that money goes to iOS only — so **D-123
  is not discharged and go-live moves again**, which §4 of the closure report states plainly.
- **No Swift is executed by any gate** (W-038). Every client property asserted in this milestone is
  asserted by reading the source, not by running it.
- **The 503 branch of `/v1` is unreachable** (W-039). A fail-direction decision, and the owner's.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-19 · Tree: `dbbc436`
