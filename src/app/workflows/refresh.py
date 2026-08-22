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
import datetime as dt
import fcntl
import hashlib
import json
import os
import sqlite3
import statistics
import sys
import tempfile
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from app.workflows.build import main as build_main
from app.workflows.categories import CATEGORIES
from app.workflows.rank import category_ranking
from app.workflows.recommend import BUDGETS, eligible_rows, round_optional_score, round_score

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
#: Another cycle holds the lock. Nothing was attempted and nothing is wrong — a scheduler firing
#: while the previous run is still going is ordinary, and it must not read as a failure or it will
#: page somebody for working correctly.
EXIT_BUSY = 4
#: The candidate built fine and is WORSE than what is being served, so it was refused (D-128).
#: A first-class outcome and not an error: nothing is broken, and the right response is to look at
#: the upstream rather than at this process.
EXIT_REFUSED = 3


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


#: D-128. A surface losing MORE than this fraction of its ranked models is damage, not churn.
#:
#: Not zero, and the reason matters more than the number: boards drop models constantly, so
#: "refuse on any loss" would refuse nearly every real refresh and freeze the product at whatever
#: artifact happened to be current — while every gate reported healthy and every cycle exited
#: cleanly. **That failure looks exactly like success**, which is why it is the one to fear. A
#: refusal is recoverable by waiting; a freeze is only recoverable by someone noticing.
#:
#: A quarter is a judgement recorded as one. The smallest surface ships 13 models, so it trips at
#: three — above routine churn, below anything a real outage could hide behind.
MAX_SURFACE_LOSS = 0.25


#: D-132. How much of a surface's roster may be NEW, and how far its median price may move, before
#: a human has to look. Both are a quarter, deliberately the same figure as D-128's shrinkage
#: limit: the rule a reader can hold in their head is that **a surface may not change by more than
#: a quarter in either direction without somebody looking.**
#:
#: ORDINARY MOVEMENT, MEASURED — the sentence D-128 lacked and had to be corrected for. Between two
#: consecutive builds against live sources on 2026-08-22: **0% new names on all nine surfaces, and
#: 0.0% median price movement on all nine.** Rosters are stable; individual prices move without
#: shifting a median. So a quarter is not a tight threshold being defended, it is a wide one that
#: ordinary movement does not come close to — which is the right shape, because the failure to fear
#: is the product freezing while every check reports healthy.
MAX_SURFACE_GAIN = 0.25
MAX_MEDIAN_PRICE_MOVE = 0.25


def upward_anomalies(live: ServingSummary, candidate: ServingSummary) -> list[str]:
    """Ways the candidate is implausibly BETTER. Empty means nothing suspicious.

    W-049, and it is the failure the refresh CREATED rather than one it exposed. Every other
    automated defence on served content is a shrinkage detector — the `minimum_rows` floors, and
    every axis of D-128. All of them exempt gains, on the reasoning that a model getting worse is
    news rather than damage. **The inverse had no guard at all**, so an upstream that added
    fabricated high-rated models, or dropped prices, produced a larger and cheaper artifact that
    every check called healthy and that shipped to readers twice a day.

    Under the owner's ruling of 2026-08-22 the outcome is always REFUSE. This function never
    decides that something is fine on balance; it reports what looks wrong and the cycle stops.
    """
    reasons: list[str] = []

    for name, was in sorted(live.models.items()):
        now = candidate.models.get(name, frozenset())
        if not now:
            continue  # a surface losing everything is `degradations`' business, not this one
        if not was:
            # It was blind and now answers. That is a surface RETURNING — exactly what happened
            # when arena came back and `assistant` went from nothing to 65 models — and refusing it
            # would freeze the product for the one event everybody wants.
            continue
        fresh = now - was
        if len(fresh) > len(now) * MAX_SURFACE_GAIN:
            reasons.append(
                f"{name} would be {len(fresh)} of {len(now)} models this artifact has never seen "
                f"({len(fresh) / len(now):.0%}, over the {MAX_SURFACE_GAIN:.0%} limit); a board "
                "adds models one or two at a time"
            )

    for name, before in sorted(live.median_price.items()):
        after = candidate.median_price.get(name, 0.0)
        if before <= 0 or after <= 0:
            continue
        move = abs(after - before) / before
        if move > MAX_MEDIAN_PRICE_MOVE:
            direction = "down" if after < before else "up"
            reasons.append(
                f"{name}'s median price would move {direction} {move:.0%} "
                f"(${before:.2f} to ${after:.2f}, over the {MAX_MEDIAN_PRICE_MOVE:.0%} limit); one "
                "provider changing a price does not move a surface's median"
            )

    return reasons


