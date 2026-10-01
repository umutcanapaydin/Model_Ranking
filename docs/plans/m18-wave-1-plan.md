---
record_type: plan
id: m18-wave-1-plan
status: draft
process_version: v6.6
date: 2026-09-29
---
# M18-W1 plan — the app on the owner's iPhone

**Working plan for `wave/m18-w1`**, deleted before merge. Issues #87 and #86. Milestone plan:
`docs/plans/m18-plan.md` §2 W1. Risk: **HIGH**. The engine listens beyond loopback for the first
time. (No security pass of its own: D-172, the owner's ruling of 2026-09-29.) The pull request opens only after the reviews and
`/pre-merge`.

## The spike (done, 2026-09-29, never committed)

A scratch engine bound to the Mac's LAN address (`192.168.0.26:8082`) answered the app built to
point at it: `/v1/categories`, `/v1/recommendations` and `/v1/boards`, each 200, from the
simulator. ATS does not apply to an IP literal. The simulator does not enforce iOS's local-network
permission, so the phone's prompt text (`NSLocalNetworkUsageDescription`) is set in the wave but
first seen on the owner's device.

## Design (D-171)

- **The engine checks the Host.**
  - With `MODEL_RANKING_ALLOWED_HOSTS` set, a request whose Host (port stripped) is not on the list
    gets 400. The service always sets it, so DNS rebinding is refused on loopback too (closure
    security seat INFO I-4).
  - Unset, as in tests and by-hand development, every Host is served, as today.
- **The bind is fail-closed.** `MODEL_RANKING_BIND` feeds uvicorn's single `--host`, and defaults to
  `127.0.0.1`. The startup check refuses a bind that is not loopback when no allowed Hosts are set.
- **The installer opts in.**
  - `scripts/install_engine_service.sh` writes `MODEL_RANKING_BIND=127.0.0.1` and
    `MODEL_RANKING_ALLOWED_HOSTS=127.0.0.1,localhost` into the wrapper.
  - With `--lan` it binds `0.0.0.0` and adds the Mac's `<LocalHostName>.local` and LAN address to
    the allowed Hosts.
  - The wrapper stays mode 700.
- **The app's engine address is per build.**
  - The Info plist key `EngineURL` comes from the build setting `ENGINE_URL` (default
    `http://127.0.0.1:8080`), set in `ios/Config/Engine.xcconfig`. The owner overrides it in a
    git-ignored `ios/Config/Engine.local.xcconfig`.
  - `EngineClient.localDefault` reads the key, and falls back to loopback when it is missing or not
    an http(s) URL with a host.
  - The partial plist declares `NSAllowsLocalNetworking` (for `.local`) and the local-network usage
    text.
- **Nothing new leaves the phone** (D-126; D-160 as amended). The same requests go to a different
  host.
- **#86.** The wrapper's exec line has exactly one `--host`, read from `MODEL_RANKING_BIND`. The
  preflight refuses a bad start when run for real. The written wrapper's mode is checked after an
  install.

## K.8 contracts, grep-verified at `e82011b`

```
ios/ModelRanking/Engine/EngineClient.swift:144:    static let localDefault = URL(string: "http://127.0.0.1:8080")!
scripts/engine_service.sh:73:exec "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host 127.0.0.1 --port "$PORT"
src/app/adapter/main.py:545:def validate_startup_config(env: str | None = None) -> tuple[str, ...]:
```

## Phases

- **P0:** this plan and D-171.
- **P1:** the engine's Host check and bind, red first.
- **P2:** the installer's opt-in and the service tests (#86), red first.
- **P3:** the app's per-build address and plist keys, red first. Verified on the simulator against an
  opted-in engine.
- **P4:** the owner's steps (`docs/owner-iphone.md`), the reviews, and the security pass.

## The one alternative

**A hosted engine the phone reaches anywhere.** It is more useful, but it needs the licences ruled
(#88) and the Stage 5.1 release review first. The home network needs neither.
