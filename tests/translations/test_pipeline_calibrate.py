"""The pipeline's null model and confidence, and the isotonic calibration fit."""

from __future__ import annotations

import random

import numpy as np
import pytest

from translations import calibrate, pipeline
from translations.analysis.common import View
from translations.calibrate import CalibrationMap, fit_alphabet, isotonic, raw_score
from translations.decode import KeyedHypothesis
from translations.gloss import Gloss
from translations.lexicon import whitakers
from translations.strata import StratumRow


def keyed(key: dict[str, str]) -> KeyedHypothesis:
    """A plain-channel keyed hypothesis."""
    return KeyedHypothesis(
        hypothesis_id="H1",
        representation="merged",
        variant="clusius_rariorum-o3|plain",
        key=key,
        gain_per_token=-1.0,
        holdout_gain_per_token=-1.0,
        converged=True,
        p_value=0.5,
    )


def stratum(line_id: str) -> StratumRow:
    """A stratum row with only the fields the pipeline reads."""
    return StratumRow(
        line_id=line_id,
        page_id=line_id.split(":")[0],
        folio_id="f1",
        quire_id="A",
        side="r",
        line_number=1,
        section="herbal",
        page_section="herbal",
        page_section_disputed=False,
        currier_language="A",
        hand="1",
        line_type="paragraph",
        illustration_type="H",
        position="@",
        is_first_line_of_page=True,
        is_last_line_of_page=True,
        has_uncertain=False,
        has_illegible=False,
        has_alternatives=False,
        has_high_ascii=False,
        mismatch_status="exact_match",
        in_consensus=True,
        is_holdout=False,
    )


def test_permuted_keys_keep_the_letter_multiset() -> None:
    key = {"a": "x", "b": "y", "c": "z"}
    for permuted in pipeline.permuted_keys(key, random.Random(0), 5):
        assert sorted(permuted.values()) == sorted(key.values())
        assert set(permuted) == set(key)


def test_raw_score_is_zero_without_a_gloss() -> None:
    assert raw_score(None, 1.0, 1.0) == 0.0
    assert raw_score(Gloss("x", "x", 1.0, "lexicon", ""), 0.5, 0.5) == pytest.approx(0.25)


def test_isotonic_is_monotone_and_pools_violators() -> None:
    scores = np.array([0.1, 0.2, 0.3, 0.4])
    outcomes = np.array([0.0, 1.0, 0.0, 1.0])
    levels, fitted = isotonic(scores, outcomes)
    assert levels == [0.1, 0.2, 0.3, 0.4]
    assert fitted == sorted(fitted)
    assert fitted[1] == fitted[2] == pytest.approx(0.5)


def test_calibration_map_interpolates_and_round_trips() -> None:
    fitted = CalibrationMap("H1", (0.0, 1.0), (0.0, 1.0), 10, 1.0, 0.9, "latin", "substitution")
    assert fitted(0.5) == pytest.approx(0.5)
    assert CalibrationMap.from_dict(fitted.as_dict()) == fitted


def test_an_empty_map_is_never_confident() -> None:
    assert CalibrationMap("H1", (), (), 0, 0.0, 0.0, "x", "y")(1.0) == 0.0


def test_fit_alphabet_drops_words_using_rare_letters() -> None:
    assert fit_alphabet(["aa", "ab", "az"], size=2) == ["aa", "ab"]


def test_transform_words_matches_the_language_model_assumption() -> None:
    assert calibrate.transform_words(["salve"], "abjad") == ["slv"]
    assert calibrate.transform_words(["salve"], "plain") == ["salve"]


def test_null_p_values_are_bounded_by_the_number_of_permutations() -> None:
    lexicon = whitakers.build_lexicon([whitakers.Entry("ab", ("ab",), "N", "A", ("thing",))])
    cache = pipeline.GlossCache(lexicon)
    words = [["x", "y"], ["y", "x"]]
    entry = keyed({"x": "a", "y": "b"})
    lengths = {1: 1.0, 2: 1.0}
    real = pipeline._scores(words, entry, entry.key, cache, lengths)
    nulls = pipeline.null_p_values(words, entry, real, cache, lengths, random.Random(0), count=4)
    assert ((nulls >= 1 / 5) & (nulls <= 1.0)).all()


def test_translate_renders_every_line_and_hedges_by_reliability() -> None:
    lexicon = whitakers.build_lexicon([whitakers.Entry("ab", ("ab",), "N", "A", ("thing",))])
    view = View(name="t", lines=[[["x", "y"]]], rows=[stratum("f1r:1")])
    entry = keyed({"x": "a", "y": "b"})
    fitted = CalibrationMap("H1", (0.0, 1.0), (0.0, 1.0), 10, 1.0, 1.0, "latin", "substitution")
    lines = pipeline.translate(
        view,
        entry,
        pipeline.GlossCache(lexicon),
        fitted,
        {("f1r:1", 0): 0.5},
        {},
        {},
        random.Random(0),
    )
    assert len(lines) == 1
    token = lines[0].tokens[0]
    assert token.intermediate == "ab"
    assert token.english == "thing"
    assert token.confidence <= 0.5  # the reliability weight caps it


def test_translate_works_on_a_view_with_no_stratum_rows() -> None:
    lexicon = whitakers.build_lexicon([whitakers.Entry("ab", ("ab",), "N", "A", ("thing",))])
    view = View(name="control", lines=[[["x", "y"]]])
    fitted = CalibrationMap("H1", (0.0, 1.0), (0.0, 1.0), 10, 1.0, 1.0, "latin", "substitution")
    lines = pipeline.translate(
        view,
        keyed({"x": "a", "y": "b"}),
        pipeline.GlossCache(lexicon),
        fitted,
        {},
        {},
        {},
        random.Random(0),
    )
    assert lines[0].line_id == "control:1"
    assert lines[0].tokens[0].reliability == 1.0
