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
``T2-slot`` / ``T3-merge``
    Depend on the morphology induction (Phase 1.4) and the glyph-merge search
    (Phase 2) and raise :class:`NotImplementedError` until those land.

The comma policy decides whether ``,`` — the *uncertain* word separator — is a
word break or word-internal.
"""

from __future__ import annotations

import re

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


def tokenize_word(word: str, variant: Tokenizer = Tokenizer.T1_GLYPH) -> list[str]:
    """Split one word into units of the requested variant."""
    if variant is Tokenizer.T0_CHAR:
        return list(word)
    if variant is Tokenizer.T1_GLYPH:
        return glyphs(word)
    raise NotImplementedError(f"{variant} requires an induction from a later phase")


def tokenize_line(
    text: str,
    variant: Tokenizer = Tokenizer.T1_GLYPH,
    comma: CommaPolicy = CommaPolicy.BREAK,
) -> list[list[str]]:
    """Split a line into words, each a list of units."""
    return [tokenize_word(word, variant) for word in split_words(text, comma)]


def unit_stream(
    text: str,
    variant: Tokenizer = Tokenizer.T1_GLYPH,
    comma: CommaPolicy = CommaPolicy.BREAK,
) -> list[str]:
    """Flatten a line to a single stream of units, word boundaries dropped."""
    return [unit for word in tokenize_line(text, variant, comma) for unit in word]
