"""Bounded YAML loading for the project's three curated inputs (W-005).

`yaml.safe_load` blocks code execution. It does not block **alias expansion**: a small document can
declare an anchor, alias it into itself repeatedly, and expand to gigabytes while being parsed —
the "billion laughs" shape. M4's security review measured it here: MemoryError in about ten seconds
under a 1 GiB limit, from a file of a few hundred bytes.

**Correction, measured by two review seats at M6-W3:** the M4 note says `safe_load` itself raises
MemoryError in about ten seconds. It does not — PyYAML shares constructed objects between aliases,
so the attack document loads in about a millisecond. The blowup is real and it is DOWNSTREAM: the
same object serialised with `json.dumps` measured 2.29 GB. The control belongs exactly where it is,
before anything walks the result; the original description of where the cost lands was wrong and is
not repeated here.

That was ACCEPTED at M4 with a stated trigger, and the trigger is what matters now. Both YAML inputs
were repo-committed data with no untrusted producer, so the boundary was theoretical. **M6 puts a
network surface in front of the same process.** Nothing in `/v1` reads YAML today, and this guard is
not a claim that it does — it is the ledger row's own condition being met: the trust boundary changed
when the deployment shape changed, and a guard installed after the first untrusted producer appears
is a guard installed too late.

**What this does NOT do.** It does not parse YAML more safely than PyYAML does; it bounds what the
parser is given and what the parser is allowed to expand into. The size limit is the cheap half; the
alias limit is the half that matters, because expansion is where a small input becomes a large one.
"""

from __future__ import annotations

from typing import Any

import yaml

#: Curated files are small: the largest shipped one is a few tens of KB. A megabyte is two orders of
#: magnitude of headroom and still refuses anything that could plausibly be an expansion attack's
#: source document.
MAX_YAML_BYTES = 1_048_576

#: The node budget an expanded document may not exceed. The shipped curated files compose to a few
#: thousand nodes, so this is ample headroom and still two orders of magnitude below the point where
#: expansion becomes a memory problem.
MAX_EXPANDED_NODES = 500_000


class YamlGuardError(yaml.YAMLError, ValueError):
    """A document was refused before it was materialised. Loud, never partially applied.

    **Inherits `yaml.YAMLError`, and that is a contract requirement rather than tidiness.** The
    first version subclassed `ValueError` alone, so every caller's `except yaml.YAMLError` handler
    was bypassed and `SourceError` was never raised — malformed roster YAML went from a clean
    `exit 2` to an uncaught traceback and `exit 1`, and in that CLI `exit 1` means "stale rosters
    found". A CI cadence job would have read a parse failure as a staleness result. CLI exit codes
    are a K.8 frozen contract; a new exception type is a change to it.

    `ValueError` is retained so the guard's own callers can keep catching it as a value error.
    """


def _expanded_size(node: yaml.Node, memo: dict[yaml.Node, int], in_progress: set[yaml.Node]) -> int:
    """How many nodes this subtree becomes once aliases are resolved.

    **This is the whole guard, and the first version did not have it.** That version counted alias
    TOKENS and capped the count, which cannot bound expansion: the measured attack uses only 63
    aliases and expands to 9^8 nodes, because each level aliases the level below it and the growth
    is multiplicative in DEPTH, not additive in count. A flat count is the wrong instrument for an
    exponential quantity — it passed the exact document it was written to refuse.

    `yaml.compose` builds the graph with aliases as SHARED references, so walking it is linear in
    the document's real size. The multiplication happens here, in integers, instead of in memory.
    """
    # **Both of these are per-CALL, and that is the whole point.** The first version kept the
    # in-progress set at module scope and never cleared it on the raise path, so one hostile
    # document left node addresses behind and CPython recycled them into the next parse: measured
    # by the W3 Tester at 159 of 160 legitimate loads of `data/plans.yaml` refused as recursive
    # after a single attack. The same change had just routed the remote-fed Aider input through
    # here, so one hostile HTTP body would have persistently disabled YAML ingestion — a denial of
    # service introduced by the fix for a denial of service.
    # Keyed on the NODE, not `id(node)`. `yaml.Node` is hashable by identity, so this costs nothing
    # and removes a lifetime argument: an id collision used to produce a wrong count, and since the
    # cycle check went in it would produce a spurious "recursive anchor" refusal — the same denial
    # of service that fix closed, arriving by a different route. The code review raised this in
    # round 1 and I did not take it; a lifetime argument is exactly what failed the round after.
    key = node
    if key in memo:
        return memo[key]
    # A node reached again while it is still being counted is a CYCLE, and a cycle expands without
    # bound. The first version seeded the memo with 1 and let the recursion unwind, which scored a
    # self-referential anchor at 12 and let it through. Unbounded is not small.
    if key in in_progress:
        raise YamlGuardError("document contains a recursive anchor, which expands without bound")
    in_progress.add(key)
    total = 1
    if isinstance(node, yaml.SequenceNode):
        total += sum(_expanded_size(child, memo, in_progress) for child in node.value)
    elif isinstance(node, yaml.MappingNode):
        total += sum(
            _expanded_size(k, memo, in_progress) + _expanded_size(v, memo, in_progress)
            for k, v in node.value
        )
    in_progress.discard(key)
    memo[key] = total
    return total


def safe_load_bounded(raw: object, *, what: str) -> Any:
    """`yaml.safe_load` with a size bound and an EXPANSION bound, both fail-closed.

    `what` names the input in the error, because "a YAML file was too large" is not actionable and
    this project's rule is that a refusal says which artefact it refused.
    """
    if not isinstance(raw, str):
        msg = f"{what}: expected raw YAML text, got {type(raw).__name__}"
        raise YamlGuardError(msg)

    size = len(raw.encode("utf-8"))
    if size > MAX_YAML_BYTES:
        msg = f"{what}: {size} bytes exceeds the {MAX_YAML_BYTES}-byte curated-input limit"
        raise YamlGuardError(msg)

    # Compose first: this resolves the anchor/alias GRAPH without materialising the expansion, so
    # the cost here is the document's real size, not its expanded size.
    try:
        node = yaml.compose(raw, Loader=yaml.SafeLoader)
    except yaml.YAMLError as exc:
        msg = f"{what}: not parseable as YAML: {exc}"
        raise YamlGuardError(msg) from exc
    if node is None:
        return None

    expanded = _expanded_size(node, {}, set())
    if expanded > MAX_EXPANDED_NODES:
        msg = (
            f"{what}: expands to {expanded} nodes, past the {MAX_EXPANDED_NODES} limit — alias "
            "expansion is how a small curated file becomes a large one in memory"
        )
        raise YamlGuardError(msg)

    return yaml.safe_load(raw)
