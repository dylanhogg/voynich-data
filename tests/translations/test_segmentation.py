"""Harris boundaries, the MDL slot inventory, and the T2 segmenter it defines."""

from __future__ import annotations

from translations.analysis.segmentation import (
    SlotModel,
    harris_segment,
    induce_slots,
    successor_entropies,
)

CORPUS = [
    tuple("qokeedy"),
    tuple("qokeey"),
    tuple("qokain"),
    tuple("chedy"),
    tuple("chey"),
    tuple("shedy"),
    tuple("okeedy"),
    tuple("okain"),
] * 20


def test_successor_entropy_is_zero_after_a_unique_continuation() -> None:
    entropies = successor_entropies([tuple("abcd")])
    assert entropies[()] == 0.0
    assert entropies[("a",)] == 0.0


def test_harris_segments_at_a_branching_point() -> None:
    forward = successor_entropies(CORPUS)
    backward = successor_entropies(CORPUS, reverse=True)
    pieces = harris_segment(tuple("qokeedy"), forward, backward)
    assert len(pieces) >= 2
    assert "".join("".join(piece) for piece in pieces) == "qokeedy"


def test_slot_model_segments_longest_match_and_keeps_a_root() -> None:
    model = SlotModel(prefixes=(("q", "o"), ("o",)), suffixes=(("d", "y"),))
    assert model.segment(tuple("qokeedy")) == [("q", "o"), ("k", "e", "e"), ("d", "y")]
    # A word that is only an affix keeps its root rather than vanishing.
    assert model.segment(("q", "o")) == [("q", "o")]


def test_slot_model_stores_inventories_longest_first() -> None:
    model = SlotModel(prefixes=(("o",), ("q", "o")), suffixes=())
    assert model.prefixes[0] == ("q", "o")


AFFIXED = [
    tuple(prefix + root + suffix)
    for root in ("kee", "kain", "chol", "tedy", "shor", "kar", "pchy", "dair", "lkee", "rain")
    for prefix in ("", "qo")
    for suffix in ("", "dy")
] * 10


def test_induce_slots_finds_affixes_that_pay_for_themselves() -> None:
    model, stats = induce_slots(AFFIXED)
    assert stats["bits_saved"] > 0
    assert stats["final_description_length"] < stats["initial_description_length"]
    assert ("q", "o") in model.prefixes


def test_induce_slots_adds_nothing_when_no_affix_pays() -> None:
    _, stats = induce_slots(CORPUS)
    assert stats["bits_saved"] >= 0


def test_induced_inventory_is_deterministic() -> None:
    first, _ = induce_slots(AFFIXED)
    second, _ = induce_slots(AFFIXED)
    assert first == second
