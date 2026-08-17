#!/usr/bin/env python3
"""Black-box customer-journey tester — V3C-106 (shipped in v4.1; the v3.5/v4.0 Makefile
called this file and it did not exist: Phase-0 repair, Increment 11).

Stdlib ONLY (urllib) — no requests, no pytest, no project imports. It talks to a DEPLOYED URL
exactly like a customer would: no test doubles, no internal helpers, no DB access.

QM bar (v3.5 ruling — a journey that skips these is a smoke ping, not a journey):
  1. cold entry        — an unauthenticated caller gets a correct, honest answer (not a stack trace)
  2. credential lifecycle — obtain a credential the way the SHIPPED DOCS say, then use it
  3. paying-customer round trip — the primary value action, asserting RESPONSE CONTENT, not just 200
  4. one cross-wave sequence — two features that were built in different waves, used together

Security custody (v3.5): tokens are MINTED short-TTL at run time or read from the environment.
Never store a secret in this file. Never print a token, even on failure.

Usage:
    python scripts/journey.py --base-url https://host            # all steps
    python scripts/journey.py --base-url https://host --step 3   # one step
Exit: 0 = every step PASS · 1 = any step FAIL · 2 = a step is still a TODO stub.

Wire-up: fill each `step_*` function for your product. Leave the ledger printing intact —
it is the artifact the deploy gate and every fixpack reads.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = float(os.environ.get("JOURNEY_TIMEOUT", "15"))
UA = "gp-journey/4.1 (black-box)"


class StepTodo(Exception):
    """Raised by an unfilled step: the journey is not wired yet (exit 2, never a silent pass)."""


def call(
    base: str,
    path: str,
    method: str = "GET",
    body: dict | None = None,
    token: str | None = None,
    extra_headers: dict | None = None,
) -> tuple[int, dict | str]:
    """One HTTP call. Returns (status, parsed-json-or-text). Never raises on 4xx/5xx."""
    url = urllib.parse.urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    data = json.dumps(body).encode() if body is not None else None
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    # The scheme is CHECKED rather than the warning suppressed: urllib will happily open `file:`
    # and custom schemes, and a journey pointed at a local file would "pass" against no server.
    if not url.startswith(("http://", "https://")):
        msg = f"refusing a non-HTTP base URL: {url!r}"
        raise ValueError(msg)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310
            raw = r.read().decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:  # 4xx/5xx are DATA here, not exceptions
        raw = e.read().decode("utf-8", "replace")
        status = e.code
    except Exception as e:  # network/DNS/TLS/timeout — a journey failure, not a crash
        return 0, f"{type(e).__name__}: {e}"
    try:
        return status, json.loads(raw)
    except Exception:
        return status, raw


def mint_token(base: str) -> str:
    """Return a SHORT-TTL credential obtained the way the SHIPPED DOCS describe.

    Preferred: read JOURNEY_TOKEN from the environment (CI-held, scoped, short-lived).
    Otherwise: perform the documented exchange (fill it in). NEVER hardcode a secret.
    """
    tok = os.environ.get("JOURNEY_TOKEN")
    if tok:
        return tok
    raise StepTodo(
        "credential acquisition not wired: set JOURNEY_TOKEN (CI-held, short-TTL) or implement "
        "the documented exchange here — V3C-100's human path must work from the shipped docs alone"
    )


# ─────────────────────────── the four steps (fill these) ───────────────────────────

def step_1_cold_entry(base: str) -> str:
    """Unauthenticated caller gets an honest answer. This one works out of the box."""
    status, body = call(base, "/health")
    if status != 200:
        raise AssertionError(f"/health returned {status}: {str(body)[:200]}")
    if isinstance(body, dict) and "build" in body:
        return f"/health 200, build={body.get('build')}"
    return "/health 200 (no build field — L.7 asks for one: tag/SHA in /health)"


def step_2_credential_lifecycle(base: str) -> str:
    """NOT APPLICABLE to this product, declared rather than stubbed.

    The template's step 2 mints a credential the way the shipped docs say and uses it. This
    service has no authentication surface to exercise: `/v1` is a public read-only API over
    published benchmark data (D-115), and the QM bar asks for a credential lifecycle because most
    products have one, not because a product without one may skip the question.

    So the question is ANSWERED instead of deferred: the check is that no authenticated surface
    exists to have a lifecycle. If one is ever added, this step starts failing and whoever added it
    inherits the job of wiring it — which is the opposite of a stub, and the reason this is not
    left raising StepTodo. An unwired step exits 2 forever; a wrong claim of N/A would exit 0
    forever.
    """
    status, body = call(base, "/v1/whoami")
    if status not in (404, 405):
        raise AssertionError(
            f"/v1/whoami answered {status}: an authenticated surface appears to exist, so this "
            f"step is no longer N/A and must be wired. Body: {str(body)[:160]}"
        )
    return "n/a by design — public read-only API, no credential surface (D-115)"


def _check_picks(answer: dict) -> int:
    """CONTENT: every pick carries the fields a user is shown, with usable values."""
    picks = answer.get("picks") or []
    for pick in picks:
        for field in ("label", "model", "score", "blended_per_m", "why"):
            if pick.get(field) in (None, ""):
                raise AssertionError(
                    f"{answer.get('surface')} pick {pick.get('model')!r} has no {field}; "
                    "a served answer with an empty field is not an answer"
                )
        if not isinstance(pick.get("score"), (int, float)):
            raise AssertionError(f"score is {pick.get('score')!r}, not a number")
    return len(picks)


def step_3_paying_customer_round_trip(base: str) -> str:
    """The primary value action, asserting CONTENT: a real recommendation with real picks.

    Status 200 is not the check. M6 shipped an artifact that answered 200 with ZERO picks for every
    query while `/health` reported a healthy build (W-023), and Stage 4.3 verifies deploys with
    `/health` — so a journey that stopped at status codes would have called that deploy good.
    """
    status, body = call(base, "/v1/recommendations?task=coding&budget=unlimited")
    if status != 200:
        raise AssertionError(f"/v1/recommendations returned {status}: {str(body)[:200]}")
    if not isinstance(body, dict):
        raise AssertionError(f"expected a JSON object, got {type(body).__name__}")

    answers = body.get("answers") or []
    if len(answers) != 2:
        raise AssertionError(
            f"a coding request must return BOTH coding surfaces (owner Ruling A, D-115); got "
            f"{len(answers)}: {[a.get('surface') for a in answers]}"
        )
    surfaces = sorted(a.get("surface") for a in answers)
    if surfaces != ["agentic-coding", "coding"]:
        raise AssertionError(f"unexpected surfaces: {surfaces}")

    total = sum(_check_picks(a) for a in answers)
    if total == 0:
        raise AssertionError(
            "every surface answered with ZERO picks. This is exactly W-023's shape: a deploy that "
            "looks healthy and cannot answer. Rebuild the artifact with `app.workflows.build`"
        )

    # Nothing may rank one coding surface above the other (Ruling A frozen by D-115).
    banned = {"primary", "primary_surface", "top_pick", "display_order", "rank", "suggested"}
    for answer in answers:
        present = banned & set(answer)
        if present:
            raise AssertionError(f"a precedence field reached the payload: {sorted(present)}")

    return f"{total} picks across both coding surfaces, all fields populated, no precedence field"


def step_4_cross_wave_sequence(base: str) -> str:
    """Two features from different waves, used together — discovery then recommendation.

    `/v1/categories` (M6-W1) publishes what may be asked for; `/v1/recommendations` (M6-W1, its
    engine reworked in M7-W2/W3) answers it. The seam is that the discovery surface must not name
    a task the answering surface rejects, which no single-endpoint test can see.
    """
    status, body = call(base, "/v1/categories")
    if status != 200:
        raise AssertionError(f"/v1/categories returned {status}: {str(body)[:200]}")
    ids = [c.get("id") for c in (body.get("categories") or [])] if isinstance(body, dict) else []
    if not ids:
        raise AssertionError(f"/v1/categories published no categories: {str(body)[:200]}")

    checked = []
    for task in ids:
        code, payload = call(base, f"/v1/recommendations?task={task}&budget=unlimited")
        if code != 200:
            raise AssertionError(
                f"discovery published task {task!r}, but asking for it returned {code} — the two "
                f"surfaces disagree about what exists: {str(payload)[:160]}"
            )
        answers = payload.get("answers") or [] if isinstance(payload, dict) else []
        if not answers:
            raise AssertionError(f"task {task!r} returned no answer object at all")
        # A surface with nothing to say must SAY so rather than return a bare empty list.
        for answer in answers:
            if not answer.get("picks") and not answer.get("unavailable_reason"):
                raise AssertionError(
                    f"{answer.get('surface')} returned an empty answer with no reason; silence is "
                    "the one answer this product may not give"
                )
        checked.append(task)

    return f"discovery published {len(ids)} tasks and every one answers: {', '.join(checked)}"


STEPS = [
    ("cold entry (unauthenticated, honest answer)", step_1_cold_entry),
    ("credential lifecycle (docs-driven, short-TTL)", step_2_credential_lifecycle),
    ("paying-customer round trip (asserts CONTENT)", step_3_paying_customer_round_trip),
    ("cross-wave sequence (two waves, used together)", step_4_cross_wave_sequence),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Black-box customer journey (V3C-106)")
    ap.add_argument("--base-url", required=True, help="deployed base URL, e.g. https://host")
    ap.add_argument("--step", type=int, default=0, help="run only step N (1-based)")
    args = ap.parse_args()

    base = args.base_url
    selected = [(i, n, f) for i, (n, f) in enumerate(STEPS, 1) if args.step in (0, i)]
    if not selected:
        print(f"no such step: {args.step}", file=sys.stderr)
        return 1

    print(f"JOURNEY {base}  ({len(selected)} step(s), timeout {TIMEOUT}s)")
    print("-" * 72)
    failed = todo = 0
    for idx, name, fn in selected:
        t0 = time.time()
        try:
            detail = fn(base)
            print(f"  PASS  {idx}. {name}  [{time.time()-t0:.2f}s] — {detail}")
        except StepTodo as e:
            todo += 1
            print(f"  TODO  {idx}. {name} — {e}")
        except Exception as e:  # AssertionError and anything the product did to us
            failed += 1
            print(f"  FAIL  {idx}. {name}  [{time.time()-t0:.2f}s] — {type(e).__name__}: {e}")
    print("-" * 72)
    print(f"JOURNEY {'FAIL' if failed else ('INCOMPLETE' if todo else 'PASS')}: "
          f"{len(selected)-failed-todo} pass, {failed} fail, {todo} unwired")
    if failed:
        return 1
    if todo:
        print("Unwired steps are exit 2 BY DESIGN — an unfilled journey must never report success.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
