---
record_type: review
id: m16-wave-4-review
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M16-W4 -- independent review (Code-Reviewer + Tester, HIGH tier)

**Seat:** independent, Code-Reviewer and Tester combined. I wrote none of this wave: not the plan,
not the code, not the P1 security pass.

**Scope:** `git diff origin/main...HEAD` at HEAD `7ee8f7d` (draft PR #6), the seventeen commits
`cd2f4e7..7ee8f7d`. The code phases are `fbe892e..7ee8f7d`:
- P1: `fbe892e`, `f2ffaee`, and the security fix round `de44a16`, `cd2f942`.
- P2: `477ef68`, `420a216`.
- P3: `1271c59`, `4ed843b`.
- P4: `c90ebc1`, `c518fd3`.
- P5: `a25b1ef`, `7ee8f7d`.

I read the code against:
- the plan `docs/plans/m16-wave-4-plan.md`;
- D-157 and D-158 in `docs/decisions.md`;
- the measurement record `docs/research/m16-w4-derived-registry-2026-09-23.md`;
- the P1 security review `docs/reviews/m16-wave-4-security-p1.md`.

**Policy:** I read my policy only from the protected base:
- `git show origin/main:subagent-profiles/Code-Reviewer.md`
- `git show origin/main:subagent-profiles/Tester.md`

The diff touches no policy path. `git diff --stat origin/main...HEAD -- subagent-profiles AGENTS.md
.agents .claude permission-matrix.md docs/security-baseline.md` is empty. I searched the added lines
for text addressed to a reviewer, and the only hits are the research record's own "verdict" columns.
So there is no injection-class finding. No test line is deleted or weakened: `git diff
origin/main...HEAD -- tests/` has no removed lines.

**Families:** the author is recorded as Claude, and this seat is also Claude. No second family was
available, so this is the fallback. My context was fresh: I did not see the author's session or the
security seat's session.

**Snapshot.** Every result below is against HEAD `7ee8f7d` and these md5s. They were identical in
the repository and in my copy, and they were unchanged at the end.
- `registry.py` `d1a9277d...`
- `epoch_bundle.py` `c48997a3...`
- `refresh.py` `1e538807...`
- `build.py` `3b9f16f9...`
- `nightly.py` `a96f548a...`
- `protocols.py` `469cd93f...`
- `sources.py` `a4e251f7...`

The owner's `advisor.db` and `advisor.db.refresh.json` were `214139e9...` and `d729a3f6...` before
and after my work. I read them only as copies in the session scratch directory.

**How I worked:**
- I did all work in an `rsync` copy of the tree in the session scratch directory. The copy left out
  the two untracked files that are not this branch's (an HTML page and a Markdown note at
  the root).
- The copy's editable-install `.pth` was repointed at the copy's own `src`, and every `__pycache__`
  was cleared, so the copied bytecode could not stand in for mutated source.
- `make` ran with `-o install -o .venv/bin/python`.
- I downloaded `https://epoch.ai/data/benchmark_data.zip` once into scratch: HTTP 200, 2,306,806
  bytes. The unpacked directory matches the archive's member list exactly.
- I built a fresh candidate from live upstreams and that bundle (`python -m app.workflows.build
  --db <scratch>/c.db --epoch-dir <scratch>/epoch`).
- I ran real refresh cycles on copies of the served artifact: one with `--fetch-epoch`, one with the
  owner's hand-kept bundle directory.

I made no git state change. I started nothing on :8080; a GET to `/health` found no engine running.
The only repository file I created is this one. Twice I ran a read-only `python -c` probe from the
repository root, which may have refreshed gitignored `__pycache__` files; nothing tracked changed.
`git status --short` shows the same two untracked files before and after, plus this record.

**Disclosed contamination, and how I cleared it.** The session scratch directory already held a
`tree/` from an earlier seat. My `rsync` merged into it. That left two stale files that are not on
this branch: an earlier seat's scratch re-review test module and the deleted W3 plan. I found them through the first
gate run: `lint` failed on that test file.
- I removed both and re-ran the gate from clean caches. All gate numbers below are from that clean
  run.
- The mutant results are unaffected. Every RED was produced by a named list of this branch's test
  files, which did not include the stale file. A stale extra test can only add a RED, never hide
  one, so the GREEN mutants stay GREEN.

