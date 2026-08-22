"""REQ-REV-001 / D-133 — a self-review cannot close a wave green, and a cited review must exist.

K.7 was bypassed four times in this project, every one declared in the open and every one closed
GREEN. The problem was never concealment; nothing blocked. And when the gate for this requirement
was first run it failed the ONE wave record claiming K.7 was satisfied, because that row cited two
review files which have never existed (W-056).

So the two halves are tested separately, because they scope differently on purpose:
  * **format** (cite a record; the record declares its seat) applies from M11 onward, since GPF-001
    forbids a tool retroactively invalidating records written before it existed;
  * **a broken citation** applies in EVERY era, because citing a file that is not there was never
    acceptable and scoping it would have hidden W-056.
"""

from __future__ import annotations

import pathlib

import pytest
from scripts.wave_check import SEAT_RULE_FROM_MILESTONE, review_seat_problems

ROW = "| 3 | Review per tier — V3C-78 | {evidence} | {status} |"


def _repo(tmp_path: pathlib.Path, reviews: dict[str, str | None]) -> pathlib.Path:
    """A tree with `docs/reviews/`. A None value means the file is CITED but never written."""
    (tmp_path / "docs" / "reviews").mkdir(parents=True)
    for name, seat in reviews.items():
        if seat is None:
            continue
        (tmp_path / "docs" / "reviews" / name).write_text(
            f"---\nrecord_type: review\nid: {name[:-3]}\nstatus: ratified\nseat: {seat}\n---\n# r\n",
            encoding="utf-8",
        )
    return tmp_path


def test_a_self_review_cannot_close_a_wave_green(tmp_path: pathlib.Path) -> None:
    """`seat: author` + a passing row is the exact shape of all four historical bypasses."""
    root = _repo(tmp_path, {"m11-w1-review.md": "author"})
    row = ROW.format(evidence="`docs/reviews/m11-w1-review.md`", status="✅")

    problems = review_seat_problems(row, root, milestone=11)

    assert problems, "a self-review passed a wave green; that is W-055 happening a fifth time"
    assert "seat: author" in problems[0]
    assert "WAIVE" in problems[0], "the gate must name the remedy that counts the bypass (V4C-13)"


def test_an_independent_review_closes_it(tmp_path: pathlib.Path) -> None:
    """Fixture blindness: without this the test above could pass because EVERYTHING fails."""
    root = _repo(tmp_path, {"m11-w1-review.md": "independent"})
    row = ROW.format(evidence="`docs/reviews/m11-w1-review.md`", status="✅")

    assert review_seat_problems(row, root, milestone=11) == []


def test_a_waived_row_is_left_to_block_d(tmp_path: pathlib.Path) -> None:
    """A self-review that ADMITS it is one is the intended outcome, not a second failure.

    Block D already forces a WAIVED row to name PRESSURE, NO-ENVIRONMENT or a ledger id. Failing it
    here as well would mean the only way to close is to claim independence — a gate that makes
    honesty more expensive than the alternative teaches the wrong thing.
    """
    root = _repo(tmp_path, {"m11-w1-review.md": "author"})
    row = ROW.format(
        evidence="`docs/reviews/m11-w1-review.md`", status="WAIVED — NO-ENVIRONMENT, ledger W-055"
    )

    assert review_seat_problems(row, root, milestone=11) == []


def test_a_passing_row_that_cites_no_review_at_all_fails(tmp_path: pathlib.Path) -> None:
    root = _repo(tmp_path, {})
    row = ROW.format(evidence="Single combined pass at MED, plus the author's fault injection", status="✅")

    problems = review_seat_problems(row, root, milestone=11)

    assert problems and "cites no review record" in problems[0]


def test_a_review_without_a_seat_declaration_fails_from_m11(tmp_path: pathlib.Path) -> None:
    (tmp_path / "docs" / "reviews").mkdir(parents=True)
    (tmp_path / "docs" / "reviews" / "r.md").write_text(
        "---\nrecord_type: review\nid: r\nstatus: ratified\n---\n# r\n", encoding="utf-8"
    )
    row = ROW.format(evidence="`docs/reviews/r.md`", status="✅")

    problems = review_seat_problems(row, tmp_path, milestone=11)

    assert problems and "declares no `seat:`" in problems[0]


