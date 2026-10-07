---
record_type: register
id: roadmap-2026-10-07-post-m19
status: ratified
process_version: v6.6
date: 2026-10-07
---
# Roadmap snapshot — after M19 (2026-10-07)

A snapshot, never edited after it is written (seed I.1).

**Where the product is.** The engine runs on the owner's Mac, and is ready to run on Fly.io; the app
runs on the owner's iPhone, and is ready for TestFlight:
- **The engine** names every model as its maker spells it, one release one model (M19-W1), and each
  pick carries its model's id (D-182). On the Mac it refreshes nightly as before. A hosted image
  carries a public artifact without the seven sources whose terms do not permit it (D-185, #88), and
  `scripts/deploy_hosted_engine.sh` deploys `main`'s tip to Fly.io, stamped and read back.
- **The app** keeps its privacy and arithmetic promises on the compiled module (D-180, D-181). It
  reads a question of fact as a doubt (D-184). Its Release build asks the hosted engine; it has an
  icon, a privacy manifest and the encryption answer.
- **The gates** count CI's skips, run the tests offline on macOS, and read the plan's tier and globs
  before the push (D-183).

Nothing is deployed or uploaded. Two M19 pull requests are open, stacked in order: #196 (W4), then
#197 (W5), then the closure.

**What the owner decides next.**
- Whether to ship W4's reading as measured: #66 improved and missed its bars, #113 is where it was
  (#196).
- The deploy and the upload: the steps are `docs/release-testflight.md`, after the merges.
- The four hook commits marked OWNER APPROVAL (#197), and the owner's settings (#190).
- Whether D-185's licence ruling stands.

**What is next, not yet planned (M20).**
- The first deploy's own checks: `make journey` against the hosted engine, `make cold-start` with
  Docker, and the owner's TestFlight readback.
- A stranger's first use, by `docs/research/stranger-first-use-protocol.md` (#91), on TestFlight. Its
  questions become the next held-out set; the M19 sets retire (#195).
- The medium bugs left: #113 and #191, the image rule beyond `vision`, past three attempts.
- The hosted engine's limits: a rate limit and the budget argument (#187, #188); the guard's spellings
  (#189).
- The open backlog: the reading's word lists (#186, #192, #194), the probe harness tests (#193), and
  the low-severity bugs (#85, #124, #163 to #165, #168, #178).