## Verdict

**BLOCKING: 1 BLOCKING, 1 MAJOR, 3 MINOR, 3 NIT.**

**What this wave got right.**
- **P1 (the fetch) is sound.** All six security-pass fixes hold under the reviewer's hostile
  archives and my own set of 24. One of mine is a corrupt `ZIP_ZSTANDARD` member through the real
  cycle, which carries and leaves no scratch.
- **P2 reads the 2026-09 layout.** `everyday` arrives from the real bundle, and drift is recorded by
  name.
- **P3 closes the Fable 5.1 leak.** All 16 Fable 5.1 price aliases and 7 score names resolve to
  `claude-fable-5.1` on live data.
- **P5 is wired end to end.**
- **D-132 does refuse the first derived artifact, as the plan says it should.** The measured refresh
  exit was 3, with 9 surfaces over the new-names limit.
- **The gate is green**, and 32 of my 38 mutants are RED (5 GREEN, 1 equivalent).

**What blocks.** P4's grammar removes tokens that are not decoration:
- a `-vN` suffix;
- everything after `:` or `@`;
- a vendor prefix that leaves a bare token.

So the property D-157 clause 3 promises "by construction", that a variant never merges into its
parent, is false. Two models on today's live data are false merges of different versions: one score
credited to another model's price. A DeepSeek release named `deepseek-v5` would merge with DeepSeek
V2 the day it is priced. D-157's own revisit trigger reads "a derived registration is found merging
two different models". That trigger fires on this branch, before merge.

## Security-fix verification (docs/reviews/m16-wave-4-security-p1.md, fixed in `cd2f942`)

| Finding | Status | Evidence I ran |
|---|---|---|
| F1 BLOCKING: hostile archives crash the whole cycle | **HOLDS** | `unpack` is total. Every one of 24 hostile payloads became `SourceError` or was safely accepted, and none escaped: bad UTF-8 name, corrupt LZMA, corrupt BZIP2, corrupt deflate, CRC mismatch, encrypted flag, method 99, truncated central directory, file-then-dir, dir-then-file, `.`, a 300-character name, a 6,000-character path, and corrupt `ZIP_ZSTANDARD` twice (frame header, and mid-stream as a CRC failure). Through the real `refresh()`, a corrupt zstd member gives exit 0 (published), `epoch_gpqa` not in `sources_last_ok`, and no scratch left. A fetcher raising `MemoryError` after writing a file gives the same. `_fetched_epoch` catches `Exception` (`refresh.py:886`). Mutants M5 and M7 are RED. |
| F2 MINOR: scratch leaks | **HOLDS** | `except BaseException: rmtree; raise` (`refresh.py:893`): M8 is RED. The sweep covers `candidate`, `sources`, `last-ok` and `epoch` older than a day, under the lock (`refresh.py:903`): M11 and M12 are RED. `git check-ignore -v` matches `.gitignore:60-62` for `advisor.db.x.epoch/…`, `.sources` and `.last-ok`. The real `--fetch-epoch` cycle left nothing beside the copy. |
| F3 MINOR: memory before the member cap | **HOLDS as remedied** | `MAX_BUNDLE_BYTES = 16 MiB` (`epoch_bundle.py:35`), pinned by `test_epoch_bundle_fetch.py:315`, and M6 (member cap) is RED. I did not re-measure peak RSS. |
| F4 MINOR: no total deadline | **HOLDS** | On a real loopback socket dripping 1 byte every 0.2 s, `fetch_bounded_bytes(..., deadline=2.0)` raised "deadline" in under 5 s. M10 is RED. The check runs per chunk, so a total stall is bounded by httpx's 60 s read timeout on top of the deadline. |
| F5 NIT: redirects followed | **HOLDS** | `follow_redirects=False` (`epoch_bundle.py:133`). A loopback 302 is a `SourceError`, and M9 is RED. |
| F6 NIT: error normalisation | **HOLDS** | A size refusal reads "the bundle expands past …" (M4 is RED on `:307`). Name collisions and `ENAMETOOLONG` arrive as `SourceError`, as the F1 row shows. |

