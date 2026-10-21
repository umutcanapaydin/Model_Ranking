"""The one place this project names its external evidence sources (REQ-ING-012).

**Why this module exists, and it is the M6 lesson applied before it could bite again.**
Building the evidence database needs a list of (client, ingest function) pairs. A smoke gate needs
a list of (client, parser) probes. Written independently those are two hand-typed enumerations of
the same five dependencies in two files, and M6 found four separate instances of exactly that shape
— a precedence guard, a YAML wiring predicate, a list of YAML inputs, and a set of smoke-test
endpoints — where every one was missing precisely the member that mattered.

So the list lives here once. `build.py` derives its work from it and `scripts/smoke_deps.py` derives
its probes from it, which means a source cannot be added to the build and forgotten in the gate.

**What this module does NOT solve, stated so nobody reads more into it than is here.** Naming the
sources in one place makes the two consumers agree with each other; it does not make either agree
with reality. That is what `test_sources.py` is for: it walks `src/app/clients/` with `ast` and
fails if a client class exists that this registry neither ingests nor declares a local bundle.
The list of things to check is produced by code, not typed.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from app.clients.aider import AiderClient, parse_polyglot
from app.clients.arc_prize import ArcAgi2Client, parse_arc_agi_2
from app.clients.arena import (
    ARENA_BOARDS,
    ArenaClient,
    ArenaDocumentClient,
    ArenaFactualityClient,
    ArenaImageEditClient,
    ArenaImageToVideoClient,
    ArenaSearchClient,
    ArenaSearchFactualityClient,
    ArenaTextToImageClient,
    ArenaTextToVideoClient,
    ArenaVideoEditClient,
    ArenaVisionClient,
    ArenaWebDevClient,
    parse_arena,
)
from app.clients.arena_slices import ArenaSliceClient
from app.clients.datacurve import DatacurveClient, parse_datacurve
from app.clients.epoch import EpochClient
from app.clients.epoch_board import EpochBoardClient
from app.clients.litellm import LiteLLMClient, parse_pricing
from app.clients.livebench import LiveBenchClient, parse_livebench
from app.clients.metr import MetrClient, parse_metr
from app.clients.models_dev import ModelsDevClient, parse_models_dev
from app.clients.osworld import OSWorldClient, parse_osworld
from app.clients.protocols import RawSource
from app.clients.swebench import SweBenchClient, parse_verified
from app.clients.terminalbench import TerminalBench4Client, parse_terminalbench_4
from app.workflows.board_tables import EPOCH_BOARDS as _EPOCH_BOARDS
from app.workflows.ingest import (
    RunContext,
    SourceReport,
    ingest_aider,
    ingest_arc_agi_2,
    ingest_arena,
    ingest_datacurve,
    ingest_epoch,
    ingest_litellm,
    ingest_livebench,
    ingest_metr,
    ingest_models_dev,
    ingest_osworld,
    ingest_swebench,
    ingest_terminalbench_4,
)

IngestFn = Callable[[sqlite3.Connection, RawSource, RunContext], SourceReport]
ParseFn = Callable[[str], tuple[list[object], int]]


@dataclass(frozen=True)
class RemoteSource:
    """One external dependency, named once for every consumer that needs it."""

    name: str
    client: Callable[[], RawSource]
    ingest: IngestFn
    parse: Callable[..., object]
    minimum_rows: int
    """The floor below which a technically-successful fetch is a FAILED dependency.

    A 200 carrying an empty list is the failure mode this number exists for: it passes a status
    check, passes a parser, and produces a database that answers every question with silence.
    """
    writes_scores: bool = True
    """Whether this source contributes EVIDENCE rows (`scores`) rather than pricing.

    The distinction was implicit until M8 and cost a test its meaning: a guard asserting that
    every ingested source can be attributed swept in `litellm` and `openrouter` (then the second price source), which write
    `pricing` and never appear in `scores.source`, so it demanded citations for data that is
    never cited. Only evidence needs attribution, and only this field says which is which.
    """

    required: bool = True
    """Whether the build refuses to produce an artifact at all without this source.

    **Set False only when the artifact is still honest without it**, and understand what that
    costs: a source is the sole evidence for at least one category, so dropping it does not thin
    the answers on that surface, it empties them. An optional source that fails downgrades the
    build to exit 3 with the affected surface named in `required_operator_actions` — never to a
    silent exit 0, and never to a surface that answers with an empty list instead of saying it has
    no evidence.
    """


@dataclass(frozen=True)
class LocalBundle:
    """A source read from an owner-placed local bundle, never fetched at runtime.

    D-101 and the M5 data-boundary invariant make acquisition the operator's job: the bundle is
    downloaded and unpacked out of band, and this project only ever READS the allowlisted files
    inside it. A runtime fetch would be the violation, not the check.

    **These are ingested, not skipped.** M7-W1 found that the build produced an artifact in which
    `agentic-coding` had zero picks on every query, because the pipeline ingested the five remote
    sources and no local bundle at all — leaving M6's Ruling A (both coding answers, neither
    leading) true in the contract and hollow in the data. A bundle that is absent at build time is
    reported like a failed optional source, never omitted in silence.
    """

    name: str
    client_type: type
    ingest: IngestFn
    reason: str

    @property
    def client_class(self) -> str:
        """The class name, derived rather than restated, for the registry-coverage test."""
        return self.client_type.__name__


REMOTE_SOURCES: tuple[RemoteSource, ...] = (
    RemoteSource(
        name="litellm",
        client=LiteLLMClient,
        ingest=ingest_litellm,
        parse=parse_pricing,
        # The feed carries thousands of entries; a hundred is a shape change, not a slow day.
        minimum_rows=100,
        writes_scores=False,  # pricing, not evidence
    ),
    RemoteSource(
        # D-194: the second price source, in OpenRouter's place; the makers' own entries only.
        name="models_dev",
        client=ModelsDevClient,
        ingest=ingest_models_dev,
        parse=parse_models_dev,
        minimum_rows=50,
        writes_scores=False,  # pricing, not evidence
    ),
    RemoteSource(
        name="swebench",
        client=SweBenchClient,
        ingest=ingest_swebench,
        parse=parse_verified,
        minimum_rows=1,
    ),
    RemoteSource(
        name="aider",
        client=AiderClient,
        ingest=ingest_aider,
        parse=parse_polyglot,
        minimum_rows=1,
    ),
    # D-194 (#265): TB 4.0's leaderboard, Apache-2.0, in place of Epoch's copy of TB 2.0. 21 submissions
    # on 2026-10-13; ten is a broken listing, not a quiet month.
    # D-194 (#265): ARC Prize's own runs on ARC-AGI-2's public evaluation set, MIT, in place of Epoch's copy
    # of its leaderboard. Read from the derivation committed at a pinned revision (`app.clients.arc_prize`),
    # so it fails only on a broken file; 30 settings is well under the 50 the derivation holds.
    RemoteSource(
        name="arc_agi_2",
        client=ArcAgi2Client,
        ingest=ingest_arc_agi_2,
        parse=parse_arc_agi_2,
        minimum_rows=30,
    ),
    RemoteSource(
        name="terminalbench_4",
        client=TerminalBench4Client,
        ingest=ingest_terminalbench_4,
        parse=parse_terminalbench_4,
        minimum_rows=10,
    ),
    RemoteSource(
        name="arena",
        client=ArenaClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=250,
        # W-024. This was **1**, which cannot catch anything: a "successful" fetch of a single row
        # would have passed. It matters more now that the board is read as an ordered PREFIX of a
        # 10,359-row split — the stop condition trusts that ordering, and this floor is what turns
        # a wrong guess into a FAILED dependency instead of a silently thin `assistant` surface.
        # The board has carried ~389 models; 250 is comfortably below any real day and far above
        # any truncation.
        # OPTIONAL by the owner's ruling at M7-W1 (W-024, ADR D-121). The HF datasets-server has
        # been returning HTTP 500 for hours, and making the whole artifact unbuildable by one
        # upstream outage would block the milestone on somebody else's incident. It is optional
        # only because the serving surface DISCLOSES a missing source rather than answering with
        # an empty list — arena is the sole evidence for `assistant`, so without it that surface
        # has nothing to say and must say so.
        required=False,
    ),
    # ── M14-W2: two more boards of the SAME dataset, under the same grant ──────────────────
    #
    # They are OPTIONAL for the same reason `arena` is (D-121): the serving surface discloses a
    # missing source rather than answering with an empty list, and one upstream incident must not
    # make the whole artifact unbuildable. Each is the sole evidence for its own surface, so
    # without it that surface has nothing to say and says so.
    RemoteSource(
        name="arena_document",
        client=ArenaDocumentClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=ARENA_BOARDS["document"].minimum_rows,  # one source of truth (M14-W2 m2)
        required=False,
    ),
    RemoteSource(
        name="arena_factuality",
        client=ArenaFactualityClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=ARENA_BOARDS["text_factuality"].minimum_rows,
        required=False,
    ),
    # ── M15-W3: three more boards of the same dataset, chosen by measurement (W1's survey) ────
    #
    # OPTIONAL for the reason every Arena board is (D-121), and each is the sole evidence for its
    # own surface: without it that surface says so rather than answering.
    RemoteSource(
        name="arena_vision",
        client=ArenaVisionClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=ARENA_BOARDS["vision"].minimum_rows,
        required=False,
    ),
    RemoteSource(
        name="arena_search",
        client=ArenaSearchClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=ARENA_BOARDS["search"].minimum_rows,
        required=False,
    ),
    RemoteSource(
        name="arena_search_factuality",
        client=ArenaSearchFactualityClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=ARENA_BOARDS["search_factuality"].minimum_rows,
        required=False,
    ),
    # D-216 (#265): Datacurve's own DeepSWE leaderboard, public, no token (70 configurations on
    # 2026-10-21). OPTIONAL as every sole-evidence board is (D-121): a night the site fails is carried
    # by the refresh (D-156), or past the carry window `agentic-coding` says it has no evidence; it never
    # fails another source's night. The floor is half the recorded board, as Arena's are: below it, a
    # cut file, not a quiet month.
    RemoteSource(
        name="datacurve_deepswe",
        client=DatacurveClient,
        ingest=ingest_datacurve,
        parse=parse_datacurve,
        minimum_rows=35,
        required=False,
    ),
    # M21-W1 (#185): LMArena's own WebDev board, `web-dev`'s primary under CC-BY-4.0. OPTIONAL as
    # every Arena board is (D-121): without it the surface says it has no evidence.
    RemoteSource(
        name="arena_webdev",
        client=ArenaWebDevClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=ARENA_BOARDS["webdev"].minimum_rows,
        required=False,
    ),
    # #378 (D-218 clause 1): LMArena's five image and video boards, each its own surface's only
    # evidence, ranked on quality only. OPTIONAL as every Arena board is (D-121).
    *(
        RemoteSource(
            name=ARENA_BOARDS[config].id,
            client=client,
            ingest=ingest_arena,
            parse=parse_arena,
            minimum_rows=ARENA_BOARDS[config].minimum_rows,
            required=False,
        )
        for config, client in (
            ("image_edit", ArenaImageEditClient),
            ("text_to_image", ArenaTextToImageClient),
            ("image_to_video", ArenaImageToVideoClient),
            ("text_to_video", ArenaTextToVideoClient),
            ("video_edit", ArenaVideoEditClient),
        )
    ),
    # #379 (D-219): OSWorld-Verified's own workbook, `computer-use`'s second board: 20 general models at 100
    # steps on 2026-10-22. OPTIONAL (D-121): a night the site fails is carried by the refresh (D-156), and
    # the surface still answers from its primary. The floor is half the recorded board: below it, a cut file.
    RemoteSource(
        name="osworld_verified",
        client=OSWorldClient,
        ingest=ingest_osworld,
        parse=parse_osworld,
        minimum_rows=10,
        required=False,
    ),
    # #379 (D-218 clause 2, D-219): METR's own time-horizon file, `long-tasks`'s only board: 26 models on
    # 2026-10-22. OPTIONAL as every sole-evidence board is (D-121): a night the site fails is carried by the
    # refresh (D-156), or past the carry window the surface says it has no evidence. Floor: half the board.
    RemoteSource(
        name="metr_time_horizons",
        client=MetrClient,
        ingest=ingest_metr,
        parse=parse_metr,
        minimum_rows=13,
        required=False,
    ),
    # #379 (D-219): LiveBench 2.0's own release files, a board of `everyday`: 49 models in release 2026-10-14.
    # OPTIONAL (D-121): a night the site fails is carried (D-156), and the surface answers from its primary.
    RemoteSource(
        name="livebench",
        client=LiveBenchClient,
        ingest=ingest_livebench,
        parse=parse_livebench,
        minimum_rows=24,
        required=False,
    ),
)

LOCAL_BUNDLES: tuple[LocalBundle, ...] = (
    LocalBundle(
        name="epoch_swe_bench_verified",
        client_type=EpochClient,
        ingest=ingest_epoch,
        reason="D-101: owner-placed bundle, read from disk; a runtime fetch would breach the boundary",
    ),
    # D-216 (#265): `epoch_deepswe_external`, Epoch's copy of DeepSWE, is no longer read from the bundle;
    # `agentic-coding` ranks on Datacurve's own dataset (`datacurve_deepswe` above).
)


#: M17-W2 (#22, D-164): Arena's category slices, a FOURTH kind of registry entry and the Epoch
#: boards' shape again: many boards declared as data (`ARENA_SLICES`), read through one client,
#: named once here; the boards are `app.clients.arena_slices.ARENA_SLICES`. One download per
#: config carries every slice of it.
ARENA_SLICE_CLIENT = ArenaSliceClient


#: The one client every declared board reads through. Held here rather than named as a string
#: wherever it is needed, so the registry-coverage test derives it instead of typing it.
EPOCH_BOARD_CLIENT = EpochBoardClient

#: The Epoch boards are declared in `app.workflows.board_tables` (#214), which imports no client; the
#: refresh reads them from here as before.
EPOCH_BOARDS = _EPOCH_BOARDS
