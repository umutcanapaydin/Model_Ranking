# Engineering practices

**How this file was cut, v6.0.** Every rule that stood here was scored against nine projects, and a
rule survived only if the failure it prevents was **observed in two or more of them**. 128 rules
went in; **47 cleared that bar**. The bar is the owner's: *"to get into this methodology a problem
has to have been produced again and again in different projects, so that we can write the thing
that prevents it."* The full table — every rule, its count, the projects and the citing line — is kept in the
methodology's own repository, because a rule removed without a record is a rule someone re-derives next
quarter.

**49 rules stand below.** The arithmetic, since it does not add up on its own:

| | |
|---|---|
| cleared the bar (2+ projects) | 47 |
| dropped anyway, as stale or superseded | −5 |
| kept below the bar, because a gate in this package refuses the change | +6 |
| written for this cut, no corpus score yet | +1 |

The five dropped despite clearing the bar were not cut for lack of evidence. Two described a git
cadence this version replaced, one pointed at a `make` target removed four versions ago, one was a
CANDIDATE block that never got its second ecosystem, and one restated the go-live rules three lines
below where they already appear. Each is named with its reason in that register.

The six kept below the bar say so on their own line. Deleting the prose while the gate still runs
leaves an error message nobody can explain.

**This file holds rules that live nowhere else.** Where another file is the authority — the security
baseline, the permission matrix, the issue rules — this one points and stops. Of the rules cut, most
were already written down somewhere else in this same package. That is not a coincidence, it is the
top-scoring finding in the corpus: *one fact written in two places drifts,* observed in five of nine
projects.

---

## Tests are the truth signal

- **Every acceptance criterion has a citing test; red-test the reported symptom first (gate).** No "done" without a test that cites the criterion; when fixing a reported bug, reproduce
 it with a FAILING test before diagnosing, then make it green (red→green). Enforced at the Quality
 Gate and the per-wave Tester. *(4 projects)*
- **Run the tests; don't trust markdown that says "tests pass"** (seed E.1). *(3)*
- **Tests cite REQ-IDs and D-IDs** in comments — e.g. `# covers REQ-CC-001, D-026` (seed E.2). PASS
 verdicts WITHOUT `file:line` evidence are BLOCKING per `permission-matrix.md` §11. *(3)*
- **One canonical mock per integration + a contract test .** Build one canonical
 mock/fake-client per external integration before the integration code; consolidate parallel mocks
 into it; keep a contract test that runs against the real API so the mock cannot drift. Tests drive
 the canonical fake, never bespoke per-test stubs. *(3)*
- **A fixture supplies a NON-DEFAULT value drawn from the measured record (clause).**
 When a mapping short-circuits one input to a no-op and every developer machine, every CI run and
 every fixture supplies exactly that input, the real branch has never run — and coverage reports it
 covered. In one project an entitlement mapping reached customers the day a console began sending a
 real group name: **a P0 capability certified DONE by a test that fed the right value into the
 wrong parameter, having never functioned.** So at least one fixture configures the dependency in a
 non-default state and drives one real request end to end, and **every rule a test double enforces
 cites the dependency's own source or a contract test** — a rule in a double with no citation is a
 hypothesis wearing a test's clothes. *(3)*
- **Coverage gaps are design tells** — not metric targets (seed J.3). *(3)*
- **Acceptance-criterion tests ship in the same wave as the feature** (seed E.5) — never defer the
 test that proves a *hard* criterion (concurrency, survives-restart) to closure. On subagent death,
 verify the criterion's test EXISTS, not just that the code compiles. *(2)*
- **Full gate in-sandbox via a runtime shim** (seed C.10) — when the sandbox runtime lags prod,
 inject the version-only-missing names (`datetime.UTC`, `StrEnum`) via `sitecustomize.py` and run
 the WHOLE suite; keep the one behaviour-version-dependent test `skip`-marked for the real target.
 *(2)*
- **Hermetic gate (C.6):** trust a verdict only from a reproducible environment — clean venv
 built solely from the manifest, dev tools pinned (not `>=`-floored), stale bytecode cleared, ONE
 designated authoritative gate host. A permissive dev sandbox passes code the real gate fails. *(2)*

## Security

`docs/security-baseline.md` is the authority and carries the origins, the review checks and the
traceability table. Four rules are repeated here because each one is a **gate** you will meet before
you meet the document:

- **No plaintext creds / no default-admin password .** Hash credentials from day one;
 secrets from env or a secrets manager, never inline literals. `make bootstrap-check` **C7**. *(2)*
- **CORS allowlist, never allow-all + credentials .** `make bootstrap-check` **C9**. *(2)*
- **Validate security-critical config at startup; fail the prod process .** Never silently
 default to an insecure value — auth-off, empty key, `0`. *(2)*
