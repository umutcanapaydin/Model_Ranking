---
record_type: review
id: owner-bundle-552-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-02
---
# Security Review — owner bundle for #552

**Reviewer:** Security-Reviewer subagent (an owner bundle owes a review before it is applied, `scripts/owner_bundle.py`)
**Independent:** yes. This seat did not write the patch, the script or the proposal. It extracted the patch from the proposal, applied it to its own `git archive` export of this branch's head (no git work tree), and ran the step against records it built itself.
**Date:** 2026-11-02
**Reviewed patch:** c06a8459993713c34890800fab23cb4ea623c8815564b7ba59ac0255d75808aa
**Reviewed head:** 55d731b884a7d205c7de95d953b6df3542503f99
**Risk tier:** HIGH. The patch changes the dispatched deploy workflow (`nightly-hosted.yml`, a brief `Deploy commands:` entry) and gives a job a write-scoped token, `issues: write`, in that workflow.

## Verdict
MINOR

## Findings

### BLOCKING
- none

### MINOR

- **M1** `.github/workflows/nightly-hosted.yml` (patched), the `silent` step, read with the `deploy` job's `if:` at `:110-112` of the head: a failure of the new step can still skip the night's deploy.
  The `deploy` job's `if:` uses no status function, so GitHub adds `success()`: the deploy runs only when the whole `refresh` job succeeded. The step runs under the default `bash -e`. `errexit` is off only inside the `if` condition; in the `then` branch it still applies, so a failure of the second `python3 scripts/silent_sources.py "$record"` or of the `echo ... >> "$GITHUB_OUTPUT"` fails the step, the job and so the deploy.
  Evidence: this seat ran the step's exact script under `bash --noprofile --norc -e`. A record whose `silent` holds a lone surrogate (`{"silent": {"x\ud800": "2026"}}`) passes the `--issue` call, because `json.dumps` escapes it. The plain call then dies with `UnicodeEncodeError` and the step exits 1.
  The proposal says "It never fails the job, so it never holds the deploy back" (`docs/proposals/nightly-silent-sources.md:17`, and the step's own comment). That is true of the `else` branch only.
  Failure scenario: a malformed name or stamp in the carried record fails the plain-mode print. Every nightly deploy after that is skipped until someone notices, while Fly serves the last good image. This fails safe; nothing is exposed.
  Remedy: add `continue-on-error: true` to the step, so the claim holds by construction. Or end both `then`-branch lines with `|| true`.

- **M2** `tests/unit/test_nightly_hosted.py`: no test holds the proposal's security claims. `grep -n 'notice\|issues\|silent'` finds nothing in that file. The claims are: `notice` is the only job with `issues: write`, it holds nothing else, it checks out no code and runs no third-party action, it runs only on `refs/heads/main`, and the `silent` step cannot fail the job (`docs/proposals/nightly-silent-sources.md:18-24`). Without a test, a later edit can widen the token or move the job's `if:` without any gate failing.
  Remedy: add these as test cases in the same file, on both copies:
  - each job's `permissions` map is exactly as listed
  - `issues: write` appears only under `notice`
  - `notice` has no `uses:`
  - `notice`'s `if:` holds `github.ref == 'refs/heads/main'`
  - the `silent` step has `continue-on-error: true` (after M1)

- **M3** `.github/workflows/nightly-hosted.yml:7-18` (unchanged by the patch): the header still says "Two jobs" and "Both jobs run only on main". After the patch there are three jobs, and the third holds a write token. The next reader of the file reads the trust layout from that header. Remedy: name `notice` and its one permission there. This is an edit to the agent's proposal copy, so it ships with the next bundle.

### PASS
- **The patch:** extracted with the proposal's `awk` line; its sha256 is `c06a8459…5d75808aa`, as named. It applies cleanly to `55d731b`, and after it the two copies are byte-identical (`cmp`). The `diff -r` of base and patched exports shows only the two files.
- **Least privilege:**
  - The workflow-level `permissions: contents: read` is untouched.
  - `refresh` keeps `contents: read, actions: read` and gains only an output.
  - The new step has no `env:` and no token; the job's only token-bearing step is still the fetch step.
  - `notice` declares `issues: write` alone, so its token carries that plus the implicit `metadata: read`. It has no checkout, no `uses:`, and runs only the runner's `gh`, so no repository code ever runs with the write token.
  - `deploy`, its `fly-production` environment and its `FLY_API_TOKEN` are untouched: both hunks end before `deploy:`.
  - `deploy` does not depend on `notice`, so a failure of `notice` cannot touch the deploy.
- **Expression and shell injection:**
  - The output never appears as `${{ }}` inside a `run:`. It reaches the shell only through `env: NOTICE` and is written with `printf '%s\n' "$NOTICE"`, quoted. In `if:` it is only compared with `''`.
  - `echo "notice=$(cat ...)"` does not re-evaluate the file's text.
  - `silent_sources.py --issue` prints `json.dumps(...)` with defaults, which is one line with `\n` and U+2028 escaped. A newline in a name therefore cannot start a second `GITHUB_OUTPUT` line. Measured: a name holding `\n::error::injected\n@octocat | x` produced one `notice=` line.
  - `$open` comes from `--jq '.[0].number'`, a number.
- **Non-main dispatches:** `notice` requires `github.ref == 'refs/heads/main'`. Off main, `refresh` is skipped by its own `if:`, so the output is empty as well. A dispatch on a tag named `main` has the ref `refs/tags/main`, not `refs/heads/main`.
- **Which issue gets written:** the issue lookup filters by `--author app/github-actions`. An issue someone else opens with the same title is never commented on.
- **Mentions in the issue:** names and stamps go into inline code with backticks replaced (`scripts/silent_sources.py:44-46`), so `@name` in a single-line value mentions nobody. Multi-line values are R1.
- **The deploy gate:** `deploy_gate.unnamed_starts`, run in-process on both exports (git listing and protected bases stubbed, brief's four deploy commands), returns `[]` on both. It reads 37 run commands at base and 56 patched. The workflow now names `scripts/silent_sources.py`, as `_workflow_names` confirms, so that script joins the deploy surface and a change to it will owe a deploy-time review. This is the intended effect of D-239 and D-242.
  The new steps set no `shell:`, start their one script by its name, run no interpreter code (`-c`) and feed no program on stdin (D-242 clauses 1, 2 and 4).
- **No-record and empty-map nights:** a missing record takes the `else` branch (a `::warning::`, exit 0). An empty `silent` map writes `notice=` and `notice` is skipped.
- **Tests:** `tests/unit/test_nightly_hosted.py` and `tests/unit/test_silent_sources_552.py` on the patched export: 58 passed. 3 failed, and the same 3 fail on the unpatched export: they need a git checkout (`git rev-parse HEAD`, file modes), which an archive export lacks.

## Gates passed
- [ ] Secret scan green (`make secrets` on the release commit): not run by this seat. The patch holds no literal credential; the only token is `${{ github.token }}`.
- [x] `make deps` (pip-audit) green: not applicable, no dependency changes.
- [x] `make slopsquat` green: no new import, and no new action (`notice` uses none).
- [x] Default-deny preserved for new external surfaces: `issues: write` is held by one job with no code checkout.
- [x] Permission-matrix not violated: the agent did not apply the workflow. The owner applies the bundle.
- [x] Prompt-injection hygiene: record values reach the issue as data, in inline code (see R1 and R2).
- [x] Auth/PII checks + human review trigger fired: no auth/PII/payment/migration path.
- [x] SAST: no `${{ }}` in a `run:`, quoted shell expansions, no interpreter code.

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- D-243 clause 1 → `src/app/workflows/refresh.py:1131-1148`, `:1279`; `tests/unit/test_silent_sources_552.py:57`, `:63`, `:71`, `:80`
- D-243 clause 2 (one issue, opened once and commented after) → the patch's `notice` job. It is untested in CI (M2); the proposal's `## Checked before proposing` is the evidence offered.
- D-243 clause 3 → the patch is an owner bundle; `docs/proposals/nightly-silent-sources.md:37-42`
- `scripts/silent_sources.py` → `tests/unit/test_silent_sources_552.py:115`, `:122`, `:137`, `:147`

## Risks queued
- **R1** `scripts/silent_sources.py:44-46`, `:78-79`: names and stamps are not checked for control characters or `|`. If a value held a newline:
  - the plain-mode print would put `::error::`/`::warning::` workflow-command lines in the log;
  - in the issue body the newline would end the table row and its inline code, so the next line would render as raw Markdown, where an `@mention` fires.

  Measured on a crafted record. Not exploitable today: the keys are the registry's source names (`refresh.py:1236`, `outcome.arrived`), and the stamps are the cycle's own ISO time or the carried value (`refresh.py:1231-1232`) from the main-only `hosted-state` artifact. No upstream payload string reaches them. Hardening is agent-side: in `read_silent`, refuse a name or stamp outside `[A-Za-z0-9._:+-]` (exit 2 already means "cannot be read"), or escape it.
- **R2** Trust boundary: the `refresh` job parses untrusted upstream data, and its `silent` output now feeds the one job holding a write token. Code execution in `refresh`, for example a parser exploit that rewrites `scripts/silent_sources.py` in the job's workspace before the last step, could choose the JSON `notice` posts with `gh api --input`. That JSON could set any title and body, and `labels`, `assignees` or `milestone` on a new issue. The blast radius is this repository's issues; there is no contents or deploy write.
  Narrowing: `notice` posts fixed fields only. Either `gh issue create -R ... --title 'Sources silent for 7 or more nights' --body-file <body>` and `gh issue comment <n> --body-file <body>`, with the refresh step writing the body alone. Or `gh api ... -f title=... -F body=@<body>`. Neither needs interpreter code (D-242 clause 4).
- **R3** `gh issue list --search` reads the search index, which can lag a just-created issue by minutes. Two nights cannot overlap (the `concurrency` group), so a duplicate needs a hand-dispatched run just after a scheduled one. That would be a second issue, not a security fault.
