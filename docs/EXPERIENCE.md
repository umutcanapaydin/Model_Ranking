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
