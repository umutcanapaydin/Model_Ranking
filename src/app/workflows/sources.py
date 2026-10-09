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
from app.clients.arena import (
    ARENA_BOARDS,
    ArenaClient,
    ArenaDocumentClient,
    ArenaFactualityClient,
    ArenaSearchClient,
    ArenaSearchFactualityClient,
    ArenaVisionClient,
    ArenaWebDevClient,
    parse_arena,
)
from app.clients.arena_slices import ArenaSliceClient
from app.clients.deepswe import DeepSWEClient
from app.clients.epoch import EpochClient
from app.clients.epoch_board import EpochBoardClient
from app.clients.litellm import LiteLLMClient, parse_pricing
from app.clients.openrouter import OpenRouterClient, parse_models
from app.clients.protocols import RawSource
from app.clients.swebench import SweBenchClient, parse_verified
from app.workflows.board_tables import EPOCH_BOARDS as _EPOCH_BOARDS
from app.workflows.ingest import (
    RunContext,
    SourceReport,
    ingest_aider,
    ingest_arena,
    ingest_deepswe,
    ingest_epoch,
    ingest_litellm,
    ingest_openrouter,
    ingest_swebench,
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
    every ingested source can be attributed swept in `litellm` and `openrouter`, which write
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
        name="openrouter",
        client=OpenRouterClient,
        ingest=ingest_openrouter,
        parse=parse_models,
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
)

LOCAL_BUNDLES: tuple[LocalBundle, ...] = (
    LocalBundle(
        name="epoch_swe_bench_verified",
        client_type=EpochClient,
        ingest=ingest_epoch,
        reason="D-101: owner-placed bundle, read from disk; a runtime fetch would breach the boundary",
    ),
    LocalBundle(
        name="epoch_deepswe_external",
        client_type=DeepSWEClient,
        ingest=ingest_deepswe,
        # This one is the sole primary evidence for `agentic-coding`, which is half of the answer
        # Ruling A froze. Without it that surface has nothing to say.
        reason="M5 data boundary: an allowlisted CSV inside the same owner-placed Epoch bundle",
    ),
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
