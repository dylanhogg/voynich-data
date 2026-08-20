"""Paragraph / block segmentation of the manuscript (plan §5.1, §5.2).

The plan expected this to be derived from the ``position`` locator plus layout
heuristics. It does not need to be: IVTFF already marks paragraph starts
(``<%>``) and ends (``<$>``) inline, and the builders drop those tags on the way
to ``text_clean``. Reading them back through
:func:`vcat.text_processing.inline_tags` gives an *annotated* segmentation
rather than a guessed one.

Lines carrying neither tag are attached to the block in progress; a page break
always closes a block, because a paragraph never continues across a folio in
this dataset's numbering.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from translations.io import Line, load_lines
from vcat.text_processing import inline_tags

PARAGRAPH_START = "<%>"
PARAGRAPH_END = "<$>"


@dataclass(frozen=True)
class Block:
    """One paragraph-like block of consecutive lines."""

    block_id: str
    page_id: str
    line_ids: tuple[str, ...]
    opened_by_marker: bool
    closed_by_marker: bool

    @property
    def n_lines(self) -> int:
        """Lines in the block."""
        return len(self.line_ids)


def build_blocks(lines: list[Line] | None = None) -> list[Block]:
    """Segment the corpus into paragraph blocks, in document order."""
    rows = lines if lines is not None else load_lines()
    blocks: list[Block] = []
    current: list[str] = []
    page = ""
    opened = False
    counter = 0

    def close(closed_by_marker: bool) -> None:
        nonlocal current, counter, opened
        if not current:
            return
        counter += 1
        blocks.append(
            Block(
                block_id=f"{page}:b{counter}",
                page_id=page,
                line_ids=tuple(current),
                opened_by_marker=opened,
                closed_by_marker=closed_by_marker,
            )
        )
        current = []
        opened = False

    for line in rows:
        tags = inline_tags(line.text)
        if line.page_id != page:
            close(False)
            page, counter = line.page_id, 0
        if PARAGRAPH_START in tags:
            close(False)
            opened = True
        current.append(line.line_id)
        if PARAGRAPH_END in tags:
            close(True)
    close(False)
    return blocks


def block_of_line(blocks: list[Block]) -> dict[str, str]:
    """Map every line id to the id of the block containing it."""
    return {line_id: block.block_id for block in blocks for line_id in block.line_ids}


def position_in_block(blocks: list[Block]) -> dict[str, str]:
    """Label each line ``first`` / ``middle`` / ``last`` / ``only`` in its block."""
    labels: dict[str, str] = {}
    for block in blocks:
        for index, line_id in enumerate(block.line_ids):
            if block.n_lines == 1:
                labels[line_id] = "only"
            elif index == 0:
                labels[line_id] = "first"
            elif index == block.n_lines - 1:
                labels[line_id] = "last"
            else:
                labels[line_id] = "middle"
    return labels


def validation(blocks: list[Block], lines: list[Line] | None = None) -> dict[str, object]:
    """How well-marked the segmentation is, and what it left to inference.

    There is no ground-truth paragraph annotation to score against, so what is
    reported is coverage of the markers and the residue: blocks that had to be
    opened or closed by a page break rather than by a tag.
    """
    rows = lines if lines is not None else load_lines()
    line_types = {line.line_id: line.line_type for line in rows}
    sizes = Counter(block.n_lines for block in blocks)
    both = sum(1 for block in blocks if block.opened_by_marker and block.closed_by_marker)
    label_blocks = sum(
        1
        for block in blocks
        if all(line_types.get(line_id) == "label" for line_id in block.line_ids)
    )
    return {
        "blocks": len(blocks),
        "lines": sum(block.n_lines for block in blocks),
        "opened_by_marker": sum(1 for block in blocks if block.opened_by_marker),
        "closed_by_marker": sum(1 for block in blocks if block.closed_by_marker),
        "fully_marked": both,
        "fully_marked_share": both / len(blocks) if blocks else 0.0,
        "single_line_blocks": sizes[1],
        "label_only_blocks": label_blocks,
        "median_lines_per_block": (
            sorted(block.n_lines for block in blocks)[len(blocks) // 2] if blocks else 0
        ),
        "max_lines_per_block": max((block.n_lines for block in blocks), default=0),
    }
