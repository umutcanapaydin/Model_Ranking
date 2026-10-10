---
record_type: review
id: m21-closure-security-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 closure security review, and the release re-read for v2

**Independent:** yes. I wrote none of M21's code, tests or records, and sat in none of its wave seats.

> **Two jobs in one record.** This is the M21 closure security seat (D-172: one seat per milestone, at
> its close). It is also the release security re-read: does M21's change to the release surface change
> the verdict of record (`docs/reviews/release-security.md`, MINOR, carried for build 3 by
> `docs/reviews/m20-closure-security-review.md`) before the owner deploys and uploads v2?
>
> **Range.** `git diff origin/closure/m20...9cbba60`: the four M21 waves (W1 #236, W2 #240, W3 #250,
> W4 #251), stacked. Merge base `972b55e`, 156 commits, 144 files, +31,099/-1,652. I read every slice on
> a security surface: the limiter (`src/app/adapter/main.py`), the deploy script, the public derivation
> (`public.py`), the registry and source tables, the new Arena board, the phone's changed files
> (`ContentView.swift`, `EngineClient.swift`, `HeldReading.swift`, `Language.swift`,
> `ModelFamilies.swift`, `Router.swift`, `StandingsStore.swift`), the compiled client gate and its
> records, the Bash guard (`.claude/hooks/bash_guard.py`, `.claude/settings.json`), `scripts/watchdog.py`,
> the Makefile's Swift legs and the close checks (`scripts/wave_check.py`, `scripts/check_records.py`).
>
> **Policy** was read from the profile (`.claude/agents/Security-Reviewer.md`),
> `docs/security-invariants.md`, `AGENTS.md` §5 and `permission-matrix.md` §5.
>
> Nothing was deployed. No new evasion payload was written: the guard was judged from its code, its
> conformance cases, mutants of its own fail-closed paths, and ordinary commands. The only repository
> file I write is this one, and I do not commit it.

## Verdict
MINOR

Nothing is BLOCKING and nothing is MAJOR. There are **6 MINOR** (S1 to S6) and **2 INFO** (S7, S8).

**The release verdict stands for v2: yes.** It stays MINOR, under the conditions in "The release re-read" below.

The scale is the M18 to M20 seats':
- **BLOCKING:** ships and can be exploited now, or the permission matrix §11 human-review trigger fires.
- **MAJOR:** not exploitable today, but a release control is weaker than its record says, in a way
  that would hide an exploitable state.
- **MINOR:** an invariant or a control that a code change could break with every gate green, or a
  claim wider than its test. Not exploitable in the current scope.
- **INFO:** checked and recorded; no action unless stated.

## Summary

- **Nothing typed leaves the phone (D-126, D-160).** M21's phone changes add no network, file,
  logging, sharing or URL call; I checked every added line. `ModelFamilies.swift` is a static set
  of words, generated from the registry and limited to letters (`registry.py:505`). It only lets a
  question that names model families route to `everyday`, and only when the engine served `everyday`
  (`Router.swift:547`). The request still carries only a surface id the engine served (INV-64, INV-70).
  `make client-decls` passes at `9cbba60`: 21 files, 4 configurations.
- **The limiter (W1, #228) keeps INV-88.** It still fails open and still runs after the Host check. A
  `/v1/boards` answer still counts as thirty, now in a window of its own. A refused request is not
  charged. Other spellings of the boards path are charged the same (probe below). Each new behaviour
  has a test that kills its mutant.
- **The deploy (W1, #198) fails closed and still ships only `main`'s tip.** The new refusal comes after
  the tip check and before anything is derived, a dry run included. One half has no test (S5).
- **D-190's source is clean.** `arena_webdev` is fetched through the existing Arena client, from the
  host every Arena board declares. The phone credits it under CC-BY-4.0 with the licence link
  (`ContentView.swift:1569`). `public.LEFT_OUT` is still empty (D-186), so nothing is left out on v2.
  The survivor check for LiteLLM's copies of OpenRouter's prices (#205) is held: its mutant is killed.
- **The compiled gate's records (G-1, G-2, G-10 to G-15) are honest by their catch-alls, with one
  exception.** G-10 says the gate runs before every push on the owner's Mac. It does not: the
  pre-push hook is not installed there, and no M21 session loaded the repository's hooks (S1).
- **The Bash guard's second reading (W4) fails closed on every error path I could reach.** Two of
  those paths have no test (S2). An agent can edit the guard's file in the middle of a session (S3).
  G-7 does not list one class it misses: a push whose destination git chooses itself (S4). None of
  this changes the release surface. The guard protected no M21 session anyway (`docs/control-events.csv:24`).

## Findings

### BLOCKING
None. No auth, PII, payment or migration path is in the range, so the §11 trigger does not fire.

### MAJOR
None.

### MINOR

**S1** `docs/security-invariants.md:193` (G-10), `docs/control-events.csv:24`, `Makefile:418-421`,
`scripts/client_decl_gate.py:2051`. **G-10 says the compiled gate runs before every push on the
owner's Mac. Nothing runs it automatically anywhere.**
- **What G-10 says.** The gate "is authoritative on a Mac with Xcode, the owner's, where `make
  check-fast` and `make check` run before every push".
- **Measured.**
  - The owner's clone sets no `core.hooksPath`. I read `git config` on
    `~/Desktop/ILGAR/model_ranking/.git`, and checked the global setting too. So the pre-push
    `make gate` never runs.
  - Every M21 session started outside the repository, so the post-edit `make check-fast` never ran
    either. The ledger's row 24 records both facts.
  - CI's Linux lane prints SKIPPED.
- **What follows.** The compiled halves of INV-62 to INV-67, INV-75, INV-76, INV-85 and INV-89 hold
  only when someone runs the gate by hand. The W4 close says it was run, and I ran it at `9cbba60`: it
  passes.
- **Failure scenario.** A later change adds a form that only the compiled gate refuses: one outside
  the spellings the text pins read (G-14). It is pushed and merged with every automatic check green,
  and in the next archive the typed text can leave the phone. G-10 says this cannot happen on the
  owner's Mac.
- **Why MINOR, not MAJOR.** The true state is recorded in the ledger (row 24, #142), the gate passes
  at the head, and v2 ships nothing exploitable.
- **Fix.**
  - The owner runs `make hooks` once in the clone. Then `make gate`, which includes `client-decls`
    through `make check` (`Makefile:130`, `:264`), runs before every push.
  - Until then, G-10 says "once `make hooks` is installed" and cites row 24.
  - Release condition 2 below covers v2.

**S2** `.claude/hooks/bash_guard.py:676`, `:680-682`, `.claude/settings.json:51`
(`printf '%s' "$p" | "$py" "$g" || exit 2`). **Two of the guard's fail-closed paths have no test. One
of them is the only limit on an older Claude Code.**
- **The 5 s deadline.** Mutant G2 never starts the timer, and `conformance/test-hook-claims.py` still
  passes.
  - The harness's brace-word case (`:514`) is blocked by the brace rule at once, so it never reaches
    the deadline.
  - G-7 and `INSTALL.md` say that below Claude Code 2.1.295 "only the guard's own 5 s bound protects".
  - The deadline is also the only limit on the guard's own work. `judge_command` tries up to 64
    programs behind wrappers (`:497-501`), and each one may recurse through `eval` or `sh -c`
    (`:545`, `:612-614`) as deep as 12 levels.
- **`|| exit 2`.** Mutant G4 drops it, and the harness still passes. Without it, a guard that dies
  with exit 1 makes the hook exit 1. Only exit 2 blocks, and `onFailure` is documented in this repository
  for a timeout only, so the call may run. Two ways to die with exit 1:
  - an interpreter older than 3.8 cannot compile the guard;
  - an exception near the 5 s mark reaches the `except` block with the timer still running, since
    `:680` stops the timer only on the normal path, and the alarm can then raise out of `main`.
- **The timer is SIGALRM.**
  - Python handles the signal between bytecodes, so one long call into C, such as a regex over a
    32 KB program word (`:513`), runs to its end before the guard blocks.
  - SIGALRM and `setitimer` do not exist on Windows. There `main` raises `AttributeError` and blocks
    every Bash call, `git status` included, in the Git Bash setup that `INSTALL.md` supports. That is
    the safe direction, but no test covers it and nothing switches it off.
- **Failure scenario.** A later edit drops the `setitimer` call or `|| exit 2`, and every gate stays
  green. Then, on Claude Code below 2.1.295, an input that keeps the guard busy past the hook's
  timeout runs without the guard reading it.
- **Fix.**
  - Bound the guard with a timer thread that writes the BLOCKED line and calls `os._exit(2)`. That
    works on every OS and also stops a call into C.
  - Add a unit test that imports the guard with `DEADLINE_S` near zero and checks for exit 2 on
    `git status`.
  - Add a harness case whose stub guard exits 1. It must block. It belongs beside the allow-all stub
    (`conformance/test-hook-claims.py:446-454`).

**S3** `.claude/settings.json:51` (`g="$CLAUDE_PROJECT_DIR/.claude/hooks/bash_guard.py"`),
`:36-40`, `docs/security-invariants.md:191` (G-7). **The second reading is a file in the working
tree, read again on every call, so an agent can change it in the middle of a session.**
- **Why.** Claude Code takes a snapshot of the hooks in `settings.json` when a session starts. I
  rely on its hooks documentation ("configuration safety") here, and did not re-read it, since I had
  no network. So the text reading cannot change during a session, but the file the hook runs can:
  - the `Write|Edit` guard refuses only `.env` paths;
  - the second reading allows a write by redirection or by `sed -i`.
- **Failure scenario.** In a session started in the repository, an agent "fixes" a false block by
  editing `bash_guard.py`. From its next call, the second reading is whatever the agent wrote. Then
  `fly ssh console`, `git push --all` and `git stash clear` pass, because only the second reading
  blocks them. The text reading's forms still block. G-7 does not list this class.
- **Fix.**
  - Pin the guard's sha256 in the hook's command, which is part of the snapshot, and block on a
    mismatch. Add a harness case that changes one byte.
  - Add `.claude/**` and `.githooks/**` to the `Write|Edit` guard.
  - Add the class to G-7.

**S4** `permission-matrix.md:52`, `docs/security-invariants.md:155` (INV-82), `:191` (G-7),
`.claude/hooks/bash_guard.py:636-643`, `conformance/test-hook-claims.py:381`. **The records say a
push to `main` is blocked. Only a push that names `main` is.**
- **The claims.** The matrix says a push to the default branch is "**ENFORCED** by the `Bash`
  PreToolUse guard". INV-82 says an agent "cannot … push the protected branch".
- **What is held.** Both readings block a destination the command names: `main`, `heads/main` or
  `refs/heads/main`.
- **What passes.** A destination git chooses itself:
  - a bare `git push`, which is one of the harness's MUST_ALLOW cases;
  - `git push origin HEAD`, or `@`;
  - an upstream, `push.default` or `remote.pushDefault`.
- **Failure scenario.** From a checkout on `main`, each of these pushes `main`. G-7's list of what is
  not held does not name this class; it names only `-c` and `git config`.
- **Not exploitable.** `main` is protected on GitHub. I read the protection for this record:
  `enforce_admins` is on, force pushes and deletions are off, and reviews and 6 status checks are
  required.
- **Fix.**
  - G-7 and the guard's docstring name the class.
  - The matrix says "a destination the command names".
  - GitHub's branch protection is the control of record for the rest.

**S5** `scripts/deploy_hosted_engine.sh:79-83`; no row in `docs/security-invariants.md`. **M21 adds
a release control with no register row, and one of its two refusals has no test.**
- **The control.** The deploy refuses data that another release built (#198, the W1 review's M4).
- **The untested half.** Mutant D1 removes the refusal of a missing or unreadable record, and
  `test_data_release_stamp.py` and `test_deploy_hosted.py` still pass (51 tests).
  - Without that refusal, a missing record reads as `missing`.
  - The general refusal at `:84-90` then prints the hint `DEPLOY_ACCEPT_DATA_FROM=missing`.
  - Following the hint deploys a copy that no record dates.
- **The rest is held.** D2 (no refusal at all) and D3 (any acceptance accepts any release) are both
  killed.
- **Failure scenario.** A later edit merges the two refusals into one, and every gate stays green. The
  owner follows the printed hint and ships data from an unknown release under HEAD's stamp.
- **Fix.**
  - Add the INV-90 row below.
  - Add a test: with no record, `DEPLOY_ACCEPT_DATA_FROM=missing` is refused; with an unreadable
    record, so is `DEPLOY_ACCEPT_DATA_FROM=unreadable`.

**S6** `scripts/client_decl_gate.py:93` (`"ObjectiveC"` in `MODULES`), `:829` (`SINK_MODULES`),
`:234-247` (`BY_NAME`), `docs/security-invariants.md:195` (G-12); #241, which asks this seat to read
it. **The by-name rule refuses three families of the Objective-C runtime by prefix, while the module
that declares the whole runtime is allowed.**
- **What is refused.** `BY_NAME` refuses the runtime's `objc_`, `class_` and `method_` functions, plus
  `NSExpression`, `NSPredicate`, key-value coding and `perform` on `NSObject`, `Mirror`,
  `NSClassFromString` and `NSSelectorFromString`.
- **What is not.**
  - The runtime's other C families (`sel_registerName`, `object_*`, `ivar_*`, `protocol_*`, `imp_*`)
    and `NSProtocolFromString` match no rule of the compiled gate. None of them is in `EGRESS`
    (`tests/unit/test_router_hints.py:617-650`). I read this from the code and planted nothing.
  - `@_silgen_name` binds a function the app declares to any symbol, by its linker name. The
    compiled gate sees a declaration in `main`, so only the text pin's spelling holds it (`:649`).
- **The cost of closing it is nil.** The shipping client resolves nothing in `ObjectiveC`. I measured
  0 of the 2,800 references in the simulator Release dump.
- **G-12 is honest as written**, because its catch-all says "any other way … is not held". This is a
  narrowing, at no cost.
- **Failure scenario.** A later change makes a selector from a string with the runtime's own C
  functions, and calls it through one of the target-and-selector APIs that G-12 already lists. No
  rule refuses either half.
- **Fix.**
  - Take `ObjectiveC` out of `MODULES` and `SINK_MODULES`.
  - Plant one runtime call in the fixture under `the module allowlist`.
  - Add `@_silgen_name` to G-12's examples, as held by the text pin only.

### INFO

**S7** #245. **Two of the issue's three facts no longer hold at `9cbba60`.**
- **A text pin does restate the client's imports.** `CLIENT_IMPORTS`
  (`tests/unit/test_router_hints.py:606`) is checked on every `import` in every client file
  (`:735-739`), on every lane. It was already in `origin/closure/m20`.
- **The module-rule mutant is now killed on both lanes.** Mutant C1 turns off the import half of
  `_module_problem`.
  - Without Xcode it fails `test_the_committed_dump_is_the_fixture_as_it_compiles` and
    `test_the_self_test_requires_the_release_rule_in_each_release_configuration`. Both run the
    self-test on the committed dump.
  - With Xcode it fails `test_the_gate_refuses_its_compiled_fixture` as well.
- **What remains is the declaration half:** a symbol resolved through a re-export in a module off the
  list, with no `import` line. On CI's Linux lane only the `EGRESS` spellings hold it. That is G-10
  and G-14 as written, and S1 covers the owner's Mac.
- **Disposition.** Narrow #245 to that half, or close it into #243.

**S8** `.claude/settings.json:49-50`, `INSTALL.md:16-19`, G-7. **This seat did not verify
`onFailure: "block"`.**
- The harness checks only that the key is present (`conformance/test-hook-claims.py:518-521`), not
  what Claude Code does with it.
- The owner's Mac runs Claude Code 2.1.296, read from the installed version's path.
- I could not check the key's handling:
  - this session's permission classifier refused my read of the installed binary;
  - the documentation is not reachable offline.
- G-7 says a version that ignores the key lets a stalled hook's call through. Whether an older
  version ignores the key or rejects the entry is not known here.
- **Owner check, once:** in a session started in the repository, `/hooks` lists the Bash hook.

### PASS (observations)

- **The limiter (`main.py:816-843`).**
  - It fails open: on an exception it serves the request, and warns once a minute naming only the
    exception's type (`:830-835`).
  - The Host check is still outside it (INV-26), held by `test_a_wrong_host_is_refused_before_it_is_counted`.
  - Each client's two counts live in one table entry, so the table's limit and its crowding rule are
    unchanged.
  - Measured in process: `/v1/boards`, `/v1/%62oards` and `/v1/boards?x=1` answer
    `200, 200, 200, 200, 429, 429` under a limit of 120. `/v1/boards/` is a `307` with no body.
    `//v1/boards` is a 404.
  - Per client and minute it serves at most 4 boards answers (about 2 MB without gzip) plus 120
    small ones. The boards bound is the M20 fix's, and only question traffic left that window.
- **The deploy (`deploy_hosted_engine.sh:37-48`) is unchanged before the new block.** It needs a clean
  tree, untracked files included, and HEAD must equal the freshly fetched `origin/main`. The refusal
  runs before anything is derived, a dry run included (`test_the_refusal_runs_before_anything_is_derived`).
  - The record is parsed with `json.load` inside `set -euo pipefail`. Any error makes it `unreadable`,
    which is always refused.
  - `FROM` is at most 7 characters and is passed to `fly` quoted.
  - An unchanged night keeps the older builder's name (`refresh.py:789-798`). The refusal may then
    need the named override, which is the safe direction.
- **The phone.**
  - `HeldReading` moved into the Engine unchanged in logic, with Swift tests.
  - The new `StandingsStore.currentKept(fetch:)` dates the standings by the store's own clock
    (`StandingsStore.swift:86`). That closes a 64-bit channel from the screen into the standings
    file, and `PROVENANCE` holds the dated form to the store.
  - The refusal sentences (`Language.swift:828-850`) are the app's own wording, chosen by the error
    code.
  - The engine's message moves into `diagnostic` (`EngineClient.swift:106`), which no app file reads.
- **No new egress, storage or dependency.**
  - `pyproject.toml`, the locks, `fly.toml`, the `Dockerfile`, `.dockerignore`, `ios/Config/`, the
    project file and the privacy manifest do not change in the range.
  - New imports are from the standard library, or are PyYAML, which is already declared, used with
    `safe_load` on CI's own workflow file (`tests/skips.py`).
  - The router probes read and write local files only, and are built into neither the app nor the
    test package.
  - The Swift legs now run inside `scripts/offline.sb`, with SwiftPM's own sandbox off. The package
    has no external dependency, so the only manifest that runs is the repository's.
- **`scripts/watchdog.py`.**
  - It stops a hang with SIGINT, then SIGKILL, to the command's process groups, never its own.
  - It never calls `abort`.
  - Its `pgrep` call takes a pid list, not a shell.
- **The close checks** call git with argument lists. A start that a record names reaches git only
  inside `rev-parse --verify <x>^{commit}`, so a record cannot inject an option.
- **The registry rules cannot move a source's rows to another source.** They map names to model
  ids. The derivation deletes by the `source` column of `scores`, `pricing` and `access`, and no
  table was added in the range.

## New invariants (proposed rows for `docs/security-invariants.md`)

| INV | Invariant | Source | Negative test(s) | Gap |
|---|---|---|---|---|
| INV-90 | The hosted deploy runs only from a clean tree at the freshly fetched tip of `origin/main`. Before anything is derived, a dry run included, it refuses served data that another release built, unless the owner names that release in `DEPLOY_ACCEPT_DATA_FROM`. A missing or unreadable record is refused whatever is named. | D-185 cl. 5; #198; the M21-W1 review's M4 and its second round's R1 | `tests/unit/test_deploy_hosted.py::test_only_the_tip_of_origin_main_deploys`<br>`::test_a_commit_not_on_origin_main_is_refused`<br>`::test_an_uncommitted_tree_is_refused_before_anything_is_built`<br>`::test_an_untracked_file_is_refused_before_anything_is_built`<br>`tests/unit/test_data_release_stamp.py::test_data_built_by_another_release_is_refused` (D2 killed)<br>`::test_the_refusal_runs_before_anything_is_derived`<br>`::test_data_from_another_release_deploys_when_the_owner_names_it` (D3 killed)<br>`::test_unknown_accepts_no_missing_or_unreadable_record` | Partial: "whatever is named". D1 survives (S5) |

To INV-82, once S2's tests exist: the deadline test and the stub that exits 1. Until then, G-7 holds
three more facts: the guard's 5 s bound and the hook's `|| exit 2` have no test (S2), the guard file
is not part of the session's snapshot (S3), and a destination git chooses itself is not held (S4).

INV-88's row already names the new behaviour, and its mutants L1 and L2 are killed. INV-87's copies
check is held (P1 killed).

## The release re-read

**What M21 changed on the release surface, read in full:**

| Where | Change | Judgement |
|---|---|---|
| `src/app/adapter/main.py` (limiter) | Two counts per client, a refused request not charged, `/v1/boards` weighted 30 in its own window | Holds INV-88. Fails open, Host check first, no route, no egress (PASS) |
| `scripts/deploy_hosted_engine.sh` | Refuses another release's data; stamp names the data's release | Fails closed, still `main`'s tip only (PASS); S5 is a test gap |
| `fly.toml`, `Dockerfile`, `.dockerignore` | None | — |
| `web-dev`'s source (D-190) | `arena_webdev` from LMArena's dataset, CC-BY-4.0, credited on screen | Same client, host and grant as every Arena board (PASS). Epoch's copy is still served on TestFlight under D-186 |
| Error sentences (`Language.swift`) | The app's own sentence per error code | No new flow (PASS) |
| The gate (`make client-decls`) | More by-name and URL rules; records state the residue by class | PASS at `9cbba60`; S1, S6, S7 |
| `nightly.py` | `APP_BUILD` joins the child's allowed environment | A build stamp, no secret (INV-40) |
| `ios/Config/`, privacy manifest, `EngineClient.swift`'s network code | None, apart from the diagnostic string | The HTTPS address of the Release archive is unchanged |

**Does it change the verdict of record? No. The verdict stays MINOR, and it stands for v2**, on these
conditions:
1. **Merge, then deploy from `main`'s tip.** Merge the M21 pull requests in order. Let the Mac's engine
   refresh once with the new release before the deploy (runbook, step 2). Do not use
   `DEPLOY_ACCEPT_DATA_FROM` for v2: `web-dev`'s new board arrives only with this release's data
   (D-190).
2. **Run the compiled gate on `main`'s tip** after the merges and before the archive: `make check`,
   which includes `client-decls`. No automatic step runs it (S1). Or run `make hooks` once, so that
   every push runs it.
3. **Check the `Fly-Client-IP` header after the deploy**, as the runbook says (G-9).
4. **Archive and upload.**
   - Raise the build number: `CURRENT_PROJECT_VERSION` is still 3 in the tree.
   - Archive only after the deploy's `/health` check passes.
   - The `plutil` readback of the signed archive must say `https://model-ranking.fly.dev`.
5. **Keep the habits.** Run `fly auth logout` after each deploy. Watch the usage page while people
   test. `fly scale count 0` stops the engine at once.
6. **Before external testers,** the owner rules on D-185's table (D-186 clause 3), unchanged.
   `web-dev` no longer goes dark if Epoch's copy is left out.

## Gates run on `9cbba60`

| Check | Result |
|---|---|
| `gitleaks detect --log-opts=972b55e..9cbba60` | 154 commits, no leaks |
| `gitleaks detect --no-git` on the tree | no leaks |
| `ruff check --select S,BLE src scripts` | 19 findings, the same set as at `origin/closure/m20` (compared line for line, without line numbers) |
| `ruff check --select S` on `.claude/hooks`, the new scripts and `scripts/check_records.py` | clean; BLE001 only on the guard's intended fail-closed catch |
| `pytest tests` inside `scripts/offline.sb`, under `scripts/watchdog.py` | 2511 passed, 25 skipped |
| `scripts/client_decl_gate.py` (`make client-decls`) | PASS, 21 files, 4 configurations |
| `conformance/test-hook-claims.py` | PASS, 2 claims, 18 legs, 0 unbacked |
| `make deps`, `make slopsquat` | not run, because they reach PyPI. No dependency changes in the range, so INV-80's state is the release record's |

## Mutants

Each mutant was applied to a scratch copy (`git archive 9cbba60`) and restored by its bytes and
sha256. The worktree was never written; `git status` shows only this record.

| # | The edit | Tests run | Result |
|---|---|---|---|
| L1 | A refused request is charged | `test_rate_limit.py` | killed: `test_a_refused_request_is_not_charged` |
| L2 | One count for both kinds of request | `test_rate_limit.py` | killed: `test_a_boards_answer_after_light_requests_crosses_the_limit_and_is_said` and 2 more |
| D1 | The missing or unreadable refusal removed | `test_data_release_stamp.py`, `test_deploy_hosted.py` | **survived** (S5) |
| D2 | Another release's data not refused | same | killed: `test_the_refusal_runs_before_anything_is_derived` and 2 more |
| D3 | Any acceptance accepts any release | same | killed: `test_data_from_another_release_deploys_when_the_owner_names_it` |
| P1 | The copies' survivor count dropped | `test_public_artifact.py`, `test_webdev_board.py` | killed: `test_a_missed_copy_of_a_left_out_source_stops_the_derivation` |
| G1 | The 32 KB bound removed | the hook harness | killed |
| G2 | The 5 s timer never armed | the hook harness | **survived** (S2) |
| G3 | An error in the guard allows | the hook harness | killed (8 cases) |
| G4 | The hook's `\|\| exit 2` dropped | the hook harness | **survived** (S2) |
| C1 | The import half of the module rule off | `test_client_decl_gate.py`, the two pin files, `test_security_invariants.py`; without and with Xcode | killed on both lanes (S7) |

**Score:** 11 mutants, 8 killed, 3 survived. Each survivor is in a finding.

## Skip ledger

| Check | Why it did not run | Consequence |
|---|---|---|
| Swift suites, `make ui-test`, `xcodebuild`, a signed archive | Off limits, or the W4 close's runs stand | The phone's changes were judged from their code and the compiled gate. The W4 close records `make swift-test` and `make ui-test` |
| `fly`, Docker, the deploy, a probe of the hosted engine | Off limits | G-9 rests on the runbook's check (condition 3) |
| What Claude Code does with `onFailure` | The permission classifier refused my read of the installed binary; the documentation is not reachable offline | S8 |
| A new guard payload, and timing of the guard's regexes | Not crafted, by the dispatch | S2's points about calls into C and about Windows are read from the code |
| The questions in `docs/research/*-runs/` and every held-out file | The dispatch forbids them | Not opened |

**Network.** Only read-only `gh`: issues #241 and #245, and `main`'s branch protection. Every test
and probe ran in process or inside `scripts/offline.sb`. No process of mine is still running, and none
ended in SIGABRT.

## Dispositions, at the closure

| finding | disposition |
|---|---|
| S1 | fixed `70eb084`: G-10 says nothing runs the compiled gate automatically until `make hooks`; the runbook's v2 section runs `make check` on `main`'s tip and `make hooks` once |
| S2 | fixed `3143da4` (red `efc0790`, `5ef5c6f`; OWNER APPROVAL): the guard's deadline is a timer thread, and a guard that exits 1 blocks |
| S3 | fixed `3143da4` and `419d5dc` (red `efc0790`; OWNER APPROVAL): the hook pins the guard's sha256, and neither Bash nor the Write and Edit tools write into `.claude/` or `.githooks/` |
| S4 | fixed `3143da4` and `70eb084`: G-7 and the permission matrix name the push to a destination git chooses itself, held by branch protection only |
| S5 | fixed `ee22b3d` (red `8fe7332`): no name accepts a missing or unreadable record; INV-90 in the register |
| S6 | fixed `d894287` (red `5575a0a`): `ObjectiveC` is off the client's allowlist, and the fixture holds a runtime call the gate refuses |
| S7 | #245 narrowed to the declaration half (comment), named in G-10 (`70eb084`) |
| S8 | the owner's check, once: `/hooks` in a session started in the repository (the runbook's v2 section, `70eb084`) |
