"""Synthetic ground truth: real plaintext enciphered into Voynich-like text.

This is the only place in the programme where the answer is known, so it is
what confidence calibration (Phase 4.6) and the Phase 5 audit are measured
against. If the pipeline cannot recover a key it invented itself, its output on
the real manuscript means nothing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from vcat.eva_charset import EVA_BASIC, EVA_COMPOUNDS
from vcat.exceptions import ConfigurationError

Words = list[list[str]]

SCHEMES = ("substitution", "abjad", "verbose")
VOWELS = frozenset("aeiou")

# Cipher alphabet: single EVA glyphs first, then compounds, in a fixed order.
CIPHER_UNITS: tuple[str, ...] = tuple(sorted(EVA_BASIC)) + tuple(sorted(EVA_COMPOUNDS))


@dataclass(frozen=True)
class Key:
    """The key used to encipher, kept so recovery can be scored unit by unit."""

    scheme: str
    mapping: dict[str, tuple[str, ...]]

    @property
    def plaintext_alphabet(self) -> tuple[str, ...]:
        """Plaintext symbols this key covers, sorted."""
        return tuple(sorted(self.mapping))


def _make_key(plaintext_symbols: list[str], scheme: str, rng: random.Random) -> Key:
    ciphertext_symbols: list[tuple[str, ...]]
    pool = list(CIPHER_UNITS)
    rng.shuffle(pool)
    if scheme == "verbose":
        # Two glyphs per plaintext symbol: the "verbose cipher" hypothesis.
        ciphertext_symbols = [(first, second) for first in pool for second in pool]
        rng.shuffle(ciphertext_symbols)
    else:
        ciphertext_symbols = [(unit,) for unit in pool]
    if len(plaintext_symbols) > len(ciphertext_symbols):
        raise ConfigurationError(
            "Cipher alphabet too small",
            {"plaintext": len(plaintext_symbols), "cipher": len(ciphertext_symbols)},
        )
    return Key(
        scheme=scheme, mapping=dict(zip(plaintext_symbols, ciphertext_symbols, strict=False))
    )


def encipher(words: list[str], scheme: str, rng: random.Random) -> tuple[Words, Key]:
    """Encipher normalised plaintext words under ``scheme``.

    ``substitution`` maps each letter to one glyph, ``abjad`` drops vowels
    first, ``verbose`` maps each letter to a fixed pair of glyphs. Returns the
    ciphertext as unit lists plus the key that produced it.
    """
    if scheme not in SCHEMES:
        raise ConfigurationError("Unknown cipher scheme", {"scheme": scheme, "known": SCHEMES})

    if scheme == "abjad":
        words = [
            stripped for word in words if (stripped := "".join(c for c in word if c not in VOWELS))
        ]

    symbols = sorted({char for word in words for char in word})
    key = _make_key(symbols, scheme, rng)
    ciphertext: Words = [[unit for char in word for unit in key.mapping[char]] for word in words]
    return ciphertext, key
