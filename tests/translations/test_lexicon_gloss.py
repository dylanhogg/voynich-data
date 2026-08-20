"""Whitaker's Words parsing, the gloss fallback chain and the specificity model."""

from __future__ import annotations

import random

import pytest

from translations import gloss
from translations.lexicon import whitakers

# One record per DICTLINE column layout: four 19-char stems, codes, meanings.
RECORD = (
    "alb".ljust(19)
    + "alb".ljust(19)
    + "albi".ljust(19)
    + "zzz".ljust(19)
    + "ADJ    3 1 POS          X X X A S ".ljust(34)
    + "white, pale (fair); bright [clear];"
)


@pytest.fixture(scope="module")
def small() -> whitakers.Lexicon:
    """A two-entry lexicon, enough to exercise every rung of the chain."""
    entries = [
        whitakers.Entry("alb", ("alb", "albi"), "ADJ", "A", ("white", "bright")),
        whitakers.Entry("cum", ("cum",), "PREP", "A", ("with",)),
    ]
    return whitakers.build_lexicon(entries)


def test_parse_line_reads_stems_frequency_and_senses() -> None:
    entry = whitakers.parse_line(RECORD)
    assert entry is not None
    assert entry.stems == ("alb", "alb", "albi")
    assert entry.frequency == "A"
    assert entry.glosses == ("white, pale", "bright")


def test_parse_line_skips_a_record_with_no_gloss() -> None:
    assert whitakers.parse_line("short line") is None


def test_clean_gloss_removes_annotations() -> None:
    assert whitakers.clean_gloss("white (fair) [clear];") == "white"


def test_lookup_is_exact_and_stripped_removes_one_ending(small: whitakers.Lexicon) -> None:
    assert small.lookup("alb") is not None
    assert small.lookup("albis") is None
    stripped = small.stripped("albis")
    assert stripped is not None and stripped[0].lemma == "alb"


def test_near_verifies_the_edit_distance(small: whitakers.Lexicon) -> None:
    assert small.near("alc") is not None  # one substitution from "alb"
    assert small.near("xyz") is None


def test_commoner_entry_wins_a_contested_stem() -> None:
    rare = whitakers.Entry("a", ("a",), "N", "F", ("rare",))
    common = whitakers.Entry("a", ("a",), "PREP", "A", ("common",))
    built = whitakers.build_lexicon([rare, common])
    assert built.lookup("a") is not None
    assert built.lookup("a").english == "common"  # type: ignore[union-attr]


def test_candidates_rank_exact_above_stripped_above_nearest(small: whitakers.Lexicon) -> None:
    assert [candidate.source for candidate in gloss.candidates("cum", small)] == ["lexicon"]
    assert [candidate.source for candidate in gloss.candidates("alc", small)] == ["nearest"] * 2
    assert gloss.candidates("albis", small)[0].source == "stripped"
    assert gloss.candidates("xqzv", small) == []


def test_short_takes_the_first_sense() -> None:
    assert gloss.short("when, at the time/on each occasion") == "when"


def test_specificity_falls_with_length() -> None:
    lexicon = whitakers.build_lexicon(
        [whitakers.Entry(letter, (letter,), "N", "A", ("x",)) for letter in "abcde"]
    )
    scores = gloss.specificity(lexicon, "abcde", random.Random(0), samples=100)
    assert scores[1] == 0.0  # every one-letter string is in this lexicon
    assert scores[4] == 1.0  # no four-letter string is


def test_specificity_of_saturates_past_the_sampled_range() -> None:
    assert gloss.specificity_of({1: 0.1, 2: 0.5}, 9) == 0.5
    assert gloss.specificity_of({1: 0.1}, 0) == 0.0
