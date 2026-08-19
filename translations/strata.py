"""Per-line stratum table and the train/held-out split (plan §3.1).

Strata are confounds, not decoration: Currier A/B, hand, section and line type
behave like different systems, so every headline number is reported per
stratum. Two derived subsets live here as well:

``consensus``
    lines whose transcriptions broadly agree (mismatch status exact /
    normalized / high similarity). A finding that survives only on full ZL is a
    transcription artifact.
``holdout``
    a seeded, page-level 20% split. Held-out pages are illegal inputs to any
    key search and are only touched at the Phase 4 validation gate.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from translations.config import CONFIG
from translations.determinism import derived_rng
from translations.io import Line, Mismatch, load_lines, load_mismatches, load_pages


@dataclass(frozen=True)
class StratumRow:
    """One line with everything needed to slice the corpus."""

    line_id: str
    page_id: str
    folio_id: str
    quire_id: str
    side: str
    line_number: int
    section: str
    page_section: str
    page_section_disputed: bool
    currier_language: str
    hand: str
    line_type: str
    illustration_type: str
    position: str
    is_first_line_of_page: bool
    is_last_line_of_page: bool
    has_uncertain: bool
    has_illegible: bool
    has_alternatives: bool
    has_high_ascii: bool
    mismatch_status: str
    in_consensus: bool
    is_holdout: bool


def holdout_pages(page_ids: list[str]) -> frozenset[str]:
    """Deterministic page-level held-out set (``CONFIG.holdout_fraction``)."""
    ordered = sorted(set(page_ids))
    rng = derived_rng("holdout-split")
    shuffled = list(ordered)
    rng.shuffle(shuffled)
    count = round(len(ordered) * CONFIG.holdout_fraction)
    return frozenset(sorted(shuffled[:count]))


def build_strata(
    lines: list[Line] | None = None,
    pages: dict[str, dict[str, Any]] | None = None,
    mismatches: dict[str, Mismatch] | None = None,
) -> list[StratumRow]:
    """Join lines, page metadata and mismatch status into a stratum table."""
    lines = lines if lines is not None else load_lines()
    pages = pages if pages is not None else load_pages()
    mismatches = mismatches if mismatches is not None else load_mismatches()

    last_line = {line.page_id: line.line_number for line in lines}
    holdout = holdout_pages([line.page_id for line in lines])

    rows: list[StratumRow] = []
    for line in lines:
        page = pages.get(line.page_id, {})
        section = page.get("section", {})
        mismatch = mismatches.get(line.line_id)
        status = mismatch.status if mismatch else "absent"
        rows.append(
            StratumRow(
                line_id=line.line_id,
                page_id=line.page_id,
                folio_id=page.get("folio_id", ""),
                quire_id=page.get("quire_id", ""),
                side=page.get("side", ""),
                line_number=line.line_number,
                section=line.section,
                page_section=section.get("value", ""),
                page_section_disputed=bool(section.get("disputed", False)),
                currier_language=line.currier_language,
                hand=line.hand,
                line_type=line.line_type,
                illustration_type=line.illustration_type,
                position=line.position,
                is_first_line_of_page=line.line_number == 1,
                is_last_line_of_page=line.line_number == last_line[line.page_id],
                has_uncertain=line.has_uncertain,
                has_illegible=line.has_illegible,
                has_alternatives=line.has_alternatives,
                has_high_ascii=line.has_high_ascii,
                mismatch_status=status,
                in_consensus=status in CONFIG.consensus_statuses,
                is_holdout=line.page_id in holdout,
            )
        )
    return rows


def group_by(rows: list[StratumRow], field: str) -> dict[str, list[StratumRow]]:
    """Group rows by a stratum field, in sorted key order."""
    groups: dict[str, list[StratumRow]] = defaultdict(list)
    for row in rows:
        groups[str(getattr(row, field))].append(row)
    return {key: groups[key] for key in sorted(groups)}
