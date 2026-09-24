"""M17-W2 P1 -- Arena's category slices, read from the dataset's own parquet file (#22, D-164).

Network-free: every parquet here is built in the test with `pyarrow`, and the one download test
goes through respx. The live shape (29 `text` slices, 11 `vision`, one publish date) is recorded
in `docs/plans/m17-wave-2-plan.md`.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import respx

from app.clients.arena import ARENA_BOARDS, ELO_BAND
from app.clients.arena_slices import (
    ARENA_SLICES,
    MAX_PARQUET_BYTES,
    SLICE_CONFIGS,
    ArenaSlice,
    ArenaSliceClient,
    parquet_url,
    parse_arena_slices,
)
from app.clients.fakes import slice_parquet
from app.clients.protocols import SourceError

NEWEST = "2026-09-13"
OLDER = "2026-08-30"


def _parquet(rows: list[dict[str, Any]], *, drop: str | None = None) -> bytes:
    """The canonical fake's file (`app.clients.fakes.slice_parquet`), from this file's row dicts."""
    return slice_parquet(
        [(r["model_name"], r["rating"], r["category"], r.get("date", NEWEST)) for r in rows],
        drop=drop,
    )


def _row(name: str, rating: float, category: str, date: str = NEWEST) -> dict[str, Any]:
    return {"model_name": name, "rating": rating, "category": category, "date": date}


LEGAL = ArenaSlice("text", "industry_legal_and_government", measured_rows=375)
OCR = ArenaSlice("vision", "ocr", measured_rows=108)
MULTI = ArenaSlice("text", "multi_turn", measured_rows=400)


# --- the parse -----------------------------------------------------------------------------------


def test_each_declared_slice_gets_its_own_rows_and_overall_is_not_one_of_them() -> None:
    raw = _parquet([
        _row("a", 1400.0, "overall"),
        _row("a", 1390.0, "industry_legal_and_government"),
        _row("b", 1380.0, "industry_legal_and_government"),
        _row("a", 1370.0, "multi_turn"),
        _row("c", 1360.0, "exclude_ties"),
    ])
    rows, skipped = parse_arena_slices(raw, [LEGAL, MULTI], source_url="u")

    assert {r.raw_name: r.score for r in rows[LEGAL.source_name]} == {"a": 1390.0, "b": 1380.0}
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a"]
    assert set(rows) == {LEGAL.source_name, MULTI.source_name}
    for board in (LEGAL, MULTI):
        for row in rows[board.source_name]:
            assert (row.source, row.benchmark, row.metric) == (board.source_name, board.benchmark, "elo")
            assert row.run_date == NEWEST
        assert skipped[board.source_name] == 0


def test_a_slice_is_served_only_on_its_configs_newest_date() -> None:
    """FP-M2-2, per slice: `vision/creative_writing` has 34 rows and none on the newest date."""
    raw = _parquet([
        _row("a", 1400.0, "overall"),
        _row("a", 1300.0, "multi_turn", OLDER),
        _row("b", 1310.0, "multi_turn", OLDER),
        _row("a", 1390.0, "industry_legal_and_government"),
    ])
    rows, skipped = parse_arena_slices(raw, [LEGAL, MULTI], source_url="u")

    assert rows[MULTI.source_name] == []
    assert skipped[MULTI.source_name] == 2, "a stale slice is refused AND counted"
    assert [r.raw_name for r in rows[LEGAL.source_name]] == ["a"]


def test_a_slice_absent_from_the_file_parses_to_nothing_rather_than_failing_the_rest() -> None:
    raw = _parquet([_row("a", 1390.0, "industry_legal_and_government")])
    rows, _ = parse_arena_slices(raw, [LEGAL, MULTI], source_url="u")
    assert rows[MULTI.source_name] == []
    assert len(rows[LEGAL.source_name]) == 1


@pytest.mark.parametrize("rating", [float("inf"), float("nan"), ELO_BAND[1] + 1, -1.0])
def test_a_rating_outside_the_elo_band_is_refused_and_counted(rating: float) -> None:
    raw = _parquet([
        _row("a", 1390.0, "industry_legal_and_government"),
        _row("bad", rating, "industry_legal_and_government"),
    ])
    rows, skipped = parse_arena_slices(raw, [LEGAL], source_url="u")
    assert [r.raw_name for r in rows[LEGAL.source_name]] == ["a"]
    assert skipped[LEGAL.source_name] == 1


def test_a_file_with_no_readable_date_is_refused_rather_than_served_undated() -> None:
    """P1 review M1: with no date, "the newest snapshot" cannot be chosen, and a file carrying two
    snapshots would serve a stale-but-higher rating as current. So the file fails closed."""
    raw = _parquet([
        _row("a", 1390.0, "industry_legal_and_government", ""),
        _row("b", 1380.0, "industry_legal_and_government", ""),
    ])
    with pytest.raises(SourceError, match="date"):
        parse_arena_slices(raw, [LEGAL], source_url="u")


def _typed(**overrides: Any) -> bytes:
    """A two-row file whose columns can be given any arrow type (the review's hostile files)."""
    columns: dict[str, Any] = {
        "model_name": pa.array(["a", "b"]),
        "rating": pa.array([1390.0, 1380.0]),
        "category": pa.array(["multi_turn", "multi_turn"]),
        "leaderboard_publish_date": pa.array([NEWEST, NEWEST]),
    }
    columns.update(overrides)
    sink = io.BytesIO()
    pq.write_table(pa.table(columns), sink)
    return sink.getvalue()


@pytest.mark.parametrize(
    ("column", "values"),
    [
        # Wave review B1 / security S1: a date32 at its maximum made `to_pylist` raise OverflowError,
        # which is not a SourceError, so the build re-raised it and the whole nightly cycle failed.
        ("leaderboard_publish_date", pa.array([2**31 - 1] * 2, type=pa.date32())),
        ("leaderboard_publish_date", pa.array([2**62] * 2, type=pa.date64())),
        ("leaderboard_publish_date", pa.array([0, 1], type=pa.timestamp("s"))),
        ("rating", pa.array(["1390", "1380"])),
        ("model_name", pa.array([1, 2])),
        ("category", pa.array([1.0, 2.0])),
    ],
)
def test_a_column_of_an_unexpected_type_is_refused_before_it_is_read(
    column: str, values: Any
) -> None:
    """The live file's types (string, double, string, string) are the only ones read: anything else
    is a changed file, refused as one before a value is converted."""
    with pytest.raises(SourceError, match=f"column {column} has type"):
        parse_arena_slices(_typed(**{column: values}), [MULTI], source_url="u")


def test_any_failure_inside_the_reader_is_reported_as_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security S1: an allowlist of exception classes is how OverflowError escaped. Whatever the
    library raises inside the reader becomes an error the parent turns into a SourceError."""
    from app.clients import parquet_reader

    def explode(*_: object, **__: object) -> None:
        raise OverflowError("date out of range")

    monkeypatch.setattr(pq.ParquetFile, "iter_batches", explode)
    answer = parquet_reader.read_rows(_parquet([_row("a", 1390.0, "multi_turn")]), _limits())
    assert "OverflowError" in answer["error"]


CEILING_FILE = Path(__file__).resolve().parents[1] / "fixtures" / "arena_slices" / "ceiling.parquet"


def test_the_reader_answers_rows_or_an_error_in_process(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The reader's protocol, driven in this process so its paths are measured: rows for a good
    file, an error for a changed one, and `main` writing one JSON line per row and an end line."""
    import json

    from app.clients import parquet_reader

    good = _parquet([_row("a", 1390.0, "multi_turn"), _row("b", 1380.0, "multi_turn")])
    assert [r["model_name"] for r in parquet_reader.read_rows(good, _limits())["rows"]] == ["a", "b"]
    assert "type" in parquet_reader.read_rows(_typed(rating=pa.array(["x", "y"])), _limits())["error"]
    assert "parquet" in parquet_reader.read_rows(b"not parquet", _limits())["error"]
    assert "declares" in parquet_reader.read_rows(good, {**_limits(), "max_rows": 1})["error"]
    assert "longer" in parquet_reader.read_rows(
        _parquet([_row("x" * 300, 1390.0, "multi_turn")]), _limits())["error"]
    assert "decoded" in parquet_reader.read_rows(good, {**_limits(), "max_decoded_bytes": 1})["error"]

    class _Stdin:
        buffer = io.BytesIO(good)

    monkeypatch.setattr(sys, "stdin", _Stdin)
    monkeypatch.setattr(sys, "argv", ["reader", json.dumps(_limits())])
    # The watchdog and the alarm belong to the reader's own process. Started here they would live
    # on in this test worker and end it later (a watchdog did exactly that under xdist).
    monkeypatch.setattr(parquet_reader, "_guard", lambda _limits: None)
    parquet_reader.main()
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [line["row"]["model_name"] for line in lines[:-1]] == ["a", "b"]
    assert lines[-1] == {"end": 2}


def test_the_reader_reads_its_peak_from_proc_on_linux(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Re-review 2, BLOCKING-R2-1: on Linux a child's `ru_maxrss` starts from its parent's peak, so a
    reader started by a large parent passed its ceiling at once. `VmHWM` is this process's own."""
    from app.clients import parquet_reader

    status = tmp_path / "status"
    status.write_text("Name:\tpython\nVmPeak:\t 999999 kB\nVmHWM:\t   12345 kB\n", encoding="utf-8")
    monkeypatch.setattr(parquet_reader.sys, "platform", "linux")
    monkeypatch.setattr(parquet_reader, "_PROC_STATUS", status)
    assert parquet_reader._peak_rss() == 12345 * 1024


def _limits() -> dict[str, int]:
    import app.clients.arena_slices as module

    return module.reader_limits()


def _run_reader(monkeypatch: pytest.MonkeyPatch, program: str) -> None:
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "_reader_command", lambda: [sys.executable, "-c", program])
    parse_arena_slices(_parquet([_row("a", 1390.0, "multi_turn")]), [MULTI], source_url="u")


_ROW = '{"row": {"model_name": "a", "rating": 1390.0, "category": "multi_turn", "leaderboard_publish_date": "2026-09-13"}}'


@pytest.mark.parametrize(
    ("program", "match"),
    [
        # A native crash, as a segfault would be. SIGKILL rather than `os.abort()`: an abort writes a
        # macOS crash report and pops a dialog on the owner's screen on every test run.
        ("import os, signal; os.kill(os.getpid(), signal.SIGKILL)", "exited -9"),
        ("import sys; sys.exit(7)", "exited 7"),
        ("print('not json')", "not its protocol"),
        # Re-review 2, MINOR-R2-2: the row-shape and end-line checks, each on its own.
        ("print('{\"row\": 5}'); print('{\"end\": 1}')", "not its protocol"),
        (f"print({_ROW!r})", "no end line"),
        (f"print({_ROW!r}); print('{{\"end\": 2}}')", "end line counts 2"),
    ],
)
def test_a_reader_that_fails_is_a_source_error(
    monkeypatch: pytest.MonkeyPatch, program: str, match: str
) -> None:
    with pytest.raises(SourceError, match=match):
        _run_reader(monkeypatch, program)


def test_an_answer_over_its_bound_is_cut_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security re-look 2, S-R2-1: the parent buffered the reader's whole answer, and an 8 KB file
    whose values JSON escapes six-fold took the refresh process to 797 MiB."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_ANSWER_BYTES", 10_000)
    with pytest.raises(SourceError, match=r"answer.*10000 bytes"):
        _run_reader(monkeypatch, f"for _ in range(1000): print({_ROW!r})")


