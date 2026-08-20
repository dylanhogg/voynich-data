"""Token alignment and the reliability weight."""

from __future__ import annotations

from dataclasses import replace

import pytest

from translations import alignment
from translations.config import CONFIG
from translations.strata import StratumRow


def stratum(**overrides: object) -> StratumRow:
    """A stratum row with everything clean unless overridden."""
    base = StratumRow(
        line_id="f1r:1",
        page_id="f1r",
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
        position="+",
        is_first_line_of_page=True,
        is_last_line_of_page=False,
        has_uncertain=False,
        has_illegible=False,
        has_alternatives=False,
        has_high_ascii=False,
        mismatch_status="exact_match",
        in_consensus=True,
        is_holdout=False,
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_similarity_is_one_for_identical_words() -> None:
    assert alignment.similarity(["ch", "e", "d", "y"], ["ch", "e", "d", "y"]) == 1.0


def test_similarity_counts_glyph_units_not_characters() -> None:
    # One unit differs out of four, so 0.75 — not 1 - 1/5 over the ASCII string.
    assert alignment.similarity(["ch", "e", "d", "y"], ["sh", "e", "d", "y"]) == pytest.approx(0.75)


def test_align_words_pairs_equal_sequences_in_order() -> None:
    left = [["a"], ["b"], ["c"]]
    assert alignment.align_words(left, left) == [(0, 0), (1, 1), (2, 2)]


def test_align_words_opens_a_gap_for_a_missing_word() -> None:
    left = [["a"], ["b"], ["c"]]
    right = [["a"], ["c"]]
    pairs = alignment.align_words(left, right)
    assert [source for source, _ in pairs] == [0, 1, 2]
    assert [target for _, target in pairs].count(None) == 1


def test_reliability_is_agreement_when_nothing_else_is_wrong() -> None:
    assert alignment.reliability(0.8, "aligned", stratum(), False, False) == pytest.approx(0.8)


def test_reliability_compounds_independent_doubts() -> None:
    weight = alignment.reliability(
        1.0, "aligned", stratum(has_uncertain=True, has_illegible=True), True, True
    )
    expected = (
        alignment.PENALTY_UNCERTAIN
        * alignment.PENALTY_ILLEGIBLE
        * alignment.PENALTY_HAPAX
        * alignment.PENALTY_RARE_UNIT
    )
    assert weight == pytest.approx(expected)


def test_reliability_falls_back_when_there_is_no_counterpart() -> None:
    assert alignment.reliability(0.0, "gap", stratum(), False, False) == pytest.approx(
        alignment.PENALTY_NO_COUNTERPART
    )


def test_penalties_are_all_below_one() -> None:
    penalties = (
        alignment.PENALTY_NO_COUNTERPART,
        alignment.PENALTY_UNCERTAIN,
        alignment.PENALTY_ILLEGIBLE,
        alignment.PENALTY_ALTERNATIVES,
        alignment.PENALTY_HAPAX,
        alignment.PENALTY_RARE_UNIT,
    )
    assert all(0.0 < penalty < 1.0 for penalty in penalties)


@pytest.mark.skipif(not CONFIG.default_transcription, reason="config missing")
def test_build_rows_covers_every_zl_token() -> None:
    rows = alignment.build_rows()
    assert len(rows) == 33728
    assert {row.status for row in rows} <= {"aligned", "gap", "no_it_line"}
    assert all(0.0 <= row.reliability <= 1.0 for row in rows)


def test_summary_reports_more_token_agreement_than_line_agreement() -> None:
    summary = alignment.summarise(alignment.build_rows())
    # Phase 1 measured 29.3% of lines identical; tokens must do better than that.
    assert summary["exact_token_agreement"] > 0.5
    assert 0.0 < summary["mean_reliability"] <= 1.0