def degradations(live: ServingSummary, candidate: ServingSummary) -> list[str]:
    """Every way the candidate would be WORSE than what is being served. Empty means it is safe.

    Reasons are returned rather than a boolean, because the operator's first question on a refusal
    is always "worse how", and a rule that cannot answer that gets disabled the second time it
    fires.

    Deliberately NOT degradations: a surface gaining models, prices moving either way, scores
    falling. **A model getting worse is news, not damage** — reporting what the measurements say is
    the product, and refusing to publish a decline would be worse than publishing it.
    """
    reasons: list[str] = []
    for name, was in sorted(live.surfaces.items()):
        now = candidate.surfaces.get(name, 0)
        if was and not now:
            reasons.append(f"{name} answered with {was} models and would now answer nothing")
        elif was and now <= was * (1 - MAX_SURFACE_LOSS):
            lost = was - now
            reasons.append(
                f"{name} would lose {lost} of {was} models "
                f"({lost / was:.0%}, at or over the {MAX_SURFACE_LOSS:.0%} limit)"
            )

    # The budget axis. A surface that answered a reader on some budget and would now answer nothing
    # is "fewer surfaces answering" in the only sense a reader experiences — REQ-REF-003's own
    # words — and it is invisible to every row count, because the rows are all still there and
    # merely unaffordable.
    for name, budgets in sorted(live.eligible.items()):
        after = candidate.eligible.get(name, {})
        for budget, was_eligible in sorted(budgets.items()):
            if was_eligible and not after.get(budget, 0):
                reasons.append(
                    f"{name} offered {was_eligible} models at the {budget} budget "
                    "and would now offer none"
                )
    return reasons


#: Fields of a ranked row that are DELIBERATELY outside the fingerprint, each with its reason.
#:
#: The set is an exclusion list rather than an inclusion list, and the direction is the point: a
#: field added to `RankingRow` is hashed by DEFAULT and has to be excluded on purpose. An inclusion
#: list fails the other way — a new published field silently falls out of the comparison, which is
#: exactly what happened. An independent review measured the cost: `evidence_date`, `vendor`,
#: `input_per_m` and `output_per_m` were all published to users and none was hashed, so **the same
#: scores republished with FRESH EVALUATION DATES read as "nothing a user would notice changed"**.
#: The refresh was structurally incapable of publishing a freshness improvement, which inverts this
#: milestone's entire purpose.
#: MEASURED, not guessed: these two are the only fields of a ranked row that appear in neither
#: `PUBLIC_RANKING_FIELDS` nor `PUBLIC_PICK_FIELDS`, so no reader can see them on any surface and a
#: change to one must not swap what everybody else sees. `higher_effort` and `higher_effort_score`
#: are deliberately NOT here — they are absent from a ranking row and present on a PICK, which is
#: still somewhere a reader looks.
UNHASHED_ROW_FIELDS = {
    "evidence_source",
    "secondary_cost",
}


def _row_digest(row: object) -> str:
    """One ranked row, as the reader would receive it.

    Scores are rounded exactly as the output boundary rounds them (D-109); prices are NOT, because
    `rank.py` already rounds them to the two decimals the product prints and re-rounding here to one
    would mask a visible one-cent move.
    """
    parts: list[str] = []
    for field in fields(row):  # type: ignore[arg-type]
        if field.name in UNHASHED_ROW_FIELDS:
            continue
        value = getattr(row, field.name)
        if field.name == "score":
            value = round_score(value)
        elif field.name == "secondary_score":
            value = round_optional_score(value)
        elif field.name in ("input_per_m", "output_per_m"):
            # `rank.py:311` rounds `blended_per_m` to two decimals and leaves these two RAW, so a
            # median carrying float noise in its ninth decimal would otherwise read as a change
            # nobody can see. Two decimals, matching the precision the product prints prices at —
            # and NOT one, which would mask a visible cent (the mistake this fingerprint already
            # made once with the blended price).
            value = round(value, 2)
        parts.append(f"{field.name}={value}")
    return "|".join(parts) + "\n"


