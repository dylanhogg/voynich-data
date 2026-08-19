"""Estimators: entropy with bias correction, bootstrap, compression, effect sizes."""

from __future__ import annotations

import math

import numpy as np

from translations.analysis.stats import (
    Estimate,
    block_entropy,
    bootstrap_ci,
    chao_shen,
    cohens_h,
    compression_ratios,
    conditional_entropy,
    h0,
    miller_madow,
    plugin_entropy,
    relative_difference,
    separated,
)
from translations.determinism import derived_rng


def test_plugin_entropy_of_uniform_alphabet() -> None:
    counts = np.array([25, 25, 25, 25])
    assert plugin_entropy(counts) == 2.0


def test_miller_madow_corrects_upwards() -> None:
    counts = np.array([3, 3, 3, 1])
    assert miller_madow(counts) > plugin_entropy(counts)


def test_chao_shen_also_corrects_upwards_with_singletons() -> None:
    counts = np.array([10, 1, 1, 1])
    assert chao_shen(counts) > plugin_entropy(counts)


def test_block_and_conditional_entropy_on_a_periodic_sequence() -> None:
    sequence = np.array([0, 1] * 500)
    assert block_entropy(sequence, 1) > 0.9
    # Perfectly predictable given one symbol of context.
    assert conditional_entropy(sequence, 2) < 0.05


def test_h0_is_log2_alphabet() -> None:
    assert h0(np.array([0, 1, 2, 3])) == 2.0


def test_bootstrap_ci_is_reproducible_and_brackets_the_point() -> None:
    blocks = [np.array([index % 5]) for index in range(200)]

    def statistic(sample: list[np.ndarray]) -> float:
        return float(np.concatenate(sample).mean())

    first = bootstrap_ci(statistic, blocks, derived_rng("t"), 50)
    second = bootstrap_ci(statistic, blocks, derived_rng("t"), 50)
    assert first == second
    assert first.low is not None and first.high is not None
    assert first.low <= first.value <= first.high


def test_separated_detects_disjoint_intervals() -> None:
    assert separated(Estimate(1.0, 0.9, 1.1), Estimate(2.0, 1.9, 2.1))
    assert not separated(Estimate(1.0, 0.9, 1.5), Estimate(1.4, 1.2, 2.1))
    assert not separated(Estimate(1.0), Estimate(2.0))


def test_compression_ratios_are_below_one_for_repetitive_text() -> None:
    ratios = compression_ratios("daiin." * 500)
    assert set(ratios) == {"gzip", "bz2", "lzma"}
    assert all(0 < value < 0.2 for value in ratios.values())


def test_relative_difference_and_effect_size() -> None:
    assert relative_difference(1.5, 1.0) == 0.5
    assert relative_difference(1.0, 0.0) is None
    assert cohens_h(0.5, 0.5) == 0.0
    assert math.isclose(cohens_h(1.0, 0.0), math.pi)
