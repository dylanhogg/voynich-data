"""External cribs and the protocol for using them (plan §4.4).

The catalogue is **empty on purpose**. The zodiac month names, the f116v
marginalia and plant identifications are Phase 3 work (§5), and they cannot be
entered here by hand: this plan is fully automated, so an anchor only enters the
catalogue once it has a checksummed source behind it.

The protocol is implemented now so that anchors can never leak into the search
when they do arrive: an anchor may **rank** finished candidates, and its score is
always reported in its own column, separate from the corpus-derived score. It is
never training data, never a constraint on the LM, and never ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Anchor:
    """One external constraint on a reading."""

    anchor_id: str
    locus: str
    voynich_form: str
    expected_reading: str
    source: str
    confidence: str


CATALOGUE: tuple[Anchor, ...] = ()


def anchor_score(readings: dict[str, str], catalogue: tuple[Anchor, ...] = CATALOGUE) -> float:
    """Share of catalogued anchors a candidate's readings agree with.

    Returns 0.0 for an empty catalogue, which is the current state: no candidate
    gets anchor credit until Phase 3 supplies sourced anchors.
    """
    if not catalogue:
        return 0.0
    hits = sum(
        1 for anchor in catalogue if readings.get(anchor.voynich_form) == anchor.expected_reading
    )
    return hits / len(catalogue)
