"""Stratum table, consensus subset and the frozen held-out split."""

from __future__ import annotations

from translations.config import CONFIG
from translations.strata import build_strata, group_by, holdout_pages


def test_strata_row_count_and_join() -> None:
    rows = build_strata()
    assert len(rows) == 4072
    first = rows[0]
    assert first.line_id == "f1r:1"
    assert first.quire_id == "qA"
    assert first.folio_id == "f1"
    assert first.is_first_line_of_page


def test_consensus_subset_matches_report() -> None:
    rows = build_strata()
    assert sum(row.in_consensus for row in rows) == 3414


def test_holdout_split_is_deterministic_and_page_level() -> None:
    rows = build_strata()
    pages = sorted({row.page_id for row in rows})
    first = holdout_pages(pages)
    assert first == holdout_pages(list(reversed(pages)))
    assert len(first) == round(len(pages) * CONFIG.holdout_fraction)

    holdout_page_ids = {row.page_id for row in rows if row.is_holdout}
    train_page_ids = {row.page_id for row in rows if not row.is_holdout}
    assert holdout_page_ids == set(first)
    assert not holdout_page_ids & train_page_ids


def test_group_by_is_sorted_and_total_preserving() -> None:
    rows = build_strata()
    groups = group_by(rows, "currier_language")
    assert list(groups) == sorted(groups)
    assert sum(len(group) for group in groups.values()) == len(rows)
    assert len(groups["A"]) == 1562
    assert len(groups["B"]) == 2437
