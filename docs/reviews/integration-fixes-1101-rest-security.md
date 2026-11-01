---
record_type: review
id: integration-fixes-1101-rest-security
status: draft
seat: independent
process_version: v7.2
date: 2026-11-01
---
# Security Review — integration/fixes-1101, the rest of the stack (the owner's guard commit, #544, the deploy-gate group, the tooling group, #549)

**Reviewer:** Security-Reviewer subagent (light mode; a delta review of the rest of the stack, which `make review-need RANGE=f8ad11b..HEAD` routes to security for its gate, control and policy files)
**Independent:** yes. I wrote none of this code. I have not reviewed these branches before. I read the earlier verdict, docs/reviews/integration-fixes-1101-security.md, for its findings only.
**Date:** 2026-11-01
**Release range:** f8ad11b..7fdf27e. 31 commits: the owner's guard commit `5f514da` (#533, #529, D-236); #544 (`864c415`, `d673ec2`, `6e37695`, merged by `9da5f82`); the deploy-gate group #543, #546, #534, #541, #548 (merged by `6020d0a`); the tooling group #528, #536, #530, #531, #525 (merged by `936cec3`); #549 (`627582c`, `e2d5a38`, `1faffb3`, merged by `7c0f2cc`); the process log `7fdf27e`. Every commit carries the owner's identity, and every non-merge commit but `5f514da` carries a `GP-Task:` trailer. `5f514da` is the owner's own. The earlier part of the stack, 74f8c07..5fd1d2b, is reviewed in docs/reviews/integration-fixes-1101-security.md. f8ad11b adds only docs to it (`docs/control-events.csv`, `docs/owner-actions.md`, `docs/process-log.md`, the verdict).
**Reviewed head:** 7fdf27e66403c57a0da1f843e3c0138bc9f6bd31
**Risk tier:** HIGH (deploy gate, Bash guard and wave_check control changes). The brief's `Paths that make a change HIGH:` is `none` (docs/project-brief.md:110, at the base 74f8c07), so the §11 senior-review trigger does not fire.

## Verdict
MINOR

Nothing in the range weakens a refusal that existed before it. The owner's commit is the reviewed patch, byte for byte. #534, #541 and #546/#548 only widen what the gate and wave_check read: a union of bases, more names on the surface, and exact refs. #549 (D-239) adds a refusal. It is new, and its reader fails open on ordinary shell and YAML (M1, M2, M3). Each miss stays quiet. I showed this end to end with `unnamed_starts` on planted repositories. It is MINOR, not BLOCKING, for three reasons. Before the range, none of these shapes was refused either. The real `nightly-hosted.yml` (all four copies) has no unnamed start and none of these shapes. And an agent cannot author the dispatched copy, which is the default branch's `.github/workflows/` file. It should be fixed before the owner merges the next change to a deploy workflow, because that review is the moment D-239 exists for. M4 is a test-criterion change beyond D-238's ruling. M5 is a short-name ref read left in a deploy script the range touches.

I worked only in `scratchpad/wtq-sec`, detached at 7fdf27e, with its own `.venv` from `make install` and its own `advisor.db` (sha256 `a0362a7a5b73…`). The probes ran in `scratchpad/secrest/` (planted origin and clone repositories, built by Python scripts). Nothing contacted the hosted engine, Fly or a launchd service. The deploy-script tests put stand-ins for `fly` and `curl` first on PATH (tests/unit/test_deploy_hosted.py:5-6, :60-63). The policy files were read at the base. `AGENTS.md`, `permission-matrix.md`, `docs/security-baseline.md` and `.claude/agents/Security-Reviewer.md` do not change in 74f8c07..7fdf27e (`git diff --stat` is empty).

## Findings

### BLOCKING
- none

