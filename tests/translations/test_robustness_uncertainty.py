"""Cross-transcription and uncertainty-sensitivity helpers (real corpus, cheap paths)."""

from __future__ import annotations

from translations.analysis.common import voynich_view
from translations.analysis.robustness import METRICS, metric_row, paired_views
from translations.analysis.uncertainty import alternatives_footprint, metrics
from translations.config import Transcription


def test_metric_row_covers_the_battery() -> None:
    row = metric_row(voynich_view())
    assert set(METRICS) <= set(row)
    assert row["tokens"] == 33728


def test_paired_views_use_exactly_the_same_lines() -> None:
    pair = paired_views(Transcription.IT)
    assert pair is not None
    view, reference = pair
    assert {row.line_id for row in view.rows} == {row.line_id for row in reference.rows}
    assert len(view.rows) == 4061


def test_non_eva_sources_are_available_for_structural_metrics() -> None:
    for source in (Transcription.CD, Transcription.FG, Transcription.GC):
        pair = paired_views(source)
        assert pair is not None, source
        assert pair[0].n_words > 10_000


def test_second_alternative_reading_changes_only_flagged_lines() -> None:
    footprint = alternatives_footprint()
    assert footprint["lines_with_alternatives"] == 584
    assert 0 < footprint["tokens_changed_by_second_option"] < 2000


def test_uncertainty_metrics_shape() -> None:
    row = metrics(voynich_view())
    assert row["lines"] == 4072
    assert 0 < row["hapax_rate"] < 1