Still accepted, and still safe:
- A member named `a.csv\x00/../../x.csv` is truncated by `zipfile` to `a.csv`.
- `sub/C:/x.csv` unpacks inside the directory on APFS.
- An empty zip, or a bare end-of-central-directory record, is accepted with 0 files. Every declared
  board is then drift and carries: I measured `epoch_eci` in `drift` through the real cycle. That is
  the right reading of "a bundle that arrived without its boards".

## Findings

### BLOCKING-1 -- the D-157 grammar strips version and variant tokens, so different models merge under one derived id

**Where.** `derive_identity`, `src/app/workflows/registry.py:375-400`:
- `:387` `re.split(r"[:@]", text, maxsplit=1)[0]` keeps only the text before the first `:` or `@`.
- `:389-393` drops any dotted head in `_DOTTED_PREFIXES`, including vendor names.
- `:395` `re.sub(r"-v\d+\Z", "", text)` drops any trailing `-vN`, not only Bedrock's API tag.

**The contract it breaks.**
- D-157 clause 3: "A variant never merges into its parent by construction: the derived id keeps
  every token the name carries after its version."
- The module comment at `registry.py:333-336`: "It never removes a date or a word … can never merge
  a variant into its parent."
- The test module docstring: `tests/unit/test_registry_derived.py:8-9`.
- The PR body: "it never removes a date or a word".

**Registered false merges on today's data** (fresh build, live upstreams, fresh bundle):
- **`deepseek-coder`.** The Arena text score of `deepseek-coder-v2` (1191.1) is linked to the price
  of the `deepseek/deepseek-coder` API alias ($0.14 / $0.28). The display is "deepseek-coder-v2".
  The `-v2` generation token was removed.
- **`mistral7b-instruct`.** Arena's `mistral-7b-instruct` score (1023.4) is priced by Bedrock
  `mistral.mistral-7b-instruct-v0:2` (four aliases, v0.2) and Fireworks `mistral-7b-instruct-v3`
  (v0.3). `-v0:2` loses `:2` at `:387`, and then `-v0` goes at `:395`. `-v3` goes at `:395`. So three
  versions of one model family are priced as one model. Meanwhile
  `mistral-7b-instruct-v0.2` is registered separately as `mistral7b-instruct-v0.2`: the grammar
  splits v0.2 AND merges it, in the same build.

**44 names in today's data lose a `-vN` other than `-v1`**, across 17 derived ids. The measurement
script is in the session scratch directory, and the ids are below. Most are not registered today,
only because the other half is missing:
- `DeepSeek-V2` goes to `deepseek`.
- `anthropic.claude-v2` and `claude-v2:1` go to `claude`.
- `firefunction-v2`, `deepseek-prover-v2`, `granite-13b-chat-v2`, `nemotron-nano-9b-v2`,
  `fugu-ultra-v2` and `skyfall-36b-v2` each lose their generation.

**The latent merge is one upstream release away.** The curated table has DeepSeek rules up to V4
(`registry.py:118-124`). A LiteLLM alias `deepseek/deepseek-v5` matches none of them, derives to
`deepseek`, and meets Epoch's `DeepSeek-V2` score already staged there. The registry then shows
"DeepSeek-V2" at V5's price. Reproduced:

```python
conn = _conn(["deepseek/deepseek-v5"], [("DeepSeek-V2", "B", "unspecified")])
reconcile(conn).derived   # -> ('deepseek',)   expected ()
```

**Every other class I tried, each reproduced with `derive_identity`:**

