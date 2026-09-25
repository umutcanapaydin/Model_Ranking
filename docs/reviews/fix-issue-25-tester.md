---
record_type: review
id: fix-issue-25-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---

# Issue #25 Tester Review (fix-issue)

**Reviewer:** Tester subagent (fresh eyes; did not write the fix or its tests)
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `6834c7d..29a2687` (`git merge-base origin/main HEAD` = `6834c7d`): `245e5b3` (red tests) + `29a2687` (fix), branch `fix/issue-25-download-bounds`
**Risk tier:** severity:low, triage `work-issue` (egress for every source: a sensitive area)
**Acceptance criterion:** issue #25 plus the plan the owner approved in session on 2026-09-25: every hop `https` to a host the source declares (its own by default; the slice client declares `huggingface.co` and `.hf.co`), at most five redirects, a deadline over the whole fetch (connection, headers, redirects, body), and the Arena rows client (`arena.py::_get_page`) reads through the same path.
**Workspace:** the fix worktree, read-only apart from in-place fault injection (md5 of every mutated file checked after each mutant, and all four at the end). The pre-fix tree was extracted with `git archive 245e5b3` into a scratch directory; no `git checkout` or `git restore` was used. Nothing committed.

## Verdict
MINOR. Both halves of #25 are fixed. The red tests fail on `245e5b3` for the reasons the issue gives, and HEAD is green. Every criterion has a test that exercises it. 16 of 24 mutants are killed by the suite. Three of the survivors are equivalent. Five show real gaps next to the criteria: a look-alike of an exact host, the 429 branch of `fetch_bounded_bytes`, the default deadline, the value 5 in the redirect cap, and the slice client's use of its hosts. `make check-fast` passes. The full suite made no outbound connection. `smoke_deps` passes for every live source. Nothing blocks: each gap is one test to add. The code is correct today, and one gap (T5) is caught by the live contract test.

## Acceptance-criterion coverage