# --- the era split, which is the half that found W-056 ------------------------------------------


def test_the_format_rules_do_not_reach_back_before_the_rule_existed(tmp_path: pathlib.Path) -> None:
    """GPF-001: a tool may not retroactively invalidate records written before it existed.

    An M6 record whose review row cites a review with no `seat:` — the shape of five real records
    in this repository — must pass, or shipping this gate would have meant rewriting history to
    suit a field invented afterwards.
    """
    (tmp_path / "docs" / "reviews").mkdir(parents=True)
    (tmp_path / "docs" / "reviews" / "old.md").write_text(
        "---\nrecord_type: review\nid: old\nstatus: ratified\n---\n# r\n", encoding="utf-8"
    )
    row = ROW.format(evidence="`docs/reviews/old.md`", status="✅")

    assert review_seat_problems(row, tmp_path, milestone=SEAT_RULE_FROM_MILESTONE - 1) == []


@pytest.mark.parametrize("milestone", [6, 8, 11, None])
def test_a_citation_to_a_file_that_does_not_exist_fails_in_every_era(
    tmp_path: pathlib.Path, milestone: int | None
) -> None:
    """W-056, the finding this gate made on its first run — and the reason it is NOT era-scoped.

    `m8-wave-5-close.md` cited `docs/reviews/m8-code-review.md` and
    `docs/reviews/m8-security-review-independent.md`, and neither has ever existed. Had the broken
    citation been scoped alongside the format rules, the one record in this project claiming K.7
    was satisfied would have kept a green ✅ resting on two paths that are not there.
    """
    root = _repo(tmp_path, {"never-written.md": None})
    row = ROW.format(evidence="`docs/reviews/never-written.md`", status="✅")

    problems = review_seat_problems(row, root, milestone=milestone)

    assert problems, f"a citation to a nonexistent review passed at milestone {milestone}"
    assert "does not exist" in problems[0]
    assert "claim about a conversation" in problems[0]


# --- through the REAL entry point (V4C-49: every load-bearing path needs one) -------------------
#
# The independent seat's MAJOR-2: unwiring `review_seat_problems` from `main()` left pytest,
# `wave_check_all.py` and `check_records.py` all green. Every test above called the function
# directly, so the gate could be disconnected without a single assertion noticing — which is this
# project's "a control cited but not run", inside the wave that exists to stop exactly that.


def _wave_record(tmp_path: pathlib.Path, review_row: str) -> pathlib.Path:
    """A wave-close record that passes every OTHER block, so only the review row is under test."""
    (tmp_path / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "reviews").mkdir(parents=True, exist_ok=True)
    record = tmp_path / "docs" / "plans" / "m11-wave-9-close.md"
    record.write_text(
        "---\nrecord_type: wave\nid: m11-wave-9-close\nstatus: draft\n"
        "process_version: v5.0\ndate: 2026-08-22\n---\n"
        "# Wave-Close Checklist — probe\n\n"
        "| # | Check | Evidence | ✅/WAIVED |\n|---|---|---|---|\n"
        f"{review_row}\n"
        "| 9 | Gates green | `make check` exit 0 | ✅ |\n\n"
        "Touched: `src/app/probe.py`\n\n"
        "K.8 contracts: none moved.\n\n"
        "Filled by: a probe · Date: 2026-08-22 · Wave commit range: `aaaaaaa..HEAD`\n",
        encoding="utf-8",
    )
    return record


def test_the_gate_is_actually_wired_into_the_command_that_runs(tmp_path: pathlib.Path) -> None:
    """Unwire `review_seat_problems` from `main()` and THIS is the test that goes red."""
    from scripts.wave_check import main

    (tmp_path / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "reviews").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "reviews" / "self.md").write_text(
        "---\nrecord_type: review\nid: self\nstatus: ratified\nseat: author\n---\n# r\n",
        encoding="utf-8",
    )
    record = _wave_record(tmp_path, "| 3 | Review per tier | `docs/reviews/self.md` | ✅ |")

    assert main(["wave_check.py", str(record)]) != 0, (
        "a self-review closed a wave green through the real entry point; every unit test above "
        "can pass with the gate disconnected"
    )


