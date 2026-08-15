---
record_type: experience
id: model-ranking-experience
status: ratified
date: 2026-08-11
---
# EXPERIENCE — model_ranking (living; V3C-81 — quarterly handover BLOCKS without it)

## 2026-08-11 — M1: Data Layer + Recommendation Engine (coding)

**What the pipeline caught that I would have shipped:**
- W3 fresh-eyes review FAIL: my curated regexes false-matched REAL aliases (gpt-5-pro → gpt-5,
  flash-lite → flash, grok-4-fast → grok-4…) — the exact bug class the spike had, one layer deeper.
  Redundancy (a second reader probing with a real-world corpus) caught what the author's own tests
  could not, because the author writes tests for the failures he can imagine.
- W4 review BLOCKING: the engine emitted a factually false "why" when the quality floor was unmet.
  Lesson: every fallback branch needs its own honesty check — silent degradation plus confident
  prose is the worst failure shape for a recommendation product.
- The first LIVE run failed loudly on Aider duplicate model entries — a data condition no fixture
  modeled. The control (UNIQUE + loud SourceError + rollback) worked exactly as designed.
  **Doctrine adopted: the first live run happens INSIDE the wave, not after it.** (Seed candidate.)

**Friction (V4C-13):** `make check`/gitleaks deferred host-side ×4 waves (sandbox has no venv/gitleaks;
same tools ran directly). Same control deferred 4× — per the rule this triggers review of the CONTROL:
proposal → CI runs `make check` on the owner's GitHub repo so the sandbox gap stops mattering (M2).
- Cowork device bridge dropped mid-commit once (W2-W4 files); recovered next session, no loss —
  cloud workspace held state. Continuity-in-files worked as advertised.

**Starter defect found:** stray `src/__init__.py` breaks `make typecheck` (mypy src) — removed here;
should be reported upstream to the General_Pipeline template (candidate for its next cut).

**Numbers:** 4 waves · 74 tests · coverage 88% · 6 fault-injections (all RED, md5 reverts) ·
reviews: 14 MINOR + 3 BLOCKING found, all closed · live run: 2154 prices, 173+68 scores,
42 canonical models · security close: PASS, 0 BLOCKING.

## 2026-08-11 — M2: New Sources + Everyday-Assistant Category

**Owner amendments worked:** no per-wave git (milestone-boundary only) and council-instead-of-owner
for questions. No council convened — no decision rose to that bar; the closest was Arena's dataset
shape, resolved by evidence (WebFetch of the dataset card) rather than deliberation. Lesson: most
"questions for the owner" are actually questions for a primary source.

**What the reviews caught this time:** thresholds as code-branches (a third category would have
silently inherited Elo thresholds on a % scale — latent-debt class, caught BEFORE the third
category exists); assistant export overwriting the coding artifact; Arena page-cap silent
truncation; a CI smoke step whose failures vanished behind `head` (no pipefail). Pattern across
M1+M2: reviewers keep catching *the failure the author's imagination didn't contain* — redundancy
pays on every wave.

**Honesty engineering:** REQ-REC-006's stale disclosure is a deterministic proxy, and its
limitation (a never-refreshed DB cannot self-report stale) is now WRITTEN IN THE DOCSTRING rather
than discovered later. Doctrine: when a control is a proxy, its blind spot ships in its docs.

**Sandbox boundary institutionalized:** HF/OpenRouter unreachable from the build sandbox → live
verification moved to CI (weekly cron + manual dispatch). First live Arena/OpenRouter run happens
in CI — treat its first green run as a milestone-closure condition analog (M1 doctrine: first live
run belongs inside the wave; here the wave's live half runs where the network is).

**Numbers:** 4 waves · 109 tests (104 unit + 5 gated) · coverage 90% · fault-injection ×4 (all RED,
md5 reverts) · reviews: 11 MINOR + 2 PROCESS found, all applied · security close: PASS, 3 new
invariants · D-105 recorded.