| Criterion | Citing test | Asserts | Result |
|---|---|---|---|
| A redirect to a host the source did not declare is refused and never requested (default: the first URL's own host) | `tests/unit/test_fetch_bounds.py:38` `test_a_redirect_to_another_host_is_refused` | `SourceError` "refused a hop to https://evil.example", and the evil route `not called` | GREEN |
| Every hop is `https`: a redirect down to `http` is refused | `tests/unit/test_fetch_bounds.py:47` `test_a_redirect_down_to_plain_http_is_refused` | `SourceError` "refused a hop to http://source.example" | GREEN |
| The first URL must be `https` | `tests/unit/test_fetch_bounds.py:81` `test_a_first_url_that_is_not_https_is_refused` | `SourceError` "refused a hop to http://…" | GREEN (see T6) |
| A declared CDN hop is followed (`huggingface.co` → `us.aws.cdn.hf.co`) | `tests/unit/test_fetch_bounds.py:55` `test_a_redirect_to_a_declared_host_is_followed` | body `b"PAR1"` returned through the hop | GREEN |
| A `.domain` entry admits subdomains, never look-alikes | `tests/unit/test_fetch_bounds.py:65` `test_a_suffix_entry_is_a_domain_not_a_substring` | `evilhf.co` refused under `.hf.co` | GREEN (exact entries: see T1) |
| Each source declares its hosts (Arena rows: the datasets-server only; slices: `huggingface.co`, `.hf.co`) | `tests/unit/test_fetch_bounds.py:86` `test_every_remote_client_declares_where_it_may_go` | the two attribute values | GREEN (use of the slice value: see T5) |
| At most five redirects | `tests/unit/test_fetch_bounds.py:73` `test_more_redirects_than_the_bound_is_a_source_error` | `MAX_REDIRECTS + 2` hops give a `SourceError` "redirect" | GREEN (the value 5: see T4) |
| The deadline bounds the whole fetch: headers, every redirect hop, body | `tests/unit/test_fetch_bounds.py:180-190` `test_the_deadline_bounds_the_whole_fetch[_header_drip / _slow_redirect / _body_drip]` | `SourceError` "deadline" in under 2.5 s with `deadline=1.0`, a 5 s per-operation timeout, loopback only | GREEN (default deadline: see T3) |
| The deadline also holds mid-body (M16-W4 F4, kept) | `tests/unit/test_epoch_bundle_fetch.py:332` `test_a_download_past_its_deadline_is_a_source_error` | `SourceError` "deadline" with a mocked clock | GREEN |
| The Arena rows client reads through the same path | `tests/unit/test_fetch_bounds.py:96` `test_the_arena_rows_client_refuses_a_redirect_off_its_host` | `ArenaClient().fetch_raw()` refuses a hop to `evil.example` | GREEN |
| The Arena 429 retry still works through the new path | `tests/unit/test_arena_client.py:82` `test_429_backs_off_then_succeeds`, `:97` `test_429_exhaustion_fails_loud_without_full_rows_fallback` | one sleep of `Retry-After` = 1.0 then success; exhaustion is a `SourceError` with no fallback to the filter endpoint | GREEN (exhaustion branch: see T2) |
| Every failure is a `SourceError` (the IDNA crash, S-R3) | `tests/unit/test_arena_slices.py:607` `test_a_redirect_to_a_malformed_host_is_a_source_error` | `Location: http://xn--/x` → `SourceError` | GREEN |
| The byte cap still holds (decoded bytes, counted while reading) | `tests/unit/test_arena_slices.py:597`, `tests/unit/test_yaml_guard.py:243` | "exceeded" at the cap | GREEN |
| Epoch bundle keeps `follow_redirects=False` and a deadline | `tests/unit/test_epoch_bundle_fetch.py:315` | the kwargs passed to `fetch_bounded_bytes` | GREEN (behaviour through `bounded_get`: see T7) |

The tests cite the issue in the module docstring of `tests/unit/test_fetch_bounds.py:1` ("#25 -- …"). The two edited tests cite it inline (`test_epoch_bundle_fetch.py:357`, `test_yaml_guard.py:287`).

## Red to green on the reported symptoms

`245e5b3` was extracted by `git archive` and run with the worktree's venv (`PYTHONPATH` set to the extracted `src`; `app.clients.protocols.__file__` confirmed the pre-fix module was loaded).

- **The red commit's own test file:** 8 failed, 3 errors. The errors are the `loopback_http` fixture: `monkeypatch.setattr(protocols, "ALLOWED_SCHEMES", …)` fails on a module that has no such name. Each failure is a real symptom: the hop to `evil.example` was requested (`AllMockedAssertionError`), the `http` hop was followed, `hosts=` / `MAX_REDIRECTS` / `ArenaClient.hosts` did not exist, and the first `http` URL went to DNS.
- **The deadline half, on its behaviour:** with the fixture set to `raising=False` and `hosts=` dropped, the red commit's `_header_drip` hung (SIGKILLed at 40 s). Its drip loop had no end, so the red test hung the run instead of failing. `29a2687` bounded it with `_MISBEHAVE_S = 4.0`. HEAD's test file against the pre-fix source fails as it should: `_header_drip` ran 4.18 s and ended with "Server disconnected…" instead of "deadline". `_slow_redirect` ran 8.59 s and ended with "Exceeded maximum allowed redirects." (20 hops). `_body_drip` passed. It was already bounded before the fix, so it stands as a regression guard, not a red.
- **HEAD:** `tests/unit/test_fetch_bounds.py` 11 passed in 3.14 s. Each deadline case takes about 1.02 s.

## Suite result

- `make check-fast`: **PASS** in 35.3 s (lint, typecheck, records, test, client-decls, swift-test). Test leg: `1333 passed, 17 skipped`. The 17 skips are the env-gated contract tests (`RUN_CONTRACT_TESTS=1`) and `EPOCH_DATA_DIR` tests, not this change.
- Full suite, with `MODEL_RANKING_REQUIRE_ARTIFACT=1` and `-n auto`, run again under a network logger (a pytest plugin wrapping `socket.connect`, `connect_ex` and `getaddrinfo` in every xdist worker, logging any non-loopback and non-AF_UNIX target): `1333 passed, 17 skipped`, **0 outbound connects or lookups logged**. A self-test confirmed the logger is installed in the workers and does log.
- Coverage on touched code (check-fast run): `protocols.py` 97% (missing 188-189, the 429 branch of `fetch_bounded_bytes`: T2), `arena.py` 92%, `arena_slices.py` 99%.
- `scripts/smoke_deps.py`, run once: **PASS**. litellm, openrouter, swebench and aider come from their own hosts. The six Arena boards come through the datasets-server. `arena_slices_text` (26 slices, 9402 rows) and `arena_slices_vision` (9 slices, 843 rows) come through the CDN hop. The Epoch sources are `n/a` in this script (owner-placed bundle). The Epoch download was not re-probed live.
- The worker thread after a deadline (loopback probe, infinite header drip, `timeout=5`, `deadline=1`): the caller got the `SourceError` at 1.12 s, the server saw the hang-up at 1.36 s, and the worker thread was gone by 6 s. It lingers for at most one per-operation timeout. It is a daemon and bounded, so this is not a finding.

## Callers (regression look)

| Caller | URL / hosts | Deadline now | Result |
|---|---|---|---|
| litellm, swebench, aider | `raw.githubusercontent.com`, own host by default, answers 200 with no redirect | default 4 × 30 s = 120 s (none before) | smoke PASS |
| openrouter | `openrouter.ai`, own host | default 120 s (none before) | smoke PASS |
| epoch_bundle | own host, `follow_redirects=False`, `deadline=120` | 120 s | unit test of the kwargs; not probed live (T7) |
| arena (rows/filter) | declared `datasets-server.huggingface.co` | default 120 s | respx tests and smoke PASS |
| arena_slices | declared `huggingface.co`, `.hf.co` | 120 s | smoke PASS through the CDN (T5) |

Two tests that patched `httpx.stream` now patch `httpx.Client.stream` (`test_epoch_bundle_fetch.py:357-358`, `test_yaml_guard.py:287-303`). This is a necessary change of seam, not a weakening: the assertions are the same. No test was deleted or skipped.

## Fault injection (in place, restored by string replacement in a `finally` block, md5 checked after each)

Each mutant was run against the whole suite (`pytest -n auto -x tests`) under a hard subprocess timeout (SIGKILL of the process group). Every file was restored byte-identical: `protocols.py` 9815260e…, `arena.py` 9bd77c69…, `arena_slices.py` 146c3007…, and a final md5 comparison of all four files matched the pre-injection hashes. `git status` was clean after.

| # | Mutant | Result | Killing test / note |
|---|---|---|---|
| F1 | hop check off (`protocols.py:109` → `if False`) | KILLED | `test_fetch_bounds.py:38` |
| F2 | request hook not registered (`:116` `event_hooks={}`) | KILLED | `test_fetch_bounds.py:38` |
| F3 | first-URL pre-check removed (`:113`) | survived, **equivalent** | the request hook also runs before the first request, so the refusal comes from there and nothing is sent |
| F4 | scheme check off (`:74` `True and any(`) | KILLED | `test_fetch_bounds.py:47` |
| F5 | `ALLOWED_SCHEMES` admits `http` | KILLED | `test_fetch_bounds.py:47` |
| F6 | suffix entry matched as a substring (`entry.lstrip(".")`) | KILLED | `test_fetch_bounds.py:65` |
| F7 | exact entries also suffix-match (`host.endswith(entry)`) | **SURVIVED** | T1 |
| F8 | `max_redirects` dropped (httpx's 20) | KILLED | `test_fetch_bounds.py:73` |
| F9 | `MAX_REDIRECTS = 20` | **SURVIVED** | T4 |
| F10 | `follow_redirects` argument ignored (always `True`) | **SURVIVED** | T7 |
| F11 | deadline join removed (`worker.join()`) | KILLED, no hang | `test_fetch_bounds.py:182[_header_drip]` ("Server disconnected…" at the 4 s hang-up) |
| F12 | no default deadline (`else 1e9`) | **SURVIVED** | T3 |
| F13 | in-body expiry check off | KILLED | `test_epoch_bundle_fetch.py:332` |
| F14 | `is_alive` check removed | survived, **equivalent** in effect | it falls through to the same `late` error, except in a narrow race where the worker's close error is reported instead |
| F15 | worker's error dropped | KILLED | `test_arena_slices.py:597` |
| F16 | a 429 raised inside `_read` | KILLED | `test_arena_client.py:82` |
| F17 | `fetch_bounded_bytes` 429 check removed (`:187-189`) | **SURVIVED** | T2 |
| F18 | Arena 429 retry off (`arena.py:185`) | KILLED | `test_arena_client.py:82` |
| F19 | `Retry-After` looked up by its mixed-case key | KILLED | `test_arena_client.py:82` (sleeps `[2.0]`, not `[1.0]`) |
| F20 | Arena 429 exhaustion branch removed (`arena.py:194-196`) | survived, outcome masked | the empty 429 body fails `json.loads`, so it is still a loud `SourceError`: T2 |
| F21 | Arena `hosts=self.hosts` not passed (`arena.py:181`) | survived, **equivalent** (I agree with the author) | the default is the first URL's host, and `ROWS_API` and `FILTER_API` are both on `datasets-server.huggingface.co`; the declared value is pinned at `test_fetch_bounds.py:91` |
| F22 | slice client `hosts=self.hosts` not passed (`arena_slices.py:221`) | **SURVIVED** | T5: offline it is invisible, live it would refuse the CDN hop on every nightly run |
| F23 | slice hosts lose `.hf.co` | KILLED | `test_fetch_bounds.py:92` |
| F24 | byte cap off | KILLED | `test_arena_slices.py:597` |

## MINOR (the author fixes each on this branch or files it as an issue)

- **T1** `src/app/clients/protocols.py:75`: no test refuses a look-alike of an **exact** entry. The mutant `host.endswith(entry)` for every entry (F7) survives the whole suite. Under it the default host `source.example` admits `evilsource.example`, and `huggingface.co` admits `evilhuggingface.co`. That is the look-alike hole this fix exists to close, and it would apply to every source that uses its default host. `test_fetch_bounds.py:65` covers only a dotted entry. One test fixes it: a redirect from `https://source.example/…` to `https://evilsource.example/x` with the default hosts must be refused.
- **T2** `src/app/clients/protocols.py:187-189` (uncovered in the coverage report) and `src/app/clients/arena.py:194-196`: `_read` now lets a 429 through without `raise_for_status`, so `fetch_bounded_bytes` must turn it into a failure. Deleting that check (F17) survives. A 429 body would then be handed as data to litellm, openrouter, swebench, aider, the slices and the Epoch bundle. Before the fix, `raise_for_status` did this and nothing needed a test. The Arena exhaustion branch (F20) is masked the same way: `test_arena_client.py:97` uses an empty 429 body, and a JSON error body (`{"error": …}`) would go through as a page. Add a respx 429 → `SourceError` test for `fetch_bounded_bytes`, and give the exhaustion test a JSON body.
- **T3** `src/app/clients/protocols.py:58,105`: the default deadline (`DEADLINE_FACTOR` × `timeout` = 120 s) is not pinned. Replacing it with no deadline (F12) survives. The Arena rows client, litellm, openrouter, swebench and aider pass no deadline, so for them this default is the only bound on the whole fetch. The criterion "a deadline over the whole fetch" holds for them only through this line. Add a loopback case with `deadline=None` and a small `timeout`, for example a header drip with `timeout=0.3` that expects "deadline" within about 4 × 0.3 s.
- **T4** `src/app/clients/protocols.py:55`: "at most five redirects" is proven only relative to the constant (`test_fetch_bounds.py:74` loops `MAX_REDIRECTS + 2`). `MAX_REDIRECTS = 20` (F9) survives. Pin the number: assert `MAX_REDIRECTS == 5`, or build a 5-hop chain that succeeds and a 6-hop chain that fails.
- **T5** `src/app/clients/arena_slices.py:221`: that the slice client passes its hosts is not proven offline. Dropping `hosts=self.hosts` (F22) survives every offline test. Only the env-gated live contract test (`tests/integration/test_arena_openrouter_contract.py:52`) and `smoke_deps` would see the CDN hop refused. The first sign would be a failed nightly slice fetch. `test_fetch_bounds.py:55` tests the helper with the tuple typed in, not the client. Add a `slice_download` respx test: `ArenaSliceClient("text").fetch_bytes()` follows a 302 from `parquet_url("text")` to `https://us.aws.cdn.hf.co/…`.
- **T6** `tests/unit/test_fetch_bounds.py:81`: this test is not under `@respx.mock`. When the guard is broken it reaches the resolver: on the pre-fix code it performed a real DNS lookup for `source.example` (`[Errno 8] nodename nor servname provided`). The suite is hermetic only while the code under test works. Add `@respx.mock` so that a regression fails on a mock instead of going to the network. Related wording: the module docstring (`:13-14`) and the fixture (`:134`) say `http` is allowed "for 127.0.0.1 only". The fixture allows `http` for every host, and the timing test's `hosts=("127.0.0.1",)` (`:189`) is what restricts it. The docstring should say that.
- **T7** `src/app/clients/protocols.py:115`: that `follow_redirects=False` reaches the client is not proven. Ignoring the argument (F10) survives, because the Epoch test (`test_epoch_bundle_fetch.py:315-328`) fakes `fetch_bounded_bytes` and checks only the kwarg. This gap existed before #25, and the fix rewrote the line. The host allowlist now limits the damage to Epoch's own host. A respx 302 with `follow_redirects=False` → `SourceError` would pin it.

## BLOCKING
- none

## Tests added or extended by this review
- none. The seat writes only this file. The fault-injection harness, the network logger and the loopback probes lived in the session scratchpad and were not committed.
