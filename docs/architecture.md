# Architecture — model_ranking

> What the system looks like and the contracts between its parts, as the code stands after
> M19's five waves (2026-10-07). Per seed A.2, the PRD, the ADRs and this document are adversarial sources of
> truth until shown consistent; §7 lists where a record and the code disagree. Cites ADRs in
> `docs/decisions.md` and files, never line numbers.

---

## 1. System diagram

```
UPSTREAM SOURCES (untrusted input)
  prices : LiteLLM, OpenRouter
  scores : SWE-bench Verified, Aider, seven Arena boards and Arena's category slices (Hugging Face),
           the Epoch AI bundle (a zip from epoch.ai; also each model's accessibility)
      |  bounded HTTP fetches, made only by the refresh's child process
      v
OWNER'S MAC: launchd service com.ilgar.modelranking.engine, a deployed release of main (D-170)
  engine process (FastAPI + uvicorn, :8080)
    nightly task --spawns--> refresh child: fetch, build a candidate, guard it, rename it into place
                                 ^ curated data/plans.yaml, data/rosters.yaml
                                 v
                             advisor.db  (one SQLite file: the artifact)
    routes read it read-only: /health  /v1/categories  /v1/recommendations  /v1/budgets  /v1/boards
      |  HTTP GET, Host-checked; loopback by default, the home network by opt-in (D-171)
      |
      |  the owner's deploy: app.workflows.public derives a public copy, without the sources
      |  whose terms do not permit it (D-185), and the image carries it
      v
FLY.IO, serving TestFlight since 2026-10-07: one machine, the `hosted` image, Host model-ranking.fly.dev
    the same five routes over HTTPS; no refresh (D-116); a new deploy per refresh made public;
    one client limited to 120 requests a minute, a /v1/boards answer counting thirty (#187, INV-88)
      |
      v
IPHONE APP (SwiftUI): a Debug build asks the Mac, a Release build (TestFlight) asks Fly.io
  question -> router (on-device model, then sentence similarity, then manual) -> surface + refinements
           -> reading (signals in code + the model's verdict): a search, a note, or a one-tap question back
  EngineClient: GET /v1/categories, /v1/recommendations?task=SURFACE&budget=unlimited, /v1/boards
  StandingsStore (kept one day, on the device) -> Combine.swift -> the product's own combined list
  screens: home (cards, or the combined list), full ranking, model detail, combined-list detail
  never sent: the question's text, its refinements, the reader's removals, the gap register
```

The product is a dashboard over published measurements of AI tools (D-126). It reads the boards,
says how old they are, and has no opinion of its own. Every number a reader sees is computed by
deterministic, tested code (D-104).

## 2. The parts

| Component | Owns | Does not own |
|---|---|---|
| `src/app/clients/` | One client per upstream: bounded fetches, parsers, the parquet reader process, fakes for tests | Ranking policy; anything the serving process loads (W-125) |
| `src/app/workflows/` | Ingest, registry, build, refresh, ranking, recommendation, floors, standings, serving bounds, schema; the client-free tables and records the server shares with the clients (`board_tables`, `run_records`); the CLIs (`build`, `refresh`, `recommend`, `coverage`, `schema migrate`) | HTTP |
| `src/app/adapter/` | The HTTP surface (`main.py`) and the nightly schedule (`nightly.py`) | Computing a number; running ingestion in the serving process |
| `data/` | Curated plans and rosters; the Epoch bundle URL | Benchmark evaluation dates |
| `ios/ModelRanking/Engine/` | Routing, reading the question, the engine client, the standings store, the combination, the notices, every rule a screen applies; run by `swift test` through `ios/Package.swift` | Ranking a model; any number the engine did not send, except the two named arithmetic files |
| `ios/ModelRanking/ContentView.swift` | Rendering the screens | Decisions |
| `ios/UITests/` | The UI test target, run locally by `make ui-test` (D-175) | Judging the on-device model's reading (the router probe measures it) |
| `scripts/install_engine_service.sh`, `scripts/engine_service.sh`, `scripts/remove_engine_service.sh` | Deploying, starting and removing the engine service on the Mac | — |
| `Dockerfile`, `fly.toml`, `scripts/deploy_hosted_engine.sh`, `src/app/workflows/public.py` | The hosted engine: its image, its one machine and Host, the one way to deploy it, and the public artifact it carries (D-185) | Refreshing: the hosted engine serves what the owner's Mac derived |
| `requirements/*.lock` | The exact versions, with hashes, that every install takes, written by `make lock` (D-177) | Choosing versions: `pyproject.toml` declares the ranges |
| `src/app/workers/` | Nothing (an empty package) | — |

### 2.1 The build and its sources

`python -m app.workflows.build --db PATH` builds a new artifact. It writes to a uniquely named
temporary file and renames it onto the target only when the build finished. Its exit codes follow
D-120: `0` built and servable, `2` failed, `3` built but not servable.

