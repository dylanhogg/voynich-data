"""Applying a committed key, and turning glossed tokens into hedged English."""

from __future__ import annotations

import pytest

from translations import render
from translations.decode import KeyedHypothesis, parse_key


def keyed(variant: str, key: dict[str, str]) -> KeyedHypothesis:
    """A keyed hypothesis carrying only what the decode stage reads."""
    return KeyedHypothesis(
        hypothesis_id="H1",
        representation="merged",
        variant=variant,
        key=key,
        gain_per_token=-1.0,
        holdout_gain_per_token=-1.0,
        converged=True,
        p_value=0.5,
    )


def test_variant_string_carries_the_channel_language_and_order() -> None:
    entry = keyed("vulgate_clementine-abjad-o3|fixed-width-3", {})
    assert entry.channel == "fixed-width-3"
    assert entry.width == 3
    assert entry.language == "vulgate_clementine"
    assert entry.transform == "abjad"
    assert entry.order == 3


def test_plain_channel_leaves_units_alone() -> None:
    entry = keyed("clusius_rariorum-o3|plain", {"qo": "a", "ol": "b"})
    assert entry.units(["qo", "ol"]) == ["qo", "ol"]
    assert entry.decode(["qo", "ol"]).plaintext == "ab"


def test_fixed_width_channel_groups_units() -> None:
    entry = keyed("x-o3|fixed-width-2", {"qool": "a"})
    assert entry.units(["qo", "ol", "d"]) == ["qool", "d"]


def test_unknown_units_fall_back_to_the_rare_symbol_and_are_counted() -> None:
    entry = keyed("x-o3|plain", {"qo": "a", "?": "z"})
    decoded = entry.decode(["qo", "never-seen"])
    assert decoded.plaintext == "az"
    assert decoded.n_rare == 1
    assert decoded.key_coverage == pytest.approx(0.5)


def test_units_mapped_to_the_boundary_are_deleted() -> None:
    decoded = keyed("x-o1|plain", {"qo": "a", "ol": "#"}).decode(["qo", "ol"])
    assert decoded.plaintext == "a"
    assert decoded.n_deleted == 1


def test_parse_key_reads_the_search_repr() -> None:
    assert parse_key("{'qo': 'a', 'ol': 'b'}") == {"qo": "a", "ol": "b"}


@pytest.mark.parametrize(
    ("confidence", "band"), [(0.9, "high"), (0.5, "medium"), (0.2, "low"), (0.05, "none")]
)
def test_bands_follow_the_plan_thresholds(confidence: float, band: str) -> None:
    assert render.RenderedToken("daiin", "water", confidence).band == band


def test_speculative_marks_every_band_differently() -> None:
    marks = [
        render.speculative(render.RenderedToken("daiin", "water", confidence))
        for confidence in (0.9, 0.5, 0.2, 0.05)
    ]
    assert marks == ["water", "*water*", "?water?", "⟨daiin⟩(≈water)"]


def test_speculative_falls_back_to_transliteration_with_no_gloss() -> None:
    assert render.speculative(render.RenderedToken("daiin", "", 0.9)) == "⟨daiin⟩"


def test_gated_masks_everything_below_the_medium_band() -> None:
    tokens = [
        render.RenderedToken("a", "water", 0.9),
        render.RenderedToken("b", "fire", 0.2),
        render.RenderedToken("c", "", 0.9),
    ]
    _, gated, confidence = render.render_line(tokens)
    assert gated == "water UNKNOWN UNKNOWN"
    assert confidence == pytest.approx((0.9 + 0.2 + 0.9) / 3)
    assert render.gated_coverage(tokens) == pytest.approx(1 / 3)


def test_an_empty_line_renders_to_empty_strings() -> None:
    assert render.render_line([]) == ("", "", 0.0)
