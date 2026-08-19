"""The Phase 0 entrypoint: reporting grid, strata summary, manifest."""

from __future__ import annotations

from translations.phase0 import GRID, corpus_grid, strata_summary
from translations.strata import build_strata


def test_grid_covers_tokenizer_comma_and_transcription() -> None:
    assert len(GRID) == 8


def test_corpus_grid_reports_every_cell() -> None:
    grid = corpus_grid()
    assert len(grid) == len(GRID)
    zl_chars = grid["T0-char|CB=break|zl"]
    zl_glyphs = grid["T1-glyph|CB=break|zl"]
    assert zl_chars["lines"] == 4072
    assert zl_glyphs["units"] < zl_chars["units"]
    # The comma policy changes the word count but never the unit count.
    assert grid["T0-char|CB=join|zl"]["words"] < zl_chars["words"]
    assert grid["T0-char|CB=join|zl"]["units"] == zl_chars["units"]


def test_strata_summary_totals() -> None:
    summary = strata_summary(build_strata())
    assert sum(summary["currier_language"].values()) == 4072
    assert summary["consensus_lines"] == 3414
    assert summary["pages"] == 206
    assert 0 < summary["holdout_pages"] < summary["pages"]
