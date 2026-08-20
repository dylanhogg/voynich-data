"""Tokenization contract tests, on hand-checked lines from the built corpus.

Lines used (from ``output/eva_lines.jsonl``):

- ``f1r:1``   first line of the manuscript, plain paragraph text
- ``f1r:2``   contains the uncertain separator ``,``
- ``f1r:19``  contains high-ASCII tokens ``@192;`` and ``@130;``
- ``f2r:10``  contains the ligature connector ``'``
- ``f68r1:1`` circular/astronomical page (typed ``paragraph`` in the data)
- ``f66r:1``  a label line
"""

from __future__ import annotations

import pytest

from translations.config import CommaPolicy, Tokenizer
from translations.tokenize import glyphs, split_words, tokenize_line, tokenize_word, unit_stream

F1R_1 = "fachys.ykal.ar.ataiin.shol.shory.cthres.y.kor.sholdy"
F1R_2 = "sory.ckhar.or,y.kair.chtaiin.shar.ase.cthar.cthar,dan"
F1R_19 = "dchar.shcthaiin.okaiir.chey.@192;chy.@130;tol.cthols.dloo"
F2R_10 = "qo'ky.cholaiin.shol.sheky.daiincthey.keol.saiin.e'a'iin"
F68R1_1 = "shokchy.chteey.choteey.cphol.cheor.opcheeol.otor.choctheeey.okchoal"
F66R_1 = "rary"


def test_split_words_break_policy() -> None:
    assert split_words(F1R_2, CommaPolicy.BREAK)[:4] == ["sory", "ckhar", "or", "y"]
    assert len(split_words(F1R_2, CommaPolicy.BREAK)) == 11


def test_split_words_join_policy() -> None:
    assert split_words(F1R_2, CommaPolicy.JOIN)[:3] == ["sory", "ckhar", "ory"]
    assert len(split_words(F1R_2, CommaPolicy.JOIN)) == 9


def test_glyphs_merge_compounds_longest_first() -> None:
    assert glyphs("fachys") == ["f", "a", "ch", "y", "s"]
    assert glyphs("cthres") == ["cth", "r", "e", "s"]
    assert glyphs("ckhar") == ["ckh", "a", "r"]
    assert glyphs("cphol") == ["cph", "o", "l"]
    assert glyphs("shokchy") == ["sh", "o", "k", "ch", "y"]


def test_glyphs_high_ascii_is_one_unit() -> None:
    assert glyphs("@192;chy") == ["@192;", "ch", "y"]
    assert glyphs("@169;") == ["@169;"]


def test_glyphs_drops_ligature_connector() -> None:
    assert glyphs("qo'ky") == ["q", "o", "k", "y"]
    assert glyphs("e'a'iin") == ["e", "a", "i", "i", "n"]


def test_char_variant_is_text_as_is() -> None:
    assert tokenize_word("fachys", Tokenizer.T0_CHAR) == list("fachys")
    assert tokenize_word("@192;chy", Tokenizer.T0_CHAR) == list("@192;chy")


def test_label_line() -> None:
    assert tokenize_line(F66R_1, Tokenizer.T1_GLYPH) == [["r", "a", "r", "y"]]


def test_circular_page_line() -> None:
    line = tokenize_line(F68R1_1, Tokenizer.T1_GLYPH)
    assert len(line) == 9
    assert line[0] == ["sh", "o", "k", "ch", "y"]
    assert line[3] == ["cph", "o", "l"]


def test_glyph_variant_is_never_longer_than_char_variant() -> None:
    for text in (F1R_1, F1R_2, F1R_19, F2R_10, F68R1_1):
        chars = unit_stream(text, Tokenizer.T0_CHAR)
        units = unit_stream(text, Tokenizer.T1_GLYPH)
        assert len(units) < len(chars)


def test_t3_requires_a_merge_partition() -> None:
    # Phase 3 implements T3-merge; like T2 it refuses to run without its induction.
    with pytest.raises(ValueError, match="T3-merge"):
        tokenize_word("fachys", Tokenizer.T3_MERGE)


def test_t3_applies_the_merge_partition() -> None:
    assert tokenize_word("fachys", Tokenizer.T3_MERGE, merges=(("ch", "y"),)) == [
        "f",
        "a",
        "chy",
        "s",
    ]


def test_t2_requires_an_induced_segmenter() -> None:
    with pytest.raises(ValueError, match="segmenter"):
        tokenize_word("qokeedy", Tokenizer.T2_SLOT)


def test_t2_applies_the_segmenter_to_glyph_units() -> None:
    def segmenter(units: list[str]) -> list[list[str]]:
        return [units[:2], units[2:]]

    assert tokenize_word("qokeedy", Tokenizer.T2_SLOT, segmenter) == ["qo", "keedy"]
