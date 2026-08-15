# HANDOVER — model_ranking (agent → agent, 2026-08-11)

> ## ⚠ SUPERSEDED FOR CURRENT STATE — written before M3 and M4 existed.
> **A newer handover covers this boundary: [`docs/handovers/handover_m5-start.md`](handovers/handover_m5-start.md).**
> Read that one for where the project IS. This file is kept verbatim because its product
> explanation and its "what bites" list are still accurate and worth reading — but every
> statement here about *status, milestones or open work* is two milestones out of date.

> **You are the stranger this was written for.** Continuity lives in files, not sessions.
> Read this top-to-bottom once (~10 min), then `docs/closure-report-m2.md` and `note.txt`.
> The pipeline methodology (General Pipeline) is being **replaced with v4.3.1 by the owner** —
> follow whatever THAT package says for process. This document is about **the product**:
> what it is, what exists, what is true, what bites, and what comes next.

---

## 1. What this project is

An **AI advisor engine**. Given a use case and a budget, it answers with three labeled picks —
**Best Quality / Best Value / Budget Pick** — from public benchmark + pricing data, with evidence
dates, confidence grades, and honest disclosure when data is stale. It is the backend of a planned
iOS app; there is no app yet and no HTTP API yet.

**The thesis (from two independent AI research reports the owner commissioned, plus a critical
comparison of them — all three predate the code):** don't build another leaderboard mirror; build
the *decision layer*. The defensible asset is the curated mapping model ↔ app ↔ subscription plan,
which nobody maintains and no feed provides.

**Owner:** Umut Can Apaydın (ILGAR). Works in Turkish; **write to him in Turkish, plain language,
no jargon dumps.** He is not a day-to-day coder — he steers, decides scope, and runs commands you
give him. Give him exact copy-pasteable commands, and tell him what a result means, not just what
it says.

---

## 2. Where everything lives

| What | Where |
|---|---|
| **GitHub repo (source of truth)** | `github.com/umutcanapaydin/Model_Ranking`, branch `main` |
| **Owner's local clone** | `/Users/umutcanapaydin/Desktop/ILGAR/model_ranking` (his Mac; venv at `.venv/`, Python 3.14) |
| **Agent container clone (mine)** | `/home/claude/model_ranking/repo_push` — clone of the GitHub repo, kept in sync, gates run here |
| **Owner's terminal outputs** | `/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/terminal_out_N.txt` — he pastes run results here for you to read |
| **Research corpus (pre-code)** | owner archive: `llmbenchmarkappresearch.md`, `llmaibenchmarkingmobileappresearch.md`, plus my critical comparison (delivered in chat 2026-08-06) |
| **Cowork-mounted view of his repo** | `~/mnt/ILGAR/model_ranking` via `device_bash` — **read/write files here, but see §7: git in this mount is crippled** |

**Commit history (4 commits, all pushed):**

```
805718b  FP-M2-2: Arena category value 'overall' + newest-snapshot-only
42e53aa  FP-M2-1: Arena live fetch — server-side category filter + 429 backoff
5cb1c42  M2: new sources + everyday-assistant category
8152490  M1: data layer + recommendation engine (coding)
```

---

## 3. Current state (verified 2026-08-11)

**Green:** 107 unit tests + 5 network-gated contract tests. `ruff` clean, `black` clean,
`mypy --strict` clean on `src` AND `tests`. Coverage ~90% (unit run). ~4 000 lines src+tests.
**All 13 contract tests pass live on the owner's machine** (his run, out-of-sandbox — this is what
closed M2's last item).

**What the engine does today, live:**
- **Sources (5, all free/legal, no scraping):** LiteLLM pricing JSON (GitHub raw), OpenRouter
  `/api/v1/models` (no auth), SWE-bench Verified leaderboard JSON (GitHub raw), Aider polyglot YAML
  (GitHub raw), Arena/LMArena leaderboard via **HF datasets-server `/filter`** (CC-BY-4.0).
