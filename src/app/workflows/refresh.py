"""One refresh cycle: build a candidate, compare what it would SERVE, publish or discard.

REQ-REF-001/-002. The product's claim is that it says what is true about AI tools right now, and
until this module its evidence was as fresh as the last time a human remembered to type a command.

**What this module deliberately does NOT do: build.** It calls `app.workflows.build`'s own entry
point with a temporary target and lets that code own every safety property it already has — the
unique workspace, the read-back before publish, the cleanup under `except BaseException`, the
refusal to leave a partial artifact. Reimplementing any of that here would create a second
definition of "safe to serve", and this project has spent several milestones on what happens when
one set acquires two definitions (`docs/plans/m9-plan.md` §3).

So the only new judgement here is the one the build cannot make: **is this candidate worth
publishing at all?** W1 answers the narrow half of that — did anything a user would notice change.
The half that decides whether the candidate is WORSE is W2, and it is deliberately absent rather
than half-written.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.workflows.build import main as build_main
from app.workflows.categories import CATEGORIES
from app.workflows.rank import category_ranking
from app.workflows.recommend import round_optional_score, round_score

# NOTHING IS IMPORTED FROM `app.adapter`, and that is REQ-REF-007 rather than tidiness. D-116 keeps
# ingestion off the serving host; a refresh that imports the adapter to borrow a helper has reached
# into the serving process, and the boundary would then exist only in prose. The adapter has its own
# `open_readonly`; this opens read-only with the stdlib URI form directly, which is two lines of
# `sqlite3` and not a second definition of any project behaviour.

#: Published, because something a user would notice changed.
EXIT_PUBLISHED = 0
#: Nothing a user would notice changed, so nothing was published. **A RESULT, not an error** —
#: the same shape as the recommendation CLI's exit 1 meaning "no model fits this budget". A
#: scheduler that treats this as a failure will page somebody every twelve hours for working
#: correctly, which is how an alert channel gets muted.
EXIT_UNCHANGED = 1
#: The candidate could not be built, or could not be published. The live artifact is untouched.
EXIT_FAILED = 2


@dataclass(frozen=True)
class RefreshOutcome:
    """What one cycle did, in the terms it decided on."""

    published: bool
    reason: str
    live_fingerprint: str | None
    candidate_fingerprint: str
    surfaces: int

    def as_json(self) -> str:
        return json.dumps(
            {
                "published": self.published,
                "reason": self.reason,
                "live_fingerprint": self.live_fingerprint,
                "candidate_fingerprint": self.candidate_fingerprint,
                "surfaces_answering": self.surfaces,
            }
        )


def serving_fingerprint(conn: sqlite3.Connection) -> tuple[str, int]:
    """A digest of what this artifact would SERVE, plus how many surfaces answer.

    REQ-REF-002 says "changed" is decided on served content, and every word of that is load-bearing:

    * **Not file bytes.** SQLite rewrites pages for reasons that have nothing to do with the answer;
      two byte-different files routinely serve identical results.
    * **Not timestamps.** `observed_at` moves on every single build. A fingerprint including it
      would report "changed" every twelve hours forever, which makes the comparison decorative and
      turns every cycle into a publish — the exact churn this exists to avoid.
    * **Derived through `category_ranking`**, the same function that serves, so the fingerprint
      cannot drift from what is published. A hand-written query here would be a second definition
      of "the answer".

    Scores are rounded exactly as the output boundary rounds them (D-109), because they are not
    rounded before that and float noise in the last decimal — invisible to every user — must not
    count as a change.

    **Prices are NOT rounded here, and that is a correction.** `rank.py` already rounds
    `blended_per_m` to two decimals when it builds the row, which is the precision the product
    publishes (`$8.55/1M`). Passing it through `round_score` again dropped it to ONE decimal — so a
    price moving by a cent, which a user can see on the screen, would have been fingerprinted as
    unchanged and never published. Rounding twice at different precisions is not extra safety; it
    is a second, quieter output boundary that disagrees with the real one.

    A surface with no evidence contributes its id and an empty marker rather than nothing, so a
    category GOING BLIND changes the fingerprint. That is the single most important thing a refresh
    could fail to notice, and W2's refusal rule is built on this same count.
    """
    digest = hashlib.sha256()
    answering = 0
    for name in sorted(CATEGORIES):
        spec = CATEGORIES[name]
        # NO `except sqlite3.DatabaseError: rows = []` HERE, and its absence is the point.
        #
        # The first version of this function had exactly that, meaning well: a surface whose table
        # is missing should read as empty rather than crash. What it actually did was turn a CORRUPT
        # FILE into a perfectly plausible fingerprint of "every surface empty" — so a candidate of
        # pure junk produced a valid-looking answer, compared unequal to the live one, and was
        # PUBLISHED over a working artifact. Found by this module's own test, not by review.
        #
        # A database error while asking what this artifact would serve means one thing: it cannot
        # be determined. `fingerprint_of` turns that into None, and None means do not publish. An
        # unbuilt-but-valid artifact still fingerprints fine — it simply has no rows, which raises
        # nothing.
        rows = category_ranking(conn, spec)
        digest.update(f"surface:{name}:{len(rows)}\n".encode())
        if rows:
            answering += 1
        for row in rows:
            digest.update(
                (
                    f"{row.model}|{round_score(row.score)}|"
                    f"{round_optional_score(row.secondary_score)}|"
                    f"{row.blended_per_m}|{row.harness}|{row.effort}\n"
                ).encode()
            )
    return digest.hexdigest(), answering


def fingerprint_of(path: Path) -> tuple[str, int] | None:
    """The fingerprint of an artifact on disk, or None when there is nothing readable to compare.

    None is not an error and must not be treated as one: the first refresh on a fresh machine has
    no live artifact, and that is a publish rather than a failure.
    """
    if not path.is_file():
        return None
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        # `connect` on a URI is LAZY: it succeeds against a file of random bytes and only fails when
        # something reads. So the file is made to prove it is a database before anything is asked
        # about what it would serve — otherwise "it opened" is mistaken for "it is readable", which
        # is the `stat` is not `open` finding this project already paid for once at M7.
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return serving_fingerprint(conn)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def refresh(
    target: Path,
    *,
    build_args: Sequence[str] = (),
    builder: Callable[[list[str]], int] | None = None,
) -> tuple[RefreshOutcome, int]:
    """Run one cycle against `target`. Returns the outcome and the process exit code.

    **`builder` defaults to None and is resolved HERE, not in the signature.** Writing
    `builder: Callable = build_main` binds the module attribute at DEFINITION time, so patching
    `refresh.build_main` has no effect and a test that believes it injected a fake runs the real
    build against the real network.

    This project has now found that defect four times: a `sources` default argument, the identical
    bug written into `_ingest_bundles` twenty minutes after fixing it, a `boards` parameter that
    existed and never reached its caller — and this one, written into the module whose docstring
    claimed the parameter was "read at CALL time" while the code bound it at definition time. The
    claim and the code disagreed in the same sentence. Caught by this module's own CLI tests, which
    took twelve seconds because they were running the real build.
    """
    builder = build_main if builder is None else builder
    live = fingerprint_of(target)

    # The candidate is built NEXT TO the live artifact, because publishing is an atomic rename and
    # a rename is only atomic within one filesystem. A candidate in the system temp directory would
    # publish by COPY on a machine where /tmp is a different mount, and a copy is exactly the
    # partially-written artifact every guard in `build.py` exists to prevent.
    handle, raw = tempfile.mkstemp(prefix=f"{target.name}.", suffix=".candidate", dir=target.parent)
    os.close(handle)
    candidate = Path(raw)
    candidate.unlink(missing_ok=True)  # sqlite creates it; mkstemp only reserved the name

    try:
        # The build prints its own report to stdout, and this function prints ITS outcome there
        # too — so an unattended caller reading stdout got two JSON documents concatenated and
        # could parse neither. Measured, not imagined: the first real CLI run produced
        # `JSONDecodeError: Extra data: line 115`.
        #
        # The build's report is diagnostics and belongs in the log; the refresh outcome is the
        # RESULT and belongs on stdout alone. Redirecting rather than discarding keeps both.
        with contextlib.redirect_stdout(sys.stderr):
            code = builder(["--db", str(candidate), *build_args])
        if code not in (0, 3):  # 3 = an optional source is blind and said so (D-121)
            outcome = RefreshOutcome(
                published=False,
                reason=f"the candidate could not be built (build exit {code}); "
                "the live artifact is untouched",
                live_fingerprint=live[0] if live else None,
                candidate_fingerprint="",
                surfaces=0,
            )
            return outcome, EXIT_FAILED

        fresh = fingerprint_of(candidate)
        if fresh is None:
            outcome = RefreshOutcome(
                published=False,
                reason="the candidate built but cannot be read back; the live artifact is untouched",
                live_fingerprint=live[0] if live else None,
                candidate_fingerprint="",
                surfaces=0,
            )
            return outcome, EXIT_FAILED

        if live is not None and fresh[0] == live[0]:
            return (
                RefreshOutcome(
                    published=False,
                    reason="nothing a user would notice changed",
                    live_fingerprint=live[0],
                    candidate_fingerprint=fresh[0],
                    surfaces=fresh[1],
                ),
                EXIT_UNCHANGED,
            )

        try:
            candidate.replace(target)
        except OSError as exc:
            return (
                RefreshOutcome(
                    published=False,
                    reason=f"the candidate could not be published: {exc}; "
                    "the live artifact is untouched",
                    live_fingerprint=live[0] if live else None,
                    candidate_fingerprint=fresh[0],
                    surfaces=fresh[1],
                ),
                EXIT_FAILED,
            )

        return (
            RefreshOutcome(
                published=True,
                reason="first artifact" if live is None else "the served content changed",
                live_fingerprint=live[0] if live else None,
                candidate_fingerprint=fresh[0],
                surfaces=fresh[1],
            ),
            EXIT_PUBLISHED,
        )
    finally:
        # Whatever happened, the candidate does not survive this function. It is either the live
        # artifact now or it is gone; a `.candidate` file left on disk is litter that the next
        # cycle cannot tell from a live sibling's work.
        candidate.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.workflows.refresh",
        description="Build a candidate artifact and publish it only if what is served changed.",
    )
    parser.add_argument("--db", default="advisor.db", help="the live artifact to refresh")
    parser.add_argument("--plans", help="passed through to the build")
    parser.add_argument("--rosters", help="passed through to the build")
    parser.add_argument("--epoch-dir", help="passed through to the build")
    args = parser.parse_args(argv)

    passthrough: list[str] = []
    for flag, value in (("--plans", args.plans), ("--rosters", args.rosters),
                        ("--epoch-dir", args.epoch_dir)):
        if value:
            passthrough += [flag, value]

    outcome, code = refresh(Path(args.db), build_args=passthrough)
    print(outcome.as_json())
    return code


if __name__ == "__main__":
    sys.exit(main())
