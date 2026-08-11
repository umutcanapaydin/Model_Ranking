# License & Commercial-Use Review — `<WRAPPED_OR_FORKED_OSS_ENGINE>`

> Stage-0 gate (FB-4 / seed F.10, Pipeline v2.2). Complete this BEFORE building on any
> third-party OSS engine you run, wrap, or fork. Copy this file to `docs/license-review.md`,
> fill it, and have it reviewed. `make bootstrap-check` (C6) looks for `docs/license-review.md`.
> **This is a risk flag, not legal advice — confirm with legal counsel before any commercial release.**

---

## 1. What are we building on?

- **Engine / dependency:** `<name + version + upstream URL>`
- **How we use it:** `<run unmodified as a service / wrap behind our own API / modify (fork) / embed>`
- **Consumption posture (v3.1, V3C-71):** `wrap (call its API only) | fork (patch it) | port (reimplement)` + the trigger conditions for changing it. **Rule: a wrapper never touches the wrapped system's datastore.** Record the posture + triggers as an ADR field.
- **Is our product delivered over a network (SaaS / API / MaaS)?** `<yes / no>`
- **Is our product proprietary / closed-source?** `<yes / no>`

## 2. License

- **License:** `<e.g., AGPL-3.0 / GPL-3.0 / SSPL / Apache-2.0 / MIT / BSD / proprietary>`
- **Extra terms (Section 7 / attribution / trademark):** `<e.g., visible attribution + link required>`
- **Class:** `<permissive (MIT/Apache/BSD) | weak copyleft (LGPL/MPL) | strong copyleft (GPL) | network copyleft (AGPL/SSPL)>`

## 3. The obligations that matter to us

`<List the concrete obligations triggered by HOW we use it. For network copyleft (AGPL/SSPL):
source-disclosure on network use, and any required attribution.>`

## 4. Decision matrix (how we use it -> legal effect -> verdict)

| How we use it | Legal effect | Verdict |
|---|---|---|
| **Modify / fork** (edit + compile into our product) | Our changes inherit the license; network copyleft forces source disclosure to all users | `<❌ usually incompatible with a proprietary product>` |
| **Wrap unmodified** (run as a separate service; our code calls it over its API; we never edit it) | Our own product stays proprietary; only the unmodified upstream source must remain available + attribution kept | `<✅ usual safe path>` |
| **Wrap headless** (use only its backend; our own portal; its UI not exposed) | As above, and frees us from UI attribution | `<✅ cleanest for white-label>` |

## 5. Recommended path + risk if we get it wrong

- **Recommended:** `<e.g., "wrap, don't fork": run a fixed, unmodified copy as an internal service behind our own proprietary control plane; keep upstream source + attribution available.>`
- **Risk if violated:** `<takedown demand, forced source disclosure, reputational + contract/IP exposure.>`

## 6. Decision required from management / legal

- [ ] Approved (with legal review) to proceed under the recommended path, **or**
- [ ] Pursue a commercial license from the upstream owner, **or**
- [ ] Build from scratch / choose a permissively-licensed alternative.

---

**Reviewed by:** `<name>`   ·   **Legal sign-off:** `<name / pending>`   ·   **Date:** `<YYYY-MM-DD>`
**Verdict:** `<APPROVED — recommended path / BLOCKED — needs commercial license or rebuild>`
