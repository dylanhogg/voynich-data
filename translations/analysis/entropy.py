"""§3.2 — information-theoretic suite.

The headline claim under test: *Voynich h2 is anomalously low versus natural
language at matched sample size*. It is only worth anything if it survives on a
second transcription, on the consensus subset, and against baselines cut to the
manuscript's own token count.
"""

from __future__ import annotations

import numpy as np

from translations.analysis.common import View, encode_forms, encode_lines, encode_units, text_of
from translations.analysis.context import Context
from translations.analysis.stats import (
    Estimate,
    block_entropy,
    bootstrap_ci,
    compression_ratios,
    conditional_entropy,
    h0,
    relative_difference,
    separated,
)
from translations.config import CONFIG
from translations.determinism import derived_rng
from translations.report import Topic, fmt, table

ORDERS = tuple(range(1, CONFIG.max_ngram_order + 1))


def conditional_entropies(view: View) -> dict[str, float]:
    """h1…h5 over units, with word boundaries in the stream."""
    sequence = encode_units(view)
    return {f"h{order}": conditional_entropy(sequence, order) for order in ORDERS}


def h2_estimate(view: View, resamples: int = CONFIG.bootstrap_resamples) -> Estimate:
    """h2 with a block bootstrap CI over lines."""
    lines = encode_lines(view)

    def statistic(blocks: list[np.ndarray]) -> float:
        return conditional_entropy(np.concatenate(blocks), 2)

    return bootstrap_ci(statistic, lines, derived_rng(f"h2-{view.name}"), resamples)


def word_entropies(view: View) -> dict[str, float]:
    """Unigram and conditional word-level entropy (heavily undersampled at h2)."""
    forms = encode_forms(view.forms)
    return {
        "word_h1": block_entropy(forms, 1),
        "word_h2": conditional_entropy(forms, 2),
    }


def entropy_row(view: View, estimate: Estimate) -> dict[str, float | None]:
    """Every entropy number reported for one view, given its bootstrapped h2."""
    sequence = encode_units(view)
    row: dict[str, float | None] = {
        "n_words": float(view.n_words),
        "n_units": float(view.n_units),
        "H0": h0(sequence),
        **conditional_entropies(view),
        "h2_ci_low": estimate.low,
        "h2_ci_high": estimate.high,
        **word_entropies(view),
        **{f"compress_{name}": value for name, value in compression_ratios(text_of(view)).items()},
    }
    return row


def _entropy_table(rows: dict[str, dict[str, float | None]]) -> str:
    headers = ["view", "words", "H0", *[f"h{order}" for order in ORDERS], "h2 CI", "word h1"]
    body = [
        [
            name,
            int(row["n_words"] or 0),
            row["H0"],
            *[row[f"h{order}"] for order in ORDERS],
            f"[{fmt(row['h2_ci_low'])}, {fmt(row['h2_ci_high'])}]",
            row["word_h1"],
        ]
        for name, row in rows.items()
    ]
    return table(headers, body)


def run(ctx: Context) -> Topic:
    """Compute the entropy suite over grid, strata, baselines and nulls."""
    resamples = CONFIG.bootstrap_resamples
    estimates = {
        view.name: h2_estimate(view, resamples)
        for view in [ctx.base, *ctx.grid.values(), *ctx.strata.values(), *ctx.comparisons.values()]
    }

    grid = {name: entropy_row(view, estimates[view.name]) for name, view in ctx.grid.items()}
    strata = {name: entropy_row(view, estimates[view.name]) for name, view in ctx.strata.items()}
    comparisons = {
        name: entropy_row(view, estimates[view.name]) for name, view in ctx.comparisons.items()
    }

    base_estimate = estimates[ctx.base.name]
    claim_rows = []
    claim_data = {}
    for name, view in ctx.comparisons.items():
        other = estimates[view.name]
        claim_rows.append(
            [
                name,
                other.value,
                base_estimate.value - other.value,
                relative_difference(base_estimate.value, other.value),
                separated(base_estimate, other),
            ]
        )
        claim_data[name] = {
            "h2": other.as_dict(),
            "delta_voynich_minus_other": base_estimate.value - other.value,
            "ci_separated": separated(base_estimate, other),
        }

    it_row = grid["T1-glyph|CB=break|it"]
    consensus_row = strata["consensus"]
    survives = {
        "on_IT": bool(it_row["h2"] is not None and it_row["h2"] < 3.0),
        "on_consensus": bool(consensus_row["h2"] is not None and consensus_row["h2"] < 3.0),
    }

    sections = [
        "## Tokenization × transcription grid\n\n" + _entropy_table(grid),
        "## Strata\n\n" + _entropy_table(strata),
        "## Baselines (sample-size matched), nulls and pseudo-Voynich\n\n"
        + _entropy_table(comparisons),
        "## Headline claim: Voynich h2 versus everything else\n\n"
        + f"Voynich h2 = {fmt(base_estimate.value)} "
        + f"[{fmt(base_estimate.low)}, {fmt(base_estimate.high)}] "
        + f"bits/glyph over {ctx.base.n_words:,} words.\n\n"
        + table(
            ["comparison", "h2", "Voynich − other", "relative", "CIs disjoint"],
            claim_rows,
        )
        + "\n\nThe claim survives on IT: "
        + fmt(survives["on_IT"])
        + "; on the consensus subset: "
        + fmt(survives["on_consensus"])
        + ".",
        "## Compression bounds\n\n"
        + table(
            ["view", "gzip", "bz2", "lzma"],
            [
                [name, row.get("compress_gzip"), row.get("compress_bz2"), row.get("compress_lzma")]
                for name, row in (
                    {"voynich|base": entropy_row(ctx.base, base_estimate)} | comparisons
                ).items()
            ],
        ),
    ]

    data = {
        "grid": grid,
        "strata": strata,
        "comparisons": comparisons,
        "headline": {
            "voynich_h2": base_estimate.as_dict(),
            "versus": claim_data,
            "survives": survives,
        },
        "bootstrap_resamples": resamples,
    }
    return Topic(
        topic="entropy",
        title="Phase 1 — Information-theoretic suite",
        sections=sections,
        data=data,
    )