- **Categories (data, not code):** `coding` (primary: SWE-bench Verified %) and `assistant`
  (primary: Arena text Elo).
- **CLI:** `python -m app.workflows.recommend --db advisor.db --budget dusuk|orta|sinirsiz --task coding|assistant`
  → JSON with three picks, `close_call`, `stale_notice`. Exit codes: `0` ok, `1` no eligible model,
  `2` usage/DB error.
- Latest real coding answer: quality **Claude 4.5 Opus** 79.2%, value **MiniMax M2** 75.8% @ $0.52/1M,
  budget **DeepSeek V3.2** 70.0% @ $0.31/1M (confidence High — two independent benchmarks).

**Data flow:** `clients/*` fetch raw text (each behind the `RawSource` protocol, each with its own
30 s timeout) → pure parser functions → `workflows/ingest.py` replaces that source's working set in
one transaction → `workflows/registry.py` maps aliases to canonical models (ordered first-match
regex table) → `workflows/rank.py` builds median prices + per-category ranking → 
`workflows/recommend.py` filters by budget, computes the Pareto frontier, emits three picks.
SQLite file is **disposable** — rebuilt from sources any time.

---

## 4. The rules this codebase lives by (break these and you break the product)

1. **A score is always a model + harness pair.** SWE-bench numbers belong to a model *and* its agent
   harness. Any query that drops the harness reports a wrong number.
2. **Never average across scales.** Elo and % are different units. Each category ranks ONLY on its
   primary benchmark's native scale; secondary benchmarks are displayed as evidence, never blended.
   Locked by `test_no_cross_scale_averaging_structural`. If someone asks for one "overall AI score",
   the answer is D-105, not a reflex yes.
3. **Never invent a price or a score.** Missing/zero/bool prices are skipped and counted, never
   coerced to 0 (schema `CHECK > 0` backs this).
4. **Unmatched model names are dropped and counted, never guessed.** The drop list is data
   (`ReconcileReport.dropped_names`) — walk it at closures; it's how registry drift becomes visible.
5. **Fail loud, fail closed, per source.** A broken source aborts ITS ingestion with a `SourceError`;
   the transaction rolls back so the previous working set survives. No silent truncation anywhere.
6. **No LLM in the data or scoring path** (D-104). The engine is rule-based and explainable. A future
   natural-language intake may only translate user text into filters.
7. **Only documented data endpoints.** No HTML scraping. **Artificial Analysis is banned** until a
   commercial agreement exists (their free tier is 100 req/day, internal-use-only — verified).
8. **Honesty is a feature.** Near-ties are disclosed (`close_call`), stale evidence is disclosed
   (`stale_notice`), and when the budget pick can't meet the quality floor the output says
   "UYARI: … kaliteden ödün veriyorsun" instead of pretending.

---

## 5. Decisions on record (`docs/decisions.md`)

| ID | Decision |
|---|---|
| D-100 | Python 3.11+, FastAPI adapter is `/health`-only for now, SQLite disposable |
| D-101 | Free-and-legal sources only; no scraping; AA banned; provenance mandatory |
| D-102 | The pre-project Cowork spike is throwaway; production code was rebuilt with tests |
| D-103 | Operating mode A0.5 (agent closes waves; owner reviews at milestones) |
| D-104 | Recommendation engine is deterministic; no LLM in scoring |
| D-105 | Category layer: primary-benchmark-per-category, no cross-scale averaging; RankingRow/Pick generalized |
| **D-106** | **OWNER DIRECTIVE: the agent runs the test gate and authors/pushes commits on his behalf.** Scope: green gates only, at wave/milestone boundaries; token never persisted; force-push / history rewrite remain forbidden. |

---

## 6. History, honestly (what actually happened, including what went wrong)

**M0 (research).** Two AI-written research reports were compared critically. Verified findings: the
Artificial Analysis free tier is internal-use-only (one report had it wrong), HELM entered
maintenance mode 2026-06-01 (the other report was right). Conclusion: build the decision engine, not
a leaderboard.