| Two different products | Both derive to |
|---|---|
| `DeepSeek-V2`, `DeepSeek-V3`, `deepseek-v4`, `deepseek-v5` | `deepseek` |
| `claude-v1`, `anthropic.claude-v2`, `anthropic.claude-v2:1` (Claude 1, 2, 2.1) | `claude` |
| `mistral-7b-instruct-v0:1`, `-v0:2`, `-v3` | `mistral7b-instruct` |
| `vertex_ai/gemini-1.5-pro@001`, `@002` (two releases; the dash spellings `-001` and `-002` stay apart) | `gemini1.5-pro` |
| `vertex_ai/claude-3-5-sonnet@20240620` and the undated `claude-3.5-sonnet` (OpenRouter's is the 20241022 model) | `claude3.5-sonnet` (registered today; the prices happen to be equal) |
| `anthropic/claude-3.7-sonnet:thinking` and the plain model; the display `Claude 3.7 Sonnet: Thinking` | `claude3.7-sonnet` |
| `gpt-5:high` (the effort is lost silently, not stored) | `gpt5` |
| `us.deepseek.r1-v1:0`, `deepseek.r1` / `deepseek.v3-v1:0` | the bare tokens `r1` / `v3` |
| every `ft:<base>:…` fine-tune price | `ft` |

The separator rules at `:396-397` held against everything I tried, including the rule that reads
`opus-5-5` as 5.5 and `3-235b` as a parameter count: sizes, dates, `-it`/`-instruct`, `fp8`,
`thinking`, `max`/`pro`/`mini`, `a22b`, `0324`. I found no merge from them, only splits.

**Why BLOCKING and not MAJOR:**
- **It is the dangerous direction the plan names.** A false merge silently attributes one model's
  score or price to another.
- **It already happens in the artifact this PR asks the owner to publish.** Both registered merges
  sit on `assistant`, which reads Arena text.
- **It violates the ADR's central invariant.** D-157 exists to relax "never guessed", and its
  safety argument is that a variant cannot merge by construction.
- **The existing tests pin the wrong half.** `test_route_region_and_version_separators_are_decoration`
  asserts that `-v1:0` and `@default` are decoration. Nothing asserts that `-v2`, `@002` or
  `:thinking` are not.
- **The remedy is small**, and it moves the failure to the safe direction the ADR already accepts:
  splitting.

**Remedy.**
1. Delete the `-vN` strip, or narrow it to the exact Bedrock API-tag shape AFTER a region or vendor
   dotted prefix was removed, and only `-v1` or `-v1:0`. Even `-v0:2` is a model version, as
   Mistral's Bedrock ids show, so a split is the only safe reading of anything else.
2. After `:`, strip only a closed list of route decorations (`batch`, `free`, `exacto`, and the like).
   Return `None` for `ft:` and keep any other suffix as a token: `:thinking` becomes `-thinking`.
3. After `@`, strip only `default` and `latest`. Keep any other `@` suffix as a token.
4. Drop a VENDOR dotted head only when what remains starts with that vendor's own family word.
   `anthropic.claude…` and `meta.llama…` qualify; `deepseek.r1` does not and becomes `deepseek-r1`.
   Region heads (`us`, `eu`, `global`, …) stay removable.
5. Add the reproductions above as red tests: a parametrised "never one id" list, plus the
   `deepseek-v5` + `DeepSeek-V2` reconcile. Then re-run the measurement record; the counts will move
   slightly toward splits.
6. Correct the three texts that claim the property.

### MAJOR-1 -- the refresher actually running on the owner's machine never fetches, and after the deliberate publish it is refused every twelve hours

**Where.** `scripts/refresh_job.sh:18` and `:24` (unchanged by this wave), installed as the launchd
job `com.hcs.modelranking.refresh`. It is loaded (`launchctl list`: status 0), and its log shows it
publishing at 2026-09-23 06:22. It runs `app.workflows.refresh --epoch-dir
<the owner's 2026-08-15 bundle directory>`. D-158 gives an owner-supplied directory precedence, so
this job never fetches. Only `adapter/nightly.py` passes `--fetch-epoch`, and no engine was running
when I checked. The PR's claim "the nightly command passes it" is true of a scheduler that is not
the one refreshing today.

**What that directory does under this branch** (measured on copies of the served artifact):
- It has the OLD layout (`epoch_capabilities_index.csv`). So every run records `epoch_eci` as drift:
  "missing CSV … `epoch_capabilities_index/eci_scores.csv`". `everyday`'s primary board then carries
  and, 30 days after its last arrival, expires.
- Before the owner publishes the derived artifact, every run is refused by D-132 (the P4 roster
  jump), like any cycle.
- **After the owner publishes it**, a refresh with that directory is refused: **exit 3**, "the
  candidate is worse than what is being served -- agentic-coding would lose 5 of 18 models". The
  stale bundle lacks the rows the fresh one added. So from the deliberate publish onward, the only
  running refresher refreshes nothing, LiteLLM and Arena included, every twelve hours, until someone
  notices.

**Why MAJOR:** the wave's goal ("every board the product reads is fetched by the nightly refresh
itself") is not met where the product runs, and merging moves the running refresher from "stale
Epoch" to "refused every cycle". It is not BLOCKING because nothing wrong is served (the guards
refuse), and because the launchd job is already scheduled for retirement (D-151, D-154,
`scripts/retire_refresh.sh`).

