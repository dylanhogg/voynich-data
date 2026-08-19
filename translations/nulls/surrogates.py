"""Shuffling surrogates: each destroys one kind of structure and keeps the rest."""

from __future__ import annotations

import random

Words = list[list[str]]


def shuffle_chars(words: Words, rng: random.Random) -> Words:
    """Shuffle all units across the corpus, keeping the word-length profile.

    Destroys everything except unit frequencies and word lengths: the floor.
    """
    pool = [unit for word in words for unit in word]
    rng.shuffle(pool)
    output: Words = []
    cursor = 0
    for word in words:
        output.append(pool[cursor : cursor + len(word)])
        cursor += len(word)
    return output


def shuffle_within_word(words: Words, rng: random.Random) -> Words:
    """Shuffle units inside each word; word inventory and order preserved.

    Tests slot structure: if word-internal ordering is rigid, this surrogate
    should look very different from the real text.
    """
    output: Words = []
    for word in words:
        shuffled = list(word)
        rng.shuffle(shuffled)
        output.append(shuffled)
    return output


def shuffle_word_order(words: Words, rng: random.Random) -> Words:
    """Shuffle the order of words; vocabulary and word forms preserved.

    Tests whether word order carries information.
    """
    output = list(words)
    rng.shuffle(output)
    return output
