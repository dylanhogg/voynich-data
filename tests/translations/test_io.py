"""Loaders read the built artifacts and expose the same counts the reports state."""

from __future__ import annotations

from translations.config import Transcription
from translations.io import load_lines, load_mismatches, load_pages, transcription_text


def test_load_lines() -> None:
    lines = load_lines()
    assert len(lines) == 4072
    assert lines[0].line_id == "f1r:1"
    assert lines[0].text_clean.startswith("fachys.ykal")
    assert len({line.page_id for line in lines}) == 206


def test_load_pages() -> None:
    pages = load_pages()
    assert len(pages) == 226
    assert pages["f1r"]["quire_id"] == "qA"


def test_load_mismatches() -> None:
    mismatches = load_mismatches()
    assert len(mismatches) == 4072
    row = mismatches["f1r:1"]
    assert row.status in {
        "exact_match",
        "normalized_match",
        "high_similarity",
        "content_mismatch",
        "it_missing",
    }
    assert "zl" in row.sources_present


def test_transcription_text_uses_central_cleaning() -> None:
    lines = load_lines()
    mismatches = load_mismatches()
    line = lines[0]
    zl = transcription_text(line, mismatches[line.line_id], Transcription.ZL)
    it = transcription_text(line, mismatches[line.line_id], Transcription.IT)
    assert zl == line.text_clean
    assert it is not None
    assert "<" not in it and "[" not in it


def test_transcription_text_missing_source_is_none() -> None:
    lines = load_lines()
    mismatches = load_mismatches()
    missing = [line for line in lines if "it" not in mismatches[line.line_id].sources_present]
    assert missing, "expected some IT-missing lines"
    assert transcription_text(missing[0], mismatches[missing[0].line_id], Transcription.IT) is None
