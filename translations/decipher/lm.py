"""Character language models over the candidate plaintext languages (plan §4.3.2).

Dense n-gram tables over a small alphabet (26 letters plus a word boundary), so
scoring a decoded corpus is one numpy fancy-index rather than a Python loop —
which is what makes hundreds of thousands of key evaluations affordable on CPU.

Smoothing is Witten–Bell, built bottom-up from order 1. Kneser–Ney was not used:
its advantage is on word-level models with rich continuation structure, and at
this alphabet size the two are indistinguishable next to the noise in the
decipherment score itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from translations.corpora import load_corpus
from vcat.exceptions import ConfigurationError

BOUNDARY = "#"
VOWELS = "aeiou"
LETTERS = "abcdefghijklmnopqrstuvwxyz"
ALPHABET: tuple[str, ...] = (BOUNDARY, *LETTERS)
MAX_ORDER = 4  # 27**5 dense tables would be 115 MB each; see plan §4.3 deltas.


@dataclass(frozen=True)
class CharLM:
    """Dense order-``n`` character model, log2 probabilities."""

    name: str
    order: int
    alphabet: tuple[str, ...]
    table: np.ndarray  # shape (V,) * order, last axis is the predicted symbol

    @property
    def size(self) -> int:
        """Alphabet size."""
        return len(self.alphabet)

    def index(self, symbols: str) -> np.ndarray:
        """Encode a string to symbol ids, unknown characters folded to boundary."""
        lookup = {symbol: index for index, symbol in enumerate(self.alphabet)}
        return np.fromiter(
            (lookup.get(character, 0) for character in symbols), dtype=np.int64, count=len(symbols)
        )

    def bits(self, ids: np.ndarray) -> float:
        """Total bits to encode an id sequence under this model."""
        if ids.size < self.order:
            return 0.0
        views = [ids[offset : ids.size - self.order + 1 + offset] for offset in range(self.order)]
        return float(-self.table[tuple(views)].sum())

    def bits_per_symbol(self, ids: np.ndarray) -> float:
        """Average bits per symbol."""
        return float(self.bits(ids) / max(ids.size - self.order + 1, 1))


def _counts(ids: np.ndarray, order: int, size: int) -> np.ndarray:
    """Dense n-gram counts of an id sequence."""
    if ids.size < order:
        return np.zeros((size,) * order)
    flat = np.zeros(size**order, dtype=np.float64)
    codes = np.zeros(ids.size - order + 1, dtype=np.int64)
    for offset in range(order):
        codes = codes * size + ids[offset : ids.size - order + 1 + offset]
    np.add.at(flat, codes, 1.0)
    return flat.reshape((size,) * order)


def _witten_bell(counts: np.ndarray, lower: np.ndarray) -> np.ndarray:
    """One Witten–Bell interpolation step: counts over a backed-off distribution."""
    totals = counts.sum(axis=-1, keepdims=True)
    distinct = (counts > 0).sum(axis=-1, keepdims=True).astype(float)
    # A context never seen falls back entirely to the lower-order model.
    weight = np.where(totals + distinct > 0, distinct / np.maximum(totals + distinct, 1e-12), 1.0)
    higher = np.divide(counts, np.maximum(totals + distinct, 1e-12))
    return higher + weight * lower


def train_char_lm(text: str, order: int = 3, name: str = "lm") -> CharLM:
    """Train a Witten–Bell smoothed character model on normalised text.

    ``text`` is a space-separated word stream; spaces become the boundary symbol
    so that word length is part of what the model knows.
    """
    if not 1 <= order <= MAX_ORDER:
        raise ConfigurationError("Unsupported LM order", {"order": order, "max": MAX_ORDER})

    size = len(ALPHABET)
    lookup = {symbol: index for index, symbol in enumerate(ALPHABET)}
    stream = BOUNDARY + text.replace(" ", BOUNDARY) + BOUNDARY
    ids = np.fromiter(
        (lookup.get(character, 0) for character in stream), dtype=np.int64, count=len(stream)
    )

    distribution = np.full((size,), 1.0 / size)
    for current in range(1, order + 1):
        counts = _counts(ids, current, size)
        lower = np.broadcast_to(distribution, (size,) * current)
        distribution = _witten_bell(counts, lower)

    with np.errstate(divide="ignore"):
        table = np.log2(np.maximum(distribution, 1e-300))
    return CharLM(name=name, order=order, alphabet=ALPHABET, table=table)


_NO_VOWELS = str.maketrans("", "", VOWELS)
TRANSFORMS: tuple[str, ...] = ("plain", "abjad", "abbrev")


def abbreviate(word: str) -> str:
    """A crude, deterministic stand-in for medieval Latin abbreviation (H4).

    Suspension of the commonest endings, nasal contraction before a consonant,
    and ``-que`` written as a single sign. Real scribal practice is irregular and
    context-dependent; this is a proxy, and the hypothesis record says so.
    """
    if word.endswith("que") and len(word) > 4:
        word = word[:-3] + "q"
    for ending in ("orum", "arum", "ibus", "us", "um", "is", "em"):
        if word.endswith(ending) and len(word) > len(ending) + 1:
            word = word[: -len(ending)]
            break
    contracted = []
    for index, character in enumerate(word):
        following = word[index + 1] if index + 1 < len(word) else ""
        if character in "mn" and following and following not in VOWELS:
            continue
        contracted.append(character)
    return "".join(contracted)


@lru_cache(maxsize=32)
def corpus_lm(
    corpus_id: str, order: int = 3, transform: str = "plain", n_words: int = 300_000
) -> CharLM:
    """Train (and cache) a model on a reference corpus.

    ``transform`` selects the plaintext form the hypothesis assumes: ``abjad``
    strips vowels (H3) and ``abbrev`` applies the abbreviation proxy (H4).
    Scoring vowel-suppressed plaintext against a vowel-ful model rewards the
    wrong keys — the synthetic recovery test makes that obvious.
    """
    if transform not in TRANSFORMS:
        raise ConfigurationError("Unknown LM transform", {"transform": transform})
    words = load_corpus(corpus_id).words[:n_words]
    if transform == "abjad":
        words = [stripped for word in words if (stripped := word.translate(_NO_VOWELS))]
    elif transform == "abbrev":
        words = [short for word in words if (short := abbreviate(word))]
    suffix = "" if transform == "plain" else f"-{transform}"
    return train_char_lm(" ".join(words), order, f"{corpus_id}{suffix}-o{order}")
