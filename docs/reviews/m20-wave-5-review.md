---
record_type: review
id: m20-wave-5-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 5 Code Review (the hosted engine's rate limit, #187; the fresh held-out measurement, #195)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `0c499b7^..4256437`, the wave's own commits `0c499b7` (red), `8f49a14`, `57a61de` and
`4256437`, each read with `git show`. The worktree is detached at `4da392c`, the merge of W4 into W5.
**Risk tier:** HIGH (plan §3: `src/app/adapter/main.py` and `fly.toml` are security globs)

## Verdict
MINOR

The limiter does what plan §2 W5 asks for: a limit per client that fails open (AGENTS.md §5). Its
memory is bounded, `/health` is exempt, the 429 uses the API's one error shape with `Retry-After`
and nosniff, and an unreadable limit refuses to boot only in a strict environment. Nothing blocks.
- The client key is the whole address, so one IPv6 host bypasses the limit and can reset every
  count (M1).
- Two of the riskiest faults, a window that never ends and a dropped boot check, survive the tests
  (M2, M3).
- The fail-open path is silent (M4).
- The cost note understates the worst case (M5).
- In the measurement record, the tables match the scorer exactly, but three sentences say more than
  the runs show (M6).

## How it was checked

- **Plan first:** `docs/plans/m20-plan.md` §2 W5 (lines 119-125) and §3, then AGENTS.md §5 line 98
  ("fairness/rate-limit fail OPEN"), then the diffs.
- **Middleware order:** `@app.middleware` inserts at position 0, so the stack is `_no_sniff` →
  `_limited` → `_known_host` → CORS → GZip. A 429 still gets nosniff from the outer `_no_sniff`.
- **Concurrency:** `_over_limit` runs on the event loop with no `await` inside it, so its
  read-modify-write is atomic. The Dockerfile runs one uvicorn process (`Dockerfile:59`, no
  `--workers`), so there is one table per machine, as the runbook says.
- **The header:** `X-Forwarded-For` is never read; the key comes from `Fly-Client-IP` only, and is
  truncated to 64 characters.
- **Faults planted** in `src/app/adapter/main.py`, by Python byte-swap with sha256 checked before and
  after (`f4c8459…616f`, restored), running `tests/unit/test_rate_limit.py` each time:

  | fault | result |
  |---|---|
  | the overflow `clear()` removed | killed (memory test) |
  | the fail-open branch made to refuse | killed |
  | the boot check line dropped (`main.py:662`) | **survived** |
  | the window never ends (`minute = 0`, `main.py:255`) | **survived** |
  | an unreadable limit in a relaxed lane refuses (`main.py:232` → `return 1`) | **survived** |
  | a default limit of 120 when unset | **survived** |
- **The measurement:** I ran `score.py`. It prints counts only; I printed no question. Every number
  in the record's §2 table and §4 table matches it, and both wording-tier runs are byte-identical on
  each side. I recounted §3 and the "not measured" claim from the run files with a script that
  prints counts only. The three signal words in `HELD_OUT_ONLY_REVIEWED` are each in `Reading.swift`
  at `bd273bc` (`git show bd273bc:…Reading.swift | grep -c` → 1, 1, 1). The held-out gate tests
  pass (`test_ios_client_contract.py -k "held_out or signal_word"`: 6 passed).

## Findings

### BLOCKING
None

### MINOR

- **M1** `src/app/adapter/main.py:244-261` (and `docs/release-testflight.md:47`): the client is the
  whole address, and a full table is cleared all at once.
  - **Failure scenario:** a Fly app with a public service is normally given an IPv6 address
    besides the shared IPv4. A scraper on one host with an ordinary IPv6 /64 sends each request
    from a different address in it. Every request is then a new client, so the limit never bites.
    Once 10,000 new keys arrive, `_RATE_WINDOWS.clear()` (line 260) wipes every count, including
    the count of an address that was being refused.
  - **Measured by calling `_over_limit`:**
    - one address is refused at request 121;
    - after 10,000 addresses from `2001:db8:1:2::/64` in the same minute, that address is served
      again (`rate_window_count()` is 2).
  - So the runbook's "one scraper can draw at most about … 60 MB a minute" does not hold for a
    scraper that rotates IPv6 addresses.
  - **Fix:**
    - Key an IPv6 client on its /64: `ipaddress.ip_network(f"{ip}/64", strict=False)`. A header
      that does not parse stays its own key.
    - When the table is full, first drop the entries of an earlier minute, which can never count
      again. Clear the whole table only if it is still full after that.
    - Add a test for each: two addresses in one /64 share a count, and a spray of new keys does not
      reset a refused key.
    - Make the runbook say "one address (one IPv6 /64)".

- **M2** `tests/unit/test_rate_limit.py` (no test exists): nothing tests the window ending.
  - **Failure scenario:** a regression that never resets the count survives every test, for
    example the planted `minute = 0` at `main.py:255`, a wrong divisor, or comparing `start`
    against the wrong value. Every real client is then locked out for good after 120 requests,
    until the machine restarts. That is a fail-closed fault in a control that must fail open.
  - **Fix:** a test that injects the clock (`monkeypatch.setattr(main.time, "time", ...)`):
    - the first three requests answer 200;
    - the fourth answers 429, with `Retry-After` equal to the seconds left in the minute;
    - at the next minute the same client answers 200 again.

- **M3** `tests/unit/test_rate_limit.py:57-59, 81-90`: the configuration paths are tested beside the
  boot, not through it. Three planted faults survive:
  - **(a)** Deleting `problems.extend(rate_limit_problems())` (`main.py:662`). The test is named
    `test_an_unreadable_limit_refuses_to_boot_in_production`, but it calls only
    `rate_limit_problems()`, and no test anywhere calls `validate_startup_config` with a bad limit.
    A production engine with `MODEL_RANKING_RATE_LIMIT=lots` would then boot with no limit.
  - **(b)** `_rate_limit` refusing in the relaxed lane (`main.py:232` returns 1 instead of 0). The
    docstring says "a relaxed environment serves rather than refuses", and nothing checks it.
  - **(c)** A default limit when the variable is unset. The "owner's Mac" test sends only 10
    requests, so any default above 10 passes it.
  - Also, the file cites no `REQ-REL-004` (`.agents/rules/practices.md:42`, seed E.2).
  - **Fix:**
    - Assert that `validate_startup_config("production")` raises a `ConfigError` whose text names
      `MODEL_RANKING_RATE_LIMIT`, and that `validate_startup_config("test")` returns it as a
      warning.
    - Add a relaxed-lane test where `"lots"` serves every request.
    - Assert `main._rate_limit() == 0` when the variable is unset.
    - Add `# covers REQ-REL-004`.

- **M4** `src/app/adapter/main.py:772-778`: failing open is silent, and so is a refusal.
  - **Failure scenario:** a limiter that throws on every request in production serves everything,
    which is right (AGENTS.md §5). But nothing records it, so the owner believes the cost bound
    holds while it is off.
  - The other direction is silent too. Real testers on a mobile carrier's shared IPv4 address
    (carrier-grade NAT) can start getting 429s, and the owner has no line to see it.
  - The rule this breaks: AGENTS.md §5, "a control skipped or bypassed is recorded, never hidden",
    and the Code-Reviewer profile §2b on swallowed exceptions.
  - **Fix:**
    - In the `except`, `logging.getLogger(__name__).warning("rate limiter failed open: %s",
      type(exc).__name__)`, at most once a minute.
    - Log one line per client the first time it is refused in a window, with the key truncated or
      hashed.
    - A `caplog` test for each.

- **M5** `docs/release-testflight.md:44-49`: the cost note's worst case is too low.
  - "0.5 MB x 120 = 60 MB a minute" is right for one clock minute. A fixed window, however, allows
    120 requests at :59 and 120 more at :00, so a 60-second span can draw 240 answers, about
    120 MB.
  - It is per address, and per IPv6 address until M1 is fixed.
  - It never gives the figure the owner weighs against a bill with no cap: one scraper running all
    day at the limit draws about 86 GB a day.
  - The 0.5 MB is the worst case, a client that does not ask for gzip. With gzip the answer is
    about 36 KB (`main.py:731`).
  - **Fix:** "about 60 MB a minute on average and up to twice that across a minute boundary, per
    address (per IPv6 /64 once M1 lands); about 86 GB a day if one scraper runs all day without
    gzip".

- **M6** `docs/research/m20-w5-family-probe.md:65-71, 86, 97`: three sentences and one label say
  more than the runs.
  - **(a) Line 67:** "The weak kinds are the same on both tiers". The scorer contradicts it:

    | kind | wording tier | model tier |
    |---|---|---|
    | real language tasks (g4) | 1 of 9 | 5 to 7 of 9 |
    | general "which AI" (g1) | 6 to 7 of 8 | 3 of 8 |
    | words with a second meaning (g3) | 8 of 12 | 3 to 5 of 12 |

    Only the real domain questions (g5) are weak on both tiers.
  - **(b) Line 86:** "added a domain three times where the label has none, and missed six". The
    count from `after-family.json` differs:
    - 2 of the 3 additions are on questions labelled `none`;
    - the third replaced a labelled domain with another one;
    - 7 labelled domains were not read.
  - **(c) Lines 65-66:** "This milestone did not change what the model tier answers". Two runs per
    side show only that no change is detectable:
    - the net −2 is within the 2-point spread;
    - 8 to 14 rows differ between before and after, against 8 to 10 within a side;
    - one row that was stable flipped each way.
  - **(d) Line 97:** the 126.8 and 117.3 means are over the 54 lists built from more than one
    board, not over the 65 lists answered. Over all 65 they are 124.0 and 116.1.
  - **Fix:** reword (a) through (c) to what the scorer shows, and label (d). Every other count in
    the record matches the scorer and the run files.

## Acceptance criteria evidence

- **REQ-REL-004** (`docs/prd.md`), checked against the tests that cite it:

  | clause | code | test |
  |---|---|---|
  | 429 `rate_limited` with `Retry-After` | `main.py:774-778` | `test_rate_limit.py:35-41` |
  | per client, from `Fly-Client-IP` | `main.py:244-250` | `:44-48` |
  | `/health` never limited | `main.py:769` | `:51-54` |
  | no limit on the owner's Mac | `main.py:225-232` | `:57-59`, weak (M3c) |
  | fails open | `main.py:770-773` | `:62-70` |
  | bounded memory | `main.py:208, 259-260` | `:73-78` |
  | an unreadable limit refuses to boot | `main.py:662` | `:81-90`, beside the boot, not through it (M3a) |
  | `fly.toml` sets 120 | `fly.toml:32` | `:93-96` |
- **#195:**
  - `docs/research/m20-w5-family-probe.md` and the runs in `docs/research/m20-w5-runs/`;
  - the M19 sets are added to `RETIRED_HELD_OUT` (`tests/unit/test_ios_client_contract.py:214-219`);
  - `HELD_OUT_ONLY_REVIEWED` holds three words, each present at `bd273bc`.

## K.8 contract drift check

```
$ grep -n "\"primary_board\"" src/app/adapter/main.py
1438:                "primary_board": spec.primary_source,
```

The wave's own commits touch no file under `ios/`, no `src/app/workflows/` and no `/v1` route. The
line moved from 1354 because 83 lines were added above it. Verdict: OK.

## K.9 candidates spotted outside this wave's scope

- **K1** `ios/ModelRanking/Engine/Language.swift:815`: a Turkish reader sees the engine's English
  sentence for every refusal. `case let .refused(_, _, message): return message`, and
  `recovery(.turkish)` is `nil` for `.refused` (`:833`).
  - **Failure scenario:** a Turkish tester on a shared carrier address gets a 429, the refusal a
    real tester is now most likely to see, and the phone shows "Too many requests from one client;
    try again shortly." in English. The same holds for `evidence_unavailable`.
  - **Bug.** Fix: map the known refusal codes (`rate_limited`, `evidence_unavailable`,
    `unknown_host`) to Turkish text by code, and fall back to the engine's message for an unknown
    code. A test for each code.

## Risks queued to next M

- **R1** The key trusts `Fly-Client-IP` from whoever sends it (`main.py:246-248`).
  - On Fly, the proxy is expected to set that header and overwrite any value a client sends; that
    is unverified here.
  - Off Fly, any client chooses its own key per request, which bypasses the limit and, through M1's
    clear, resets everyone's count. Today the limit is set only in `fly.toml`.
  - **What would show it is real:** after the deploy, send `limit + 1` requests from one address,
    each with a different forged `Fly-Client-IP`. If none is refused, the proxy passes the header
    through. Then trust the header only when `APP_ENV` is production, or key on the socket peer.
- **R2** A strict engine with the limit unset or `0` boots unlimited and says nothing
  (`rate_limit_problems` returns `[]`, `main.py:213-222`). The only guard is the `fly.toml` test
  (`test_rate_limit.py:93-96`), which holds while REQ-REL-003's single deploy path holds.
  - **What would show it is real:** a deploy that sets the environment some other way, for example
    `fly secrets` or a second `fly.toml`. Then make a strict environment require a positive limit;
    the owner's Mac runs `APP_ENV=test` (`scripts/engine_service.sh:53`), so it is not affected.
