---
record_type: plan
id: m19-wave-5-plan
status: draft
process_version: v6.6
date: 2026-10-07
---
# M19-W5 plan — a first release: the engine hosted, the app on TestFlight

**Working plan for `wave/m19-w5`**, stacked on `wave/m19-w4`, deleted at the wave's close. The
milestone plan (`docs/plans/m19-plan.md` §2 W5) runs this wave only if the owner calls a release.
The owner called it on 2026-10-07: "we need to deploy the engine to a real supabase or something and
we need to go for testflight".

**Risk: HIGH.** The serving image, the launcher and the engine's host list change, and a public
surface is prepared. The Stage 5.1 security review runs on the whole release and is BLOCKING before
any deploy (milestone plan §2 W5). Nothing is deployed or uploaded in this wave: the account,
billing, signing and App Store Connect steps are the owner's, handed over as exact commands.

## Decisions taken on the owner's standing instruction (2026-09-29)

- **The host stays Fly.io (D-116, the owner's choice of 2026-08-15), not Supabase.** Supabase hosts
  Postgres, auth, storage and Deno edge functions; the engine is a long-running Python server reading
  one SQLite file, which Supabase cannot run without a rewrite (D-116 weighed it). Fly.io runs the
  existing image as it is, with HTTPS on its own name; `flyctl` is on the owner's Mac. D-123's stop
  (Fly asks for a card before it places a machine) is the owner's step.
- **The data ships inside the hosted image, at build time.** D-116 allows a build- or deploy-time
  artifact and keeps ingestion on the owner's Mac. A volume (`fly.toml`'s `[[mounts]]`) starts empty,
  so a first deploy would refuse to boot until a file was uploaded by hand; an image that carries
  its artifact is one immutable pair of code and data, and a rollback restores both.
- **The hosted artifact is public, and carries only the sources whose terms permit it** (#88; the
  licence table in the new ADR). Left out: ARC-AGI, DeepSWE, Terminal-Bench, SWE-bench's own board,
  MMLU and OpenRouter. `abstract`, `agentic-coding` and `computer-use` say they have no evidence
  there; `coding` ranks on Epoch's SWE-bench Verified. The owner's Mac keeps every source under
  W-129's ruling. The owner may overrule before the deploy.

## Issues

| Issue | What | Phase |
|---|---|---|
| #94 | The image refuses every outside request: no Host list | P2 |
| #88 | Data licences for a release beyond the owner's Mac | P3 |
| #147 | The owner's Mac name and LAN address in the public tree | P1 |
| #145 | The launcher's preflight judged by its output, not its exit status | P1 |
| #141 | The serving image takes its Python base by tag | P1 |
| #142 | The force-push guard passes `-uf`, `-fu` and `--mirror` (bug, medium) | P5 |

#81 (CI workflows) and #115 (the Turkish local-network prompt, checked on the owner's phone) stay
the owner's.

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P1 | #147, #145, #141 | No tracked file names the owner's Mac or home address: tests and docs use `my-mac.local` and `192.0.2.x`. The launcher refuses when the preflight exits non-zero with no output, shown red on a planted silent kill. Both `FROM` lines name the base by digest, and a test refuses a `FROM` without one |
| P2 | #94 | The image tells its startup check where it binds (`MODEL_RANKING_BIND`), so a bind beyond loopback with no Host list refuses to boot; shown red first. A hosted stage copies the artifact in; `fly.toml` names the one Host the engine answers to, from its app name, and its health check sends it. `scripts/deploy_hosted_engine.sh` builds the public artifact, deploys with `APP_BUILD` stamped and reads `/health` back; it runs only when the owner runs it |
| P3 | #88 | The public artifact: derived from the built one with the left-out sources removed, each affected surface saying it has no evidence, as an unavailable optional source does (D-121). A test holds that no left-out source's rows survive. The licence table and the ruling are an ADR |
| P4 | — | TestFlight readiness: an app icon, `PrivacyInfo.xcprivacy` with the reasons for the APIs the app uses, `ITSAppUsesNonExemptEncryption` false, a Release `ENGINE_URL` on the hosted name over HTTPS, and `docs/release-testflight.md` with the owner's steps (signing team, archive, upload, internal testers) |
| P5 | #142 | The guard blocks any short-option cluster after `push` holding `f`, and `--mirror`; `conformance/test-hook-claims.py` gains the three. A hook change: its own commit, for the owner's approval by merging (AGENTS.md §3) |
| P6 | — | Code-Reviewer, Tester, and the Stage 5.1 security review on the release, BLOCKING before any deploy |
