"""Estimators shared by the Phase 1 modules.

Plug-in entropy on 170k symbols overestimates order-3+ structure badly, so every
entropy here is reported with a bias correction (Miller–Madow and Chao–Shen) and
a block bootstrap CI that resamples *lines*, preserving within-line structure.
"""

from __future__ import annotations

import bz2
import gzip
import lzma
import math
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

LN2 = math.log(2.0)


@dataclass(frozen=True)
class Estimate:
    """A point estimate with a bootstrap interval."""

    value: float
    low: float | None = None
    high: float | None = None
    n: int = 0

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly form."""
        return {"value": self.value, "ci_low": self.low, "ci_high": self.high, "n": self.n}

    @property
    def width(self) -> float:
        """CI width, or 0.0 when no interval was computed."""
        if self.low is None or self.high is None:
            return 0.0
        return self.high - self.low


def _ngram_codes(sequence: np.ndarray, order: int) -> np.ndarray:
    """Encode order-``order`` blocks as single integers."""
    if order == 1:
        return sequence
    alphabet = int(sequence.max()) + 1 if sequence.size else 1
    codes = np.zeros(sequence.size - order + 1, dtype=np.int64)
    for offset in range(order):
        codes = codes * alphabet + sequence[offset : sequence.size - order + 1 + offset]
    return codes


def plugin_entropy(counts: np.ndarray) -> float:
    """Maximum-likelihood (plug-in) entropy in bits."""
    total = counts.sum()
    if total == 0:
        return 0.0
    probabilities = counts / total
    return float(-(probabilities * np.log2(probabilities)).sum())


def miller_madow(counts: np.ndarray) -> float:
    """Plug-in entropy with the Miller–Madow bias correction."""
    total = counts.sum()
    if total == 0:
        return 0.0
    return float(plugin_entropy(counts) + (counts.size - 1) / (2.0 * float(total) * LN2))


def chao_shen(counts: np.ndarray) -> float:
    """Chao–Shen coverage-adjusted entropy — a second opinion on the bias."""
    total = counts.sum()
    if total == 0:
        return 0.0
    singletons = int((counts == 1).sum())
    coverage = 1.0 - singletons / total if singletons < total else 1.0 / total
    probabilities = coverage * counts / total
    inclusion = 1.0 - (1.0 - probabilities) ** total
    inclusion = np.where(inclusion <= 0, 1.0, inclusion)
    return float(-(probabilities * np.log2(probabilities) / inclusion).sum())


def block_entropy(sequence: np.ndarray, order: int, estimator: str = "miller_madow") -> float:
    """Entropy of order-``order`` blocks, in bits per block."""
    codes = _ngram_codes(sequence, order)
    if codes.size == 0:
        return 0.0
    _, counts = np.unique(codes, return_counts=True)
    if estimator == "plugin":
        return plugin_entropy(counts)
    if estimator == "chao_shen":
        return chao_shen(counts)
    return miller_madow(counts)


def conditional_entropy(sequence: np.ndarray, order: int, estimator: str = "miller_madow") -> float:
    """``h_order`` = H(block of ``order``) − H(block of ``order``−1), in bits/symbol."""
    if order <= 1:
        return block_entropy(sequence, 1, estimator)
    return block_entropy(sequence, order, estimator) - block_entropy(sequence, order - 1, estimator)


def h0(sequence: np.ndarray) -> float:
    """Alphabet entropy: log2 of the number of distinct symbols."""
    distinct = np.unique(sequence).size
    return math.log2(distinct) if distinct else 0.0


def bootstrap_ci(
    statistic: Callable[[list[Any]], float],
    blocks: list[Any],
    rng: random.Random,
    resamples: int,
    confidence: float = 0.95,
) -> Estimate:
    """Block bootstrap over ``blocks`` (lines), percentile interval."""
    point = statistic(blocks)
    if resamples <= 0 or not blocks:
        return Estimate(value=point, n=len(blocks))
    size = len(blocks)
    samples = np.empty(resamples, dtype=float)
    for index in range(resamples):
        draw = [blocks[rng.randrange(size)] for _ in range(size)]
        samples[index] = statistic(draw)
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(samples, [tail, 1.0 - tail])
    return Estimate(value=point, low=float(low), high=float(high), n=size)


def compression_ratios(text: str) -> dict[str, float]:
    """Compressed size / raw size for three general-purpose compressors."""
    raw = text.encode()
    if not raw:
        return {}
    return {
        "gzip": len(gzip.compress(raw, 9)) / len(raw),
        "bz2": len(bz2.compress(raw, 9)) / len(raw),
        "lzma": len(lzma.compress(raw)) / len(raw),
    }


def relative_difference(value: float, reference: float) -> float | None:
    """``(value − reference) / |reference|``; ``None`` when the reference is 0."""
    if reference == 0:
        return None
    return (value - reference) / abs(reference)


def separated(estimate: Estimate, other: Estimate) -> bool:
    """True when two bootstrap intervals do not overlap."""
    if None in (estimate.low, estimate.high, other.low, other.high):
        return False
    assert estimate.low is not None and estimate.high is not None
    assert other.low is not None and other.high is not None
    return estimate.high < other.low or other.high < estimate.low


def cohens_h(proportion_a: float, proportion_b: float) -> float:
    """Effect size for a difference of proportions."""
    return float(
        2 * math.asin(math.sqrt(max(proportion_a, 0.0)))
        - 2 * math.asin(math.sqrt(max(proportion_b, 0.0)))
    )
