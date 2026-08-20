"""One scale for every hypothesis: bits to describe the observed manuscript.

A hypothesis is a code. Its score is the total number of bits needed to
reconstruct the glyph stream exactly — the model (key, table, grammar) plus the
data under that model. This makes "meaningless table-generated text" and
"enciphered Latin" directly comparable (plan §4.2), and it *is* the MDL penalty
(§4.1): a key elaborate enough to fit anything has to pay for itself.

Two costs are easy to forget and both are charged here:

- **ambiguity bits** — if a key maps several cipher units onto one plaintext
  letter, the plaintext alone does not reconstruct the manuscript, and the
  missing choice costs ``log2(number of units sharing that letter)`` per
  occurrence. Without this, every search collapses the key onto ``e``.
- **model bits** — writing down the key, the merge partition, the syllable
  table or the automaton.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from translations.decipher.channel import (
    BOUNDARY_ID,
    CipherText,
    Merge,
    key_description_bits,
    merge_description_bits,
)
from translations.decipher.lm import ALPHABET, CharLM


@dataclass(frozen=True)
class Description:
    """A two-part code for the observed text."""

    hypothesis: str
    model_bits: float
    data_bits: float
    n_tokens: int
    detail: str = ""

    @property
    def total_bits(self) -> float:
        """Model plus data."""
        return self.model_bits + self.data_bits

    @property
    def bits_per_token(self) -> float:
        """Total bits per manuscript word."""
        return self.total_bits / max(self.n_tokens, 1)

    def as_dict(self) -> dict[str, float | str | int]:
        """JSON-friendly form."""
        return {
            "hypothesis": self.hypothesis,
            "model_bits": self.model_bits,
            "data_bits": self.data_bits,
            "total_bits": self.total_bits,
            "bits_per_token": self.bits_per_token,
            "n_tokens": self.n_tokens,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class NgramIndex:
    """Distinct cipher n-grams and their counts — the fast path for scoring keys.

    Scoring a key means summing log-probabilities over the *distinct* n-grams
    weighted by frequency, not walking 186k positions, which is what makes a
    million-evaluation search affordable on CPU.
    """

    order: int
    grams: np.ndarray  # shape (m, order)
    counts: np.ndarray  # shape (m,)
    unit_counts: np.ndarray  # cipher unit frequencies, including boundaries

    @property
    def n_positions(self) -> float:
        """Total scored positions."""
        return float(self.counts.sum())


def ngram_index(ciphertext: CipherText, order: int) -> NgramIndex:
    """Index a ciphertext for repeated key scoring."""
    ids = ciphertext.ids
    columns = [ids[offset : ids.size - order + 1 + offset] for offset in range(order)]
    stacked = np.stack(columns, axis=1)
    codes = np.zeros(stacked.shape[0], dtype=np.int64)
    for column in range(order):
        codes = codes * ciphertext.size + stacked[:, column]
    unique, index, counts = np.unique(codes, return_index=True, return_counts=True)
    return NgramIndex(
        order=order,
        grams=stacked[index],
        counts=counts.astype(float),
        unit_counts=np.bincount(ids, minlength=ciphertext.size).astype(float),
    )


def lm_bits(key: np.ndarray, index: NgramIndex, lm: CharLM) -> float:
    """Bits to encode the decoded plaintext under ``lm``."""
    decoded = key[index.grams]
    return float(-(lm.table[tuple(decoded.T)] * index.counts).sum())


def ambiguity_bits(key: np.ndarray, index: NgramIndex) -> float:
    """Bits to recover which cipher unit produced each plaintext letter."""
    shared = np.bincount(key[1:], minlength=len(ALPHABET)).astype(float)
    per_unit = np.log2(np.maximum(shared[key], 1.0))
    per_unit[BOUNDARY_ID] = 0.0
    return float((per_unit * index.unit_counts).sum())


def substitution_description(
    key: np.ndarray,
    index: NgramIndex,
    lm: CharLM,
    ciphertext: CipherText,
    hypothesis: str,
    merges: tuple[Merge, ...] = (),
    glyph_alphabet: int = 25,
) -> Description:
    """Description length of the manuscript as enciphered plaintext."""
    model = key_description_bits(ciphertext.size) + merge_description_bits(merges, glyph_alphabet)
    data = lm_bits(key, index, lm) + ambiguity_bits(key, index)
    return Description(
        hypothesis=hypothesis,
        model_bits=model,
        data_bits=data,
        n_tokens=ciphertext.n_tokens,
        detail=f"lm={lm.name}, units={ciphertext.size}, merges={len(merges)}",
    )


def markov_description(ciphertext: CipherText, order: int = 2) -> Description:
    """Baseline: an order-``order`` Markov model of the glyph stream itself.

    This is the code every hypothesis has to beat. It knows nothing about
    language — it just knows the manuscript's own n-gram statistics — so a
    hypothesis that cannot beat it is not explaining anything.
    """
    index = ngram_index(ciphertext, order + 1)
    size = ciphertext.size
    context_codes = np.zeros(index.grams.shape[0], dtype=np.int64)
    for column in range(order):
        context_codes = context_codes * size + index.grams[:, column]

    data = 0.0
    parameters = 0
    for context in np.unique(context_codes):
        mask = context_codes == context
        counts = index.counts[mask]
        total = counts.sum()
        data += float(-(counts * np.log2(counts / total)).sum())
        parameters += int(mask.sum()) - 1
    model = parameters / 2 * math.log2(max(index.n_positions, 2))
    return Description(
        hypothesis=f"baseline-markov-{order}",
        model_bits=model,
        data_bits=data,
        n_tokens=ciphertext.n_tokens,
        detail=f"{parameters} free parameters",
    )


def gain_per_token(description: Description, baseline: Description) -> float:
    """Bits per token saved against the baseline description. Higher is better."""
    return (baseline.total_bits - description.total_bits) / max(description.n_tokens, 1)