The sources are declared once, in `src/app/workflows/sources.py`, and the build and the smoke gate
both derive from that list:

- **Prices:** LiteLLM and OpenRouter. Both are required.
- **Scores fetched over the network:** SWE-bench Verified and Aider, both required. Seven Arena boards
  (`arena`, `arena_document`, `arena_factuality`, `arena_vision`, `arena_search`,
  `arena_search_factuality`, `arena_webdev`) are optional (D-121): without one, its surface says it has
  no evidence. `arena_webdev` is `web-dev`'s board since M21-W1 (D-190).
- **Arena's category slices** (text and vision) and the Agent Arena boards are read from one parquet
  file per config (`src/app/clients/arena_slices.py`). Each slice is a board of its own (D-164).
- **The Epoch AI bundle.** The refresh downloads it and the build only reads the unpacked
  directory (D-158). The build reads the SWE-bench Verified and DeepSWE CSVs, the Epoch boards the
  surfaces rank on (`EPOCH_BOARDS`), and each model's accessibility from Epoch's model metadata file
  (`src/app/workflows/access.py`).
- **Curated data in the repository:** `data/plans.yaml` and `data/rosters.yaml` (subscription
  plans, D-107), read through the bounded loader in `src/app/workflows/yaml_guard.py`.
  `data/epoch-source.yaml` keeps the bundle's URL.

