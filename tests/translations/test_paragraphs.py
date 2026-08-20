"""Paragraph blocks derived from the IVTFF markers."""

from __future__ import annotations

from translations import paragraphs
from translations.io import Line
from vcat.text_processing import inline_tags


def line(line_id: str, page_id: str, number: int, text: str) -> Line:
    """A minimal Line carrying only what the segmenter reads."""
    return Line(
        line_id=line_id,
        page_id=page_id,
        line_number=number,
        text=text,
        text_clean=text,
        line_type="paragraph",
        position="+",
        section="herbal",
        currier_language="A",
        hand="1",
        quire="A",
        illustration_type="H",
        word_count=1,
        char_count=len(text),
        has_uncertain=False,
        has_illegible=False,
        has_alternatives=False,
        has_high_ascii=False,
    )


def test_inline_tags_returns_markers_in_order() -> None:
    assert inline_tags("<%>daiin.chol<$>") == ["<%>", "<$>"]
    assert inline_tags("daiin") == []


def test_markers_open_and_close_a_block() -> None:
    lines = [
        line("p:1", "p", 1, "<%>a"),
        line("p:2", "p", 2, "b"),
        line("p:3", "p", 3, "c<$>"),
    ]
    blocks = paragraphs.build_blocks(lines)
    assert len(blocks) == 1
    assert blocks[0].line_ids == ("p:1", "p:2", "p:3")
    assert blocks[0].opened_by_marker and blocks[0].closed_by_marker


def test_a_new_start_marker_closes_the_previous_block() -> None:
    lines = [
        line("p:1", "p", 1, "<%>a"),
        line("p:2", "p", 2, "<%>b"),
    ]
    blocks = paragraphs.build_blocks(lines)
    assert [block.line_ids for block in blocks] == [("p:1",), ("p:2",)]
    assert not blocks[0].closed_by_marker


def test_a_page_break_closes_a_block() -> None:
    lines = [line("p:1", "p", 1, "<%>a"), line("q:1", "q", 1, "b")]
    blocks = paragraphs.build_blocks(lines)
    assert [block.page_id for block in blocks] == ["p", "q"]
    assert not blocks[1].opened_by_marker


def test_position_labels_cover_every_line() -> None:
    lines = [line("p:1", "p", 1, "<%>a"), line("p:2", "p", 2, "b<$>"), line("q:1", "q", 1, "c")]
    blocks = paragraphs.build_blocks(lines)
    labels = paragraphs.position_in_block(blocks)
    assert labels == {"p:1": "first", "p:2": "last", "q:1": "only"}


def test_real_corpus_segments_into_marked_blocks() -> None:
    blocks = paragraphs.build_blocks()
    report = paragraphs.validation(blocks)
    assert report["lines"] == 4072
    assert report["blocks"] == len(blocks) > 500
    # The markers, not heuristics, are doing the work.
    assert float(report["fully_marked_share"]) > 0.9