@dataclass(frozen=True)
class ServingSummary:
    """What an artifact would serve: one digest, and the size of every surface behind it.

    The digest answers "did anything change". The per-surface counts answer "did it get WORSE",
    which is a different question and the one D-128 is about. They are produced together, from one
    pass, so the two can never describe different artifacts.
    """

    digest: str
    surfaces: dict[str, int]
    #: surface -> the NAMES it ranks. Counts cannot see a roster that was replaced rather than
    #: resized, and names are what tells a new model from a fabricated one: a real board adds one
    #: or two at a time, and an injected set arrives together.
    models: dict[str, frozenset[str]]
    #: surface -> the median published price. One provider cutting a price is news; a whole
    #: surface's median moving is a feed, and a feed is what an attacker or a bug controls.
    median_price: dict[str, float]
    #: surface -> budget -> how many models a reader on that budget could actually be offered.
    #:
    #: Row counts alone cannot see the failure that matters most here. `BUDGETS` is a HARD FILTER
    #: applied before any scoring (REQ-REC-002), so a pricing feed that multiplies every price
    #: leaves every surface exactly the same SIZE while `low` and `medium` answer nothing at all,
    #: on all nine surfaces. An independent review landed that on the product and the guard did not
    #: object. D-128 had reasoned that "prices moving in either direction" is not damage because a
    #: price is a reported number — true of the score, false of the price, because the price is
    #: also a filter.
    eligible: dict[str, dict[str, int]]

    @property
    def answering(self) -> int:
        return sum(1 for count in self.surfaces.values() if count)