Every source name is reconciled to one canonical model by the curated rules in
`src/app/workflows/registry.py`. A name no rule matches becomes a derived model when it has both a
price and a score (D-157). A moving, undated alias never derives one (D-166). One release is one
model, dated or not, where its maker lists one snapshot, and each minor release's mini, nano, chat
and Codex mini is a model of its own (M19-W1, #129, #162). A model is named as its maker spells it
(`registry.DISPLAY_NAMES`, each with its maker's page, #112).

A source that fails a cycle serves its last good rows from the live artifact for up to 30 days,
counted from when it last arrived (D-156). Past that, an optional source's surfaces drop and say
so, and a required source fails the build.

### 2.2 The artifact

- One SQLite file: `advisor.db` in development, and
  `~/Library/Application Support/model-ranking/engine/data/advisor.db` under the service (D-170).
  It holds the model registry, scores, prices, price medians, accessibility and the curated plans.
- Each surface's floor is not stored. It is derived where it is read, from the served rows, by
  `src/app/workflows/floors.py`: the top third of the surface's own board (D-148, D-159).
- Every reader opens the artifact through `schema.open_readonly`, whose URI is derived from the
  resolved path, never concatenated (INV-23). Only the named writers open it writable
  (`tests/unit/test_readonly_uri.py`). The serving path performs no write.
- The refresh keeps its lock and its record beside the artifact, as `<artifact>.refresh.lock` and
  `<artifact>.refresh.json`.

### 2.3 The engine

`src/app/adapter/main.py` is a FastAPI application run by uvicorn. It declares exactly five
routes (`DECLARED_ROUTES`), all GET, and turns the docs and OpenAPI routes off.

| Route | What it serves | ADRs |
|---|---|---|
| `/health` | `status`, `version`, `build` (L.7); `evidence` (`servable` or `unavailable`); the refresh's state, last outcome, carried and expired sources, drift, derived and unmatched names | D-154, D-156, D-157 |
| `/v1/categories` | Each surface: benchmark, metric, ranking effort, close-call margin, floor (`min_quality`), out-of-100 anchor, what its price leaves out, its primary board, its family of boards and the board a refinement takes the place of (`refined_board`, D-188 clause 6; `boards`, the primary first, `app.workflows.families`, D-188), its second board's age | D-138, D-152, D-153, D-159, D-162, D-168, D-188 |
| `/v1/recommendations?task=&budget=` | One answer per surface: up to three picks, each with its model's id (`model_id`, D-182), with the facts the client words in its own language, and the full ranking in the engine's order, with source health and evidence dating. Each notice has its fact: `close_call_fact`, an empty answer's `unavailable_reason_code`, a source's `reason`. `task=coding` answers on both coding surfaces and neither leads (Ruling A) | D-115, D-125, D-136, D-176 |
| `/v1/budgets` | The budget caps (`low` $2, `medium` $8 per 1M blended tokens, `unlimited`) and the blend weights | D-134 |
| `/v1/boards` | Every board's standings as positions, never scores, and each model's name, vendor, blended price and accessibility. No parameters. Built once per artifact | D-167, D-173 |

- **The adapter computes nothing.** The numbers come from `app.workflows` (`recommend`, `rank`,
  `standings`). The adapter decides what is published through explicit allowlists
  (`PUBLIC_ANSWER_FIELDS`, `PUBLIC_PICK_FIELDS`, `PUBLIC_RANKING_FIELDS`). Scores are rounded to
  one decimal at that boundary (D-109).
- **Startup checks.** `validate_startup_config` runs at import, which is this process's only boot:
  - a CORS wildcard or a malformed origin is refused;
  - `MODEL_RANKING_DB` must name a file that opens read-only as this project's database, with the
    effort column and price medians, and at least one surface must rank (the check runs the
    serving path itself);
  - the serving bounds in `src/app/workflows/serving_bounds.py`: at most 500 rows in one answer,
    25,000 positions on `/v1/boards` and 5,000 ranked models, each overridable by its environment
    variable. A response is never trimmed to fit; an artifact past a bound does not start;
  - binding beyond loopback needs a Host list (D-171); the image tells the check where it binds, so
    an image run with no list refuses to boot (#94);
  - the nightly switch is allowed only in a relaxed environment (D-154);
  - `APP_BUILD` is required in a strict environment (L.7).

  A strict environment (production, or any value outside `development`, `dev`, `test`, `local`,
  including unset) refuses to start on a problem. A relaxed one logs it. The service runs with
  `APP_ENV=test`, and its launcher runs the same checks first and refuses to start on any problem
  (W-042).
- **Per request:** the Host check (§4), `X-Content-Type-Options: nosniff` on every response, one
  JSON error shape, a 500 that carries no exception text, gzip for responses of 1 KB or more
  (D-173), and a thread-pool cap (`MODEL_RANKING_MAX_CONCURRENCY`, default 8). An unusable artifact
  answers 503 `evidence_unavailable`, with no file path in the body.
- **A republished artifact is picked up on the next request.** Each request opens the file by
  path. The memos for the probe and for `/v1/boards` are keyed on the file's identity, not its path.
- **Credits follow what is served.** Each answer's `sources` and `attributions` name the boards it
  ranks on, each with its own licence and original source (#124), and the price sources the artifact
  carries (`rank.served_pricing_sources`, D-185): the public artifact credits LiteLLM alone.
- **The serving process loads no ingestion code.** Importing `app.adapter.main` loads no
  `app.clients` module, no `app.workflows.ingest`, no `httpx` and no `pyarrow` (W-125, fixed in
  M18-W6). The record types and tables both sides need live in client-free modules.

### 2.4 The nightly refresh

The engine runs its own refresh (D-149, D-151, D-154). The schedule is an asyncio task in the
engine's lifespan (`src/app/adapter/nightly.py`). It is on only with
`MODEL_RANKING_REFRESH=nightly`, which `scripts/engine_service.sh` sets, and only in a relaxed
environment.

- **When:** once a night, at a random minute between 23:00 and 01:00 local time.
  - At startup, after 60 seconds, it runs once if the last good cycle is more than a day old.
  - A run that falls due after its window closed (a Mac asleep) runs only if the data is a day old.
  - A nightly run is skipped when a good cycle ran in the last 4 hours.
- **How:** a child process, `python -m app.workflows.refresh --db ... --fetch-epoch`. It takes
  `--epoch-dir` instead when the owner sets `MODEL_RANKING_EPOCH_DIR`.
  - The child inherits an allowlisted environment, and only the last 64 KiB of its output goes to
    the engine log.
  - Three limits bound it (D-154 as amended in M18-W6). Its downloads share a 20-minute budget,
    after which the sources left carry their last good data (D-156). At 27 minutes the kernel ends
    the cycle (SIGALRM). At 30 minutes, and on shutdown, the engine kills it.
  - The child runs in a session of its own, and the engine kills its whole process group, so a
    grandchild such as the parquet reader cannot outlive it (W-130). The engine names itself to the
    child, and a child whose engine is gone ends itself within seconds (W-126).
  - No request ever waits on it, and the serving process never imports the refresh, the build, the
    fetchers or any client (`tests/unit/test_nightly_refresh.py`).

One cycle, in `src/app/workflows/refresh.py`:

1. Checks its environment: the artifact's directory must not be writable by group or others, and
   the clock must be usable.
2. Takes an `flock` lock. A second cycle exits `4` (busy) and records nothing.
3. Fetches the Epoch bundle into scratch beside the artifact. A refused or failed bundle is a failed
   source and carries (D-158).
4. Builds a candidate beside the artifact, carrying failed sources (D-156).
5. Compares what the candidate would serve with what is served. The fingerprint covers ranked rows,
   floors, every board no surface ranks on, and accessibility. If nothing changed, it exits `1`
   (unchanged) and publishes nothing.
6. Applies the publish guards below. Any reason exits `3` (refused), and the live artifact is
   untouched.
7. Re-reads the live artifact. If it changed during the cycle, the cycle refuses.
8. Publishes by renaming the candidate onto the artifact in the same directory, and exits `0`
   (published).
9. Writes `<artifact>.refresh.json` on every path except busy (D-129).

**Publish guards.** In one sentence: a surface may not change by more than a quarter, in either
direction, without somebody looking (D-128, D-132). The candidate is refused when:

- it is past a serving bound (D-173 clause 4);
- a surface that answered would answer nothing, or would lose a quarter or more of its models (D-128);
- a surface would offer no model at a budget where it offered some (D-128, amended);
- more than a quarter of a surface's models are ids never served before (D-132; ids, not names,
  D-173 clause 2);
- a surface's median price would move more than a quarter, either way (D-132);
- a surface's own board, or any board no surface ranks on, would lose a quarter or more of its
  rows, or would be more than a quarter new rows; a row the reconcile linked to a model is compared
  by that model, so a re-spelling is recorded, never refused (D-159, D-164, D-179);
- the number of models with an accessibility value would fall by a quarter or more (D-173 clause 3).

Not refused, on purpose:

- scores moving in either direction;
- a surface growing within the limit;
- a surface or a board returning from empty.

On a night a source expires, the guards judge against the live artifact without that source's
rows (D-156).

A failed night shows in two places only: the engine log and `/health`. The app has no refresh
control and shows no refresh state (D-151).

### 2.5 The phone

A SwiftUI app in `ios/ModelRanking/`, with iOS 18 as its deployment target. Its logic lives in the
Engine layer, `ios/ModelRanking/Engine/`, which `swift test` compiles from the same files the app
ships (`ios/Package.swift`). `ContentView.swift` only renders.

- **Router** (`Router.swift`; D-126, D-147, D-168). `TieredRouter` tries three tiers and shows the
  reader which one answered:
  1. The on-device model (FoundationModels, iOS 26 with Apple Intelligence available), within
     8 seconds. A generation schema limits its output to the surface ids `/v1/categories` served,
     plus a decline value, and one field each for language and domain from the declared table,
     plus `none`. A last closed field says whether the input is a search for a model at all
     (D-169 as amended). `ModelOutputBoundary` then drops any surface the engine did not serve and
     any refinement the chosen surface does not allow.
  2. The wording tier: first the words that name a surface outright, in English and Turkish
     (`CategoryHints.surfaceWords`, D-187), then sentence similarity (`NLEmbedding`) against example
     questions for each surface. The words need no model and no embedding; where the embedding
     cannot run, a question about AI models in general is answered from `everyday`.
  3. Manual: the chat ranking (`assistant`), marked unmeasured. The reader corrects it with the
     Change sheet.

  The router picks the question; it never ranks or recommends (D-126). A search the catalogue
  does not measure is answered with `assistant`, marked unmeasured, and counted in the gap register
  on the device (`FrontDoor.swift`). Only a search is counted. The register is kept in Application
  Support and excluded from backup.
- **Reading the question** (`Reading.swift`, `TieredRouter.read`; D-169 as amended in M18-W3).
  - Signals decided in code run on every tier: no word in any language, small talk, pasted
    content, and an instruction to the app.
  - With the model's verdict, they give one of three readings. No word or small talk alone gives a
    short note and no ranking. A doubt in code together with the model's "not a search" gives the
    note too. Either one alone gives a one-tap question back, and nothing is sent until the reader
    answers.
  - A question of fact ("who won the 2018 World Cup", its Turkish forms too) is a doubt in code,
    unless it names an AI model or a task (D-184). A greeting's thanks is small talk, and a pasted
    error or text stays pasted content unless a model question follows the colon.
  - An understood question is answered from the closest board, never "not measured" (D-187): a
    request to make or change an image from `vision`, a question about speed or sound from the
    closest surface. "Not understood" is left for a question that names no surface and either scores
    below the wording tier's floor or is in a language the embedding does not read; it goes to the
    manual tier and offers Change.
  - A note or a question back sends no request and records no gap.
- **Refinements** (`Refinements.swift`, D-168): a declared table of Arena text slices, eight task
  languages and eight domains, each with the surfaces it may refine. A coding question takes none
  (Ruling A). The on-device model chooses them where it read the question; otherwise the answer plan
  reads them from the question's words (`Refinements.read`, D-188 clause 6), the one reader, held in
  part by the text pins (INV-89). Every refinement is a slice of Arena's text vote, so it takes the place of the
  family's board of that vote (`refined_board` on `/v1/categories`): of a language and a domain, the
  language stands.
- **Engine client** (`EngineClient.swift`). The one network door, by design (D-126; held in part, INV-62).
  - The engine's address comes from the build's `EngineURL` (the `ENGINE_URL` setting in
    `ios/Config/Engine.xcconfig`), with loopback as the fallback. A Release build's address is the
    hosted engine, set after the local file's include so no local setting replaces it (D-185).
  - It uses an ephemeral session with a 10-second timeout, no cache and no cookies (INV-85), and the
    `SameHostOnly` redirect guard.
  - It reads each response as a stream and stops at the route's ceiling (#56): 4 MiB for
    `/v1/boards`, 1 MiB for `/v1/recommendations`, 256 KiB for any other route. A declared length
    over the ceiling is refused before the body is read.
  - It makes three calls: `/v1/categories` on every load, `/v1/recommendations` with the routed or
    tapped surface as `task` and `budget=unlimited`, and `/v1/boards` with no query.
- **Standings store** (`StandingsStore.swift`, D-167). Keeps the last `/v1/boards` payload for one
  day in the caches directory.
  - The payload is capped at 4 MiB before decoding, and only the fields the app decodes are stored.
  - The day's fetch starts after the answer, never before it. If a fetch fails, the kept copy is
    used.
  - The store refuses any address that is not a file on the device.
- **Combination** (`Combine.swift`; D-160, D-167, D-168, D-188). The only file allowed to do
  arithmetic on positions:
  - `combineFamily` (D-188, the default since M20): a surface's family of boards, from
    `/v1/categories`' `boards`. A model enters when half the family's boards rank it, rounded up; its
    place is the mean of its percentile positions on them, every board counting the same; an older
    or undated board is named under the list;
  - `combine` (D-167, for an engine that names no family): only the models every chosen board ranks,
    ordered by the sum of their ranks;
  - equal values share a place, broken by model id.

  `AnswerPlan.swift` decides what the screen shows: the family's list for every question asked and
  every surface chosen; a family of one board is its cards; the primary board's own answer is one
  tap away; coding shows two family lists or neither (Ruling A).
  - A model the engine picks for more than one reason is one card carrying every label it earned
    (D-175, #63 finding 1): the picks that share a `model_id` (D-182).
  - The combined list shows ten rows, and the rest on request.
  - The reader may keep only models with an API or open weights (#78). The filter reads the
    accessibility `/v1/boards` serves, hides rows, and never re-ranks: each row keeps its place, and
    the screen says how many it shows of how many.
- **Screens** (`ContentView.swift`):
  - The home screen: the question field and the routed surface with its tier. Below them, either
    one card per answer (up to three picks and a ranking preview, five models in all) or the
    combined list with its refinement chips, each removable with one tap.
  - The full ranking.
  - A model's detail (`Detail.swift`): where the number comes from, the surface's floor, and what
    the price leaves out.
  - The combined list's detail: each board with its date and attribution, how many models they
    share, the efforts mixed, and that the list is the product's own combination.
  - The gap list.

  The app speaks English and Turkish, writing each sentence from the facts the engine sends
  (`Language.swift`, D-136). The notices, too, are written from served facts (`Notices.swift`,
  D-176): the engine decides whether a notice is said, and the app how. Where a fact is missing, the
  engine's English is shown. `Uncertainty.swift` is the one file allowed arithmetic on scores
  (D-138).
- **Gates on the client.**
  - `tests/unit/test_ios_client_contract.py` and the declaration gate below: D-181 names the places
    arithmetic on a served number is permitted (scores and the tie margin in `Uncertainty.swift`, the
    anchor's conversions out of 100, positions in `Combine.swift`, prices in `priceInPages` in
    `Router.swift` and `Language.swift`). That no other place does it is held in part by the compiled
    gate and the text pins: see INV-76 in `docs/security-invariants.md`.
  - `scripts/client_decl_gate.py`: the declaration gate, which reads the declarations the compiler
    resolved, in all four build configurations (D-126, W-122). The network, the file system, the
    privacy sinks and the Release build's launch arguments are held in part by the compiled gate and
    the text pins: see INV-62, INV-63, INV-66 and INV-75 in `docs/security-invariants.md`, whose gaps
    name what is not held.
  - `tests/unit/test_router_hints.py`: the privacy pins, the text half of the client gates. What
    reaches an engine call, what the gap register keeps and the code the pins read are held in part
    by the compiled gate and the text pins: see INV-64, INV-67 and INV-78 in
    `docs/security-invariants.md`.
  - `make ui-test` (D-175): the screen's paths in the simulator, with scripted routing through the
    same boundary. It runs on the owner's Mac only, never in CI.

## 3. Data flows

**Nightly, on the Mac.** Upstream sources, then the refresh child, then a candidate, then the
guards, then an atomic rename onto the artifact. The engine reads the new file on its next request.
Nothing in this flow involves the phone.

**A question, on the phone.**

1. The reader types a question.
2. The router, on the device, picks a surface and, on the model tier, its refinements (the words
   choose them otherwise, in the answer plan).
   The reading decides whether it is a search. A note ends here, and a question back waits for
   the reader's tap. Neither sends anything.
3. The app asks `/v1/recommendations` for that surface.
4. With the standings kept, the phone combines the surface's family, a refinement in place of its
   vote's board, and shows that list; a family of one board, or an engine that names none, shows the
   engine's cards.

**Standings, once a day.** The app fetches `/v1/boards` with no query string, the same way whatever
was asked, so the request says nothing about the question (D-167 clause 1).

**What crosses from the phone to the engine.** Three GET requests. Their only parameters are
`task` and `budget`:

- `task` is a surface id the engine itself served, chosen by the router or tapped by the reader;
- `budget` is always `unlimited` in this app.

These requests cross the home network in cleartext when the opt-in is on (D-171 note 4). A
TestFlight build sends them to the hosted engine over HTTPS.

**What never crosses** (D-126; D-160 as amended by D-168 note 9; held in part by the compiled gate
and the text pins: see INV-64, INV-66, INV-67 and INV-89 in `docs/security-invariants.md`):

- the question's text;
- the refinements chosen and the reader's removals;
- the gap register;
- the kept standings;
- anything derived from the question other than the surface id.

**What crosses from the engine to the phone.** Public benchmark data only. There is no account and
no per-reader state.

## 4. Trust boundaries

**Upstream sources into the build: untrusted input.**

- Every fetch goes through `src/app/clients/protocols.py`: at most 32 MiB per response, at most five
  redirects, and each hop's host checked against the source's allowlist. Each source has a
  `minimum_rows` floor, so an empty success counts as a failure.
- The Epoch zip is refused whole for a member that names a path outside its directory, is a
  symbolic link, expands past the limit or is one too many (`src/app/clients/epoch_bundle.py`, D-158).
- Arena's parquet files are parsed in a child process under a 512 MiB memory ceiling and a time
  limit, with its answer bounded at 8 MiB (`src/app/clients/parquet_reader.py`, D-165).
- Curated YAML is bounded in size and alias expansion (`src/app/workflows/yaml_guard.py`).
- Upstream text that reaches a reader is bounded. A derived display name is at most 64 characters
  of a closed alphabet (D-157). A harness string is cut at 120 characters. A stored score is
  finite and a stored date parses (`tests/unit/test_stored_scores_are_bounded.py`).
- The publish guards (§2.4) are the last line: an upstream that floods, empties or re-prices a
  surface or a board is refused rather than served.
- Ingestion runs only in the refresh's child process, never in the serving process (D-116 clause 2,
  D-154).

**The network into the engine: the Host check** (D-171; `tests/unit/test_engine_host.py`).

- With `MODEL_RANKING_ALLOWED_HOSTS` set, a request whose Host (port removed, case ignored) is not
  on the list gets `400 unknown_host` before any route runs.
- Then the rate limit (#187, INV-88): with `MODEL_RANKING_RATE_LIMIT` set (120 in `fly.toml`), one
  client (an IPv4 address or an IPv6 /64, from `Fly-Client-IP`) past it in a clock minute gets
  `429 rate_limited` with `Retry-After`; a `/v1/boards` answer counts as thirty in a window of its
  own, so standings never block a question (#228); a refused request is not charged; `/health` is
  never limited, and a limiter that breaks serves the request (fails open).
- With no list, a request that arrived on a network address rather than loopback is refused,
  whatever the bind.
- The service always sets the list: `127.0.0.1` and `localhost`, plus the Mac's `.local` name and
  its LAN address under `--lan`. The hosted engine's list is `model-ranking.fly.dev` alone
  (`fly.toml`), and Fly's health check sends that Host (INV-86).
- The check stops a browser page that rebinds a name to the engine. It does not stop a person on
  the network, who can send an allowed Host by hand.
- Anything that forwards to loopback (a proxy, `ssh -L`, a tunnel) in front of an engine with no
  list exposes it with every Host served (D-171 note 9).
- Behind the check: GET only, `task` and `budget` closed sets (400 otherwise), echoed input capped
  at 40 characters, no cross-origin access unless origins are listed, and never a wildcard.

**The engine and the artifact: read-only readers.** Every reader goes through
`schema.open_readonly`. The serving bounds are checked when the engine starts and again on every
candidate before it is published (D-173 clause 4), so a refresh cannot publish an artifact a
restart would refuse.

**The engine's answers into the app.**

- `SameHostOnly` refuses any redirect to a host other than the configured engine, comparing hosts
  without case.
- The app allows cleartext only through `NSAllowsLocalNetworking` in `ios/Config/Info.plist`;
  there are no arbitrary loads. A Release build asks an HTTPS address.
- An undecodable payload is shown as a contract mismatch, not as an empty answer.

**The on-device model into the app.** `ModelOutputBoundary` (§2.5). Whatever the model returns
becomes a served surface id, a declared refinement, a yes/no reading, or nothing.

## 5. Deployment topology

```
owner's Mac
  launchd agent com.ilgar.modelranking.engine   (RunAtLoad, KeepAlive, ThrottleInterval 60)
    -> ~/Library/Application Support/model-ranking/engine_service.sh        (the wrapper)
    -> engine/current/scripts/engine_service.sh --service                   (the release's launcher)
    -> uvicorn app.adapter.main:app --host MODEL_RANKING_BIND --port 8080
  engine/releases/SHA      origin/main exported with git archive, its own venv from the locks, a RELEASE stamp
  engine/current           -> the live release (three kept; the previous one is never removed)
  engine/data/advisor.db   the artifact and its refresh record, kept across redeploys
  ~/Library/Logs/model-ranking-engine.log   the engine log, refresh output included
```

- **The service** (D-170). `scripts/install_engine_service.sh` deploys `origin/main`, writes the
  wrapper and the plist, and starts or restarts the service.
  - It waits up to 60 seconds for `/health` to report `release-<sha>`. If that does not happen, it
    rolls back to the previous release, or on a first install removes the service.
  - The owner runs it after each merge, or the agent does on his standing instruction. A merge is
    not live until it runs.
  - The release's venv takes `requirements/ingest.lock` and `requirements/build.lock`, hash-checked,
    then the project with `--no-deps --no-build-isolation` (D-177). Nothing else is resolved or
    fetched.
  - `scripts/remove_engine_service.sh` takes the service off and keeps the releases and the data.
- **The launcher** (`scripts/engine_service.sh`).
  - With `--service` it refuses to start a tree with no RELEASE stamp.
  - It sets `APP_ENV=test`, `MODEL_RANKING_DB` and `APP_BUILD`, and runs the startup checks.
  - It turns the nightly refresh on and starts uvicorn on `MODEL_RANKING_BIND`, which defaults to
    127.0.0.1.
  - Its preflight is judged by its exit status: a check that dies without a word stops the start
    (#145).
  - `ios/app.sh` starts the same launcher from the development checkout when the service is not
    installed.
- **The home network, by opt-in** (D-171).
  - `scripts/install_engine_service.sh --lan` binds 0.0.0.0 and adds the Mac's `.local` name and
    LAN address to the Host list. `--no-lan` closes it.
  - A plain reinstall keeps the mode it finds.
  - `--lan` binds every interface on every network the Mac joins. The macOS firewall is not a
    control for this; `--no-lan` is the only one (D-171 note 7).
  - A renamed Mac needs the installer run again.
- **The app.** The engine's address is set per build: `ENGINE_URL` in `ios/Config/Engine.xcconfig`.
  A git-ignored `Engine.local.xcconfig` overrides it for Debug builds only; a Release build always
  asks the hosted engine. `ios/app.sh` builds the simulator app pinned to loopback. Running on the
  owner's iPhone is `docs/owner-iphone.md`; TestFlight is `docs/release-testflight.md` (an icon, a
  privacy manifest, the encryption answer, a scheme that archives in Release).

```
Fly.io (D-116, D-185): prepared, deployed only by the owner
  scripts/deploy_hosted_engine.sh   origin/main's tip only, a clean tree; derives the public artifact,
                                    stamps APP_BUILD=release-<sha>-data-<digest>-from-<sha>
                                    (the release that built the data, #198; data another release
                                    built is refused unless DEPLOY_ACCEPT_DATA_FROM names it), fly deploy
                                    --remote-only --ha=false, then reads /health back
  Dockerfile, stage `hosted`        the `serve` stage (requirements/serve.lock, no pyarrow; the base by
                                    digest, #141) plus the public artifact at /srv/advisor.db, read-only,
                                    run as a non-root user
  fly.toml                          one shared-cpu-1x machine, 256 MB, always on; APP_ENV=production;
                                    MODEL_RANKING_ALLOWED_HOSTS=model-ranking.fly.dev; HTTPS forced
```

- **The public artifact** (`python -m app.workflows.public`, D-185 as amended by D-186, INV-87).
  Derived offline from the artifact the Mac serves. While the app is on TestFlight it leaves out no
  source (D-186): only the vendor plans go. A source put in `LEFT_OUT` loses every score, price and
  accessibility row and its copies under another source, the price medians are rebuilt, and the file
  is vacuumed so no byte of it is left.
- **No refresh on Fly.** A production environment refuses the nightly switch (D-154). The Mac
  refreshes; a refresh the owner wants public is one more deploy.

## 6. Cross-cutting concerns

- **AuthN / AuthZ:** none, by design. Every route is a GET over public benchmark data. There are no
  accounts, no mutating routes and no credentials, and CORS never allows credentials.
- **Logging and observability:**
  - the engine log: startup warnings, the refresh child's output tail, and one warning per artifact
    for a route that could not read it;
  - the refresh record, beside the artifact;
  - `/health`.

  The domain holds no secrets and no personal data. The app logs nothing: the client-declaration
  gate gives logging to no file.
- **Configuration:** environment variables, read when the process starts: `APP_ENV`, `APP_BUILD`,
  `MODEL_RANKING_DB`, `MODEL_RANKING_BIND`, `MODEL_RANKING_ALLOWED_HOSTS`, `MODEL_RANKING_REFRESH`,
  `MODEL_RANKING_EPOCH_DIR`, `MODEL_RANKING_CORS_ORIGINS`, `MODEL_RANKING_MAX_CONCURRENCY`, and the
  three `MODEL_RANKING_MAX_*` bounds. The app's only setting is the engine address, baked into each
  build (D-171 note 5).
- **Error handling:**
  - A failing source raises `SourceError`, aborts only its own ingestion and carries (D-156). Other
    sources proceed, and a missing optional source is disclosed on its surface (D-121).
  - The engine answers one error shape, and the app shows the engine's own message.
  - A failure to reach the engine names the address the app tried.
- **Schema evolution:** read paths stay migration-free. Operators explicitly run
  `python -m app.workflows.schema migrate --db PATH`. The command refuses missing or unusable files,
  preserves rows, and is idempotent. **Exit codes (D-120, K.8 frozen contract):**
  - `0`: migrated and servable;
  - `2`: could not migrate, and nothing changed;
  - `3`: migrated and NOT yet servable, with `required_operator_actions` naming what the schema
    cannot supply.

  A migration can add a column; it cannot supply a policy.

## 7. Conflict table: records against the code (seed A.2)

| # | Topic | The record says | The code does | Status |
|---|---|---|---|---|
| 1 | API surface | PRD §8 (M1): no API serving | Five read-only GET routes | Resolved: D-115, D-124, D-125, D-134, D-167 |
| 2 | Persistence | PRD §7: a disposable SQLite file | One SQLite artifact, built and shipped, read-only to the engine; no managed database | Resolved: D-116 |
| 3 | Source freshness | REQ-ING-003 flags staleness; no scheduler at M1 | The engine refreshes nightly in a child process | Resolved: D-151, D-154 |
| 4 | Deploy target | D-116: Fly.io (`fly.toml`, `Dockerfile`) | The engine runs on the owner's Mac; the hosted image, its artifact and its deploy script are ready, not deployed | Ready: D-185; the Stage 5.1 review passed on its re-read; the owner deploys |
| 5 | Ingestion on a serving host | D-116 clause 2: never | The Mac's engine serves the phone (opt-in) and refreshes in a child process | Accepted: D-154 clause 2 allows the switch only in a relaxed environment; the service runs `APP_ENV=test`; a production engine refuses it |
| 6 | Runtime config | AGENTS.md §5: never build-baked | The app's engine address is baked into each build | Accepted exception: D-171 note 5 (a phone app has no process environment) |
| 7 | What leaves the phone | D-160 clause 1, first wording: nothing derived from the question | The routed surface id is sent as `task` | Resolved: D-160 amendment, D-168 note 9 |
| 8 | Ingestion code in the server | D-154 clause 1, first wording | The server loads no client, parser, `httpx` or `pyarrow` | Resolved: W-125, fixed in M18-W6 (`docs/warnings.ledger.md`) |

## 8. Deliberately not there

- **No accounts.** No sign-in, no per-reader state on the engine, no mutating route.
- **No server-side model.** No language model computes, adjusts or explains a score, a price or an
  availability (D-104). The only model is the phone's own. It only picks a surface, refinements and
  whether the input is a search, each from a closed set (D-126, D-168, D-169).
- **Nothing the reader types leaves the phone.** The question's text, the refinements, the
  removals and the gap register stay on the device (§3).
- **No analytics or telemetry in the app**, and no refresh button or freshness screen (D-151).
- **No scores in the phone's standings, and no averaging across scales.** The phone combines
  positions only (D-105, D-167).
- **No managed database, CDN or multi-region serving.** The data is one small file, served by one
  process on one machine (`--ha=false`).
- **No benchmark of our own.** The product aggregates published results from documented endpoints
  only, with no scraping (D-101).

**Open items that bear on this architecture:**

- #66, #113: the second round improved #66 and missed its bars, and left #113 where it was. The
  owner decides whether it ships as measured (PR #196).
- #88: ruled by D-185 on the owner's standing instruction; the owner may overrule it.
- The hosted engine limits one client to 120 requests a minute (#187, INV-88); Fly has no spending
  cap, and the client's address is trusted from `Fly-Client-IP` (gap G-9). The budget argument is
  #188.
- `docs/security-invariants.md` names its open gaps, each on an issue. G-5 is one: in CI's test job
  a child process a test starts is beyond the suite's network guard.
- The Stage 5.1 release review ran (`docs/reviews/m19-closure-security-review.md`) and its re-read
  is MINOR (`docs/reviews/m19-release-security-reread.md`). Nothing is deployed yet.