- **No reseed / reset / drop defaulting ON .** `make bootstrap-check` **C10**. *(the env
 form is the one that ships: `os.getenv("SEED_ON_STARTUP", "true")` looks configurable, and the
 default is what runs when nobody sets the variable)*
- **Server-side authz on every mutating route .** Client-side checks are UI sugar; assume
 the client is hostile. *(2)*
- **Generic client errors; log detail server-side.** No stack, SQL or internal-path leaks; no
 user-enumeration oracles. *(2)*

## What is running is not what you built

The largest cluster in the corpus, and every rule in it is the same sentence: *named, configured or
present is not working.* Six occurrences in one project alone.

- **"Code green + image built" is NOT "the new code is live."** `curl <target>/health | jq .build`
 MUST equal the tag or SHA you intended to ship (L.7). *(3)*
- **Version-stamp the health probe** (L.7) — `APP_BUILD` (image tag / git SHA) → `/health` body
 `{status, version, build}`. A green probe proves *up*, never *which code*. Day-1 baseline;
 additive fields only. *(3)*
- **A pod restart != a rebuild != a re-pull.** Restarting re-runs the image the deployment already
 references; if `/health` shows the old build, fix the build pipeline — do not just restart. *(3)*
- **Configured != working** (L.8) — invoke every external dependency once for real
 (`make smoke-deps`) and inspect the RESULT before declaring ready. Catalog presence and valid
 credentials can sit on a backend that answers "not deployed." *(4)*
- **Config reaches the *process*, not just the values file** (L.9) — read each critical value back
 from inside the running process (safe echo: SET/EMPTY plus length, never the value). Helm,
 operators and secret mounts drop keys silently. *(3)*
- **Runtime config, never build-baked .** Config that differs per environment is read at
 runtime. A value baked into the image ignores the runtime environment, and nothing says so. *(2)*
- **Boot-prerequisite ownership :** in the image, or a named-owned provisioning row — no
 third category. A partner-built image that neither ships nor runs your migrations is the third
 category, and it is where the data goes. *(3)*
- **A human path, walked by a human who did not build it** — using only shipped docs and artifacts,
 they complete the surface's primary journey. No gate models this, which is why it is written
 down. *(3)*
- **Releases are immutable and uniquely identified**; the run stage only launches a *selected*
 release (12-factor build/release/run). *(2)*
- **Every dependency is in the manifest in the SAME edit** — or CI breaks where local
 worked. *Below the bar (1 project); kept because `make deps` and the clean-venv gate enforce it,
 and in that project the host gate was the only thing that caught the missing entry.*

## Working with subagents

- **Drift-guard between data dictionaries and consumers** — factor the coercer when three or more
 subagents produce the same helper (K.5). *(5 projects — the most reproduced finding in the
 corpus, and the general form of it: one fact in two places drifts.)*
- **Code-quality review goes to a fresh subagent** (Code-Reviewer profile, K.7). The reviewer MUST
 NOT have authored any of the wave's code. *(4)* In a single-agent lane the reviewing
 seat is a SEPARATE SESSION carrying the diff and the base-ref rules, not the authoring context, and
 **it writes a file** -- `docs/reviews/*.md` with `seat: independent` in its frontmatter
 (model_ranking, W-056; `scripts/wave_check.py` `review_seat_problems` enforces it).
- **Cross-subagent contracts are grep-verified in the plan** (K.8) — paste `grep -n <symbol>` output
 into the plan. *(2)*
- **Subagent prompts specify the bar and leave discretion** inside a ≤5-minute scope (K.6). *(2)*
- **Wave close is checklist-gated :** fill and commit the wave-close checklist; every ✅
 cites a fresh wave-scoped referent; skipped or waived checks are ledgered.
 `make wave-check FILE=...` verifies it mechanically. In one project all five wave checklists were
 written in a single commit after the fact. *(3)*
- **The security pass checks for weakened validation, broadened permissions and disabled checks**,
 and flags sensitive files (auth, crypto, secrets, CI, dependency manifests) touched outside the
 declared slice. Three rules asserted as enforced in one project were not. *(3)*
- **A plan names ONE alternative and its trade-offs** on MED and HIGH tiers — "which would a senior
 object to, and why". LOW-tier plans are exempt. *(2)*
- **Telemetry per task type at every closure** — post-closure fix rate, churn, reverts, findings
 with security double-weighted. It exists to give the owner an honest quality signal, not a
 score. *(3)*

## Git

