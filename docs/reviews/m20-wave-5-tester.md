---
record_type: review
id: m20-wave-5-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 5 Tester Review (the hosted engine's rate limit, #187; the fresh held-out measurement, #195)

**Tester:** Tester subagent (fresh eyes; wrote none of the wave's code)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `0c499b7^..2cbbf59`, the wave's own commits `0c499b7` (red), `8f49a14`, `57a61de`,
`4256437`, `3c5954f` (red) and `2cbbf59`, each read with `git show`. The worktree is detached at `2cbbf59`.
**Risk tier:** HIGH

## Verdict
MINOR

The limiter does what REQ-REL-004 says, and the Code-Reviewer's six findings are answered. Of 22
faults planted in `src/app/adapter/main.py`, the wave's tests kill 17. The 7 tests added by this
review kill the other 5, and they pass on the shipped code. Nothing blocks. Four findings remain:
- an IPv4-mapped address makes every IPv4 client one client (T1);
- a full table is scanned again on every request from a new client (T2);
- the test gaps this review closed, which the author should commit (T3);
- the runbook's post-deploy header check can raise a false alarm (T4).

## How it was checked

- **The suite.** `make check-fast`: lint, typecheck, records, client-decls and swift-test PASS.
  - The test leg stopped at W-108: `advisor.db` is not in this worktree, and
    `MODEL_RANKING_REQUIRE_ARTIFACT=1` requires it. The session's permission check refused copying
    the owner's built file in, so I did not.
  - So I ran the same suite under the same offline sandbox, without the artifact flag:
    `2158 passed, 77 skipped` on the shipped code. With this review's tests: `2165 passed, 77 skipped`
    and total coverage 91.97%. The 77 skips are the `advisor.db` tests.
  - `make lint` and `make typecheck` pass with the added tests.
- **The red commit `3c5954f`.** I extracted its tree with `git archive` into a scratch directory and
  ran the whole Python suite there, with `PYTHONPATH` set to that tree's `src`.
  - In `test_rate_limit.py`, the 5 tests for M1, M4 and R2 fail.
  - The other 4 new tests pass there: the window's end, the boot check, and the relaxed lane. They
    close test gaps (M2, M3) in code that was already right. My F8, F17 and F20 below show that they
    now kill the faults the Code-Reviewer planted.
  - 6 other tests failed only because the extracted tree had no git index (`git ls-files` exit 128).
    With `git init` and `git add -A` in the scratch copy, those 43 tests pass.
  - So the red commit fails only on its own tests. All 17 pass at `2cbbf59`.
- **Weakened tests.** `2cbbf59` changes one test, `test_a_strict_engine_without_a_limit_says_so`. It
  swaps `try/except ConfigError: pass` for `contextlib.suppress(ConfigError)`, which is the same
  test. No test was deleted or weakened.
- **The probes** (`_client_key` and `_over_limit` called directly, and the engine through
  `TestClient`):
  - **`::ffff:1.2.3.4`, `::ffff:5.6.7.8` and `::1`** all key as `::/64`. Through the engine, three
    different mapped clients answer 200, 200, 200 and a fourth answers **429** (T1).
  - **A blank header** (`""` or spaces) falls back to the connection's address.
  - **A header that does not parse** (`not-an-ip`, `1.2.3.4:5555`, `[2001:db8::1]`, a comma list) is
    its own key, and is served.
  - **A 10,000-character header** is cut to a 64-character key.
  - **A scoped address** `fe80::1%eth0` keys as `fe80::/64`. Upper case and zero-padded IPv6 key
    the same as their short form.
  - **The minute's edge:** at 59.999 the wait is 1. At 60.0 a new window starts, with a wait of 60.
    At 119.999999 the client is still refused, and at 120.0 it is served.
  - **One event loop:** 200 concurrent `_over_limit` calls at a limit of 50 refuse exactly 150.
    `_over_limit` has no `await`, so its read-modify-write cannot interleave.
  - **Many keys in one minute:** filling 10,000 keys takes 4 ms. After that, each request from a new
    client takes **493 µs** and is served uncounted (2,000 of 2,000), and the table stays at 10,000
    (T2).
- **#195 (the record against the scorer): not verified by this seat.**
  - `score.py` needs the held-out labels file as its second argument. The session's permission
    check refused the step that located that file, so I did not run the scorer and read nothing in
    the set.
  - What I checked instead are the record's own sums at `2cbbf59`, all of which agree:
    - boards per list: 11 + 8 + 27 + 15 + 4 = 65, the lists answered;
    - lists from more than one board: 8 + 27 + 15 + 4 = 54;
    - domain: 78 − 69 = 9 wrong = 2 added + 1 replaced + 6 not found, so "missing on seven".
  - The corrected sentences (`docs/research/m20-w5-family-probe.md:67-71`) carry the Code-Reviewer's
    scorer counts exactly: g4 1 of 9 against 5 to 7, and g1 6 to 7 of 8 against 3 of 8.
  - The held-out retirement tests in `test_ios_client_contract.py` pass in the full suite.
  - A run of `score.py` by a seat that may read the labels file is still owed.

## Acceptance-criterion coverage

| REQ-REL-004 clause | code | citing test (`tests/unit/test_rate_limit.py`, file cites REQ-REL-004 at :1) | result |
|---|---|---|---|
| 429 `rate_limited`, `Retry-After` | `main.py:796-800` | `:37`; the seconds left `:242` (added) | GREEN |
| per client, from `Fly-Client-IP` | `main.py:247-259` | `:46`; blank `:222`, unparsable `:216`, long `:205` (added) | GREEN |
| an IPv6 /64 is one client | `main.py:257-258` | `:120`; the whole interface id `:198` (added) | GREEN |
| a crowd never resets a held count | `main.py:266-270` | `:126`; a crowded-out client served `:231` (added) | GREEN |
| the window ends | `main.py:264, 272-273` | `:101`, `:111` | GREEN |
| `/health` never limited | `main.py:789` | `:53` | GREEN |
| no limit on the owner's Mac | `main.py:228-235` | `:59`, and `:183` (a default would silence the warning) | GREEN |
| an unreadable limit refuses to boot (strict) | `main.py:678` | `:142`; relaxed serves `:153` | GREEN |
| fails open, and says so | `main.py:792-795` | `:64`, `:158` | GREEN |
| a refusal logged once, no address | `main.py:275-277` | `:172` | GREEN |
| bounded memory | `main.py:211, 266-270` | `:75`, key length `:205` (added) | GREEN |
| concurrency (hard criterion, E.5) | `main.py:262-278` | `:253` (added) | GREEN |
| `fly.toml` sets 120 | `fly.toml:32` | `:95` | GREEN |

## Faults planted

Every fault was a Python byte swap in `src/app/adapter/main.py`. One fault at a time, then
`tests/unit/test_rate_limit.py` was run, then the original bytes were written back. The sha256 was
checked after each restore: `81533d3b…0937` before and after every fault, and at the end. "Wave's
tests" means the 17 tests at `2cbbf59`. "Added" means this review's 7.

| # | fault | wave's tests | with the added tests |
|---|---|---|---|
| F1 | IPv6 not grouped (`if parsed.version == 6` → `if False`) | killed (`:120`) | killed |
| F2 | `/64` widened to `/96` | **survived** | killed (`:198`) |
| F3 | the header no longer cut to 64 characters | **survived** | killed (`:205`) |
| F4 | `Fly-Client-IP` ignored | killed (`:46`, `:120`) | killed |
| F5 | an earlier minute's entries never dropped | killed (`:126`) | killed |
| F6 | a full table cleared (the pre-fix code) | killed (`:126`) | killed |
| F7 | a crowded-out new client refused (fail closed) | **survived** | killed (`:231`) |
| F8 | the window never ends (`minute = 0`) | killed (`:101`, `:111`, `:126`) | killed |
| F9 | `Retry-After` always 60 | **survived** | killed (`:242`) |
| F10 | `count + 1 >= limit` | killed (5 tests) | killed |
| F11 | `count > limit` | killed (7 tests) | killed |
| F12 | a refusal logged on every request | killed (`:172`) | killed |
| F13 | the refusal log names the address | killed (`:172`) | killed |
| F14 | `/health` limited | killed (`:53`) | killed |
| F15 | a broken limiter refuses | killed (`:64`, `:158`) | killed |
| F16 | a broken limiter is silent | killed (`:158`) | killed |
| F17 | the boot check dropped (`problems.extend(rate_limit_problems())`) | killed (`:142`) | killed |
| F18 | the strict no-limit warning dropped | killed (`:183`) | killed |
| F19 | a default of 120 when unset | killed (`:183`) | killed |
| F20 | an unreadable limit refuses in the relaxed lane | killed (`:153`) | killed |
| F21 | the purge drops this minute's entries | killed (`:126`) | killed |
| F22 | the middleware decides on a count read before an `await` (a race) | **survived** (only `:253` failed) | killed (`:253`) |

The wave's tests kill 17 of 22 (77%), and with the added tests all 22 are killed. No mutation runner
is wired for this stack, so there is no kill rate beyond this table.

## Findings

### BLOCKING
None

### MINOR

- **T1** `src/app/adapter/main.py:257-258`: an IPv4-mapped IPv6 address is grouped by its /64, and
  every such address shares the /64 `::/64`.
  - **Failure scenario:** the engine gets an IPv4 client in mapped form, `::ffff:a.b.c.d`. That
    happens with `uvicorn --host ::` (a dual-stack socket, where every IPv4 peer arrives mapped) when
    there is no `Fly-Client-IP`, or if a proxy ever writes the header that way.
    - Every IPv4 reader is then one client. 120 requests a minute across all of them, and every one
      gets a 429.
    - That is a fairness control failing closed, against AGENTS.md section 5.
    - Measured through the engine at a limit of 3: `::ffff:198.51.100.1`, `.2` and `.3` answer 200,
      200, 200, and `::ffff:203.0.113.9` answers 429.
    - Today's `Dockerfile:59` binds `0.0.0.0` and Fly names IPv4 clients in dotted form, so this is
      latent.
  - **Fix:**
    - Before the /64 step: `if parsed.version == 6 and parsed.ipv4_mapped: return str(parsed.ipv4_mapped)`.
    - Add a test: two mapped addresses are two clients, and `::ffff:203.0.113.7` shares a count with
      `203.0.113.7`. It fails on the shipped code, so this review could not add it.

- **T2** `src/app/adapter/main.py:266-270`: once the table holds 10,000 of this minute's entries,
  every request from a new client scans all 10,000 again on the event loop, and the scan removes
  nothing.
  - **Failure scenario:** a sprayer with more than 10,000 /64s fills the table early in a minute. A
    tunnel broker gives a /48, which holds 65,536 /64s, for free.
    - Each later request from a new /64 then costs about 0.5 ms of event-loop time: 493 µs measured
      with 2,000 requests.
    - That time blocks every connection, `/health` included. About 2,000 such requests a second fill
      the loop entirely.
    - Those requests are also served uncounted, so the scan buys nothing.
  - **Fix:**
    - Remember the minute of the last purge (`_PURGED_MINUTE`), and skip the scan when it equals
      `minute`. Within one minute, no entry can become stale.
    - Add a test that counts how many times the purge runs, or one that holds a time bound loosely.

- **T3** `tests/unit/test_rate_limit.py` (the gaps): five planted faults survived the wave's tests,
  and two edges had no test. These are F2, F3, F7, F9 and F22 in the table above.
  - **Failure scenario:**
    - A regression to a /96 key lets one host rotate its interface id past the limit (F2).
    - Dropping the 64-character cut lets each table entry grow to the header size the server accepts
      (F3).
    - Refusing a crowded-out client turns a full table into an outage for every new reader. It is
      fail-closed, and nothing went red (F7).
    - A wrong `Retry-After` makes clients retry too early or too late (F9).
    - A refactor that checks the count before an `await` lets a burst of requests in flight pass the
      limit together (F22). That is the hard concurrency criterion, and it had no test (E.5).
  - **Fix:** this review wrote the 7 tests, uncommitted, at `tests/unit/test_rate_limit.py:194-268`.
    They pass on the shipped code and kill all five faults. The author:
    - commits them;
    - adds their names to REQ-REL-004's evidence cell (`docs/prd.md:605`), which also leaves out
      `test_a_relaxed_engine_with_an_unreadable_limit_serves` and
      `test_a_strict_engine_without_a_limit_says_so`;
    - writes "in a strict environment" after "an unreadable limit refuses to boot" in that row. The
      relaxed lane serves.

- **T4** `docs/release-testflight.md:57-65`: the post-deploy check that Fly sets `Fly-Client-IP` can
  raise a false alarm.
  - **Failure scenario:** the check sends 125 requests one after another from the owner's Mac. Each
    is an HTTPS round trip, so the loop takes tens of seconds and can straddle the turn of a clock
    minute.
    - It might then send, for example, 60 requests before the turn and 65 after. Neither window
      passes 120, every answer is 200, and the runbook says "Fly passed the forged header through:
      stop sharing the app".
    - In fact Fly set the header correctly.
  - **Fix:**
    - Send `2 x limit + 10` requests (`seq 1 250`). Any 250 requests in under about two minutes put
      more than 120 into one window, so a correct proxy always shows a 429.
    - Or say: "if every answer is 200, run it once more, starting just after a minute turns".

## K.9 candidates spotted outside this wave's scope
None

## Risks queued to next M

- **R1** `src/app/adapter/main.py:792-795`: the fail-open warning has no cap. A limiter that throws
  on every request writes one WARNING per request. The Code-Reviewer's M4 suggested once a minute.
  - **What would show it is real:** after a deploy, `rate limiter failed` appearing in the Fly logs
    more than a few times a minute.
  - Then log it once per window, the way the refusal is already logged (`main.py:275-277`).

## Tests added this review (uncommitted)

All are in `tests/unit/test_rate_limit.py` and cite REQ-REL-004:
- `:198` `test_one_64_is_one_client_whatever_its_interface_id`: the whole interface id is one client
  (kills F2).
- `:205` `test_a_long_header_is_kept_short`: a key is at most 64 characters (kills F3).
- `:216` `test_a_header_that_does_not_parse_is_its_own_client`: served and counted as itself.
- `:222` `test_an_empty_header_is_the_connection`: a blank header falls back to the connection.
- `:231` `test_a_crowded_out_client_is_served`: fails open when the table is full (kills F7).
- `:242` `test_retry_after_is_the_rest_of_the_minute`: `Retry-After` is the seconds left (kills F9).
- `:253` `test_concurrent_requests_on_one_loop_never_pass_the_limit`: 12 requests in flight on one
  loop, 3 served (kills F22).
