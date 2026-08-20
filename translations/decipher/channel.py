"""Channel models: how a plaintext could have become the observed glyph stream.

Everything downstream works on :class:`CipherText` — the manuscript as integer
unit ids with word boundaries — and on keys that are plain integer arrays, so a
decode is one numpy index operation.

Each channel declares the size of its key space in bits; that number is the MDL
penalty in the scoring (plan §4.1), and it is what stops an unconstrained key
from "explaining" anything it likes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from translations.analysis.common import View
from translations.decipher.lm import ALPHABET, BOUNDARY

BOUNDARY_ID = 0
RARE = "?"  # every unit below the frequency floor is folded into this one symbol
MIN_UNIT_COUNT = 20


@dataclass(frozen=True)
class CipherText:
    """The observed text as cipher-unit ids, boundaries included."""

    name: str
    units: tuple[str, ...]  # id -> unit string; index 0 is the word boundary
    ids: np.ndarray
    n_tokens: int

    @property
    def size(self) -> int:
        """Cipher alphabet size, boundary included."""
        return len(self.units)

    @property
    def n_units(self) -> int:
        """Length of the id stream, boundaries excluded."""
        return int((self.ids != BOUNDARY_ID).sum())

    def counts(self) -> np.ndarray:
        """Unit frequencies."""
        return np.bincount(self.ids, minlength=self.size).astype(float)


def build_ciphertext(
    view: View, name: str | None = None, min_count: int = MIN_UNIT_COUNT
) -> CipherText:
    """Encode a view as a cipher stream: units, then a boundary after each word.

    Units occurring fewer than ``min_count`` times — the high-ASCII tokens and
    the rarest glyphs — are folded into a single ``?`` symbol. Left alone they
    would each claim a key slot they can never provide evidence for.
    """
    counts: dict[str, int] = {}
    for word in view.words:
        for unit in word:
            counts[unit] = counts.get(unit, 0) + 1
    inventory = sorted(unit for unit, count in counts.items() if count >= min_count)
    rare = sorted(unit for unit, count in counts.items() if count < min_count)
    lookup = {unit: index + 1 for index, unit in enumerate(inventory)}
    if rare:
        for unit in rare:
            lookup[unit] = len(inventory) + 1

    stream: list[int] = [BOUNDARY_ID]
    for word in view.words:
        stream.extend(lookup[unit] for unit in word)
        stream.append(BOUNDARY_ID)
    units = (BOUNDARY, *inventory) + ((RARE,) if rare else ())
    return CipherText(
        name=name or view.name,
        units=units,
        ids=np.array(stream, dtype=np.int64),
        n_tokens=view.n_words,
    )


Merge = tuple[str, ...]


def merge_units(
    view: View, merges: tuple[Merge, ...], name: str, min_count: int = MIN_UNIT_COUNT
) -> CipherText:
    """Re-tokenise a view treating each unit sequence in ``merges`` as one unit.

    This is the verbose-cipher channel (H2): if several glyphs spell one
    plaintext letter, the merged text is what a substitution cipher would have
    produced. Merges are sequences of *units*, so a compound glyph like ``ch``
    is never split apart.
    """
    ordered = sorted(set(merges), key=len, reverse=True)
    words: list[list[str]] = []
    for word in view.words:
        pieces: list[str] = []
        cursor = 0
        while cursor < len(word):
            for merge in ordered:
                if merge and tuple(word[cursor : cursor + len(merge)]) == merge:
                    pieces.append("".join(merge))
                    cursor += len(merge)
                    break
            else:
                pieces.append(word[cursor])
                cursor += 1
        words.append(pieces)
    return build_ciphertext(View(name=name, lines=[words]), name, min_count)


def merge_description_bits(merges: tuple[Merge, ...], glyph_alphabet: int) -> float:
    """Bits to write down a merge partition (part of the H2 key)."""
    return sum(len(merge) * math.log2(glyph_alphabet) + 1.0 for merge in merges)


def key_description_bits(cipher_size: int, plaintext_size: int = len(ALPHABET)) -> float:
    """Bits to write down a substitution key over ``cipher_size`` units."""
    return (cipher_size - 1) * math.log2(plaintext_size)


def decode(key: np.ndarray, ciphertext: CipherText) -> np.ndarray:
    """Apply a key: cipher ids -> plaintext ids."""
    return key[ciphertext.ids]


def identity_key(ciphertext: CipherText, plaintext_size: int = len(ALPHABET)) -> np.ndarray:
    """A starting key that maps every unit to a letter, boundary fixed."""
    key = np.zeros(ciphertext.size, dtype=np.int64)
    for index in range(1, ciphertext.size):
        key[index] = 1 + (index - 1) % (plaintext_size - 1)
    return key


def key_as_dict(key: np.ndarray, ciphertext: CipherText) -> dict[str, str]:
    """Human-readable key, boundary excluded."""
    return {ciphertext.units[index]: ALPHABET[key[index]] for index in range(1, ciphertext.size)}


def fixed_width_units(
    view: View, width: int, name: str, min_count: int = MIN_UNIT_COUNT
) -> CipherText:
    """Chop every word into consecutive groups of ``width`` units.

    The fixed-width form of the verbose hypothesis: if each plaintext letter is
    written with exactly ``width`` glyphs, this segmentation is the right one and
    no partition search is needed. A trailing short group is kept as its own unit.
    """
    words = [
        ["".join(word[start : start + width]) for start in range(0, len(word), width)]
        for word in view.words
    ]
    return build_ciphertext(View(name=name, lines=[words]), name, min_count)