- **Branch and draft PR.** The agent works on its own branch, commits there, pushes **that branch**
 and opens a DRAFT pull request. It never pushes the protected branch, never marks a PR ready,
 never merges. The property this protects — **no commit may be mistaken for the owner's** — is
 carried by the branch, the draft state and the ban on AI attribution. *Below the bar (0 projects,
 because it is new); kept because it is the load-bearing rule of this methodology and
 `conformance/test-git-authority.py` and `test-commit-identity.py` both enforce it.*
- **No AI attribution anywhere** — not `Co-Authored-By`, not "Generated with", not a badge, in
 commits, PR bodies, issues or comments. *This reverses the provenance rule, which required
 exactly such a trailer; that rule survived the corpus cut on 2 projects and is retained here in
 reversed form, because the evidence behind it — twelve commits in one project carrying the
 owner's name — is the same evidence, and the branch now carries what the trailer used to.*
- **In-place revert.** `git checkout <file>` and `git restore` revert to the last COMMIT — on
 uncommitted work they destroy everything since. Revert experimental edits in place and verify
 byte-identical. *Below the bar (1 project); kept because the `hook-worktree` PreToolUse hook
 blocks these commands, and in that project a reviewer undoing a deliberate fault injection with
 `git checkout` clobbered work that was not theirs.*

## Decisions and capture

- **Open the capture file BEFORE the work starts**, not after (G.1). *(3)*
- **process-log per session** — three to ten lines, ending with a `Lesson:` tag. In one project two
 days of demo-building produced zero entries. *(3)*
- **Capture every assumption as an ADR** (seed B.1) — use the `log-decision` skill. *(2)*
- **Supersede, never edit** (seed B.2) — the old ADR keeps its body and is marked
 `superseded by D-NNN`. *Below the bar (0 projects); kept because it is the invariant every
 governance record in this package depends on, and `make check-records` reads it.*
- **Hand-off files written FOR future agents are first-class deliverables** (G.7). *(2)*
- **Per-milestone retrospective with PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY verdicts**
 (G.12) at M≥3 — the `cycle-close` skill walks it. *(2)*
- **When a rule changes, update the canonical file AND every cached pointer to it.** *(2)*

## Writing and pruning

- **README and PR/issue bodies are LIVE DOCUMENTS, not history logs.** They describe what the thing
 *is*, not how it got there. When the work evolves, rewrite the affected section **in place** —
 never append a changelog, a migration note, a progress update or session narration. A body that
 has become a log is a body nobody reads to the end, and the current state is the part that
 mattered. *(2)*
- **Log at boundaries.** API entry, database write, external call, queue publish and consume.
 Structured, never a bare print. Internal pure functions need none — that is noise. *(2)*
- **Prune stale docs that contradict current decisions**, continuously. *(4)*
- **At quarterly handover, put the harness on a diet:** retire any skill, hook or MCP server that
 has not fired in 90 days. *(4)*

## Stage 0

- **`make bootstrap-check` before Stage 0 closes** (C.11 / FB-1) — it fails on stray
 `<PLACEHOLDER>`s, a non-L.7 `/health`, still-template prd/decisions/architecture, missing
 universal ADRs, an unreviewed copyleft fork, and the three security legs above. *Below the bar (1
 project); kept because it IS the gate. In that project its first execution caught two placeholders
 that had survived every human read.*
- **License and commercial-use review of any wrapped or forked OSS engine** (F.10 / FB-4) —
 AGPL/GPL/SSPL on a network service means "wrap, don't fork" plus legal sign-off; an unreviewed
 copyleft fork is BLOCKING. *Below the bar (1 project); kept because `bootstrap-check` C6 enforces
 it, and in that project the review forced an engine swap after the licence turned out to be
 AGPL v3.*

## Where the rest lives

- `docs/security-baseline.md` — the web/API security baseline, in full
- `permission-matrix.md` — the default-deny matrix and the BLOCKING taxonomy
- `.agents/rules/issues.md` — issues, labels, and the verification pipeline
- `.agents/rules/playbook-seeds.md` — the seed compendium, searched as needed
- the cut register — every one of the 128 rules, its count, the projects it was seen in and the
 line that cites it. It is **GP-INTERNAL**: it is built by reading nine projects' private
 experience files and its citations are paths into them, so it stays in the methodology's own
 repository and is not copied into a project. Ask for it by name.

## Final reply (Done Evidence template)

Moved here from `AGENTS.md` §7 at the M13 closure diet check (that file had reached 156 lines against
its 150-line cap, since M11-W1). `AGENTS.md` keeps a one-line pointer and the PASS rule.

End every task with:
- Files changed
- Tests run + outcomes
- Assumptions made
- New ADRs (D-IDs)
- Risks queued to next milestone

PASS verdicts MUST cite `file:line` evidence per acceptance criterion (otherwise BLOCKING per permission-matrix §11).
