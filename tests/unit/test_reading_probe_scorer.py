"""M19-W4 Tester: the scorer the wave's record rests on (`docs/research/m19-w4-runs/score_w4.py`).

Every number in `docs/research/m19-w4-question-reading-probe.md`, D-184's "Measured" paragraph and the
REQ-ASK-005 and REQ-IMG-003 rows is a count this scorer made from a committed run. No test read it, so
each of ten planted faults in it (a question back not counted as caught, the tier's own decline
counted as an override, the bar rounded rather than rounded up, `--show` allowed on a held-out set
...) passed the whole suite (`docs/reviews/m19-wave-4-tester.md`, S1 to S10).

The rows here are made up; none is a held-out question. The last test reads the committed runs and
their sets, counts only, and never prints a question. # covers REQ-ASK-005, REQ-IMG-003, D-184
"""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "docs/research/m19-w4-runs"
SETS = ROOT / "scripts/router_probe"


def _scorer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("score_w4", RUNS / "score_w4.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(q: str, reading: str, surface: str = "assistant", unmeasured: bool = False, declined: bool = False,
         model: str = "search", routed: str | None = None) -> dict[str, str]:
    return {"q": q, "reading": reading, "surface": surface, "unmeasured": str(unmeasured).lower(),
            "declined": str(declined).lower(), "model": model, "routed": routed or surface}


#: A made-up reading set: (question, class, expected surface).
READING_SET = [
    ("k1", "knowledge", "assistant"), ("k2", "knowledge", "assistant"), ("k3", "knowledge", "assistant"),
    ("i1", "injection", "assistant"), ("c1", "chitchat", "assistant"), ("d1", "do_task", "assistant"),
    ("n1", "nas", "assistant"), ("g1", "genuine", "coding"), ("g2", "genuine", "coding|agentic-coding"),
    ("g3", "genuine", "coding"), ("g4", "genuine", "assistant"), ("a1", "ambiguous", "assistant"),
]
READING_RUN = [
    _row("k1", "notASearch"), _row("k2", "unsure", model="not"), _row("k3", "search"), _row("i1", "unsure"),
    _row("c1", "notASearch"), _row("d1", "unsure"), _row("n1", "search"),
    _row("g1", "search", "coding"),
    _row("g2", "unsure", "agentic-coding"),            # asked, and on one of its surfaces
    _row("g3", "notASearch", "coding"),                # given the note: on no surface
    _row("g4", "search", "assistant", unmeasured=True),  # unmeasured: on no surface
    _row("a1", "unsure", model="not"),
]


def test_the_reading_measures_count_what_the_record_says_they_count() -> None:
    """S1, S2, S7, S8: a question back is caught; pasted content (`do_task`) is not a search; a
    genuine search given the note, or answered as unmeasured, is on no surface."""
    measures = _scorer().reading_measures({q: {"q": q, "class": c, "expected": e} for q, c, e in READING_SET},
                                          READING_RUN)
    assert measures["not a search caught"] == (5, 7)
    assert measures["knowledge caught"] == (2, 3)
    assert measures["genuine given the note"] == (1, 4)
    assert measures["genuine asked"] == (1, 4)
    assert measures["genuine on their surface"] == (2, 4)
    assert measures["  asked on the model's word alone (all rows)"] == (2, 12)


#: A made-up image set: (question, class, expected surface).
IMAGE_SET = [
    ("m1", "image-make", "UNMEASURED"), ("m2", "image-make", "UNMEASURED"), ("m3", "image-make", "UNMEASURED"),
    ("m4", "image-make", "UNMEASURED"), ("m5", "image-make", "UNMEASURED"),
    ("r1", "image-read", "vision"), ("r2", "image-read", "vision"), ("r3", "image-read", "vision"),
    ("r4", "image-read", "vision"),
    ("o1", "image-other", "web-dev"), ("o2", "image-other", "web-dev"), ("o3", "image-other", "web-dev"),
]
IMAGE_RUN = [
    _row("m1", "search", unmeasured=True, routed="vision"),                # the image rule's override
    _row("m2", "search", unmeasured=True, declined=True),                  # the tier's own decline
    _row("m3", "notASearch", unmeasured=True, routed="vision"),            # given the note: not told
    _row("m4", "search", "vision"), _row("m5", "search", "web-dev"),       # missed
    _row("r1", "search", "vision"), _row("r2", "unsure", "vision"),
    _row("r3", "notASearch", "vision"),                                    # given the note: not reached
    _row("r4", "search", unmeasured=True, routed="vision"),                # overridden: not reached
    _row("o1", "search", unmeasured=True, routed="web-dev"),               # overridden
    _row("o2", "search", unmeasured=True, declined=True),                  # the tier's decline: no override
    _row("o3", "search", "web-dev"),
]


def test_the_image_measures_count_what_the_record_says_they_count() -> None:
    """S3, S4, S10: a request given the note is not "told not measured"; a read request given the note
    does not reach `vision`; only the image rule's override counts as one, not the tier's own decline."""
    measures = _scorer().image_measures({q: {"q": q, "class": c, "expected": e} for q, c, e in IMAGE_SET},
                                        IMAGE_RUN)
    assert measures["make told not measured"] == (2, 5)
    assert measures["  of those, by the tier's own decline"] == (1, 2)
    assert measures["  make given the note"] == (1, 5)
    assert measures["  make missed, by the tier's surface"] == ({"vision": 1, "web-dev": 1}, 5)
    assert measures["read reaching vision"] == (2, 4)
    assert measures["  of those, only after the question back"] == (1, 2)
    assert measures["other overridden to not measured"] == (1, 3)
    assert measures["other on their surface"] == (1, 3)


