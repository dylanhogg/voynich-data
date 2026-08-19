"""Reference corpora: declaration, loading, normalisation and sample matching.

Entropy, TTR and hapax rates are strongly sample-size dependent, so baselines
are always compared at the Voynich sample size — see :func:`subsample_words`.
Comparing a 170k-char manuscript against a 4M-char Bible unmatched is the
classic failure mode in published Voynich comparisons (plan §2.4).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from translations.corpora.normalise import extract, normalise, word_stream
from translations.corpora.registry import CorpusSpec, get_spec, load_specs
from vcat.exceptions import SourceNotFoundError

__all__ = [
    "Corpus",
    "CorpusSpec",
    "available",
    "get_spec",
    "load_corpus",
    "load_specs",
    "subsample_words",
]


@dataclass(frozen=True)
class Corpus:
    """A normalised reference corpus."""

    spec: CorpusSpec
    words: list[str]

    @property
    def chars(self) -> str:
        """Char stream (word separators dropped)."""
        return "".join(self.words)

    @property
    def n_words(self) -> int:
        """Word count."""
        return len(self.words)

    @property
    def n_chars(self) -> int:
        """Char count, excluding separators."""
        return sum(len(word) for word in self.words)


def load_corpus(corpus_id: str, fold_diacritics: bool = True) -> Corpus:
    """Load, extract and normalise one corpus from the local cache."""
    spec = get_spec(corpus_id)
    if not spec.is_text:
        raise SourceNotFoundError("Corpus has no text loader", path=spec.path)
    if not spec.path.exists():
        raise SourceNotFoundError("Corpus not fetched; run `make corpora`", path=spec.path)
    raw = spec.path.read_text(encoding="utf-8", errors="strict")
    text = normalise(extract(raw, spec.format), fold_diacritics)
    return Corpus(spec=spec, words=word_stream(text))


def available() -> list[CorpusSpec]:
    """Declared text corpora present in the local cache."""
    return [spec for spec in load_specs() if spec.is_text and spec.path.exists()]


def subsample_words(corpus: Corpus, n_words: int, rng: random.Random) -> list[str]:
    """A contiguous ``n_words`` window of the corpus, start chosen by ``rng``.

    Contiguous rather than random-sampled: shuffling words would destroy the
    very structure the baselines are meant to exhibit.
    """
    if n_words >= corpus.n_words:
        return list(corpus.words)
    start = rng.randrange(corpus.n_words - n_words + 1)
    return corpus.words[start : start + n_words]
