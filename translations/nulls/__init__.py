"""Null models and surrogate corpora (plan §2.5).

"Voynichese has property X" means nothing without "and shuffled / Markov /
Latin / table-generated text does not". Everything here takes an explicit
:class:`random.Random` so surrogates are reproducible.

Corpora are handled as ``list[list[str]]``: a list of words, each a list of
units (whatever ``translations.tokenize`` produced).
"""

from __future__ import annotations

from translations.nulls.encipher import Key, encipher
from translations.nulls.markov import markov_chars, markov_words
from translations.nulls.pseudo import grille, selfcite
from translations.nulls.surrogates import (
    shuffle_chars,
    shuffle_within_word,
    shuffle_word_order,
)

__all__ = [
    "Key",
    "encipher",
    "grille",
    "markov_chars",
    "markov_words",
    "selfcite",
    "shuffle_chars",
    "shuffle_within_word",
    "shuffle_word_order",
]