def test_the_parent_stops_reading_at_the_bound_rather_than_after_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Re-review 3, MINOR-R3-1: a reader that never stops writing is cut off at the bound. An
    unbounded read would wait for the end of an answer that has none, until the time limit."""
    import time

    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_ANSWER_BYTES", 10_000)
    monkeypatch.setattr(module, "READER_TIMEOUT_S", 8.0)
    started = time.monotonic()
    with pytest.raises(SourceError, match="answer passed 10000 bytes"):
        _run_reader(monkeypatch, f"while True: print({_ROW!r}, flush=True)")
    # Tester T1: without the capped read the same message still came, from the check after the
    # time limit, with the whole answer held. The cut-off has to come well before the limit.
    assert time.monotonic() - started < 4.0


def test_only_the_tail_of_the_readers_stderr_is_quoted_and_it_is_printable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MINOR-R3-1: a megabyte of stderr, then the part an operator needs."""
    program = ("import sys; sys.stderr.write('A' * 1_000_000 + '\\x1b[31m' + 'TAILMARK');"
               " sys.exit(7)")
    with pytest.raises(SourceError, match="exited 7") as caught:
        _run_reader(monkeypatch, program)
    message = str(caught.value)
    assert "TAILMARK" in message and len(message) < 400 and "\x1b" not in message


