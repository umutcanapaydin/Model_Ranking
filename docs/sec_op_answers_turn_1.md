---
record_type: review
id: sec-op-answers-turn-1
status: draft
date: 2026-09-05
---
# Second-opinion answers — turn 1

## 0. Scope and method

This review was performed in the order requested by the owner:

1. Read `docs/handovers/handover_m13-start.md`.
2. Independently inspect the production Python engine, ingestion and refresh workflows, API,
   operational scripts, Swift engine, iOS application, tests, and build configuration.
3. Run the repository quality gate and compile the real iOS Simulator target.
4. Read `docs/second-opinion.md` only after the independent inspection was complete.

No product code was changed during the review.

The repository is unusually disciplined about one essential principle: it should never present an
unmeasured claim as measured. The architecture mostly enforces that separation: the router chooses
the question/surface, while the deterministic engine owns every score, price, and recommendation.

Verification results:

- `make check`: 785 Python tests passed and 12 conditional contract tests were skipped.
- Python coverage: 88.44%.
- Swift package tests: 132 passed, above the floor of 121.
- The real `ModelRanking` iOS Simulator target compiled successfully with code signing disabled.
- The Python test run emitted 150 warnings, many of them for unclosed SQLite connections.

## 1. Answers to the M13-blocking questions

### Q1 — What replaces the native metric label on a card?

Use `Score 83.5 / 100` only where the source metric has a real, defensible ceiling of 100. Retain a
short plain-language explanation underneath. For metrics without an honest ceiling, such as ECI,
show rank and the metric context rather than inventing a denominator or printing a bare cross-surface
`Score 161.7`.

A bare `Score N` is not acceptable. It invites comparison between numbers that are not on a common
scale. Rank alone is also insufficient everywhere because it hides the difference between a real
gap and a saturated or effectively tied board.

Recommended display rules:

- Bounded percentage metric: `Score 83.5 / 100`.
- Elo: retain the scale name or show rank plus an explanation; do not present it as a percentage.
- ECI: show rank and an ECI-specific explanation, with no invented maximum.
- Close/tied results: display a shared band or tie indication rather than overstating ordinal rank.

### Q2 — Is one cross-surface score defensible?

No. One readable score per surface is defensible; one universal model score across all nine surfaces
is not. The matrices are too sparse, the metrics are not commensurable, and Arena human preference
is a separate axis. A composite would conceal distinctions that the product currently measures
honestly.

### Q3 — What happens when the requested capability is unmeasured?

Always showing the closest measured list is acceptable only if the limitation is impossible to miss.
The screen should explicitly say what is not measured, identify which measured ranking is being
shown instead, and describe it as a starting point rather than the answer to the original question.

Recommended behavior:

- Show the nearest measured ranking.
- Put the limitation immediately above the results.
- Show the chosen surface and provide a one-tap correction.
- Offer an optional `Ask us to add this capability` action that returns a visible receipt.
- Never silently turn a request for image editing, translation, or another uncovered task into a
  confident general-assistant recommendation.

The current manual fallback needs correction. When both routing tiers decline, `TieredRouter`
returns the assistant category with `tier = manual` and `unmeasured = false`. `ContentView.ask()`
then automatically selects and loads that category, while the explanation says `Pick a surface
below.` The words, state, and action disagree.

### Q4 — What should happen to the budget strip?

Remove the strip from the primary interface. Keep price as a first-class piece of evidence on every
card, keep the best-value concept, and retain `/v1/budgets` for compatibility and non-iOS clients.

With no explicit budget selection, rename `Budget Pick` to something that does not imply the reader
set a budget, for example:

- `Affordable pick`
- `Best low-cost option`
- `Lowest-cost strong option`

The default request can continue to use `budget=unlimited`, allowing the engine to show best quality,
best value, and an affordable alternative without forcing the reader to configure a cap first.

If the input bar is eventually expected to understand phrases such as `cheap`, `under $2`, or `my
budget is $20/month`, the router may extract a structured constraint such as `{surface, budget}`.
That interpretation must be displayed as an editable chip before or with the results. The language
model may interpret the constraint, but the deterministic engine must continue to compute the actual
ranking.

