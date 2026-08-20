"""T3-merge tokenization and the Phase 3 representations."""

from __future__ import annotations

import pytest

from translations import represent
from translations.alignment import TokenRow
from translations.analysis.common import View
from translations.config import Tokenizer
from translations.strata import StratumRow
from translations.tokenize import apply_merges, tokenize_word

MERGES = (("q", "o"), ("ch", "e", "d", "y"))


def token_row(line_id: str, index: int, reliability: float) -> TokenRow:
    """A reliability row with only the fields the filter reads."""
    return TokenRow(
        line_id=line_id,
        page_id=line_id.split(":")[0],
        token_index=index,
        zl_form="x",
        it_form="x",
        status="aligned",
        agreement=reliability,
        is_hapax=False,
        has_rare_unit=False,
        line_uncertain=False,
        line_illegible=False,
        line_alternatives=False,
        in_consensus=True,
        reliability=reliability,
    )


def stratum(line_id: str) -> StratumRow:
    """A stratum row identified only by its line id."""
    return StratumRow(
        line_id=line_id,
        page_id=line_id.split(":")[0],
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
        is_last_line_of_page=True,
        has_uncertain=False,
        has_illegible=False,
        has_alternatives=False,
        has_high_ascii=False,
        mismatch_status="exact_match",
        in_consensus=True,
        is_holdout=False,
    )


def test_apply_merges_joins_longest_match_first() -> None:
    assert apply_merges(["q", "o", "k", "ch", "e", "d", "y"], MERGES) == ["qo", "k", "chedy"]


def test_apply_merges_leaves_unmatched_units_alone() -> None:
    assert apply_merges(["d", "a", "i", "i", "n"], MERGES) == ["d", "a", "i", "i", "n"]


def test_t3_requires_a_merge_partition() -> None:
    with pytest.raises(ValueError, match="T3-merge"):
        tokenize_word("qokchedy", Tokenizer.T3_MERGE)


def test_t3_merges_over_glyph_units_not_characters() -> None:
    # `ch` is one glyph unit, so a merge can group it but never split it.
    assert tokenize_word("qokchedy", Tokenizer.T3_MERGE, merges=MERGES) == ["qo", "k", "chedy"]


def test_merged_representation_shortens_words_without_losing_tokens() -> None:
    view = View(name="v", lines=[[["q", "o", "k"], ["ch", "e", "d", "y"]]])
    result = represent.merged(MERGES, origin="test")(view)
    assert result.n_words == view.n_words
    assert result.n_units < view.n_units
    assert result.forms == view.forms


def test_reliable_representation_drops_only_tokens_below_the_floor() -> None:
    rows = [token_row("p:1", 0, 0.9), token_row("p:1", 1, 0.1)]
    view = View(name="v", lines=[[["a"], ["b"]]], rows=[stratum("p:1")])
    result = represent.reliable(rows, threshold=0.5)(view)
    assert result.forms == ["a"]


def test_reliable_representation_passes_through_views_without_strata() -> None:
    rows = [token_row("p:1", 0, 0.1)]
    view = View(name="baseline", lines=[[["a"], ["b"]]])
    assert represent.reliable(rows, threshold=0.5)(view).forms == ["a", "b"]


def test_identity_representation_changes_nothing() -> None:
    view = View(name="v", lines=[[["a"], ["b"]]])
    assert represent.identity()(view) is view


def test_phase2_merges_reads_a_converged_run() -> None:
    if not represent.CANDIDATES.exists():
        pytest.skip("Phase 2 not run yet; run `make decipher`")
    merges, provenance = represent.phase2_merges()
    assert merges and all(len(merge) >= 2 for merge in merges)
    assert "searched-merges" in provenance["variant"]
    assert provenance["n_merges"] == len(merges)