def test_a_name_with_a_unicode_line_separator_is_read_whole() -> None:
    """Re-review 3, MINOR-R3-2 / security S-R3-2: `str.splitlines()` also splits on U+2028, U+2029
    and U+0085, which the reader writes raw, so one such name failed every slice of the config."""
    names = ["a\u2028b", "c\u2029d", "e\x85f", "g"]
    raw = _parquet([_row(name, 1390.0 - i, "multi_turn") for i, name in enumerate(names)])
    rows, _ = parse_arena_slices(raw, [MULTI], source_url="u")
    assert sorted(r.raw_name for r in rows[MULTI.source_name]) == sorted(names)


def test_a_reader_that_cannot_be_started_is_a_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "_reader_command", lambda: ["/nonexistent/python", "-c", "pass"])
    with pytest.raises(SourceError, match="could not be started"):
        parse_arena_slices(_parquet([_row("a", 1390.0, "multi_turn")]), [MULTI], source_url="u")


def test_a_missing_temporary_directory_is_a_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security re-look 3, S-R3-4: the temporary file for stderr was made outside the guard, so a
    missing TMPDIR ended the cycle rather than the source."""
    import app.clients.arena_slices as module

    def gone(*_: object, **__: object) -> None:
        raise FileNotFoundError("no temporary directory")

    monkeypatch.setattr(module.tempfile, "TemporaryFile", gone)
    with pytest.raises(SourceError, match="temporary"):
        parse_arena_slices(_parquet([_row("a", 1390.0, "multi_turn")]), [MULTI], source_url="u")


@pytest.mark.parametrize("failure", [OSError("/proc is gone"), ValueError("bad VmHWM"),
                                     LookupError("no VmHWM line"), MemoryError()])
def test_the_watchdog_fails_closed(monkeypatch: pytest.MonkeyPatch, failure: BaseException) -> None:
    """Re-review 3, MINOR-R3-3 / S-R3-3: a watchdog that cannot read the peak must end the reader
    as over its ceiling, never die quietly and leave it unbounded, whatever the failure is."""
    from app.clients import parquet_reader

    def unreadable() -> int:
        raise failure

    exits: list[int] = []

    def fake_exit(code: int) -> None:
        exits.append(code)
        raise SystemExit(code)

    monkeypatch.setattr(parquet_reader, "_peak_rss", unreadable)
    monkeypatch.setattr(parquet_reader.os, "_exit", fake_exit)
    with pytest.raises(SystemExit):
        parquet_reader._watch(2**40)
    # Final review NIT-2: its own exit, so the operator is not sent to look at the file.
    assert exits == [parquet_reader.EXIT_UNMEASURED]


def test_a_reader_that_cannot_measure_itself_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.clients import parquet_reader

    with pytest.raises(SourceError, match="could not measure its memory"):
        _run_reader(monkeypatch, f"import os; os._exit({parquet_reader.EXIT_UNMEASURED})")


def test_linux_without_a_peak_line_is_an_error_not_a_ceiling_1024_times_too_large(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MINOR-R3-3: the fallback read `ru_maxrss`, which Linux reports in KiB."""
    from app.clients import parquet_reader

    status = tmp_path / "status"
    status.write_text("Name:\tpython\n", encoding="utf-8")
    monkeypatch.setattr(parquet_reader.sys, "platform", "linux")
    monkeypatch.setattr(parquet_reader, "_PROC_STATUS", status)
    with pytest.raises(LookupError):
        parquet_reader._peak_rss()