### Q5 — Where should tapping a model go?

Open an in-app model detail screen first. Put the official vendor URL on that screen as a secondary
action. Do not navigate directly to a URL selected by a crawler.

The detail screen can use information already present in the payload but currently underused by the
client: benchmark, harness, effort, higher-effort result, evidence date, confidence basis, input and
output prices, and source attribution.

Official links should be accepted only through a small, versioned vendor-origin allowlist enforced
by the client. Hand-maintaining the missing official URLs for the catalogue's eleven vendors is
preferable to trusting reseller or crawler-discovered domains.

### Q6 — What should be extended first?

Repair freshness metadata first, then add `image_edit` in the same wave if the scope remains small.
The existing LMArena client and licence make image editing a practical next surface, but the product
must not force per-image pricing into the existing per-million-token schema.

If image pricing is not ready, an unpriced image surface is acceptable only when the UI explicitly
says price comparisons are unavailable and does not show Best Value or an affordable pick for that
surface. The better long-term solution is a typed pricing model supporting token, image, audio, or
other modality-specific units.

## 2. Answers to the remaining product questions

### Routing tiers

Treat `SimilarityRouter` as the baseline shipping product and `ModelRouter` as an enhancement. The
iOS 18 deployment target includes many devices that can never run Apple Intelligence. Raising the
deployment target or excluding those devices would shrink the addressable base without fixing the
core experience.

Show the model tier's unavailable reason only as concise diagnostic/help information, not as an
error that blocks the user. The similarity route still works.

### Demand logging and privacy

Do not transmit raw questions merely to count demand. If aggregate telemetry is approved, submit
only a coarse surface/capability identifier and an `unmeasured` flag, with a clearly defined privacy
contract. An explicit user action such as `Ask us to add image editing` is even easier to explain
than passive logging.

### Aider and confidence

Do not describe two available benchmarks as statistical `High confidence`. Rename the field to
coverage/evidence breadth, for example `Measured on two independent benchmarks`. A 332-day-old
secondary benchmark should either carry its age next to that statement or stop upgrading the label.

### Ranking noise and ties

Use the existing close-call thresholds to form visible tie/near-tie bands. Do not print `#1 of 50`
when the product's own threshold says twenty-five models are statistically indistinguishable from
the leader. Preserve the native evidence internally and make the uncertainty visible at the output
boundary.

### Keyboard and layout defects

Treat the question field, keyboard, missing submit affordance, and bottom-search overlap as immediate
M13 work. The question field is the proposed front door, so it cannot remain a secondary fixpack.
Add explicit focus state, a visible send button, and device/simulator verification of both hardware
and software keyboard paths.

### Tier explanation

Show the reader's question and the selected surface, for example:

`"prove a theorem" -> Mathematics`

Keep a short tier disclosure alongside it only when useful. The primary information is what the app
understood and how the user can correct it, not where the routing computation ran.

## 3. Independent code-review findings

These findings were identified before reading `docs/second-opinion.md`.

### P1 — Pareto dominance is implemented incorrectly in both engines

`recommend.py::pareto_frontier` and `subscribe.py::_pareto` remove a row only when another row has
both a strictly higher score and a strictly lower price. Correct Pareto dominance permits equality
on one dimension, provided the other is strictly better.

Consequences:

- Equal score and lower price: the more expensive row incorrectly remains on the frontier.
- Equal price and higher score: the lower-quality row incorrectly remains on the frontier.
- Value selection and reported `frontier_size` can therefore be wrong.

This was reproduced through the production functions. Both dominated rows remained in their
respective frontiers.

Recommended predicate: another row dominates when its score is greater than or equal and its cost
is less than or equal, with at least one of those comparisons strict.

### P1 — Startup validation can approve a database the serving path cannot read

`adapter/main.py::_database_unusable` checks `scores`, `pricing`, an `effort` column, and a non-empty
`px_median`. It does not validate all tables and columns subsequently read by category ranking,
including `models`.

A deliberately constructed SQLite database with the checked objects but no `models` table returned
`None` from `_database_unusable`, meaning `usable`. A production process could therefore pass the
startup probe and later convert database errors into per-surface unavailable answers.

