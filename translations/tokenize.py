"""The tokenization contract (plan §2.3).

This is the only tokenizer used by the translation programme. Results swing on
tokenization, so the variant and the comma policy are experimental factors that
travel with every reported number — never implicit defaults buried in a caller.

Variants
--------
``T0-char``
    ``text_clean`` characters as-is, including the digits of high-ASCII tokens.
    Baseline for comparability with prior work.
``T1-glyph``
    Compound-aware: ``ch sh cth ckh cph cfh`` are single units, a high-ASCII
    token ``@NNN;`` is one opaque unit, and the ligature connector ``'`` is
    dropped (it marks how glyphs are joined, it is not a glyph).
``T2-slot``
    ``T1`` re-segmented into morphs by an induced slot model. The segmenter is
    passed in — the induction lives in ``translations.analysis.segmentation``,
    so the tokenizer stays free of any model of its own.
``T3-merge``
    Depends on the Phase 2 glyph-merge search and raises
    :class:`NotImplementedError` until that lands.

The comma policy decides whether ``,`` — the *uncertain* word separator — is a
word break or word-internal.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from translations.config import CommaPolicy, Tokenizer
from vcat.eva_charset import EVA_COMPOUNDS

# Longest-first so that `cth` wins over `ch`.
_COMPOUNDS: tuple[str, ...] = tuple(sorted(EVA_COMPOUNDS, key=len, reverse=True))
_HIGH_ASCII = re.compile(r"@\d+;")
LIGATURE_CONNECTOR = "'"


def split_words(text: str, comma: CommaPolicy = CommaPolicy.BREAK) -> list[str]:
    """Split analysis-ready text into words under the given comma policy."""
    if comma is CommaPolicy.BREAK:
        parts = re.split(r"[.,]", text)
    else:
        parts = text.replace(",", "").split(".")
    return [part for part in parts if part]


def glyphs(word: str) -> list[str]:
    """Split a word into EVA glyph units (the ``T1-glyph`` unit)."""
    units: list[str] = []
    index = 0
    while index < len(word):
        high_ascii = _HIGH_ASCII.match(word, index)
        if high_ascii:
            units.append(high_ascii.group())
            index = high_ascii.end()
            continue
        for compound in _COMPOUNDS:
            if word.startswith(compound, index):
                units.append(compound)
                index += len(compound)
                break
        else:
            if word[index] != LIGATURE_CONNECTOR:
                units.append(word[index])
            index += 1
    return units


Segmenter = Callable[[list[str]], list[list[str]]]


def tokenize_word(
    word: str,
    variant: Tokenizer = Tokenizer.T1_GLYPH,
    segmenter: Segmenter | None = None,
) -> list[str]:
    """Split one word into units of the requested variant.

    ``T2-slot`` needs a ``segmenter`` mapping glyph units to morphs; without one
    it raises, because a slot tokenization with no induced model behind it would
    be a silent lie about what produced the units.
    """
    if variant is Tokenizer.T0_CHAR:
        return list(word)
    if variant is Tokenizer.T1_GLYPH:
        return glyphs(word)
    if variant is Tokenizer.T2_SLOT:
        if segmenter is None:
            raise ValueError("T2-slot requires an induced segmenter")
        return ["".join(morph) for morph in segmenter(glyphs(word))]
    raise NotImplementedError(f"{variant} requires an induction from a later phase")


def tokenize_line(
    text: str,
    variant: Tokenizer = Tokenizer.T1_GLYPH,
    comma: CommaPolicy = CommaPolicy.BREAK,
    segmenter: Segmenter | None = None,
) -> list[list[str]]:
    """Split a line into words, each a list of units."""
    return [tokenize_word(word, variant, segmenter) for word in split_words(text, comma)]


def unit_stream(
    text: str,
    variant: Tokenizer = Tokenizer.T1_GLYPH,
    comma: CommaPolicy = CommaPolicy.BREAK,
    segmenter: Segmenter | None = None,
) -> list[str]:
    """Flatten a line to a single stream of units, word boundaries dropped."""
    return [unit for word in tokenize_line(text, variant, comma, segmenter) for unit in word]
