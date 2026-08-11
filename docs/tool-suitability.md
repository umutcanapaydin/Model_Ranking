# Tool Suitability Matrix

> Single-page filter for routing tasks: what's appropriate to delegate to an AI coding agent vs. what requires human judgment / senior review. Reference in `m{N}-plan.md` when scoping waves and choosing risk tier.
>
> Source: research-handoff §9 (industry consensus across OpenAI / Anthropic / academic studies).

---

## Strong fit — Delegate freely (Risk tier LOW)

Tasks where AI agents perform reliably with light review. The Stage 3 per-wave Code-Reviewer + Tester (v3, V3C-68) is sufficient. Stage 4.1 Quality Gate runs standard checks; the closure Security review (Stage 4.0) is light at this tier.

- Test generation (unit + integration)
- Documentation updates (README, changelog, inline comments, ADR drafts via `/log-decision`)
- Refactoring with clear patterns (rename, extract, move)
- Small features with explicit acceptance criteria (≤2 files)
- Bug reproduction from clear steps (use `/triage-issue` + `/fix-issue-prepare`)
- Internal tools, CLI utilities, data parsing
- API client wrappers (Protocol implementations behind D-001 boundary)
- Migration helpers (data shape transformations)
- Boilerplate (config files, schema definitions)
- Code review first pass (via Code-Reviewer profile + `/review` skill)
- Codebase explanation / onboarding doc generation
- Requirements-to-task conversion (REQ-IDs → wave decomposition)

---

## Medium fit — Delegate with stronger spec + review (Risk tier MEDIUM)

Tasks where AI agents work but human oversight matters. Stage 3 per-wave Code-Reviewer + Tester necessary. Stage 4.1 Quality Gate must be thorough. The closure Security review (Stage 4.0) runs SAST opportunistically; a security-touching wave may pull a security pass forward (HIGH-risk trigger).

- Multi-file feature implementation (>2 files, cross-module)
- Performance improvements (require profiling validation)
- Database schema migrations (reversible only; ADR required)
- UI flows touching backend logic
- CI/CD changes (Makefile, GitHub Actions YAML edits)
- Data engineering pipelines
- Integration with external APIs (must use Protocol boundary)
- Error handling / retry logic (must be tested for all failure modes)
- Logging / observability changes (PII redaction verified)

---

## Weak fit — Senior human review mandatory (Risk tier HIGH)

Tasks where AI agents have known high failure rate. Stage 3 per-wave Code-Reviewer + Tester + the Stage 4.0 closure Security review + Stage 4.1 Quality Gate are necessary but **not sufficient**. Per permission-matrix §11, ANY change in these categories without senior human review is automatic BLOCKING.

- **Authentication / authorization logic.** Lovable CVE-2025-48757 lesson; Veracode 45% finding.
- **Cryptography.** Hand-rolled crypto is almost always wrong; AI doubles the risk.
- **Payment / financial transaction logic.** Idempotency, double-spend protection, money handling.
- **Critical security controls.** Input validation at trust boundaries, RLS, ACLs.
- **Regulated data handling.** PII redaction, PDPL / GDPR compliance, audit trail.
- **Irreversible migrations.** Schema changes that drop columns / tables; data deletion.
- **Production deploy automation.** Replit DB-deletion lesson (July 2025).
- **Complex distributed system changes** without strong tests (consistency, ordering, partial failure).
- **Large refactors** (>10 files) without architecture constraints.

Risk tier HIGH milestone gates:
- A security-touching wave pulls a security pass forward into Stage 3 (HIGH-risk trigger); the closure Security review (Stage 4.0) still runs and is BLOCKING before deploy (v3, V3C-68)
- Security-Reviewer runs full SAST scan (bandit + semgrep OR Veracode-class if budgeted via F.5)
- Mandatory senior human review appended after Stage 3 / at closure
- All BLOCKING/MINOR findings tracked through to milestone closure

---

## How to use this matrix

### Stage 0 (project bootstrap, once)
- Read this once. Identify which categories your project will touch.
- If HIGH-risk categories are present, configure `permission-matrix.md` §7 tightly.

### Stage 1 (every milestone plan)
- For each REQ-ID, classify Strong / Medium / Weak fit.
- Milestone overall risk tier = highest task in it.
- Risk tier drives the Stage 3 per-wave review (Code + Tester) + the Stage 4.0 closure Security-Reviewer scan depth + senior-review gate.

### When ambiguous
- Default UP. "Medium-but-could-be-Weak" → Weak.
- Add an ADR if a new task category emerges not in this matrix.

---

## Anti-patterns

- ❌ Treating Weak-fit tasks as Medium "because we have tests." Tests don't catch reasoning bugs about authorization.
- ❌ Treating Medium-fit tasks as Strong "because the spec is clear." Multi-file changes still drift contracts.
- ❌ Promoting from Weak to Medium without ADR.
- ❌ Letting risk tier slide DOWN over milestones ("we're good at this now"). Industry data doesn't support that; track per-milestone with G.12 retrospective.