Recommended fix: derive and validate the complete serving schema, or perform a representative
read-only query for every advertised category during startup.

### P1 — iOS loads can complete out of order

Budget and category buttons launch independent `Task { await load() }` operations. `load()` has no
cancellation, generation counter, or request identity. A slower response for the previous selection
can arrive last and overwrite the state for the current selection.

Recommended fix: keep one cancellable load task and cancel it before starting another, or capture
the requested `(task, budget)` and discard a response unless it still matches current state.

### P1 — Manual routing state contradicts the action taken

When both routers decline, the result says `manual` but carries the assistant category. The view
automatically changes to that category and loads it, while the explanation asks the reader to choose
a surface. Either manual must preserve the current selection and wait for a tap, or this outcome is
an unmeasured assistant fallback and must be labelled as such.

### P2 — Refresh fingerprint ignores a user-visible attribution change

`refresh.py::UNHASHED_ROW_FIELDS` excludes `evidence_source`. However recommendation `sources` are
derived from the ranked rows' evidence sources. Changing the evidence source alone can therefore
change user-visible attribution without changing the refresh fingerprint, causing the updated
artifact not to be published.

This was reproduced by changing only `evidence_source`; `_row_digest` remained identical.

### P2 — CORS origin validation accepts full URLs

The validator checks only whether a string begins with `http://` or `https://`. It accepts values
with paths, queries, fragments, or credentials even though those are not origins. Parse the value
and require scheme plus host and optional port, with empty path, query, fragment, and user info.

### P2 — Numeric environment limits are not consistently validated

Concurrency uses `_positive_env`, while maximum ranked-row limits call `int(...)` directly at module
import. A malformed value raises a raw `ValueError`; zero or negative values also bypass the clearer
configuration contract. All positive integer environment variables should use the same validator.

### P2 — Refresh lock errors can be misreported as contention

`refresh.py::_hold_lock` catches every `OSError` from `flock` and reports `busy`. Only `EAGAIN` or
`EWOULDBLOCK` means another process owns the lock. Permission, descriptor, or I/O failures should be
reported as failed cycles.

### P2 — Status recovery assumes valid JSON is an object

`write_status` suppresses JSON and file errors but then calls `.get()` on the loaded value. A valid
JSON list or scalar can crash status writing, including the attempt to record the original failure.
Validate `isinstance(previous, dict)` before reading counters.

### P2 — Source parsers lack consistent finite/range checks

Several parsers accept positive infinity as a price or score because they check only `> 0` or call
`float(...)`. Score sources also do not consistently enforce finite values and metric-specific
ranges. A non-finite upstream value can poison ranking, serialization, and refresh decisions.

### P2 — The runner can report important skips as passes

When the Epoch bundle or running engine is absent, `runner` records those sections as success. An
absent Xcode also records the iOS build as success, while absent Swift records no Swift result. The
final `ALL PASS` can therefore mean major legs were not executed.

Use an explicit `SKIPPED/NO-ENVIRONMENT` state and prevent the full green claim when required owner
evidence is missing.

### P3 — Same-host redirects do not preserve scheme or port

`SameHostOnly` compares only the host. A redirect to another port or a downgrade from HTTPS to HTTP
on the same host is accepted. Compare a normalized origin: scheme, host, and effective port.

### P3 — Unknown trade-off shapes become a confident generic sentence

`tradeOffSentence` returns `at a lower price` for any fact that lacks the known percent, times, or
`same` forms. An unknown future value of `cheaper`, or a missing price relationship, should return
`nil` rather than silently composing a claim the client did not understand.

### P3 — Health checks can be green while evidence is unavailable

The adapter's `/health` response can remain HTTP 200 while reporting unavailable evidence. The
Docker/Fly health checks inspect status only. If those deployment proposals are adopted, platform
health should distinguish process liveness from evidence readiness.

## 4. Refresh and deployment state

The installed launchd service is `com.hcs.modelranking.refresh`. It reports:

- state: not running;
- runs: 10;
- last exit: `78: EX_CONFIG`;
- refresh stdout/stderr files last modified on 2026-08-27;
- last durable refresh record: a successful publish on 2026-08-27.