def serving_summary(conn: sqlite3.Connection) -> ServingSummary:
    """A digest of what this artifact would SERVE, and how many models stand behind each surface.

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
    surfaces: dict[str, int] = {}
    eligible: dict[str, dict[str, int]] = {}
    names: dict[str, frozenset[str]] = {}
    prices: dict[str, float] = {}
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
        surfaces[name] = len(rows)
        eligible[name] = {b: len(eligible_rows(rows, b)) for b in sorted(BUDGETS)}
        names[name] = frozenset(row.model for row in rows)
        prices[name] = statistics.median([row.blended_per_m for row in rows]) if rows else 0.0
        for row in rows:
            digest.update(_row_digest(row).encode())
    return ServingSummary(
        digest=digest.hexdigest(),
        surfaces=surfaces,
        models=names,
        median_price=prices,
        eligible=eligible,
    )


class UnreadableArtifact(Exception):
    """The artifact is THERE and cannot be read.

    B2, found by a Stage-4.0 security review after a wave review had raised it and it went unfixed:
    `fingerprint_of` returned `None` for three different facts — no artifact, not a database, and
    any error while reading — and `_cycle` treated all three as "first artifact". So the degradation
    guard and the pre-publish baseline check were both SKIPPED and the candidate published
    unconditionally, including one that blinded every surface. The record then said `first
    artifact`, which was untrue.

    A missing artifact is a reason to publish. An unreadable one is a reason to refuse: **if you
    cannot fingerprint what you would replace, you cannot claim the replacement is not worse.**
    """


def fingerprint_of(path: Path) -> ServingSummary | None:
    """The fingerprint of an artifact on disk, or None when there is nothing readable to compare.

    None is not an error and must not be treated as one: the first refresh on a fresh machine has
    no live artifact, and that is a publish rather than a failure.
    """
    if not path.is_file():
        return None  # nothing to compare against; the caller publishes
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise UnreadableArtifact(str(exc)) from exc
    try:
        # `connect` on a URI is LAZY: it succeeds against a file of random bytes and only fails when
        # something reads. So the file is made to prove it is a database before anything is asked
        # about what it would serve — otherwise "it opened" is mistaken for "it is readable", which
        # is the `stat` is not `open` finding this project already paid for once at M7.
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return serving_summary(conn)
    except sqlite3.Error as exc:
        raise UnreadableArtifact(str(exc)) from exc
    finally:
        conn.close()


def lock_path(target: Path) -> Path:
    return target.with_name(target.name + ".refresh.lock")


@contextlib.contextmanager
def _hold_lock(target: Path) -> Iterator[bool]:
    """Hold an exclusive lock for one cycle, or yield False if another cycle holds it.

    **`flock`, and the choice removes a class of bug rather than patching one.** The first version
    used `O_CREAT|O_EXCL` plus a pid file plus a staleness age, and a Stage-4.0 security review
    demonstrated that scheme failing in three ways at once: the age rule was joined with `or`, so a
    lock past two hours was reclaimed **from a holder the pid check had just proved alive**; the age
    was measured from acquisition and never refreshed, so any cycle outliving it lost its own lock;
    and release was by PATH with no ownership check, so an evicted cycle deleted the NEW holder's
    lock on the way out, cascading. The comment beside it said the age rule was "the fallback for
    the case the pid cannot answer" — the code applied it unconditionally. That is the
    claim-disagrees-with-code defect this module had already fixed twice in the same milestone.

    Every one of those bugs exists only because the first scheme had to decide, in userspace, when
    a lock was abandoned. `flock` does not: the kernel releases it when the holding process dies,
    for any reason, including SIGKILL and a power cut. So there is no staleness rule to get wrong,
    no pid to parse (and no `OverflowError` from parsing one), and no reclaim path to race.

    The file is deliberately NOT unlinked on release. Unlinking a lock file is its own race — a
    second holder can be waiting on the inode you are about to remove — and an empty lock file
    costs nothing.
    """
    path = lock_path(target)
    handle = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            # Held by someone else. The loser does not WAIT — waiting turns a scheduler into a
            # queue — it reports BUSY and lets the next trigger try.
            yield False
            return
        os.truncate(handle, 0)
        os.write(handle, f"{os.getpid()}\n".encode())
        yield True
    finally:
        os.close(handle)  # releases the flock


def status_path(target: Path) -> Path:
    """Where a cycle records what it did, beside the artifact it was refreshing."""
    return target.with_name(target.name + ".refresh.json")


def write_status(target: Path, outcome: RefreshOutcome, code: int, *, at: float) -> Path:
    """Record this cycle. REQ-REF-004.

    Written on EVERY path, including failures and refusals — especially those. A record that only
    exists when things went well cannot distinguish "nothing needed doing" from "this stopped
    running three days ago", and that distinction is the whole point of keeping one (D-129).

    Written to a temp file and renamed, for the same reason the artifact is: a reader that catches
    this mid-write would see truncated JSON and conclude the refresh is broken, which is the
    opposite of what the record is for.
    """
    path = status_path(target)

    # W-046: the record was DEPTH-1, so cycle N+1 erased cycle N and the file could not represent
    # "two refusals in a row" — the exact state the plan's §5.2 says the product must not sit in
    # quietly. Rewriting history is not the answer; carrying two counters forward is. A transient
    # refusal also used to vanish within twelve hours, so an owner reading `runner` the next day
    # saw `published` and never learned a refusal had happened.
    previous: dict[str, object] = {}
    with contextlib.suppress(OSError, ValueError):
        previous = json.loads(path.read_text(encoding="utf-8"))

    refused_before = previous.get("consecutive_refusals", 0)
    carried = int(refused_before) if isinstance(refused_before, int) else 0
    if code == EXIT_REFUSED:
        consecutive = carried + 1
    elif code in (EXIT_PUBLISHED, EXIT_UNCHANGED):
        consecutive = 0
    else:
        # A FAILED cycle neither refused nor succeeded, so it must not clear the count: refuse,
        # fail, refuse would otherwise never reach two and never escalate.
        consecutive = carried

    last_published = previous.get("last_published_at")
    if code == EXIT_PUBLISHED:
        last_published = at

    payload = {
        "at": at,
        "at_iso": dt.datetime.fromtimestamp(at, tz=dt.UTC).isoformat(),
        "exit_code": code,
        "outcome": {
            EXIT_PUBLISHED: "published",
            EXIT_UNCHANGED: "unchanged",
            EXIT_FAILED: "failed",
            EXIT_REFUSED: "refused",
            EXIT_BUSY: "busy",
        }.get(code, "unknown"),
        "reason": outcome.reason,
        "surfaces_answering": outcome.surfaces,
        "live_fingerprint": outcome.live_fingerprint,
        "candidate_fingerprint": outcome.candidate_fingerprint,
        #: How many cycles IN A ROW have refused. One refusal is an upstream blip; two is a state
        #: the product should not sit in quietly, because the artifact is now a day old while every
        #: surface still claims to be current.
        "consecutive_refusals": consecutive,
        #: When the served artifact was last actually replaced. Cycle age answers "is the refresh
        #: running"; this answers "is what people are reading current", and they diverge exactly
        #: when it matters — a refresh cycling happily and refusing every time.
        "last_published_at": last_published,
    }
    # UNIQUE scratch, not a shared name. The artifact's candidate has always used `mkstemp` and
    # this used a fixed `<name>.writing` — the same lesson applied once. An independent review
    # produced the interleave: two cycles collided on that one path, one raised FileNotFoundError
    # on the rename, and the record left on disk carried the OTHER cycle's payload.
    handle, raw = tempfile.mkstemp(prefix=path.name + ".", suffix=".writing", dir=path.parent)
    scratch = Path(raw)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, indent=2) + "\n")
        scratch.replace(path)
    except BaseException:
        scratch.unlink(missing_ok=True)
        raise
    return path


def refresh(
    target: Path,
    *,
    build_args: Sequence[str] = (),
    builder: Callable[[list[str]], int] | None = None,
    clock: Callable[[], float] | None = None,
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
    clock = time.time if clock is None else clock
    def record(outcome: RefreshOutcome, code: int) -> tuple[RefreshOutcome, int]:
        write_status(target, outcome, code, at=clock())
        return outcome, code

    try:
        with _hold_lock(target) as held:
            if not held:
                # M1: this used to write a FULL record — from a cycle that does not hold the lock.
                # An overlapping trigger therefore overwrote a refusal, reset the counter plan §5.2
                # exists for, and wrote an outcome the map did not name, so `runner`'s busy branch
                # was dead code and execution fell through to an implicit exit 0 = PASS.
                #
                # A cycle that did nothing has nothing to record. The previous record stands.
                return (
                    RefreshOutcome(
                        published=False,
                        reason="another refresh cycle is already running; this trigger did "
                        "nothing and the live artifact is untouched",
                        live_fingerprint=None,
                        candidate_fingerprint="",
                        surfaces=0,
                    ),
                    EXIT_BUSY,
                )
            return _cycle(target, build_args, builder, record)
    except BaseException as exc:
        # B1, found by an independent review: `record()` was reachable only from the four `return`
        # sites INSIDE the try, so a builder that raised wrote no record at all — and the previous
        # record survived, saying `published` with its own old timestamp. `runner` then printed
        # "outcome: published, last cycle: minutes ago" and exited 0. **A refresh crashing on every
        # cycle read as healthy**, which is precisely what D-129 forbids: silence reported as
        # success. This function's own docstring claimed "written on EVERY path"; the claim and the
        # code disagreed.
        #
        # `BaseException` deliberately, matching `build.py`: whatever kills this cycle, the record
        # must say so before it goes. The exception is then re-raised unchanged — recording is not
        # handling.
        record(
            RefreshOutcome(
                published=False,
                reason=f"the cycle crashed: {type(exc).__name__}: {exc}; "
                "the live artifact is untouched",
                live_fingerprint=None,
                candidate_fingerprint="",
                surfaces=0,
            ),
            EXIT_FAILED,
        )
        raise


def _reason_to_refuse(
    target: Path, live: ServingSummary | None, fresh: ServingSummary
) -> str | None:
    """Why this candidate must not be published, or None if it may be.

    Extracted from `_cycle` when the complexity gate fired at eleven. Keeping it inline would have
    meant a `# noqa`, and the two checks it holds are the two the whole milestone is about — the
    last place to make a reviewer work harder.

    Both are skipped when there is no live artifact, and that is correct: a first artifact cannot
    be worse than one that does not exist. It is NOT skipped when the live artifact is unreadable —
    that raises before this is called (B2).
    """
    if live is None:
        return None

    worse = degradations(live, fresh)
    if worse:
        return "refused: the candidate is worse than what is being served — " + "; ".join(worse)

    suspicious = upward_anomalies(live, fresh)
    if suspicious:
        return (
            "refused: the candidate improved in a way ordinary upstream movement does not "
            "produce — " + "; ".join(suspicious)
        )

    # RE-READ the baseline immediately before publishing. The decision above was made against the
    # artifact as it was when this cycle started, and a hand-run `build.py` can replace it in
    # between — a review demonstrated a score of 95.0 published mid-cycle and then overwritten by
    # this cycle's candidate, whose comparison had been against the pre-build artifact. The lock
    # stops two REFRESHES; it cannot stop a person.
    try:
        current = fingerprint_of(target)
    except UnreadableArtifact:
        current = None
    if current is None or current.digest != live.digest:
        return (
            "the live artifact changed while this cycle was building; refusing rather than "
            "publishing over a decision made against an artifact that is gone"
        )
    return None


def _cycle(
    target: Path,
    build_args: Sequence[str],
    builder: Callable[[list[str]], int],
    record: Callable[[RefreshOutcome, int], tuple[RefreshOutcome, int]],
) -> tuple[RefreshOutcome, int]:
    """The cycle itself. Split out so `refresh` can record a crash around ALL of it, including the
    live-artifact read and the workspace creation, both of which used to sit outside the guard."""
    try:
        live = fingerprint_of(target)
    except UnreadableArtifact as exc:
        return record(
            RefreshOutcome(
                published=False,
                reason=f"the live artifact is present and unreadable ({exc}); refusing rather "
                "than publishing over something this cycle cannot compare against",
                live_fingerprint=None,
                candidate_fingerprint="",
                surfaces=0,
            ),
            EXIT_FAILED,
        )

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
                live_fingerprint=live.digest if live else None,
                candidate_fingerprint="",
                surfaces=0,
            )
            return record(outcome, EXIT_FAILED)

        try:
            fresh = fingerprint_of(candidate)
        except UnreadableArtifact:
            fresh = None
        if fresh is None:
            outcome = RefreshOutcome(
                published=False,
                reason="the candidate built but cannot be read back; the live artifact is untouched",
                live_fingerprint=live.digest if live else None,
                candidate_fingerprint="",
                surfaces=0,
            )
            return record(outcome, EXIT_FAILED)

        if live is not None and fresh.digest == live.digest:
            return record(
                RefreshOutcome(
                    published=False,
                    reason="nothing a user would notice changed",
                    live_fingerprint=live.digest,
                    candidate_fingerprint=fresh.digest,
                    surfaces=fresh.answering,
                ),
                EXIT_UNCHANGED,
            )

        refusal = _reason_to_refuse(target, live, fresh)
        if refusal is not None:
            return record(
                RefreshOutcome(
                    published=False,
                    reason=refusal,
                    live_fingerprint=live.digest if live else None,
                    candidate_fingerprint=fresh.digest,
                    surfaces=fresh.answering,
                ),
                EXIT_REFUSED,
            )

        # RE-READ the baseline immediately before publishing. The degradation decision was made
        # against the artifact as it was when this cycle started, and a hand-run `build.py` can
        # replace it in between — an independent review demonstrated exactly that, with a score of
        # 95.0 published mid-cycle and then overwritten by this cycle's 80.0 candidate, whose
        # comparison had been against the pre-build 74.5. The lock stops two REFRESHES; it cannot
        # stop a human, and a human is who runs `build.py`.
        try:
            candidate.replace(target)
        except OSError as exc:
            return record(
                RefreshOutcome(
                    published=False,
                    reason=f"the candidate could not be published: {exc}; "
                    "the live artifact is untouched",
                    live_fingerprint=live.digest if live else None,
                    candidate_fingerprint=fresh.digest,
                    surfaces=fresh.answering,
                ),
                EXIT_FAILED,
            )

        return record(
            RefreshOutcome(
                published=True,
                reason="first artifact" if live is None else "the served content changed",
                live_fingerprint=live.digest if live else None,
                candidate_fingerprint=fresh.digest,
                surfaces=fresh.answering,
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

    try:
        outcome, code = refresh(Path(args.db), build_args=passthrough)
    except BaseException as exc:
        # The cycle records its own crash and re-raises, so without this the interpreter exits 1 —
        # and 1 is EXIT_UNCHANGED, which this command's own documentation calls "a RESULT, not a
        # failure". A scheduler reading exit codes would have been told nothing happened.
        print(json.dumps({"published": False, "reason": f"crashed: {type(exc).__name__}: {exc}"}))
        return EXIT_FAILED
    print(outcome.as_json())
    return code


if __name__ == "__main__":
    sys.exit(main())
