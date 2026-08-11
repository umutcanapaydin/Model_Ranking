# M2 W3+W4 — Combined Code-Reviewer + Tester (fresh eyes, LOW; pair-batched, separate verdicts)
Date: 2026-08-11. Reviewer executed probes (threshold bleed, stale determinism incl. false-negative
proof, close-call wording live, CI heredoc injection).

W3 (category layer): PASS, 2 MINOR + 2 PROCESS → applied (per-category export filenames;
attribution test now covers observed_at; D-105 recorded in decisions.md incl. the documented
RankingRow/Pick generalization that deviates from plan §4 "frozen" — no external consumers).
W4 (recommender + CI): PASS, 4 MINOR → applied (thresholds moved into CategorySpec as DATA —
a third category can no longer inherit the wrong scale; _stale_notice docstring now states the
deterministic-proxy limitation honestly (never-refreshed DB can't self-report stale — accepted);
pipefail added to CI smoke + dead `-m ""` removed; assistant close-call wording test added,
frontier-only disclosure design noted).
Verified clean: no threshold bleed with 2 categories; heredoc quoted (no expansion); permissions
contents:read; div-by-zero impossible (schema CHECK > 0).
Carried to closure: ci.yml/gitignore replica-absence (device repo HAS both — verify at commit);
REQ-CI-001 wording vs push-on-main triggers (fine, noted); frontier-only close-call design.
