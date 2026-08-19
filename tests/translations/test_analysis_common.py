"""Views, surrogates and the run context."""

from __future__ import annotations

import pytest

from translations.analysis.common import (
    NULL_KINDS,
    View,
    baseline_view,
    encode_lines,
    encode_units,
    grille_view,
    is_prose,
    null_view,
    selfcite_view,
    text_of,
    voynich_view,
)
from translations.analysis.context import hapax_rate, mean_word_length, profile
from translations.corpora import available
from translations.determinism import derived_rng
from translations.strata import build_strata

LINES = [[list("qokeedy"), list("chol")], [list("daiin"), list("daiin"), list("shey")]]


def test_view_flattens_words_units_and_forms() -> None:
    view = View(name="toy", lines=LINES)
    assert view.n_words == 5
    assert view.n_units == sum(len(word) for line in LINES for word in line)
    assert view.forms[0] == "qokeedy"
    assert view.n_types == 4


def test_encode_units_and_lines_agree() -> None:
    view = View(name="toy", lines=LINES)
    assert sum(part.size for part in encode_lines(view)) == encode_units(view).size


def test_text_of_joins_forms() -> None:
    assert text_of(View(name="toy", lines=LINES)).startswith("qokeedy.chol.")


def test_voynich_view_matches_the_corpus() -> None:
    view = voynich_view()
    assert view.n_words == 33728
    assert len(view.lines) == len(view.rows) == 4072


def test_prose_rule_excludes_labels_and_circular_pages() -> None:
    rows = build_strata()
    excluded = [row for row in rows if not is_prose(row)]
    assert all(
        row.line_type != "paragraph" or row.illustration_type in ("A", "C") for row in excluded
    )
    assert 0 < len(excluded) < len(rows) * 0.1


@pytest.mark.parametrize("kind", NULL_KINDS)
def test_null_views_are_reproducible_and_sized(kind: str) -> None:
    view = View(name="toy", lines=LINES * 40)
    first = null_view(kind, view, derived_rng("n"))
    second = null_view(kind, view, derived_rng("n"))
    assert [word for line in first.lines for word in line] == [
        word for line in second.lines for word in line
    ]
    assert abs(first.n_words - view.n_words) <= len(view.lines)


def test_pseudo_views_match_token_count() -> None:
    view = View(name="toy", lines=LINES * 40)
    assert grille_view(view, derived_rng("g"), table_size=4).n_words == view.n_words
    assert selfcite_view(view, derived_rng("s")).n_words == view.n_words


@pytest.mark.skipif(not available(), reason="corpora not fetched; run `make corpora`")
def test_baseline_view_is_sample_size_matched() -> None:
    view = baseline_view("vulgate_clementine", 5000, derived_rng("b"))
    assert view.n_words == 5000
    assert all(word for word in view.words)


def test_profile_returns_the_three_tuned_quantities() -> None:
    view = View(name="toy", lines=LINES * 40)
    h2, length, hapax = profile(view)
    assert h2 > 0
    assert length == mean_word_length(view)
    assert hapax == hapax_rate(view)