**Remedy.** Add one of these to the PR's "After merge" list, and say which, BEFORE the deliberate
publish:
- (a) retire the launchd job with `scripts/retire_refresh.sh` and run the engine's own nightly; or
- (b) change `scripts/refresh_job.sh` to pass `--fetch-epoch` in place of `--epoch-dir "$EPOCH"`
  (in this PR), and have the owner reinstall it with `scripts/install_refresh_wrapper.sh`.

Either way, name the hand-kept directory as retired so nothing passes it again.

### MINOR-1 -- `ReconcileReport.scores_dropped` can be negative

`reconcile` counts `s_total` AFTER `_register_derived` has rewritten efforts
(`registry.py:599`), while `s_matched` counts the `(raw_name, effort)` pairs BEFORE it. When one
name has an explicit-effort row and an `unspecified` row whose suffix states the same effort, the
update merges two pairs into one.

```python
conn = _conn(["openai/gpt-6-astra"], [("gpt-6-astra_high", "A", "high"),
                                      ("gpt-6-astra_high", "B", "unspecified")])
reconcile(conn).scores_dropped   # -> -1
```

Today nothing but the report reads it (`drift_dropped`, `registry.py:442-444`). *Remedy:* take
`s_total` before the derived links, or count matched and dropped pairs from the table afterwards,
both at the same moment. Add the test above.

### MINOR-2 -- five load-bearing lines no test holds (the PR says "every mutant goes red")

Five of my 38 mutants stay GREEN on the full suite (table below). Each has a killer test that
passes on HEAD and goes RED on its mutant. I verified all five in scratch; they are not in the
repository.
- **M21** removes the Fable 5 parent's version guard (`registry.py:58`). No test fails, because
  `claude-fable-5.1` precedes it. **P3's actual defect class, "the parent rule had no version
  guard", is therefore unpinned:** a Fable 5.2 would fold into Fable 5 again. Killer: `canonicalize`
  of `claude-fable-5-2`, `claude-fable-5.2` and `Claude Fable 5.3` is never `claude-fable-5`.
- **M23** removes `- curated` from `_Pending.ready` (`registry.py:491-493`), so "curated rules win"
  is unpinned. `test_the_curated_rules_win` cannot reach it, because `gpt-5` derives to `gpt5`. The
  exclusion is reachable, though. Grammar fixed points exist among the curated ids (`o3`, `kimi-k2`,
  `qwen3-max`, `mistral-large`, `deepseek-r1` and 19 others), and `o3_none` / `o3_minimal` match no
  curated rule but derive to `o3`. Killer: `reconcile` of price `o3_none` + score `o3_minimal` has
  `derived == ()`.
- **M29** removes vendor-from-route. Killer: `openrouter/meta-llama/zeta-9` + `zeta-9` gives vendor
  `Meta`. Today the family fallback hides it for `gpt`.
- **M31** drops `len(derived_ids)` from `models_registered`. Killer: one derived model gives
  `models_registered == 1`.
- **M32** stops treating `_none` / `_minimal` as decoration. Killer: `gpt-6-astra_none` and
  `_minimal` derive to `gpt-6-astra`'s id. The existing test asserts only `effort is None`.

### MINOR-3 -- the deliberate publish moves eight surfaces' median price by 43-72%, and the records describe only the roster refusal

The measured refusal (a real `--fetch-epoch` cycle on a copy of the served artifact) names two guards:
- the new-names guard: 9 surfaces, from `agentic-coding` 28% to `expert` 66%;
- **the D-132 median-price guard: 8 surfaces**, for example `assistant` $2.95 → $0.81 (-72%),
  `expert` $3.00 → $0.97 (-68%) and `everyday` $3.00 → $1.08 (-64%).

