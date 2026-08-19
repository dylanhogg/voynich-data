"""Loaders for the built VCAT artifacts in ``output/`` (local only, no network)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from translations.config import PATHS, Transcription
from vcat.exceptions import SourceNotFoundError
from vcat.text_processing import clean_text_for_analysis


@dataclass(frozen=True)
class Line:
    """One transcribed line of the manuscript, as built by ``builders/``."""

    line_id: str
    page_id: str
    line_number: int
    text: str
    text_clean: str
    line_type: str
    position: str
    section: str
    currier_language: str
    hand: str
    quire: str
    illustration_type: str
    word_count: int
    char_count: int
    has_uncertain: bool
    has_illegible: bool
    has_alternatives: bool
    has_high_ascii: bool


@dataclass(frozen=True)
class Mismatch:
    """One row of the cross-transcription alignment index."""

    line_id: str
    status: str
    similarity_score: float | None
    sources_present: tuple[str, ...]
    texts: dict[str, str | None]


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        raise SourceNotFoundError("Built artifact missing; run `make build` first", path=path)
    with path.open() as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def load_lines(path: Path | None = None) -> list[Line]:
    """Load ``eva_lines`` (ZL transcription), ordered as built."""
    return [
        Line(
            line_id=row["line_id"],
            page_id=row["page_id"],
            line_number=row["line_number"],
            text=row["text"],
            text_clean=row["text_clean"],
            line_type=row["line_type"],
            position=row["position"],
            section=row["section"],
            currier_language=row["currier_language"],
            hand=row["hand"],
            quire=row["quire"],
            illustration_type=row["illustration_type"],
            word_count=row["word_count"],
            char_count=row["char_count"],
            has_uncertain=row["has_uncertain"],
            has_illegible=row["has_illegible"],
            has_alternatives=row["has_alternatives"],
            has_high_ascii=row["has_high_ascii"],
        )
        for row in _read_jsonl(path or PATHS.eva_lines)
    ]


def load_pages(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load page metadata keyed by ``page_id`` (uncertainty wrappers intact)."""
    return {row["page_id"]: row for row in _read_jsonl(path or PATHS.pages)}


def load_mismatches(path: Path | None = None) -> dict[str, Mismatch]:
    """Load the mismatch index keyed by ``line_id``."""
    return {
        row["line_id"]: Mismatch(
            line_id=row["line_id"],
            status=row["status"],
            similarity_score=row["similarity_score"],
            sources_present=tuple(row["sources_present"]),
            texts={source: row.get(f"{source}_text") for source in ("zl", "it", "cd", "fg", "gc")},
        )
        for row in _read_jsonl(path or PATHS.mismatch_index)
    }


def transcription_text(line: Line, mismatch: Mismatch | None, source: Transcription) -> str | None:
    """Analysis-ready text of ``line`` in ``source``, or ``None`` if absent.

    ZL comes from ``eva_lines`` (already cleaned by the builder); other sources
    come from the mismatch index and are cleaned here with the *same* central
    routine, never a local regex.
    """
    if source is Transcription.ZL:
        return line.text_clean
    if mismatch is None:
        return None
    raw = mismatch.texts.get(source.value)
    if raw is None:
        return None
    cleaned = clean_text_for_analysis(raw)
    return cleaned or None
