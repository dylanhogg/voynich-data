"""Pseudo-Voynich generators: rival hypotheses that produce text with no content.

``grille``   — Rugg-style: syllables read out of a table through a Cardan grille.
``selfcite`` — Timm/Schinner-style: each word copies an earlier word, sometimes
               mutated.

Both are tuned in Phase 1 to match the manuscript's h2, word-length
distribution and hapax rate. A well-matched pseudo-Voynich is the control that
makes the Phase 5 audit meaningful, so these are load-bearing, not toys.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from translations.tokenize import glyphs

Words = list[list[str]]


@dataclass(frozen=True)
class SyllableTable:
    """Three columns of syllables, read left to right to form a word."""

    prefixes: tuple[str, ...]
    midfixes: tuple[str, ...]
    suffixes: tuple[str, ...]

    @property
    def columns(self) -> tuple[tuple[str, ...], ...]:
        """The columns in read order."""
        return (self.prefixes, self.midfixes, self.suffixes)


def induce_table(words: Words, size: int = 16) -> SyllableTable:
    """Build a syllable table from the most frequent word parts of a corpus.

    First unit -> prefix column, middle units -> midfix column, last unit ->
    suffix column. Crude on purpose: Phase 1 tunes the table, this only has to
    put the generator in the right neighbourhood.
    """
    columns: list[Counter[str]] = [Counter(), Counter(), Counter()]
    for word in words:
        if len(word) < 2:
            continue
        columns[0][word[0]] += 1
        columns[1]["".join(word[1:-1])] += 1
        columns[2][word[-1]] += 1
    most_common = [
        tuple(part for part, _ in sorted(column.most_common(size))) for column in columns
    ]
    return SyllableTable(most_common[0], most_common[1], most_common[2])


def grille(table: SyllableTable, n_words: int, rng: random.Random) -> Words:
    """Generate words by sliding a diagonal three-hole grille over ``table``.

    Each placement exposes one syllable per column; the holes step down the
    table together, which is what makes the output *systematically* repetitive
    rather than independently random — the property Rugg argued for.
    """
    output: Words = []
    for _ in range(n_words):
        row = rng.randrange(max(len(column) for column in table.columns))
        parts = [
            column[(row + offset) % len(column)] for offset, column in enumerate(table.columns)
        ]
        output.append(glyphs("".join(parts)))
    return output


def selfcite(
    seed_words: Words,
    n_words: int,
    rng: random.Random,
    window: int = 20,
    mutation_rate: float = 0.3,
) -> Words:
    """Generate text by copying a recent word and occasionally mutating it.

    Reproduces the manuscript's high rate of near-repeat adjacent words without
    any underlying message.
    """
    inventory = sorted({unit for word in seed_words for unit in word})
    output: Words = [list(rng.choice(seed_words))]
    for _ in range(n_words - 1):
        source = rng.choice(output[-window:])
        word = list(source)
        if rng.random() < mutation_rate and word:
            position = rng.randrange(len(word))
            operation = rng.choice(("substitute", "insert", "delete"))
            if operation == "substitute":
                word[position] = rng.choice(inventory)
            elif operation == "insert":
                word.insert(position, rng.choice(inventory))
            elif len(word) > 1:
                del word[position]
        output.append(word)
    return output