`docs/research/m16-w4-derived-registry-2026-09-23.md` and the PR's "After merge" section mention only
the first. The medians move because the derived roster adds many older, cheaper models. Every
`cheaper_by_percent` sentence the app composes is relative to that median (the M14-W1 lesson,
recorded at `registry.py`'s modality-guard comment). The owner should see this before publishing by
hand. *Remedy:* add the median table to the measurement record, and one line to the PR.

### NIT-1 -- drift lines repeat the source name

`build.py:392` and `:451` prefix `f"{source}: "` to an exception whose message already starts with
it. Measured: `epoch_eci: epoch_eci: missing CSV in local unpacked bundle: …`. `/health` shows only
the prefix, so the effect is limited to the record.

### NIT-2 -- the display and vendor choices the grammar makes

- Epoch's MMLU board names Bedrock ids, so `nova-lite`, `nova-micro` and `nova-pro` display as
  `amazon.nova-lite-v1:0`.
- Vendor "Other" covers 23 models, including Mixtral, Yi, Granite, CodeLlama, StarCoder and DBRX.
  `_FAMILY_VENDORS` has no `mixtral`, `yi`, `granite`, `codellama` or `starcoder`.
- Neither is misleading about the model's identity. D-157 accepts the grammar's display as the cost.

### NIT-3 -- the bundle-gated tests pin the 2026-08-15 bundle

With `EPOCH_DATA_DIR` set to today's bundle, 6 of the opt-in tests fail on row counts, for example
`test_deepswe_workflow.py:177` 68 ≠ 49. Now that the refresh fetches every night, those pins no
longer describe any bundle the product reads. Queue a re-pin, or a relabel as "the 2026-08-15
snapshot", to the closure.

## Mutants

For each mutant, a script in the session scratch directory did the following:
1. Took the file's md5.
2. Replaced exactly one unique string, refusing if it matched more or less than once.
3. Ran the 13 phase test files with `pytest -n auto --no-cov`, and the full suite whenever those
   stayed green.
4. Wrote the original bytes back.
5. Asserted the md5 equal.

No restore failed. After the run, the copy's seven source md5s equal the snapshot.

| # | Mutant (load-bearing line) | Result |
|---|---|---|
| *M1* | *`_safe_relative` without `".." in path.parts`* | *GREEN, equivalent: the resolved-path layer (`_plan`) refuses the same names, and the test's `match="outside"` accepts "resolves outside"* |
| M2 | symlink member not refused | RED `test_epoch_bundle_fetch.py:55` |
| M3 | resolved-path check removed | RED `:173` |
| M4 | unpacked budget never trips | RED `:61`, `:307` |
| M5 | member read back to an exception allowlist | RED `:360` |
| M6 | member-count cap removed | RED `:70` |
| M7 | `_fetched_epoch` catches `(SourceError, OSError)` only | RED, 5 (`:123`, `:224` ×2, `:242`, …) |
| M8 | no cleanup on an interrupt | RED `:259` |
| M9 | redirects followed | RED `:315` |
| M10 | deadline check removed | RED `:332` |
| M11 | sweep skips `.epoch` | RED `:278` |
| M12 | sweep takes young scratch too | RED `:278` |
| M13 | scratch not removed after the cycle | RED `:103` |
| M14 | nightly passes nothing without an owner directory | RED `test_nightly_refresh.py:327` |
| M15 | `--fetch-epoch` ignored | RED `test_epoch_bundle_fetch.py:157` |
| M16 | board drift not recorded | RED `test_epoch_layout.py:53`, `:82` |
| M17 | bundle-client drift not recorded | RED `:53` |
| M18 | the cycle drops the build's drift | RED `:82` |
| M19 | `/health` `refresh_drift` empty | RED `:70` |
| M20 | ECI score column `eci_ci_high` | RED `:39` |
| **M21** | **Fable 5 parent without its version guard** | **GREEN, 1125 passed** (MINOR-2) |
| M22 | Fable 5.1 rule deleted | RED `test_registry.py` `test_variant_never_leaks_into_parent` |
| **M23** | **curated ids not excluded from derivation** | **GREEN, 1125 passed** (MINOR-2) |
| M24 | threshold price OR score | RED, 5 |
| M25 | underscore effort not stored | RED `test_registry_derived.py:84` |
| M26 | `5-5` not read as 5.5 | RED, 3 |
| M27 | `gpt-6` / `gpt6` not unified | RED `test_registry_disclosure.py:30` |
| M28 | modality guard removed from derivation | RED `test_registry_derived.py:64` |
| **M29** | **vendor from route disabled** | **GREEN** (MINOR-2) |
| M30 | unlinked prices not counted as dropped | RED, 2 |
| **M31** | **`models_registered` omits derived** | **GREEN** (MINOR-2) |
| **M32** | **`_none` / `_minimal` not decoration** | **GREEN** (MINOR-2) |
| M33 | `@` not stripped | RED `test_registry_derived.py:39` |
| M34 | route kept (`/` becomes `-`) | RED, 6 |
| M35 | modality refusals listed as unmatched | RED `test_registry_disclosure.py:30` |
| M36 | an unserved cycle overwrites the served lists | RED `:57` |
| M37 | top 6 unmatched, not 5 | RED `:45` |
| M38 | build report omits derived | RED `:30` |

**Totals:** 38 mutants: 32 RED, 5 GREEN (MINOR-2), and 1 equivalent (M1).

**Killer tests.** The five in MINOR-2 were verified in scratch: each passes on HEAD and is RED on
its mutant. The md5 check after that run matched too.

**Red to green, replayed.** I exported each red commit with `git archive` and ran its new tests
against that commit's own `src`, which is the pre-fix code:
- `477ef68`: 5 FAIL.
- `1271c59`: 1 FAIL (`test_variant_never_leaks_into_parent`).
- `de44a16`: 10 FAIL, which are exactly the security-pass tests.
- `a25b1ef`: 2 FAIL.
- `fbe892e` and `c90ebc1`: collection errors, because `app.clients.epoch_bundle` and
  `registry.derive_identity` do not exist yet. That is a legitimate red.

All are green at HEAD. The green commit `7ee8f7d` adds one more disclosure test,
`test_a_cycle_that_is_not_served_keeps_the_served_lists`. That strengthens the suite; nothing was
weakened.

## Hardened-invariant producer section (Code-Reviewer §2a-bis)

**Invariant 1 (D-157 clause 3): a variant never merges into its parent.**
- The only producer is `derive_identity` (`registry.py:375`). Its only consumer is `_unmatched`
  (`:532`), which feeds `_Pending` and then `_register_derived`.
- Citing tests: `test_registry_derived.py:48` (`gpt-6-astra-mini`, `-luna-pro`, `qwen3.7-plus`,
  `o3-2025-04-16`, `mistral-small-2603`, `gpt-6-astra-max`) and `:52`.
- **Gaps: BLOCKING-1.** No negative case exists for `-vN`, `@NNN`, `:variant` or vendor heads.

**Invariant 2 (D-158 clause 2): the archive is untrusted, and a refusal is a failed source.**
- Producers: `_safe_relative` and `_plan` (names, links, resolution and count), `_write` (budget and
  total over codecs), `unpack` (total over the container), `_fetched_epoch` (total over the fetcher
  plus cleanup), and `_sweep_stale_scratch`.
- Citing tests: `test_epoch_bundle_fetch.py:47`, `:55`, `:61`, `:70`, `:76`, `:123`, `:173`, `:217`,
  `:224`, `:242`, `:259`, `:278`, `:307`, `:315`, `:332` and `:360`.
- Gaps: none found. M1 is covered by the second layer.

**Invariant 3 (D-157 clause 1): the curated rules win.**
- The producer is `_Pending.ready` (`registry.py:491`).
- The only citing test is `test_registry_derived.py:107`, which cannot fail on M23 (MINOR-2).

**K.8 contract check** (`grep -rn "fetch_bounded_bytes\|derive_identity\|fetch_epoch=\|--fetch-epoch\|name_column" src`):

```
src/app/clients/protocols.py:45:def fetch_bounded_bytes(
src/app/clients/protocols.py:94:    return fetch_bounded_bytes(url, name, timeout, params).decode("utf-8", "replace")
src/app/clients/epoch_bundle.py:132:    return fetch_bounded_bytes(url, NAME, TIMEOUT_SECONDS, limit=MAX_BUNDLE_BYTES,
src/app/clients/epoch_board.py:58:    name_column: str = "Model version"
src/app/workflows/registry.py:375:def derive_identity(name: str) -> DerivedIdentity | None:
src/app/workflows/registry.py:532:    derived = derive_identity(grammar_name)
src/app/workflows/sources.py:277:        name_column="Model",
src/app/workflows/refresh.py:1139:            fetch_epoch=epoch_bundle.fetch_bundle if args.fetch_epoch else None,
src/app/adapter/nightly.py:209:    command += ["--epoch-dir", epoch_dir] if epoch_dir else ["--fetch-epoch"]
```

`fetch_bounded` keeps its signature as a wrapper, so every text source is unchanged. `/v1` is
untouched, as ruled in the plan's decision 2.

## Plan compliance (docs/plans/m16-wave-4-plan.md §Phases)

- **P1:** delivered. The nine Epoch sources are in `sources_last_ok` after a real `--fetch-epoch`
  build (all 19 arrived).
- **P2:** delivered. `everyday` arrives, and drift is by name. There is one stale directory in the
  field (MAJOR-1).
- **P3:** delivered. The guard itself is unpinned (MINOR-2).
- **P4:** the plan's own red tests exist and pass, and the measurement is recorded: 661 of 2,581
  unmatched score rows, which I reproduced exactly. But "a variant never merges" does not hold
  (BLOCKING-1).
- **P5:** delivered.
- **Decision 3 (the acquisition clock):** delivered in the record. The CI step is proposed in the PR.

## K.9 candidates outside this wave's scope

- **`:batch` prices** (batch-discounted SKUs) fold into the same model's median. This predates the
  wave for curated models; derivation extends it (`gpt6-astra` has 3 `:batch` aliases of 12).
- **`split_harness` credits an architect pair to its editor model**: `DeepSeek R1 +
  claude-3-5-sonnet-20241022` counts as Claude 3.5 Sonnet. This predates the wave; derivation
  extends it.
- **Curated models lose rows the grammar would have found.** `o3_none` and `o3_minimal` are o3's
  runs, and they stay unmatched because the curated `o3` rule refuses the suffix. They sit in the
  unmatched list. That is a curation item, not a merge.
- **The ECI board now reads the `Model` column.** Each row aggregates `model_versions`, so an ECI
  row can stand for several dated snapshots. Pairing it with an undated price is right. Pairing it
  with a dated one would need the snapshot.

## Gates

`make -k -o install -o .venv/bin/python gate` ran on the clean copy:
- **gate PASS**, exit 0.
- **lint:** ruff "All checks passed!".
- **typecheck:** mypy "Success: no issues found in 35 source files".
- **test:** pytest **1125 passed, 15 skipped** (the PR's number), total coverage 90%.
  - The touched modules: `epoch_bundle.py` 95%, `protocols.py` 100%, `registry.py` 94%,
    `build.py` 94%, `refresh.py` 96%, `nightly.py` 99%, `sources.py` 100%.
  - The uncovered new lines are `epoch_bundle.py:69` (a directory member's `continue`),
    `epoch_bundle.py:123-125` (the generic catch for name collisions, which my scratch hostile
    archives exercised), and `registry.py:399` (the grammar's `None` for an unreadable remainder).
- **coverage-floor:** "PASS: 35 module(s)".
- **records:** `check_records` PASS and its self-test PASS.
- **shell-dialect:** PASS, 11 scripts.
- **wave-check-all:** PASS, 42 records.
- **conformance:** PASS, 14 of 14 (0 dangling paths).
- **swift-test:** PASS, 268.
- **client-decls:** PASS, 4 configurations.
- **falsify:** SKIPPED (an installation).
- **secrets:** gitleaks "no leaks found".
- **deps:** "No known vulnerabilities found".
- **slopsquat:** PASS, 17.

## What I did not check

- **Live cycles.** Only the one-off real fetch, one real build and two real refresh cycles on copies.
  No night was observed end to end on the owner's machine.
- **Peak memory for F3's 16 MB central directory**, and Windows path semantics.
- **Whether each of the 241 registered derived ids is one model.** I read every group's price
  aliases and score names by eye, and audited every name the strip rules touch mechanically. A merge
  from two upstreams that spell different models identically is beyond what the grammar can see, and
  beyond what I can rule out.
- **The picks tables in the measurement record.** I reproduced the counts (241 derived, 316 models,
  661 of 2,581), not the per-surface picks.
- **Licence questions (W-129)**, the proposed CI change, and D-148's floors on fresh data. The PR
  leaves all three to the owner.
- **Security at milestone closure (Stage 4.0).** P1 was reviewed by its own seat; I verified its
  fixes and did not repeat its full scope.