The configured Python executable, repository directory, Epoch bundle directory, and log files all
exist now. Therefore a missing virtual environment is not the explanation. A Desktop/TCC spawn
restriction remains a plausible leading hypothesis, but it has not been proven from unified logs.
The separate D-128 price-change refusal remains relevant after the spawn problem is fixed.

The iOS Simulator build works, but this does not close device readiness:

- no development team is configured for signing;
- the client defaults to `http://127.0.0.1:8080`, which points to the phone itself on a device;
- no production engine is deployed;
- transport, privacy manifest, and real-device Apple Intelligence states remain unverified.

## 5. Recommended product interface

### Principle

The home screen should be a question-first experience, not a control panel. A reader should open the
app, describe the job, see what the app understood, and receive the measured ranking. Categories and
budgets should not compete with the primary input.

### Proposed home screen

```text
+----------------------------------+
| Model Ranking                 TR |
|                                  |
| What do you need a model for?    |
| +----------------------------+-> |
| | Improve my profile photo   |   |
| +----------------------------+   |
|                                  |
| Matched surface: General chat    |
| We do not rank image models yet. |
| This is the closest measured     |
| list, not an image-edit answer.  |
|                           Change |
|                                  |
| BEST QUALITY                     |
| +------------------------------+ |
| | Claude ...  Score 83.5 / 100 | |
| +------------------------------+ |
|                                  |
| BEST VALUE                       |
| +------------------------------+ |
| | Gemini ...  23x less costly  | |
| +------------------------------+ |
+----------------------------------+
```

### Remove both top strips

Remove the horizontal category strip and the budget strip from the top of the screen. The category
strip looks crowded, truncates choices, and makes the user learn the internal taxonomy before using
the product.

Categories should remain available through:

- `Matched surface: Mathematics` beside the routing result;
- a small `Change` button;
- an optional `Browse categories` link near the bottom of the home screen.

`Change` should open a bottom sheet with a clean two-column grid rather than another horizontal
scroll strip. Each item should use a human-facing title and, where useful, a restrained icon.

### Make the question bar the visual centre

The primary input should:

- support one or two visible lines;
- have a clear send button;
- use explicit `FocusState`;
- submit from both Return and the button;
- replace the send icon with progress while routing;
- disable duplicate submissions;
- retain and echo the question above the results;
- show the selected surface and one-tap alternatives.

For example:

`"Optimize my SQL query" -> Coding    Change`

If confidence in routing is low, show two nearby surfaces rather than only a warning:

`Did you mean: Coding | Web development?`

### Move model-name search away from the home screen

Remove the bottom `.searchable` model filter from the home screen. Two text inputs make the routing
bar look secondary, and the current bottom search overlaps content. Put model-name/vendor search
only on the full-ranking screen reached through `See all models`.

### Cards

Keep the first-level cards concise:

- model and vendor;
- bounded score or honest rank;
- price;
- one sentence explaining why it was selected;
- evidence breadth such as `Measured on two benchmarks`.

Move harness, effort, evidence date, detailed source attribution, price components, and confidence
basis to the model detail screen.

### Suggested implementation order

1. Make the question field reliably focusable and add a visible submit button.
2. Remove the top category and budget strips.
3. Add the matched-surface row and `Change` bottom sheet.
4. Move model filtering to the full-ranking screen.
5. Add cancellation/request identity to the loading state.
6. Correct manual and unmeasured fallback semantics.
7. Fix Pareto dominance before presenting the redesigned cards as final recommendations.
8. Add the model detail screen and allowlisted official links.
9. Repair missing freshness dates and add the image-edit surface with typed pricing semantics.

## 6. Bottom line

The product should not open by asking the reader to choose among nine categories and three price
tiers. It should open with one prominent question field. The system should visibly state what it
understood, show only rankings the engine actually measured, and let the reader correct the selected
surface in one tap.

Price should remain visible because the quality-versus-cost trade-off is the product's clearest
differentiator. Removing the budget control is simplification; hiding price would remove the reason
to use the product.

Before M13 treats the interface as finished, the Pareto error, startup schema validation hole, iOS
request race, manual-fallback contradiction, and refresh attribution fingerprint should be fixed and
covered by regression tests.
