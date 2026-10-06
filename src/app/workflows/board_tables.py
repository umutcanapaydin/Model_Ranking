"""The boards the build declares as data, and the citations they oblige (W-125, M18-W6).

The serving process reads these tables to attribute what it serves (`app.workflows.rank`). They
were defined in the clients that fetch the boards, so serving loaded the clients, their parsers and
the HTTP client (W-125). They import nothing from a client; the clients import them from here.
"""

from __future__ import annotations

from dataclasses import dataclass

METRIC = "elo"
HARNESS = "arena-crowd"
#: The ratings an Arena Elo board can plausibly carry; anything outside is refused and counted.
ELO_BAND = (0.0, 5000.0)
#: Agent Arena boards (M17-W3, #37) publish IPS scores (τ̂), not Bradley-Terry Elo: measured from
#: -0.25 to 0.35 on 2026-09-25, so negative values are real. Their own metric, harness and band.
IPS_METRIC = "ips"
AGENT_HARNESS = "arena-agent"
IPS_BAND = (-1.0, 1.0)

#: The Creative Commons licences served data is under, each in the project's `CC-BY-4.0` convention
#: and with the URI CC BY 4.0 section 3(a)(1)(C) asks a notice to carry (#124).
CC_BY_4 = "CC-BY-4.0, https://creativecommons.org/licenses/by/4.0/"
CC_BY_NC_4 = "CC-BY-NC-4.0, https://creativecommons.org/licenses/by-nc/4.0/"

# Epoch's OWN prescribed citation, quoted verbatim from the bundle's README, plus the
# licence token. Its URL and the client's are different things on purpose (W4 review
# BLOCKING-3, second half): `epoch.ai/benchmarks` is the citation target Epoch requires;
# `app.clients.epoch.EPOCH_BUNDLE_URL` is where the bytes were acquired. The
# licence is written ONCE (review MINOR-8 \u2014 it previously appeared twice, in two
# spellings, so a test could substring-match it).
EPOCH_CITATION = (
    "Epoch AI, \u2018Capabilities & benchmarking\u2019. Published online at epoch.ai. "
    "Retrieved from \u2018https://epoch.ai/benchmarks\u2019 [online resource]."
)
EPOCH_ATTRIBUTION = f"{EPOCH_CITATION} ({CC_BY_4})"

#: #124: the boards Epoch compiles from other publishers. Epoch's hub "also includes data sourced
#: from external projects, which retains its original licensing", and users "should credit the
#: original sources as indicated" (epoch.ai/benchmarks/use-this-data, read 2026-10-06). Each is
#: credited to the source its file's `Source` column names (the bundle of 2026-10-06), then to
#: Epoch's compilation. None claims a licence: Epoch's grant does not reach them, and what each
#: source's own terms permit is the owner's ruling (#88).
EPOCH_EXTERNAL_ATTRIBUTION: dict[str, str] = {
    source: f"{credit}. Via {EPOCH_CITATION}"
    for source, credit in (
        ("epoch_arc_agi", "ARC-AGI scores: ARC Prize leaderboard, https://arcprize.org/leaderboard"),
        ("epoch_deepswe_external", "DeepSWE scores: Datacurve's DeepSWE leaderboard, https://deepswe.datacurve.ai/"),
        ("epoch_mmlu", "MMLU scores: Stanford CRFM's HELM Lite leaderboard, "
                       "https://crfm.stanford.edu/helm/lite/latest/#/leaderboard/mmlu, and the model makers' "
                       "technical reports Epoch names for its other rows"),
        ("epoch_terminalbench", "Terminal-Bench 2.0 scores: Terminal-Bench v2 leaderboard, "
                                "https://www.tbench.ai/leaderboard/terminal-bench/2.0"),
        ("epoch_webdev", "WebDev Arena scores: LMArena's WebDev Arena leaderboard, https://arena.ai/leaderboard"),
    )
}

#: LMArena's dataset, under its card's CC-BY-4.0 grant (D-101). Here, not in its client, so the serving
#: process and the client read one string (W-125).
ARENA_ATTRIBUTION = (
    "Arena leaderboard data \u00a9 LMArena \u2014 lmarena-ai/leaderboard-dataset, "
    f"https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset ({CC_BY_4})"
)


