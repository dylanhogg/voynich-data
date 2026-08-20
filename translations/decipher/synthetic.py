"""Known-answer tests: encipher real text, then try to break it blind (plan §4.6).

There is no ground truth for the manuscript, so the only way to know whether the
search works is to give it a problem whose answer we hid ourselves. This module
builds those problems and scores recovery. It is also the harness the Phase 4
confidence calibration will hang off — the calibration maps themselves are
Phase 4 work.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from translations.analysis.common import View, baseline_view
from translations.decipher.channel import CipherText, build_ciphertext, fixed_width_units
from translations.decipher.lm import ALPHABET, CharLM
from translations.decipher.score import ngram_index
from translations.decipher.search import score_key, search_key
from translations.nulls.encipher import Key, encipher

VOWELS = "aeiou"
# A verbose cipher spells one letter with two glyphs, so it has to be attacked
# through the same fixed-width channel H2 uses; a one-glyph-per-letter channel
# cannot recover it however long it searches.
CHANNEL_WIDTH = {"verbose": 2}


@dataclass(frozen=True)
class Recovery:
    """How much of a hidden key the search got back."""

    scheme: str
    corpus: str
    n_tokens: int
    key_accuracy: float
    token_accuracy: float
    bits_true_key: float
    bits_found_key: float

    @property
    def found_better_than_truth(self) -> bool:
        """True when the search beat the real key — a sign the objective is off."""
        return self.bits_found_key < self.bits_true_key

    def as_dict(self) -> dict[str, float | str | int | bool]:
        """JSON-friendly form."""
        return {
            "scheme": self.scheme,
            "corpus": self.corpus,
            "n_tokens": self.n_tokens,
            "key_accuracy": self.key_accuracy,
            "token_accuracy": self.token_accuracy,
            "bits_true_key": self.bits_true_key,
            "bits_found_key": self.bits_found_key,
            "found_better_than_truth": self.found_better_than_truth,
        }


def synthetic_ciphertext(
    corpus_id: str, n_words: int, scheme: str, rng: random.Random
) -> tuple[CipherText, View, Key, list[str]]:
    """Encipher a reference corpus and return the ciphertext plus the hidden key."""
    plain = baseline_view(corpus_id, n_words, rng)
    words = ["".join(word) for word in plain.words]
    if scheme == "abjad":
        words = [
            stripped for word in words if (stripped := "".join(c for c in word if c not in VOWELS))
        ]
    ciphertext_words, key = encipher(words, scheme, rng)
    view = View(name=f"synthetic|{corpus_id}|{scheme}", lines=[ciphertext_words])
    width = CHANNEL_WIDTH.get(scheme)
    ciphertext = (
        fixed_width_units(view, width, view.name, min_count=1)
        if width
        else build_ciphertext(view, view.name, min_count=1)
    )
    return ciphertext, view, key, words


def true_key_array(key: Key, ciphertext: CipherText) -> np.ndarray | None:
    """The hidden key as a cipher-unit -> letter array.

    Works for verbose keys too, because the merged channel's units are exactly
    the concatenated glyph groups the key assigned.
    """
    letters = {letter: index for index, letter in enumerate(ALPHABET)}
    mapping = {"".join(units): plain for plain, units in key.mapping.items()}
    if not set(mapping) & set(ciphertext.units):
        return None
    array = np.zeros(ciphertext.size, dtype=np.int64)
    for index, unit in enumerate(ciphertext.units):
        if index == 0:
            continue
        array[index] = letters.get(mapping.get(unit, ""), 0)
    return array


def run_recovery(
    corpus_id: str,
    n_words: int,
    scheme: str,
    lm: CharLM,
    rng: random.Random,
    iterations: int,
    restarts: int,
) -> Recovery:
    """Encipher, search blind, and score how much of the key came back."""
    ciphertext, _, key, plaintext_words = synthetic_ciphertext(corpus_id, n_words, scheme, rng)
    result = search_key(ciphertext, lm, rng, iterations=iterations, restarts=restarts)

    truth = true_key_array(key, ciphertext)
    index = ngram_index(ciphertext, lm.order)
    bits_true = score_key(truth, index, lm) if truth is not None else float("nan")

    if truth is None:
        key_accuracy = float("nan")
    else:
        weights = index.unit_counts[1:]
        key_accuracy = float(
            (weights * (result.key[1:] == truth[1:])).sum() / max(weights.sum(), 1)
        )

    decoded = "".join(ALPHABET[symbol] for symbol in result.key[ciphertext.ids]).split("#")
    decoded_words = [word for word in decoded if word]
    matched = sum(
        1 for found, real in zip(decoded_words, plaintext_words, strict=False) if found == real
    )
    return Recovery(
        scheme=scheme,
        corpus=corpus_id,
        n_tokens=ciphertext.n_tokens,
        key_accuracy=key_accuracy,
        token_accuracy=matched / max(len(plaintext_words), 1),
        bits_true_key=bits_true,
        bits_found_key=result.bits,
    )
