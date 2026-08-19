"""§3.8 — transcription robustness.

Only 29.3% of lines are identical between the two major EVA transcriptions, so
any single-source result inherits that noise. Each headline metric is recomputed
on every transcription that covers the line, paired against ZL on exactly the
same lines, and compared to its own bootstrap CI. A metric whose cross-source
variation exceeds its CI cannot support a decipherment claim.
"""

from __future__ import annotations

import numpy as np

from translations.analysis.common import View, encode_lines, encode_units, voynich_view
from translations.analysis.context import Context, hapax_rate, mean_word_length
from translations.analysis.stats import Estimate, bootstrap_ci, conditional_entropy
from translations.analysis.syntax import near_repeats
from translations.config import CONFIG, CommaPolicy, Tokenizer, Transcription
from translations.determinism import derived_rng
from translations.report import Topic, table

METRICS: tuple[str, ...] = ("h2", "mean_word_length", "ttr", "hapax_rate", "near_repeat_within_2")


def metric_row(view: View) -> dict[str, float]:
    """The alphabet-agnostic metric battery (computed on `T0-char` units)."""
    return {
        "tokens": float(view.n_words),
        "h2": conditional_entropy(encode_units(view), 2),
        "mean_word_length": mean_word_length(view),
        "ttr": view.n_types / view.n_words if view.n_words else 0.0,
        "hapax_rate": hapax_rate(view),
        "near_repeat_within_2": near_repeats(view)["within_2"],
    }


def bootstrap_metric(view: View, metric: str, resamples: int) -> Estimate:
    """Block bootstrap CI for one metric on one view."""
    rng = derived_rng(f"robust-{view.name}-{metric}")
    if metric == "h2":
        return bootstrap_ci(
            lambda sample: conditional_entropy(np.concatenate(sample), 2),
            encode_lines(view),
            rng,
            resamples,
        )
    return bootstrap_ci(
        lambda sample: metric_row(View(name=view.name, lines=list(sample)))[metric],
        view.lines,
        rng,
        resamples,
    )


def paired_views(source: Transcription) -> tuple[View, View] | None:
    """``(source view, ZL view on the same lines)`` — a fair paired comparison."""
    view = voynich_view(f"voynich|T0|{source}", Tokenizer.T0_CHAR, CommaPolicy.BREAK, source)
    if not view.rows:
        return None
    covered = {row.line_id for row in view.rows}
    reference = voynich_view(
        f"voynich|T0|zl∩{source}",
        Tokenizer.T0_CHAR,
        CommaPolicy.BREAK,
        Transcription.ZL,
        keep=lambda row: row.line_id in covered,
    )
    return view, reference


def run(ctx: Context) -> Topic:
    """Recompute headline metrics on every transcription and rank their stability."""
    resamples = CONFIG.bootstrap_resamples
    zl_full = voynich_view("voynich|T0|zl", Tokenizer.T0_CHAR, CommaPolicy.BREAK, Transcription.ZL)
    # Only h2 is cheap enough for the full resample budget; the rest rebuild views.
    reference_ci = {
        metric: bootstrap_metric(zl_full, metric, resamples if metric == "h2" else resamples // 4)
        for metric in METRICS
    }

    per_source: dict[str, dict[str, float]] = {"zl (all lines)": metric_row(zl_full)}
    deltas: dict[str, dict[str, float]] = {}
    for source in Transcription:
        if source is Transcription.ZL:
            continue
        pair = paired_views(source)
        if pair is None:
            continue
        view, reference = pair
        source_row = metric_row(view)
        reference_row = metric_row(reference)
        per_source[f"{source} ({view.n_words:,} tokens)"] = source_row
        deltas[str(source)] = {
            metric: source_row[metric] - reference_row[metric] for metric in METRICS
        }
        deltas[str(source)]["lines"] = float(len(view.rows))

    stability = {}
    for metric in METRICS:
        width = reference_ci[metric].width
        eva_delta = abs(deltas.get("it", {}).get(metric, 0.0))
        all_delta = max((abs(row[metric]) for row in deltas.values()), default=0.0)
        stability[metric] = {
            "zl_value": reference_ci[metric].value,
            "ci_width": width,
            "eva_abs_delta": eva_delta,
            "eva_ratio": eva_delta / width if width else float("inf"),
            "all_abs_delta": all_delta,
            "all_ratio": all_delta / width if width else float("inf"),
            "robust": bool(width and eva_delta <= width),
        }

    ranked = sorted(stability.items(), key=lambda item: item[1]["eva_ratio"])

    sections = [
        "## Metrics per transcription (`T0-char`; CD/FG/GC are not EVA)\n\n"
        + table(
            ["source", "tokens", *METRICS],
            [
                [name, int(row["tokens"]), *[row[metric] for metric in METRICS]]
                for name, row in per_source.items()
            ],
        ),
        "## Paired differences against ZL on the same lines\n\n"
        + table(
            ["source", "lines", *METRICS],
            [
                [name, int(row["lines"]), *[row[metric] for metric in METRICS]]
                for name, row in deltas.items()
            ],
        ),
        "## Stability ranking\n\n"
        + table(
            [
                "metric",
                "ZL value",
                "bootstrap CI width",
                "abs Δ (ZL vs IT)",
                "Δ / CI (EVA)",
                "abs Δ (all sources)",
                "Δ / CI (all)",
                "verdict",
            ],
            [
                [
                    metric,
                    row["zl_value"],
                    row["ci_width"],
                    row["eva_abs_delta"],
                    row["eva_ratio"],
                    row["all_abs_delta"],
                    row["all_ratio"],
                    "robust within EVA" if row["robust"] else "transcription-limited",
                ]
                for metric, row in ranked
            ],
        )
        + "\n\nThe verdict column uses the EVA pair (ZL vs IT) only. CD, FG and GC use "
        + "different alphabets, so their deltas measure alphabet plus transcription and are "
        + "reported as context, not as instability of the metric. A metric marked "
        + "*transcription-limited* varies more between two EVA transcriptions than its own "
        + "sampling error, and cannot by itself support a decipherment claim.",
    ]

    data = {"per_source": per_source, "deltas": deltas, "stability": stability}
    return Topic(
        topic="robustness",
        title="Phase 1 — Transcription robustness",
        sections=sections,
        data=data,
    )
