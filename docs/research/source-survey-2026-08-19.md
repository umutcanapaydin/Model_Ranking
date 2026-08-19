---
record_type: register
id: source-survey-2026-08-19
status: draft
date: 2026-08-19
---
# Source survey for D-126's scope — what can we actually keep updated?

**Question this answers.** D-126 widened the product to all AI tools. A category may only exist where
a public, free, legally usable measurement exists — and the owner added the sharper criterion, which
is the one that decides everything here:

> **"Data that cannot be updated is garbage."**

So a source is not qualified by existing. It qualifies by being **machine-fetchable, repeatedly,
without a human in the loop**. Every claim below was tested with a real request on 2026-08-19, not
read off a README. Where a check was not performed, it says so.

---

## 1. VERIFIED AND USABLE TODAY — the Arena mirror

`https://raw.githubusercontent.com/oolong-tea-2026/arena-ai-leaderboards`

LMArena publishes no API. This repository scrapes it and republishes structured JSON.

| Property | Measured |
|---|---|
| Fetch | **HTTP 200**, `raw.githubusercontent.com` — the same pattern `litellm` and `aider` already use |
| Freshness | `data/latest.json` returned **`2026-08-19`** — the day it was tested |
| Reliability | **96 of 101 days updated (95%)**, running since 2026-05-11, from the commit history rather than the README |
| Licence | **MIT**, confirmed by fetching `LICENSE` |
| Key required | **No** |

**Leaderboards fetched and counted:**

| File | Models | Answers the user question |
|---|---|---|
| `text-to-image.json` | **76** | "make me an image" |
| `image-edit.json` | **53** | "improve my profile picture" — the owner's own example |
| `text-to-video.json` | **45** | "make a video" |
| `vision.json` | 20 | "read this screenshot / document" |
| `agent.json` | 10 | "do this task for me" (multi-metric) |
| also present | — | `image-to-video`, `video-edit`, `document`, `search`, `code`, `text` |

Row shape is simpler than what we parse today: `rank`, `model`, `vendor`, `license`, `score`.

**The risk, stated plainly.** This is a **third-party mirror of a source that has no API**. Its
continuity depends on one volunteer repository. 95% over three months is a good record and it is not
a guarantee. Mitigation is what the engine already does: source health reports the age, and a
mirror that stops updating shows as stale rather than as fresh-and-wrong.

---

## 2. VERIFIED, BUT NEEDS A DECISION — Artificial Analysis

Covers exactly what the Arena mirror does not: **speech (TTS, speech-to-text, speech-to-speech),
music (instrumental and vocal), and per-modality PRICING**.

| Property | Measured / documented |
|---|---|
| Endpoints | 12 free ones, one per modality, e.g. `/api/v2/media/text-to-speech/models/free` |
| Key required | **YES** — `x-api-key` header, free registration |
| Rate limit | Documented inconsistently: **100/24h** on one page, **1000/day** on another |
| Caching | **Explicitly encouraged** — "do not include in client side code and cache responses" |
| Attribution | **Required**, link to artificialanalysis.ai |
| Commercial display | **Not explicitly permitted or forbidden.** The docs say to contact them for redistribution terms |

**Two owner decisions before this can be used**, and neither is technical:

1. **The API key.** This project has never held a secret — `gitleaks` has been clean for two
   milestones and nothing in the deploy carries a credential. A key is an operational dependency
   that can be revoked, must be stored, and must reach the build without reaching the repository.
2. **The terms.** The PRD's founding constraint is "free and legally usable". Caching is encouraged
   and attribution is cheap, but displaying their data to end users in a consumer app is the exact
   case their docs send you to their team about.

**The technical fit is otherwise excellent**: caching server-side and serving a built artifact is
precisely what they recommend, and 12 endpoints twice a day is 24 requests against the lower of the
two published limits.

---

## 3. ALREADY ON DISK, LARGELY UNUSED — the Epoch bundle

The owner-placed bundle this project already ingests contains **77 benchmark files. We use two.**

| Benchmark | Models | Reads as |
|---|---|---|
| `epoch_capabilities_index` | **819** | general capability |
| `mmlu_external` | 696 | general knowledge |
| `gpqa_diamond` | 471 | expert reasoning |
| `otis_mock_aime_2024_2025` | 428 | mathematics |
| `terminalbench_external` | 297 | terminal / shell work |
| `scicode_external` | 218 | scientific code |
| also present | — | `os_world` (computer-use agents), `lech_mazur_writing` (writing), `simpleqa_verified` (factual accuracy), `deepresearchbench` (research), `video_mme` (video understanding), `cybench` (security), `arc_agi` (abstract reasoning) |

All share the shape we already parse: `Model version` plus a score column whose NAME varies per file.

**But this is a benchmark repository, not a category list.** `bool_q`, `hella_swag`, `wino_grande`,
`piqa`, `lambada` are academic instruments; nobody asks "which model is best at WinoGrande". The
work here is not acquisition — it is **mapping 77 instruments onto questions people actually ask**,
which is the supply-side twin of what D-126's router does on the demand side.

---

## 4. NOT ESTABLISHED — keyless speech sources

Attempted: `hf-audio/open_asr_leaderboard`, `TTS-AGI/TTS-Arena-V2`,
`ArtificialAnalysis/Text-to-Image-Leaderboard` through the HuggingFace **datasets-server**. All
returned **HTTP 401**.

**This does not mean no free speech source exists.** Those three are HuggingFace *Spaces*, and the
datasets-server serves *datasets* — the wrong endpoint was tried, which is a fault in the check and
not a finding about the world. Recorded as an open question rather than a negative result, because
writing down "no source exists" on the strength of a wrong request is how a survey becomes
misleading.

---

## What this means for the roadmap

**Image, video and vision are reachable now**, keyless and MIT, through a mirror with a measured
95% update record. That covers the owner's own example — profile-picture editing — with 53 models.

**Speech and music need a decision**, not more research: the one verified source requires a key and
has ambiguous display terms.

**Text-side categories need no acquisition at all.** The evidence is already on disk; the work is
mapping and ingestion.

**The one thing no source solves** is the pricing axis. The engine's `blended_per_m` is a token
price. An image model is priced per image, speech per minute, video per second. D-105 forbids
averaging across scales for good reason, and it applies here: **per-modality pricing is engine work
that must land before "all AI tools" is real** on the model-selection axis. On the SUBSCRIPTION axis
it does not bite — dollars per month is a unit every modality shares, which is a further argument
for the owner's decision to make tool selection the home screen.
