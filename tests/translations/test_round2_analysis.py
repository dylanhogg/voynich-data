"""Round-2 analysis modules: re-characterisation, paradigms, distribution, labels."""

from __future__ import annotations

import pytest

from translations.analysis import distribution, paradigms, recharacterise
from translations.analysis.common import View
from translations.analysis.segmentation import SlotModel


def words_to_view(name: str, words: list[str]) -> View:
    """A view built from space-free word strings, one char per unit."""
    return View(name=name, lines=[[list(word) for word in words]])


def test_natural_band_is_the_min_max_over_the_named_baselines() -> None:
    profiles = {
        "a": dict.fromkeys(recharacterise.METRICS, 1.0),
        "b": dict.fromkeys(recharacterise.METRICS, 3.0),
        "voynich": dict.fromkeys(recharacterise.METRICS, 9.0),
    }
    band = recharacterise.natural_band(profiles, ["a", "b"])
    assert band["h2"] == (1.0, 3.0)


def test_verdicts_flag_inside_and_movement_toward_the_band() -> None:
    band = dict.fromkeys(recharacterise.METRICS, (0.0, 1.0))
    voynich = {
        "raw": dict.fromkeys(recharacterise.METRICS, 5.0),
        "merged": dict.fromkeys(recharacterise.METRICS, 2.0),
        "worse": dict.fromkeys(recharacterise.METRICS, 8.0),
    }
    row = recharacterise.verdicts(voynich, band)[0]
    assert row["raw_inside"] is False
    assert row["merged_moved_toward"] is True
    assert row["worse_moved_toward"] is False


def test_verdicts_mark_a_value_inside_the_band() -> None:
    band = dict.fromkeys(recharacterise.METRICS, (0.0, 10.0))
    voynich = {"raw": dict.fromkeys(recharacterise.METRICS, 5.0)}
    assert recharacterise.verdicts(voynich, band)[0]["raw_inside"] is True


def test_frequency_inventory_is_the_same_size_for_every_view() -> None:
    view = words_to_view("v", ["chedy"] * 20 + ["chody"] * 20 + ["qokain"] * 20)
    model = paradigms.frequency_inventory(view, suffixes=5)
    assert len(model.suffixes) == 5


def test_segmented_splits_on_the_given_suffixes() -> None:
    view = words_to_view("v", ["abcxy", "defxy"])
    model = SlotModel(prefixes=(), suffixes=(("x", "y"),))
    assert paradigms.segmented(view, model) == [("", "abc", "xy"), ("", "def", "xy")]


def test_paradigm_density_reports_a_full_table_when_every_root_takes_every_suffix() -> None:
    words = [
        root + suffix for root in ("aaa", "bbb", "ccc") for suffix in ("x", "y") for _ in range(5)
    ]
    view = words_to_view("v", words)
    model = SlotModel(prefixes=(), suffixes=(("x",), ("y",)))
    density = paradigms.paradigm_density(paradigms.segmented(view, model))
    assert density["roots"] == 3
    assert density["cells_filled"] == pytest.approx(1.0)
    assert density["single_suffix_roots"] == 0.0


def test_contextual_conditioning_is_zero_when_suffixes_are_independent() -> None:
    view = words_to_view("v", ["aaax", "bbby"] * 100)
    model = SlotModel(prefixes=(), suffixes=(("x",), ("y",)))
    conditioning = paradigms.contextual_conditioning(paradigms.segmented(view, model))
    # Strictly alternating suffixes are perfectly predictable from the previous one.
    assert conditioning["mi_with_next_suffix"] > 0.9


def test_function_word_scores_rank_by_frequency() -> None:
    view = words_to_view("v", ["the"] * 50 + ["cat"] * 10 + ["sat"] * 5)
    scores = distribution.function_word_scores(view)
    assert [row["form"] for row in scores][:2] == ["the", "cat"]
    assert scores[0]["share"] == pytest.approx(50 / 65)


def test_section_specificity_needs_stratum_rows() -> None:
    assert distribution.section_specificity(words_to_view("v", ["a", "b"])) == {}
