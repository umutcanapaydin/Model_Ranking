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
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
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
    token = mint_token(base)  # raises StepTodo until wired
    status, body = call(base, "/v1/whoami", token=token)
    if status != 200:
        raise AssertionError(f"authenticated call returned {status} (token redacted): {str(body)[:200]}")
    return "credential accepted on an authenticated route"


def step_3_paying_customer_round_trip(base: str) -> str:
    raise StepTodo(
        "primary value action not wired: perform the real round trip and ASSERT CONTENT "
        "(the field/value a paying customer receives), not merely status 200"
    )


def step_4_cross_wave_sequence(base: str) -> str:
    raise StepTodo(
        "cross-wave sequence not wired: use two features built in DIFFERENT waves together — "
        "the seam is where boundary defects live (Increment 9: 100% of escaped defects)"
    )


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