### MINOR
- **M1** scripts/deploy_gate.py:711, :726-728 (`_run_tokens`, D-239 clause 1): shell comments are read as words, so a comment can hide the next commands. The docstring says this "refuses more", but it refuses less.
  - **A quote in a comment.** The block is lexed as one text, so an apostrophe in one comment and another in a later comment make everything between them one quoted word. The house style writes such comments (`# the owner's ...`).
  - **A comment ending in `\`.** The gate joins the next line onto the comment (:728). Bash does not continue a comment.
  - **`<<` in a comment.** The gate opens a here-document (:726), and the lines up to its delimiter are dropped.

  Planted repository, `gh workflow run nightly.yml` declared, one block step (`scratchpad/secrest/plant549.py`):
  ```
  control            bash scripts/*.sh                                      -> ['nightly.yml line 8: a pattern ... `scripts/*.sh`']
  comment_quotes     # the owner's state / bash scripts/*.sh / # the gate's turn  -> []
  comment_backslash  # on Windows: C:\ / bash scripts/*.sh                  -> []
  comment_heredoc    # cat <<true / bash scripts/*.sh / true                -> []
  ```
  Bash runs the hidden line in each case (`scratchpad/secrest/bashcheck.sh`: "RAN-after-backslash-comment", "RAN-after-heredoc-comment"). An unnatural `echo $((1<<true))` opens a here-document the same way.

  **Remedy:** drop a comment as the shell does before lexing: a `#` that begins a word, outside quotes, up to the end of the line, with no continuation and no here-document read inside it. Or fail closed: refuse a run block in which a comment holds a quote, ends in `\` or holds `<<`. Add each case above to tests/unit/test_deploy_gate_549.py as a refusal.
- **M2** scripts/deploy_gate.py:664, :860 (`STARTER_VALUED`, `_starter_shapes`), :779 (`_run_commands`), :1049-1052 (`_program_position`): the words before a starter's file are misread, so the file is never reached. Probes (`scratchpad/secrest/probe549/shapes.py`, and `plant549.py` end to end), each MISSED or `[]`:
  - **An option cluster.** `bash -eo pipefail scripts/*.sh` (GitHub's own bash form) and `bash -euo pipefail "$X"`: only a bare `-o` takes a value, so `pipefail` is read as the file.
  - **A redirection with a descriptor number.** `2>/dev/null bash scripts/*.sh` and `bash 2>&1 "$X"`: the `2` is lexed as a word, so it becomes the program or the operand.
  - **A wrapper's options.** `timeout -k 5 60 bash scripts/*.sh` and `timeout --kill-after=5 60 ...` (the duration after options is read as the program), `exec -a name bash "$X"` and `stdbuf -o L bash "$X"`.
  - **An assignment that makes the shell source a file.** `BASH_ENV="$X" bash scripts/deploy.sh` and `env BASH_ENV=$X bash ...`: assignments are skipped. A step's `env: BASH_ENV:` sits outside `run:` and is not read at all, and GitHub's non-interactive bash sources it.

  **Remedy:** read a short-option cluster that holds `o`/`O` as taking the next word; lex `[0-9]+` directly before a redirection operator as part of it; skip `timeout`'s duration after its options, and `exec -a`'s and `stdbuf -i/-o/-e`'s values; refuse `BASH_ENV` and `ENV` anywhere in a dispatched deploy workflow's text. Add a test for each.
- **M3** scripts/deploy_gate.py:670, :674-700 (`_RUN_KEY`, `_run_values`): only a `run:` key in block style, with a plain one-line value or a block scalar, is read. These YAML forms carry a run value Actions runs (PyYAML 6 in the worktree's venv parses each one to `{'run': ...}`), and each is MISSED:
  - a plain scalar that continues on the next line (`run: echo hi &&` and then `bash "$X"` on the line below): only the key's line is read;
  - a quoted scalar, `run: "ls scripts | xargs -n1 bash"`: shlex reads it as one word, so `xargs`, `find -exec` and `eval` are not seen; a quoted scalar over two lines is not read past its first;
  - a flow mapping, `- {name: x, run: bash "$X"}`;
  - a quoted key, `- "run": bash "$X"`.

  `run: "find ... -exec bash {} ;"` and an alias `run: *s` are refused only by accident (a `*` in the one word).
  **Remedy:** fail closed. Refuse a workflow whose text has a `run` key in any form `_RUN_KEY` does not take: a quoted key, a flow mapping, a quoted value, or a plain value with a more-indented line after it. Or read the file with a YAML parser the gate's interpreter is sure to have, and then lex each value.
- **M4** tests/unit/test_refinements.py:87-99, :102-119 (#544): `test_every_board_a_question_can_select_is_served` now excuses a refinable surface whose primary board is missing when its source is optional, has no row in the artifact, and `/v1` answers it `no_evidence`. The owner's ruling and D-238 cover CAT-10 only. D-238 does not record this exemption, and commit `6e37695` gives the reason ("an optional source that sent nothing") only in its message. The exemption is narrow (`required` is False, zero rows, and the disclosure goes through the real route), and it matches D-121. It is not a security loosening. But it widens what a release passes, beyond the ruling the dispatch asked me to hold the stack to. The CAT-10 change matches the ruling exactly (tests/unit/test_categories.py:379-399): `%`/`elo` metrics keep `window < floor`; any other metric uses `leader - window >= floor`; a missing leader fails closed; and all 20 surfaces' `metric` values are `elo`, `%...`, `ECI` or `minutes`. **Remedy:** record the exemption in an ADR clause that cites D-121, or have the owner confirm it in the PR, so the excuse is a decision and not only a test.
- **M5** scripts/deploy_hosted_engine.sh:77: `git rev-parse origin/main` is a short-name read. The line is older than the range, but the range touches this file (#531). A tag `origin/main` wins over `refs/remotes/origin/main`, and the patched guard allows `git tag origin/main HEAD` (probe: ALLOW). Scratch clone (`scratchpad/secrest/plant.py`):
  ```
  HEAD 9d1595c  origin/main before 5e91976
  short origin/main after `git tag origin/main HEAD` + `git fetch origin main`: 9d1595c   exact refs/remotes/origin/main: 5e91976
  ```
  So "HEAD is not the tip of origin/main" passes for any HEAD a session tags. The guard lets an agent run the script only with `--dry-run` (D-185, .claude/hooks/bash_guard.py:142). The exposure is the owner's own run from a checkout an agent left on its branch. That is the case this check exists for. **Remedy:** compare HEAD with `git show-ref --verify --hash refs/remotes/origin/main` after the fetch (what `brief_fields.exact_ref` does), and add a test that plants the tag.

### PASS
- **`5f514da` is the reviewed patch, unchanged.** `build/owner-guard-1101.patch` in the main checkout has sha256 `b9e185d4adaead236ee46a12d97306c59b61fff65c65f489b68f66ebe10dddea`, the hash the earlier verdict reviewed. I applied it with `git apply` to `git archive f8ad11b` (`scratchpad/secrest/patchid/tree`). All four files are byte-identical to `5f514da`'s blobs:
  - `.claude/hooks/bash_guard.py` `655f514ce7914d9d…`;
  - `.claude/settings.json` `4a09aa51fc3f…`;
  - `conformance/test-bash-guard.py` `5c123ecbb163…`;
  - `tests/unit/test_bash_guard_bounds.py` `05ed089dca37…`.

  The commit touches only those four files, and `.claude/` changes in no other commit of the range. 5fd1d2b..f8ad11b changes only docs, so the patch's base is unchanged too. The pin in `.claude/settings.json` (both hook commands) is `655f514ce791…`, the sha256 of `.claude/hooks/bash_guard.py` at 7fdf27e: `655f514ce7914d9d897a0feeb547531733b01725d227f8bb276b9cd6ff441485`.
- **#534, more bases can only refuse more.** `protected_bases` (scripts/brief_fields.py:345-363) now returns every default-branch ref's merge-base and tip, each read through `exact_ref`. It used to return only the first ref's. Each consumer of the bases reads all of them as a union or as an "all must hold":
  - `declared` unions the deploy commands (deploy_gate.py:1020-1037);
  - the working modes each require their Tester;
  - `_workflow_texts` reads every base's workflows, and an unreadable one is incomplete, which refuses (:1227-1250);
  - `devflow_pins` needs a pin at every base, or nothing is exempt (:437-449).

  So a stale `origin/HEAD` adds a base and hides nothing. `policy_root` (#543) has no caller left: grep finds none in scripts/, conformance/, .claude/hooks/ or the Makefile.
- **#546/#548, wave_check reads exact refs.** `_default_tips` (scripts/wave_check.py:440-446) reads `DEFAULT_BRANCHES` through `exact_ref`. `_merged`, `_wave_base` and `branch_adr_problems` use it (:450, :459, :536), and the closure branch is read by its full ref (:463-465). The guard refuses creating `refs/heads/master` and the other default refs in every form I probed: `git branch`, `checkout -b`, `switch -c`, `update-ref`, `fetch . HEAD:master`, `push . HEAD:master`, `worktree add -b`, `branch -c` and `symbolic-ref refs/remotes/origin/HEAD`, all BLOCK. So the two new names (`origin/master`, `heads/master`) cannot be planted to mark a close merged.
- **#541 / D-237** `_named_by_name` (deploy_gate.py:580-597) is unioned into `_workflow_names` (:600-609), so it only adds files to the surface, and `_UNREAD_IN_WORKFLOW` is unchanged.
- **#549 fails closed where it knows it cannot read.** `unnamed_starts` returns None when a base's workflow cannot be read or git cannot list the tree, and `verdicts` turns None into a refusal (deploy_gate.py:882-895, :987-991). A shlex error falls back to splitting by words, which still sees `$`/`*`. The refusal is on every entry point, because `judge` and `check` both walk `verdicts`. The real tree: `unnamed_starts(wtq-sec)` is `[]` over the four copies of `nightly-hosted.yml`, and no run block there has a comment with a quote, a `\` or `<<`.
- **#530** ios/Config/Engine.xcconfig:32-33 blanks `INFOPLIST_OTHER_PREPROCESSOR_FLAGS` and `INFOPLIST_PREFIX_HEADER` for Release after the local include. tests/unit/test_release_plist_preprocessor.py derives the list from Xcode's own `.xcspec` files, and checks a hostile local file under four conditions (narrower Release conditions included) for both SDKs. It passes here.
- **#531** scripts/deploy_hosted_engine.sh:131 reads a record nested past the recursion limit as `unreadable`, which no acceptance covers, so it fails closed.
- **#525** scripts/ui_test.sh:98-102: a failed uninstall now stops the run.
- **#536** the toolchain line is evidence only (scripts/client_decl_gate.py:1024-1044): its own subprocess errors read `unread`, and it changes no verdict (tests/unit/test_client_decl_gate_536.py:84).
- **#528** measures CPU time; the bound itself is unchanged.
- **#544, the display names are bounded.** Each derived name must still `_DISPLAY.fullmatch` and derive the same model id (src/app/workflows/registry.py:939-950). No board number moves, so D-104 holds.
- No new third-party import: `itertools` and test-local imports only. No `shell=True`, `eval`, `os.system` or YAML load in the code added; the one `os.system` in the diff is a test's workflow fixture string. No new endpoint, secret, log statement or destructive operation. `.github/`, `.githooks/`, `Dockerfile`, `deploy/`, `pyproject.toml`, `requirements/` and the Makefile are unchanged in the range.
- **Tests, run by me at 7fdf27e:** the range's tests and their neighbours (`test_deploy_gate_{534,541,543,545,549,526,517}`, `test_wave_check_{546,548}`, `test_deploy_hosted`, `test_ui_test_script`, `test_client_decl_gate_536`, `test_release_plist_preprocessor`, `test_testflight_ready`, `test_display_names`, `test_categories`, `test_refinements`, `test_media_surfaces`, `test_arena_respelling`): 399 passed. `make secrets` at 7fdf27e: "no leaks found". `deploy_gate.py --check` at 7fdf27e FAILs as it should (37 code files changed since `release-security.md`'s head 6e6f5be).

## Gates passed
- [x] Secret scan green (from the dispatcher at 936cec3: PASS over 1401 tracked files; run by me at 7fdf27e: "no leaks found")
- [x] `make deps` (pip-audit) green (from the dispatcher at 936cec3: "No known vulnerabilities found"; 936cec3..7fdf27e changes no dependency file)
- [x] `make slopsquat` green (from the dispatcher: "PASS: 20 declared dependency(ies), 0 suspect"; no new third-party import in the range)
- [x] Default-deny preserved for new external surfaces (no new surface; every gate change adds refusals or reads more)
- [x] Permission-matrix not violated (the guard change is the owner's own commit of the reviewed patch; no agent commit touches `.claude/`, `.githooks/` or `.github/`)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model in the range)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; HIGH paths are `none`)
- [x] SAST (bandit is not in the lock. I read the delta by hand. The new subprocess call in client_decl_gate.py:1035 runs a resolved `xcrun` with literal arguments, with a timeout. The new regexes (`STARTER_SHELLS`, `STARTERS`, `PATTERN`, `_RUN_KEY`) have no nested quantifier.) Conformance from the dispatcher at 936cec3: "PASS: 33 test(s) ..., 0 failing"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- D-236 guard commit = reviewed patch → `5f514da`; .claude/settings.json pin `655f514ce791` = sha256 of .claude/hooks/bash_guard.py; the patch's sha256 `b9e185d4…dddea`, applied and compared above
- #534 every default-branch ref's bases → scripts/brief_fields.py:345-363; tests/unit/test_deploy_gate_534.py:39, :46, :61
- #543 dead `policy_root` gone → scripts/deploy_gate.py (removed); tests/unit/test_deploy_gate_543.py:59, :71, :81
- #546 default branch read exactly → scripts/wave_check.py:440-450, :459, :536; tests/unit/test_wave_check_546.py:38, :47, :58, :66
- #548 closure branch by full ref → scripts/wave_check.py:462-465; tests/unit/test_wave_check_548.py:21, :30
- #541 / D-237 a name under any prefix → scripts/deploy_gate.py:580-609; tests/unit/test_deploy_gate_541.py:45, :58, :71
- #549 / D-239 unnamed start refuses → scripts/deploy_gate.py:647-895, :987-996; tests/unit/test_deploy_gate_549.py:92, :100, :111, :124, :134, :171, :187, :192 (not met for M1-M3's shapes)
- #544 / D-238 CAT-10 per scale → tests/unit/test_categories.py:379-399, :402-411; display names → src/app/workflows/registry.py:893-950, tests/unit/test_display_names.py:101, :204, :210, :214 (the refinements exemption: M4)
- #530 → ios/Config/Engine.xcconfig:29-33; tests/unit/test_testflight_ready.py:187-210; tests/unit/test_release_plist_preprocessor.py:40, :66
- #531 → scripts/deploy_hosted_engine.sh:131; tests/unit/test_deploy_hosted.py:373
- #525 → scripts/ui_test.sh:97-102; tests/unit/test_ui_test_script.py:147, :160
- #536 → scripts/client_decl_gate.py:1024-1044, :3631-3671; tests/unit/test_client_decl_gate_536.py:58, :66, :74, :84
- #528 → tests/unit/test_arena_respelling.py:77-127

## Risks queued
- **R1** conformance/test-commit-identity.py:225-226 reads `main`/`master` by short name. A tag `main` (the patched guard allows `git tag main`) makes `main..HEAD` empty in my scratch clone (`main..HEAD count: 0`). The attribution scope then reads no commit, and the agent's own authors count as "known humans". Makefile:470 (`merge-base HEAD origin/HEAD`, the `CLOSES_CHANGED` subset of `make closes`) is the same shape. Both are older than the range and outside it. Read them through `exact_ref`, or with `refs/heads/`/`refs/remotes/` names that exist.
- **R2** scripts/wave_check.py:463: `refs/heads/closure/m<N-1>` is a branch a session may create (the guard allows `git branch closure/m30 HEAD`). Planted at the close's end, it makes the wave base the end itself, so the "narrower than the wave" check (:614) compares against nothing. This is older than the range, because the short name read the same branch. #548 closed the tag route only. In light mode no wave close is graded.
- **R3** The patched guard still allows `git tag origin/main`, `git tag main` and `git tag refs/remotes/origin/main`. That is what keeps M5 and R1 reachable from a session. The earlier verdict's B1 remedy offered it as an optional second layer: refuse a tag whose short name, under `refs/` or not, is one of `DEFAULT_BRANCHES`. It belongs in the owner's next guard patch.
- **R4** scripts/deploy_gate.py:987-996: when no workflow starts an unnamed file, `make deploy-check` prints no line for D-239. So a PASS carries no evidence that the workflows were read. Print a `workflows: no start without its name (N run value(s) read)` summary.
- **R5** A here-document or here-string fed to a shell (`bash <<'EOF'`, `bash <<< "..."`) is a script on standard input. The gate sets the body aside (D-239 clause 1). #551's proposed remedy, "refuse a shell that reads its standard input from a pipe", would not catch either. Add both to #551.
