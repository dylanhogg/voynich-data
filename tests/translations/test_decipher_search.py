"""The search itself: does it find keys, and does it find the *same* key twice?"""

from __future__ import annotations

import numpy as np

from translations.analysis.common import View
from translations.decipher.channel import build_ciphertext, fixed_width_units
from translations.decipher.lm import ALPHABET, train_char_lm
from translations.decipher.score import ngram_index
from translations.decipher.search import (
    anneal,
    candidate_merges,
    em_initialise,
    random_key,
    score_key,
    search_key,
)
from translations.determinism import derived_rng

PLAIN = (
    "in principio creavit deus caelum et terram terra autem erat inanis et vacua "
    "et tenebrae super faciem abyssi et spiritus dei ferebatur super aquas "
) * 12


def _enciphered() -> tuple[View, list[str]]:
    """A toy substitution cipher over the Latin sample, one glyph per letter."""
    words = PLAIN.split()
    mapping = {
        letter: chr(ord("a") + (index * 7 + 3) % 26)
        for index, letter in enumerate(sorted(set("".join(words))))
    }
    cipher_words = [[mapping[character] for character in word] for word in words]
    return View(name="toy-cipher", lines=[cipher_words]), words


def test_random_key_is_injective_when_asked() -> None:
    key = random_key(20, derived_rng("k"), injective=True)
    assert len(set(key[1:].tolist())) == 19


def test_em_initialisation_matches_frequencies() -> None:
    view, _ = _enciphered()
    ciphertext = build_ciphertext(view, min_count=1)
    lm = train_char_lm(PLAIN, 2, "latin-toy")
    index = ngram_index(ciphertext, lm.order)
    key = em_initialise(index, lm, ciphertext.size)
    assert key[0] == 0
    assert score_key(key, index, lm) < score_key(
        random_key(ciphertext.size, derived_rng("r")), index, lm
    )


def test_search_recovers_a_toy_substitution() -> None:
    view, plaintext = _enciphered()
    ciphertext = build_ciphertext(view, min_count=1)
    lm = train_char_lm(PLAIN, 3, "latin-toy")
    result = search_key(ciphertext, lm, derived_rng("s"), iterations=20000, restarts=3)
    decoded = [
        word
        for word in "".join(ALPHABET[symbol] for symbol in result.key[ciphertext.ids]).split("#")
        if word
    ]
    matched = sum(1 for found, real in zip(decoded, plaintext, strict=False) if found == real)
    assert matched / len(plaintext) > 0.9


def test_search_is_deterministic() -> None:
    view, _ = _enciphered()
    ciphertext = build_ciphertext(view, min_count=1)
    lm = train_char_lm(PLAIN, 3, "latin-toy")
    first = search_key(ciphertext, lm, derived_rng("s"), iterations=4000, restarts=2)
    second = search_key(ciphertext, lm, derived_rng("s"), iterations=4000, restarts=2)
    assert np.array_equal(first.key, second.key)
    assert first.bits == second.bits


def test_annealing_never_returns_worse_than_its_start() -> None:
    view, _ = _enciphered()
    ciphertext = build_ciphertext(view, min_count=1)
    lm = train_char_lm(PLAIN, 3, "latin-toy")
    index = ngram_index(ciphertext, lm.order)
    start = random_key(ciphertext.size, derived_rng("a"))
    _, bits, _ = anneal(index, lm, ciphertext.size, derived_rng("a"), 2000, initial=start)
    assert bits <= score_key(start, index, lm)


def test_candidate_merges_are_frequent_unit_sequences() -> None:
    view = View(name="toy", lines=[[list("qokeedy"), list("qokain"), list("chol")] * 30])
    merges = candidate_merges(build_ciphertext(view, min_count=1), top=5)
    assert ("q", "o") in merges
    assert all(len(merge) in (2, 3) for merge in merges)


def test_fixed_width_channel_halves_the_stream() -> None:
    view, _ = _enciphered()
    plain = build_ciphertext(view, min_count=1)
    paired = fixed_width_units(view, 2, "w2", min_count=1)
    assert paired.n_units < plain.n_units