def test_the_same_record_with_an_independent_seat_passes_through_main(tmp_path: pathlib.Path) -> None:
    """Fixture blindness: the probe record must be capable of PASSING, or the test above proves
    only that some other block objects to it."""
    from scripts.wave_check import main

    (tmp_path / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "reviews").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "reviews" / "indep.md").write_text(
        "---\nrecord_type: review\nid: indep\nstatus: ratified\nseat: independent\n---\n# r\n",
        encoding="utf-8",
    )
    record = _wave_record(tmp_path, "| 3 | Review per tier | `docs/reviews/indep.md` | ✅ |")

    assert main(["wave_check.py", str(record)]) == 0


def test_a_seat_declared_in_PROSE_rather_than_frontmatter_does_not_count(
    tmp_path: pathlib.Path,
) -> None:
    """A four-line file with no frontmatter, whose BODY says `seat: independent`, closed a wave
    green until the frontmatter was parsed as frontmatter."""
    root = tmp_path
    (root / "docs" / "reviews").mkdir(parents=True)
    (root / "docs" / "reviews" / "prose.md").write_text(
        "# A review\n\nseat: independent\n\nLooks fine to me.\n", encoding="utf-8"
    )
    row = ROW.format(evidence="`docs/reviews/prose.md`", status="✅")

    problems = review_seat_problems(row, root, milestone=11)

    assert problems and "declares no `seat:`" in problems[0]


def test_a_waived_review_row_must_name_a_ledger_row(tmp_path: pathlib.Path) -> None:
    """AGENTS.md claims a waived review row "forces it to name a ledger row". It did not."""
    root = tmp_path
    (root / "docs" / "reviews").mkdir(parents=True)
    row = ROW.format(evidence="Reviewed it myself, no second seat was available", status="WAIVED — PRESSURE")

    problems = review_seat_problems(row, root, milestone=11)

    assert problems and "names no ledger row" in problems[0]


def test_a_wave_record_cannot_cite_itself_through_a_traversal(tmp_path: pathlib.Path) -> None:
    root = tmp_path
    (root / "docs" / "reviews").mkdir(parents=True)
    row = ROW.format(evidence="`docs/reviews/../plans/m11-wave-9-close.md`", status="✅")

    problems = review_seat_problems(row, root, milestone=11)

    assert problems and "escapes" in problems[0]


def test_a_broken_citation_is_seen_even_on_a_waived_row(tmp_path: pathlib.Path) -> None:
    """BLOCKING-3. The W-056 remediation set the offending row to WAIVED, and the citation scan ran
    after the waiver exit — so the record that motivated this gate became invisible to it."""
    root = tmp_path
    (root / "docs" / "reviews").mkdir(parents=True)
    row = ROW.format(
        evidence="`docs/reviews/never-written.md`", status="WAIVED — NO-ENVIRONMENT, ledger W-056"
    )

    problems = review_seat_problems(row, root, milestone=11)

    assert problems and "does not exist" in problems[0]


def test_a_review_row_labelled_something_else_is_still_seen(tmp_path: pathlib.Path) -> None:
    """The row filter was case-sensitive and matched two literal phrases, so `Fresh-eyes code
    review` was invisible and a self-review passed simply by renaming the row."""
    root = tmp_path
    (root / "docs" / "reviews").mkdir(parents=True)
    (root / "docs" / "reviews" / "self.md").write_text(
        "---\nrecord_type: review\nid: self\nstatus: ratified\nseat: author\n---\n# r\n",
        encoding="utf-8",
    )
    row = "| 3 | Fresh-eyes code REVIEW | `docs/reviews/self.md` | ✅ |"

    assert review_seat_problems(row, root, milestone=11), "renaming the row disabled the gate"