def test_a_bar_is_the_baseline_plus_two_thirds_of_the_gap_rounded_up() -> None:
    """S5: the plan's rule rounds up (`m19-wave-4-plan.md`, "rounded up"), and the record's bars follow
    from it: 14 of 20 from a baseline of 1, 18 from 14."""
    bar = _scorer().bar_for_gain
    assert (bar(1, 20), bar(14, 20)) == (14, 18)
    assert (bar(0, 20), bar(3, 20)) == (14, 15), "two thirds of the gap is rounded down or to nearest"


def _write(path: Path, rows: list[dict[str, str]]) -> str:
    path.write_text(json.dumps(rows), encoding="utf-8")
    return str(path)


def test_the_scorer_lists_no_question_of_a_held_out_set(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """S6 (D-147 clause 5): `--show` is refused on a held-out set, before any row is read or printed."""
    held = _write(tmp_path / "x_heldout_m19_questions.json",
                  [{"q": "a made-up held-out line", "class": "knowledge", "expected": "assistant"}])
    run = _write(tmp_path / "run.json", [_row("a made-up held-out line", "search")])
    assert _scorer().main([held, run, "--show"]) == 2
    out = capsys.readouterr().out
    assert out.startswith("refused") and "made-up" not in out


def test_a_run_that_does_not_answer_its_set_row_for_row_is_refused(tmp_path: Path) -> None:
    """S9: a run with a row missing, or one from another set, is never scored."""
    rows = [{"q": q, "class": c, "expected": e} for q, c, e in READING_SET]
    set_path = _write(tmp_path / "set.json", rows)
    run = _write(tmp_path / "run.json", READING_RUN[:-1])
    with pytest.raises(AssertionError, match="row for row"):
        _scorer().main([set_path, run])


#: The record's figures (`m19-w4-question-reading-probe.md` §2, §4, §6; D-184 "Measured"), from the
#: committed runs: (set, run, measure, count).
RECORD = [
    *[("notasearch_heldout_m19_questions.json", f"base-notasearch_heldout_m19-{n}.json", m, c)
      for n, m, c in [(1, "not a search caught", 18), (2, "not a search caught", 21), (1, "knowledge caught", 1),
                      (2, "knowledge caught", 3), (1, "genuine on their surface", 30), (2, "genuine on their surface", 28)]],
    *[("image_heldout_m19_questions.json", f"base-image_heldout_m19-{n}.json", "make told not measured", c)
      for n, c in [(1, 2), (2, 1)]],
    ("image_heldout_m19_questions.json", "basew-image_heldout_m19-1.json", "make told not measured", 14),
    *[("notasearch_heldout_m19_questions.json", f"final-notasearch_heldout_m19-{n}.json", m, c)
      for n, m, c in [(1, "not a search caught", 25), (2, "not a search caught", 27), (1, "knowledge caught", 6),
                      (2, "knowledge caught", 6), (1, "genuine asked", 2), (2, "genuine asked", 1)]],
    *[("image_heldout_m19_questions.json", f"final{w}-image_heldout_m19-{n}.json", "make told not measured", c)
      for w, n, c in [("", 1, 8), ("", 2, 8), ("w", 1, 18), ("w", 2, 18)]],
    *[("notasearch_heldout_m19_questions.json", f"review3-notasearch_heldout_m19-{n}.json", m, c)
      for n, m, c in [(1, "not a search caught", 24), (2, "not a search caught", 26), (1, "knowledge caught", 5),
                      (2, "knowledge caught", 5), (1, "genuine asked", 1), (2, "genuine asked", 0),
                      (1, "genuine given the note", 0), (2, "genuine given the note", 0)]],
    *[("image_heldout_m19_questions.json", f"review3{w}-image_heldout_m19-{n}.json", m, c)
      for w, n, m, c in [("", 1, "make told not measured", 4), ("", 2, "make told not measured", 3),
                         ("w", 1, "make told not measured", 14), ("", 1, "read reaching vision", 10),
                         ("", 2, "read reaching vision", 9), ("", 1, "other overridden to not measured", 0),
                         ("", 2, "other overridden to not measured", 0),
                         ("w", 1, "other overridden to not measured", 0)]],
]


def test_the_records_figures_follow_from_the_committed_runs() -> None:
    """The record's held-out figures, at the baseline, the built code (`de8c3f8`) and the code that ships
    (`d324669`), are the scorer's counts of the committed runs; and its bars follow from the baseline's
    lower run by the plan's rule. Counts only: no question is read into this file or printed."""
    scorer = _scorer()
    wrong = []
    for set_name, run_name, measure, count in RECORD:
        qs = {x["q"]: {**x, "class": x.get("class", x.get("group"))}
              for x in json.loads((SETS / set_name).read_text(encoding="utf-8"))}
        rows = json.loads((RUNS / run_name).read_text(encoding="utf-8"))
        assert {r["q"] for r in rows} == set(qs), f"{run_name} does not answer {set_name} row for row"
        measures = (scorer.image_measures if set_name.startswith("image") else scorer.reading_measures)(qs, rows)
        if measures[measure][0] != count:
            wrong.append((run_name, measure, measures[measure][0], count))
    assert not wrong, f"the record's figures and the committed runs disagree (run, measure, runs, record): {wrong}"
    knowledge = min(c for _, r, m, c in RECORD if r.startswith("base-") and m == "knowledge caught")
    made = min(c for _, r, m, c in RECORD if r.startswith("base-image") and m == "make told not measured")
    assert (scorer.bar_for_gain(knowledge, 20), scorer.bar_for_gain(made, 20), scorer.bar_for_gain(14, 20)) == (14, 14, 18)