@dataclass(frozen=True)
class ArenaSlice:
    """One category slice of one config, declared as data and stored as its own board."""

    config: str
    category: str
    #: Rows on the slice's publish date when it was declared (2026-09-13, measured 2026-09-24).
    measured_rows: int
    #: The value column and its metric. Arena's text and vision boards publish Bradley-Terry Elo in
    #: `rating`; the Agent Arena boards (M17-W3) publish IPS scores in `score` (D-105: never mixed).
    value_column: str = "rating"
    metric: str = METRIC
    #: A board that is a whole config (the Agent Arena ones) names itself; a slice's name is derived.
    source_id: str | None = None
    label: str | None = None

    @property
    def source_name(self) -> str:
        """The `scores.source` id. Distinct from every `overall` board's id (`arena_<config>`)."""
        return self.source_id or f"arena_{self.config}_{self.category}"

    @property
    def benchmark(self) -> str:
        """The label rankings join on: shared with no other board, or two boards merge (M14-W2)."""
        return self.label or f"Arena {self.config} ({self.category})"

    @property
    def harness(self) -> str:
        return AGENT_HARNESS if self.metric == IPS_METRIC else HARNESS

    @property
    def band(self) -> tuple[float, float]:
        return IPS_BAND if self.metric == IPS_METRIC else ELO_BAND

    @property
    def minimum_rows(self) -> int:
        """Half the measured count: below any real day, far above a truncated file (W-024)."""
        return self.measured_rows // 2

    @property
    def maximum_rows(self) -> int:
        """Four times the measured count: far above a board that grew, far below a file built to
        fill the artifact (security re-look 3, S-R3-5: 100,000 rows where 402 were declared)."""
        return self.measured_rows * 4

    def bounds_problem(self, rows: int) -> str | None:
        """Why `rows` parsed rows are not this slice, or None. The ONE rule the build, the smoke
        probe and the contract test hold a slice to (final review M1)."""
        if rows < self.minimum_rows:
            return f"parsed {rows} rows, below its floor of {self.minimum_rows}"
        if rows > self.maximum_rows:
            return f"parsed {rows} rows, over its ceiling of {self.maximum_rows}"
        return None


def _slices(config: str, measured: dict[str, int]) -> tuple[ArenaSlice, ...]:
    return tuple(ArenaSlice(config, category, rows) for category, rows in measured.items())


#: The 35 boards the owner ruled on 2026-09-24: every meaningful slice. Left out, each for its
#: reason (issue #22): `overall` (read by `ArenaClient`), `exclude_ties` (a
#: method variant), `hard_prompts_english` (the intersection of two slices taken here) and
#: `vision/creative_writing` (no rows on the newest date).
ARENA_SLICES: tuple[ArenaSlice, ...] = (
    *_slices("text", {
        "english": 402,
        "non_english": 402,
        "hard_prompts": 402,
        "instruction_following": 402,
        "creative_writing": 400,
        "multi_turn": 400,
        "coding": 397,
        "math": 384,
        "longer_query": 380,
        "expert": 352,
        "chinese": 373,
        "russian": 366,
        "german": 299,
        "spanish": 283,
        "french": 281,
        "korean": 269,
        "japanese": 265,
        "polish": 222,
        "industry_software_and_it_services": 402,
        "industry_writing_and_literature_and_language": 401,
        "industry_entertainment_and_sports_and_media": 400,
        "industry_life_and_physical_and_social_science": 400,
        "industry_business_and_management_and_financial_operations": 395,
        "industry_mathematical": 379,
        "industry_legal_and_government": 375,
        "industry_medicine_and_healthcare": 371,
    }),
    *_slices("vision", {
        "english": 152,
        "chinese": 117,
        "diagram": 108,
        "ocr": 108,
        "homework": 102,
        "creative_writing_vision": 90,
        "humor": 84,
        "entity_recognition": 48,
        "captioning": 34,
    }),
    # M17-W3 (#37, #24; owner ruling 2026-09-25): the six Agent Arena configs, each a board of
    # its own `overall` category, 43 rows on 2026-09-24. IPS scores in `score`, higher is better
    # (the dataset's own `rank`), negative values real.
    *(ArenaSlice(config, "overall", 43, value_column="score", metric=IPS_METRIC,
                 source_id=f"arena_{config}", label=label)
      for config, label in (
          ("agent", "Agent Arena"),
          ("agent_bash_recovery_steps", "Agent Arena (bash recovery steps)"),
          ("agent_praise_complaint", "Agent Arena (praise and complaint)"),
          ("agent_steerability", "Agent Arena (steerability)"),
          ("agent_task_outcome_explicit", "Agent Arena (explicit task outcome)"),
          ("agent_tool_hallucination", "Agent Arena (tool hallucination)"),
      )),
)