**M1 — data layer + recommendation engine (coding).** 4 waves: schema+LiteLLM → SWE-bench+Aider →
canonical registry+ranking → recommender+CLI. Every wave got a fresh-eyes review from an agent that
did not write the code. **Two of those reviews caught real defects:**
- W3 review FAILED the wave: the alias regexes false-matched *real* aliases (`gpt-5-pro` → `gpt-5`,
  `gemini-2.5-flash-lite` → `flash`, `grok-4-fast` → `grok-4`). Sibling variants would have polluted
  each other's prices. Fixed with explicit variant models + tightened lookaheads; unlisted siblings
  now DROP rather than merge.
- W4 review found the engine printing a **factually false explanation** when no model met the quality
  floor. Fixed with an explicit warning branch.
- The **first live run** then caught what no fixture had: Aider lists the same model across multiple
  runs → UNIQUE violation → loud abort. Fixed with keep-best dedupe.

**M2 — new sources + assistant category.** 4 waves: OpenRouter + median-of-per-source-medians →
Arena ingestion → category layer → `--task` + CI workflow. Reviews found 13 items including
thresholds living as code branches (a third category would have silently inherited Elo thresholds on
a % scale) and an export that would overwrite the coding artifact.

**FP-M2-1 / FP-M2-2 — the fixpacks that matter most.** The owner ran the contract tests on his
machine. OpenRouter passed first try. Arena failed twice, and both root causes trace to **fixture
values I invented in M2-W2 and never checked against live data**:
1. `text/latest` carries ALL category slices (21 259 rows), not just the overall board → the
   anti-truncation guard fired (correctly). Fixed with server-side `/filter`, plus 429 backoff.
2. The category value is **`'overall'`**, not `'full'` — my invented value filtered **0 rows**. With
   the right value: 386 rows, spanning **multiple `leaderboard_publish_date` snapshots**, so
   "keep the best score per model" would have published a **stale-but-higher Elo as current**. Fixed:
   keep only the newest snapshot, count the dropped rows.

**The durable lesson (write it on the wall):** *a fixture that encodes a remote **value** — not just
a shape — is an untested assumption wearing a test's clothing.* Contract tests proved shape and
stayed green for two waves while the value was fiction. **Probe the live source for any value you
put in a fixture, before the wave closes.**

---

## 7. Environment gotchas that will cost you an hour each (learn them free)

1. **The build sandbox cannot reach `huggingface.co`, `openrouter.ai`, or `epoch.ai`** (proxy 403).
   GitHub raw and the HF *datasets-server* work. Live validation of Arena/OpenRouter therefore runs
   **on the owner's machine or in GitHub Actions**, never here. Default test suite is network-free by
   design; live tests are gated behind `RUN_CONTRACT_TESTS=1`.
2. **`WebFetch` reaches sites the shell cannot.** This is how the Arena dataset card and the real
   `category` values were discovered. When a remote value matters, probe it with WebFetch.
3. **Git inside the Cowork mount (`~/mnt/...`) is crippled**: it cannot unlink its own lock files or
   tracked files (EPERM), so `git pull`/`checkout` half-fails and leaves `.git/index.lock` behind,
   which blocks the owner's next command. `rm` is also forbidden there — you can only `mv` files into
   a `_to_delete/` folder. **Do not run git in the mount.** Do git work in the container clone.
4. **The container cannot push to this repo** — the git proxy answers 403 because the repo isn't in
   the session's authorized sources. Until the owner adds it, deliver commits as a **git bundle**:
   `git bundle create /home/claude/x.bundle origin/main..main`, `SendUserFile` it, write it to his
   Desktop, and give him `git pull ../x.bundle main && git push origin main`.
   **Ask the owner once to add the repo to the session's sources** — that makes D-106 fully automatic.