def test_the_live_contract_tests_step_past_the_network_guard() -> None:
    """Re-review 3, MINOR-R3-4: without the marker the live slice contract test can never pass, and
    the local suite (which skips it) would not notice."""
    import importlib

    contract = importlib.import_module("tests.integration.test_arena_openrouter_contract")
    marks = {m.name for m in getattr(contract.test_every_declared_slice_satisfies_the_parser_contract,
                                     "pytestmark", [])}
    assert "slice_download" in marks


def test_a_reason_is_quoted_short_and_printable(monkeypatch: pytest.MonkeyPatch) -> None:
    """S-R2-1/S-R2-2: a 3.9 MB reason was copied 35 times into the refresh record and parsed on every
    `/health`. A quoted reason is bounded and carries no control characters."""
    program = "import json; print(json.dumps({'error': '\\x1b[31m\\n' + 'x' * 5000}))"
    with pytest.raises(SourceError) as caught:
        _run_reader(monkeypatch, program)
    message = str(caught.value)
    assert len(message) < 400
    assert "\x1b" not in message and "\n" not in message


def test_the_reader_gets_no_secret_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security re-look 2, S-R2-4: the reader inherited the whole environment, tokens included."""
    monkeypatch.setenv("HF_TOKEN", "hf_secret")
    # Asked directly, not by listing the environment: a reason is cut at 200 characters, and a
    # listing cut before `HF_TOKEN` made this test pass with the allowlist gone.
    program = "import json, os; print(json.dumps({'error': 'leaked' if 'HF_TOKEN' in os.environ else 'clean'}))"
    with pytest.raises(SourceError, match="clean"):
        _run_reader(monkeypatch, program)


def test_a_module_planted_in_the_working_directory_is_not_imported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """S-R2-4 / NIT-R2-3: `python -m` put the working directory first on the import path, and a
    planted `pyarrow.py` replaced the reader's answer. `-P` leaves it off."""
    (tmp_path / "pyarrow.py").write_text("raise SystemExit('planted module imported')\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rows, _ = parse_arena_slices(_parquet([_row("a", 1390.0, "multi_turn")]), [MULTI], source_url="u")
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a"]


def test_a_reader_whose_parent_is_gone_stops_itself() -> None:
    """Re-review 2, NIT-R2-2: a reader orphaned mid-read (the nightly killed its refresh) ends at its
    own time limit rather than running on."""
    import json
    import signal

    import app.clients.arena_slices as module

    limits = {**module.reader_limits(), "timeout_s": 1}
    reader = subprocess.Popen(  # stdin left open: the reader waits for a file that never comes
        [*module._reader_command(), json.dumps(limits)], stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=module._reader_env())
    try:
        assert reader.wait(timeout=10) == -signal.SIGALRM
    finally:
        reader.kill()
        reader.wait()
        assert reader.stdin is not None
        reader.stdin.close()  # final review NIT-1: the last ResourceWarning in this file


def test_a_reader_that_hangs_is_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "_reader_command",
                        lambda: [sys.executable, "-c", "import time; time.sleep(30)"])
    monkeypatch.setattr(module, "READER_TIMEOUT_S", 0.5)
    with pytest.raises(SourceError, match="seconds"):
        parse_arena_slices(_parquet([_row("a", 1390.0, "multi_turn")]), [MULTI], source_url="u")


