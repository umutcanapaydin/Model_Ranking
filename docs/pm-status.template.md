# PM Status Snapshot — `<PROJECT_NAME>` — `<YYYY-MM-DD>`

> A PM-readable status snapshot (Pipeline v2.1, candidate `/pm-status`). Pairs with the
> G.9 PM-friendly risk register. Rules: plain language, zero engineer vocabulary
> (no DSL / namespace / container-cluster terms), every row says what's THERE and
> what's MISSING, and any external blocker is called out by owner + ETA.
>
> Origin: EF-AI `docs/pm-status-2026-06-11.md` — the format that let a non-engineer
> read project state in 2 minutes during the M12 / S34 prod-deploy window.

**Status key:** ✅ done & verified  ·  🟡 in progress / partial  ·  ⛔ blocked (needs a decision or an external input)

## 1. Headline (one sentence)

`<e.g., "M12 hardening is code-complete and deployed; one external item (prod Redis URL) is blocking the multi-replica switch.">`

## 2. Where each piece stands

| Item | Status | What's there | What's missing |
|---|---|---|---|
| `<feature / milestone area>` | ✅ / 🟡 / ⛔ | `<the concrete thing that works today>` | `<the concrete thing not yet done, in plain language>` |
| `<...>` | | | |

## 3. External blockers (not ours to fix)

| Blocker | Owner | Status | ETA | What it's holding up |
|---|---|---|---|---|
| `<e.g., production database URL>` | `<customer / cloud team>` | waiting | `<date>` | `<what can't proceed until it lands>` |

If there are none: "No external blockers."

## 4. Decisions needed from you

1. `<decision — context — recommended option>` (numbered, with a recommendation per G.8)

If there are none: "No decisions needed right now."

## 5. Next

`<the single next thing that happens, and roughly when>`