5. **A stop hook enforces commit authorship:** commits must be authored `Claude <noreply@anthropic.com>`.
   Set `git config user.email noreply@anthropic.com && git config user.name Claude` in any clone you
   commit from. If you already committed with another identity and haven't pushed, amend it.
6. **`.github/workflows/*` cannot be written through the device bridge** (protected). Deliver workflow
   changes inside a git commit instead.
7. **The device bridge drops out.** Files already staged remain readable; just re-send when it
   reconnects. The cloud workspace keeps state across turns, so nothing is lost.

---

## 8. Working agreement with the owner (as of this handover)

- **He signs milestone plans.** Waves run without stopping; **do not pause between waves**.
- **He appears at milestone closures**, reads the closure report, and decides.
- **You run the tests and the commits** (D-106) — but the *live* contract tests he runs, because of §7.1.
- **Mid-milestone questions:** he asked for a 6-seat council (Software/Quality/Security/DevOps/PM/
  Skeptic) instead of interrupting him. In practice most "questions" dissolve against a primary
  source — check the source first; convene only for genuine judgment calls.
- **Escalate to him immediately** for: suspected secret, security finding, scanner suppression,
  plan-invalidating scope change.
- Deliver files with `SendUserFile` AND write them to his Mac via the device bridge; he reads on disk.

---

## 9. What's next (M3, not yet planned or signed)

Agreed roadmap: **M3 = subscription-plan table** — the "which $20 plan is right for me" answer.
ChatGPT Plus / Claude Pro / Gemini AI Pro / Perplexity etc.: price, included models, limits, region,
last-verified date. **There is no machine-readable feed for this anywhere** — it needs a curated
table plus a verification workflow, which is exactly why both research reports called it the moat.
Prices are volatile (several changed within 90 days), so "last verified" and a re-check cadence are
part of the product, not bookkeeping.

**Open question the owner still owes an answer to:** should Epoch AI ingestion ride along in M3, or
wait for M4? (My read: the subscription table alone is a full milestone.)

**Carried technical debt (from M2 closure + reviews):**
- ~~**Elo thresholds are a first calibration and partly arbitrary**~~ — CLOSED at M3 closure
  (2026-08-15): recalibrated against 389 live rows to `min_quality=1400`, `value_window=30`,
  `close_call=8` (docs/reviews/m3-elo-calibration.md). Changing them stays a data edit, by design.
- `ArenaClient(url=...)` constructor param is provenance-only; `fetch_raw` always uses module
  constants. Misleading API — clean up.
- GitHub Actions steps are tag-pinned (`@v4`), not SHA-pinned. Pin before the weekly cron matters.
- Median currently treats every (alias, source) equally within a source; fine today, revisit if a
  third pricing source lands.
- `stale_notice` is a deterministic proxy: a database that is never re-ingested cannot report itself
  stale. Documented in the function's docstring on purpose.
- `close_call` only inspects the runner-up **on the Pareto frontier**; a pricier near-tie is not
  disclosed. Design choice, worth revisiting with users.
- M1 closure telemetry (fix-rate, churn) was never computed — no git history existed then. From M3 on
  it's computable.

---

## 10. First moves for you (the new agent)

1. Read `note.txt`, `docs/closure-report-m2.md`, `docs/fixpack-1.md` (both fixpacks, they teach the
   most), `docs/EXPERIENCE.md`.
2. Clone the repo into your container, run the gate to see green with your own eyes:
   `pip install -e ".[dev]"` then `ruff check src tests`, `mypy src tests`, `pytest`.
3. Ask the owner (in Turkish, one question) whether Epoch belongs in M3, then draft `docs/plans/m3-plan.md`
   and **stop for his signature**.
4. When you write any fixture containing a value that came from a remote source — a category name, a
   field value, an enum — **probe the live source first**. That is the lesson this project paid for
   twice.

---

*Prepared by the outgoing lead agent, 2026-08-11. Everything above is verified against the repo at
`805718b`; where I was uncertain I said so rather than smoothing it over.*