def test_a_file_that_would_exhaust_memory_is_stopped_at_the_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Re-review BLOCKING-R1 / S-R1: pyarrow decodes a whole column chunk before any check in
    Python runs, so `ceiling.parquet` (96 distinct 1 MiB names, 6 KB on disk) decodes to 96 MiB
    whatever the batch size. The footer's claim is taken away (as a forged footer would) and the
    ceiling is what stops it. The ceiling here sits just above the reader's own size after its
    imports (about 55 MB); in production it is `MAX_READER_RSS`, 512 MiB. The file is committed,
    not built here: building it took this process past 600 MB (re-review 2, BLOCKING-R2-1)."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_UNCOMPRESSED_BYTES", 2**40)
    monkeypatch.setattr(module, "MAX_READER_RSS", 100 * 2**20)
    with pytest.raises(SourceError, match="memory ceiling"):
        parse_arena_slices(CEILING_FILE.read_bytes(), [MULTI], source_url="u")


def test_an_ordinary_file_reads_under_the_same_ceiling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Final review M2: the positive control for the ceiling test above. The same 100 MiB ceiling
    that stops `ceiling.parquet` lets an ordinary file through, so the stop is the file's doing and
    not a reader that measures itself too high."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_READER_RSS", 100 * 2**20)
    raw = _parquet([_row("a", 1390.0, "multi_turn"), _row("b", 1380.0, "multi_turn")])
    rows, _ = parse_arena_slices(raw, [MULTI], source_url="u")
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a", "b"]


def test_rows_are_counted_as_they_are_read_not_as_the_footer_declares(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Security re-look S-R2: the footer's row count can be forged. With the footer's own check
    taken out, the count kept while reading still stops the read."""
    from app.clients import parquet_reader

    monkeypatch.setattr(parquet_reader, "_check_footer", lambda *_: None)
    limits = {**_limits(), "max_rows": 2}
    answer = parquet_reader.read_rows(
        _parquet([_row(f"m{i}", 1300.0, "multi_turn") for i in range(3)]), limits)
    assert "rows" in answer["error"]


def test_a_value_longer_than_any_real_one_is_refused() -> None:
    """Security S2: one long value, repeated by dictionary encoding, grows by rows x length when
    the rows become Python strings. A real model name is well under the bound."""
    raw = _parquet([_row("x" * 1000, 1390.0, "multi_turn")])
    with pytest.raises(SourceError, match="longer"):
        parse_arena_slices(raw, [MULTI], source_url="u")


def test_decoding_past_the_budget_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security S2: the footer's sizes are the writer's claims. What is actually decoded is counted
    batch by batch, and the read stops at the budget."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_DECODED_BYTES", 64)
    raw = _parquet([_row(f"m{i}", 1300.0 + i, "multi_turn") for i in range(50)])
    with pytest.raises(SourceError, match="decoded"):
        parse_arena_slices(raw, [MULTI], source_url="u")


@pytest.mark.parametrize("stray", ["2026-09-1~", "2026-09-2 ", "not a date", "2026-13-40"])
def test_a_date_that_is_not_a_date_never_becomes_the_newest(stray: str) -> None:
    """Security re-look S-R4: compared as text, `2026-09-1~` sorts above every real date."""
    raw = _parquet([
        _row("a", 1390.0, "multi_turn"),
        _row("z", 1500.0, "industry_legal_and_government", stray),
    ])
    rows, skipped = parse_arena_slices(raw, [MULTI, LEGAL], source_url="u")
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a"]
    assert rows[LEGAL.source_name] == [] and skipped[LEGAL.source_name] == 1


def test_a_row_dated_in_the_future_is_refused_and_does_not_move_the_newest_date() -> None:
    """Security S4: the newest date was an unchecked maximum, so one stray `9999-12-31` row would
    have darkened every slice of the config."""
    raw = _parquet([
        _row("a", 1390.0, "multi_turn"),
        _row("b", 1380.0, "multi_turn"),
        _row("z", 1500.0, "industry_legal_and_government", "9999-12-31"),
    ])
    rows, skipped = parse_arena_slices(raw, [MULTI, LEGAL], source_url="u")
    assert [r.raw_name for r in rows[MULTI.source_name]] == ["a", "b"]
    assert rows[LEGAL.source_name] == []
    assert skipped[LEGAL.source_name] == 1


def test_a_file_that_is_not_parquet_is_a_source_error() -> None:
    with pytest.raises(SourceError, match="parquet"):
        parse_arena_slices(b"<html>rate limited</html>", [LEGAL], source_url="u")


@pytest.mark.parametrize("column", ["model_name", "rating", "category", "leaderboard_publish_date"])
def test_a_missing_column_is_a_source_error(column: str) -> None:
    raw = _parquet([_row("a", 1390.0, "industry_legal_and_government")], drop=column)
    with pytest.raises(SourceError, match=column):
        parse_arena_slices(raw, [LEGAL], source_url="u")


def test_a_file_declaring_more_rows_than_the_bound_is_refused_before_it_is_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The metadata is checked BEFORE the table is materialised: a small compressed file can
    declare a huge table, and reading it first is paying for it first."""
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_PARQUET_ROWS", 2)
    raw = _parquet([_row(f"m{i}", 1300.0 + i, "multi_turn") for i in range(3)])
    with pytest.raises(SourceError, match="rows"):
        parse_arena_slices(raw, [MULTI], source_url="u")


def test_a_file_declaring_more_uncompressed_bytes_than_the_bound_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.clients.arena_slices as module

    monkeypatch.setattr(module, "MAX_UNCOMPRESSED_BYTES", 10)
    raw = _parquet([_row("a", 1390.0, "multi_turn")])
    with pytest.raises(SourceError, match=r"the file declares .* bytes, over 10"):
        parse_arena_slices(raw, [MULTI], source_url="u")


def test_a_duplicate_name_on_one_slice_keeps_the_best_rating_and_counts_the_other() -> None:
    raw = _parquet([_row("a", 1300.0, "multi_turn"), _row("a", 1350.0, "multi_turn")])
    rows, skipped = parse_arena_slices(raw, [MULTI], source_url="u")
    assert [(r.raw_name, r.score) for r in rows[MULTI.source_name]] == [("a", 1350.0)]
    assert skipped[MULTI.source_name] == 1


# --- the download --------------------------------------------------------------------------------


@pytest.mark.slice_download
@respx.mock
def test_the_client_downloads_its_configs_own_parquet_file() -> None:
    body = _parquet([_row("a", 1390.0, "industry_legal_and_government")])
    route = respx.get(parquet_url("text")).mock(return_value=httpx.Response(200, content=body))
    client = ArenaSliceClient("text")
    assert client.fetch_bytes() == body
    assert route.call_count == 1
    assert client.url == parquet_url("text")
    assert "lmarena-ai/leaderboard-dataset" in client.url


@pytest.mark.slice_download
@respx.mock
def test_a_download_over_the_cap_is_cut_off() -> None:
    respx.get(parquet_url("vision")).mock(
        return_value=httpx.Response(200, content=b"x" * (MAX_PARQUET_BYTES + 1))
    )
    with pytest.raises(SourceError, match="exceeded"):
        ArenaSliceClient("vision").fetch_bytes()


@pytest.mark.slice_download
@respx.mock
def test_a_redirect_to_a_malformed_host_is_a_source_error() -> None:
    """Security re-look S-R3: `Location: http://xn--/x` raised IDNAError out of the shared download
    helper, which ended the build and lost the other config's valid slices."""
    respx.get(parquet_url("text")).mock(
        return_value=httpx.Response(302, headers={"Location": "http://xn--/x"}))
    with pytest.raises(SourceError, match="arena_slices_text"):
        ArenaSliceClient("text").fetch_bytes()


def test_no_test_downloads_a_slice_file() -> None:
    """Re-review MINOR-R2: the suite's guard sits on the client itself, so every path to a download
    (the build's default client, `fetch_slices`, `measure_slices`) meets it. Checked by identity,
    so this test never downloads anything even when the guard is gone."""
    assert ArenaSliceClient.fetch_bytes.__name__ == "_tests_never_reach_the_network"


def test_an_unknown_config_is_refused() -> None:
    with pytest.raises(SourceError, match="config"):
        ArenaSliceClient("text_style_control")


# --- the declared table --------------------------------------------------------------------------


def test_the_table_is_the_35_boards_the_owner_ruled() -> None:
    """Owner ruling 2026-09-24: every meaningful slice (26 `text`, 9 `vision`)."""
    by_config = {c: {s.category for s in ARENA_SLICES if s.config == c} for c in SLICE_CONFIGS}
    assert len(by_config["text"]) == 26
    assert len(by_config["vision"]) == 9
    assert len(ARENA_SLICES) == 35


def test_the_left_out_slices_stay_out() -> None:
    """Each with its reason in the plan: already read, a method variant, an intersection, stale."""
    declared = {(s.config, s.category) for s in ARENA_SLICES}
    for left_out in [
        ("text", "overall"),
        ("vision", "overall"),
        ("text", "exclude_ties"),
        ("text", "hard_prompts_english"),
        ("vision", "creative_writing"),
    ]:
        assert left_out not in declared


def test_every_board_has_its_own_source_id_and_benchmark() -> None:
    """`category_ranking` joins on benchmark: a shared label merges two boards (M14-W2)."""
    ids = [s.source_name for s in ARENA_SLICES]
    labels = [s.benchmark for s in ARENA_SLICES]
    assert len(set(ids)) == len(ids)
    assert len(set(labels)) == len(labels)
    overall_ids = {b.id for b in ARENA_BOARDS.values()}
    overall_labels = {b.benchmark for b in ARENA_BOARDS.values()}
    assert not set(ids) & overall_ids
    assert not set(labels) & overall_labels


def test_every_floor_is_below_its_measured_count_and_above_zero() -> None:
    for board in ARENA_SLICES:
        assert 0 < board.minimum_rows < board.measured_rows, board


# --- the serving process -------------------------------------------------------------------------


def _loads_pyarrow(module: str) -> bool:
    probe = f"import sys, {module}\nprint('pyarrow' in sys.modules)"
    return subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True,
        env={**os.environ, "APP_ENV": "test", "PYTHONPATH": "src"},
    ).stdout.strip() == "True"


@pytest.mark.parametrize("module", ["app.adapter.main", "app.clients.arena_slices"])
def test_neither_the_server_nor_the_slice_module_loads_pyarrow(module: str) -> None:
    """D-154: the server imports `app.clients.*` (W-125), so pyarrow is imported inside the read.

    The server imports `arena_slices` itself (through `rank.SOURCE_ATTRIBUTION`), so both halves
    fail on a top-level `import pyarrow`. The module half stays: it holds the rule even if the
    server's path to the module goes away (P1 review M2).
    """
    assert not _loads_pyarrow(module)


def test_the_smoke_probe_holds_every_slice_of_a_config_to_its_floor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tester T2: `smoke_deps`' one probe per config (P4), driven with the canonical fake."""
    import importlib.util

    import app.clients.arena_slices as module
    from app.clients.fakes import fake_slice_client

    spec = importlib.util.spec_from_file_location(
        "smoke_deps", Path(__file__).resolve().parents[2] / "scripts" / "smoke_deps.py")
    assert spec is not None and spec.loader is not None
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)

    vision = [board for board in ARENA_SLICES if board.config == "vision"]

    def file_with(short: str | None) -> bytes:
        rows = []
        for board in vision:
            count = board.minimum_rows - 1 if board.category == short else board.minimum_rows
            rows += [(f"m{i}", 1300.0 - i, board.category, NEWEST) for i in range(count)]
        return slice_parquet(rows)

    monkeypatch.setattr(module, "ArenaSliceClient", fake_slice_client({"vision": file_with(None)}))
    assert smoke._slice_probe("vision")().startswith(f"{len(vision)} slices")
    monkeypatch.setattr(module, "ArenaSliceClient", fake_slice_client({"vision": file_with("ocr")}))
    with pytest.raises(ValueError, match="arena_vision_ocr"):
        smoke._slice_probe("vision")()
    # Final review M1: the probe holds the ceiling the build holds, or it calls usable a slice the
    # nightly build refuses.
    ocr = next(board for board in vision if board.category == "ocr")
    over = slice_parquet([(f"m{i}", 1300.0 - i, "ocr", NEWEST) for i in range(ocr.maximum_rows + 1)]
                         + [(f"m{i}", 1300.0 - i, b.category, NEWEST) for b in vision
                            if b is not ocr for i in range(b.minimum_rows)])
    monkeypatch.setattr(module, "ArenaSliceClient", fake_slice_client({"vision": over}))
    with pytest.raises(ValueError, match=r"arena_vision_ocr.*ceiling"):
        smoke._slice_probe("vision")()


def test_one_bounds_rule_serves_the_build_the_probe_and_the_contract_test() -> None:
    """Final review M1: the floor and the ceiling are one method, not three copies."""
    board = ArenaSlice("text", "multi_turn", measured_rows=10)
    assert board.bounds_problem(5) is None and board.bounds_problem(40) is None
    assert "floor of 5" in (board.bounds_problem(4) or "")
    assert "ceiling of 40" in (board.bounds_problem(41) or "")

