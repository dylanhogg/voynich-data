"""§3.9 — sensitivity to the uncertainty flags and to the first-option convention.

``text_clean`` keeps only the first option of an ``[a:b]`` reading. That is a
convention, not a fact about the manuscript, so this module re-reads the corpus
with the second option and reports what moves.
"""

from __future__ import annotations

from translations.analysis.common import View, encode_units, voynich_view
from translations.analysis.context import Context, hapax_rate, mean_word_length
from translations.analysis.stats import conditional_entropy, relative_difference
from translations.analysis.syntax import near_repeats
from translations.config import Transcription
from translations.io import load_lines, transcription_text
from translations.report import Topic, table
from translations.strata import StratumRow

METRICS: tuple[str, ...] = ("h2", "mean_word_length", "ttr", "hapax_rate", "near_repeat_within_2")

FLAGS: tuple[str, ...] = (
    "has_uncertain",
    "has_illegible",
    "has_alternatives",
    "has_high_ascii",
)


def metrics(view: View) -> dict[str, float]:
    """The drift battery."""
    return {
        "lines": float(len(view.lines)),
        "tokens": float(view.n_words),
        "h2": conditional_entropy(encode_units(view), 2),
        "mean_word_length": mean_word_length(view),
        "ttr": view.n_types / view.n_words if view.n_words else 0.0,
        "hapax_rate": hapax_rate(view),
        "near_repeat_within_2": near_repeats(view)["within_2"],
    }


def _without(flag: str | None) -> object:
    def keep(row: StratumRow) -> bool:
        if flag is None:
            return not any(getattr(row, name) for name in FLAGS)
        return not getattr(row, flag)

    return keep


def alternatives_footprint() -> dict[str, float]:
    """How much text the first-option convention actually decides."""
    lines = load_lines()
    affected = [line for line in lines if line.has_alternatives]
    changed_tokens = 0
    changed_lines = 0
    for line in affected:
        first = line.text_clean.split(".")
        second = (transcription_text(line, None, Transcription.ZL, 1) or "").split(".")
        differences = sum(1 for a, b in zip(first, second, strict=False) if a != b)
        changed_tokens += differences
        changed_lines += bool(differences)
    return {
        "lines_with_alternatives": float(len(affected)),
        "lines_changed_by_second_option": float(changed_lines),
        "tokens_changed_by_second_option": float(changed_tokens),
    }


def run(ctx: Context) -> Topic:
    """Metric drift under flag filtering and under the second reading."""
    variants = {"all lines": ctx.base}
    for flag in FLAGS:
        variants[f"drop {flag}"] = voynich_view(f"voynich|-{flag}", keep=_without(flag))  # type: ignore[arg-type]
    variants["drop all flagged"] = voynich_view("voynich|-flagged", keep=_without(None))  # type: ignore[arg-type]
    variants["second [a:b] option"] = voynich_view("voynich|alt=1", alternative=1)

    rows = {name: metrics(view) for name, view in variants.items()}
    reference = rows["all lines"]
    drift = {
        name: {metric: relative_difference(row[metric], reference[metric]) for metric in METRICS}
        for name, row in rows.items()
        if name != "all lines"
    }
    footprint = alternatives_footprint()

    worst = max(
        (
            (abs(value or 0.0), name, metric)
            for name, row in drift.items()
            for metric, value in row.items()
        ),
        default=(0.0, "", ""),
    )

    sections = [
        "## Metrics under each filtering variant\n\n"
        + table(
            ["variant", "lines", "tokens", *METRICS],
            [
                [name, int(row["lines"]), int(row["tokens"]), *[row[metric] for metric in METRICS]]
                for name, row in rows.items()
            ],
        ),
        "## Relative drift versus all lines\n\n"
        + table(
            ["variant", *METRICS],
            [[name, *[row[metric] for metric in METRICS]] for name, row in drift.items()],
        )
        + f'\n\nLargest drift: {worst[2]} under "{worst[1]}" at {worst[0]:.1%}.',
        "## Footprint of the first-option convention\n\n"
        + table(
            ["lines with [a:b]", "lines changed by second option", "tokens changed"],
            [
                [
                    int(footprint["lines_with_alternatives"]),
                    int(footprint["lines_changed_by_second_option"]),
                    int(footprint["tokens_changed_by_second_option"]),
                ]
            ],
        ),
    ]

    data = {"variants": rows, "drift": drift, "alternatives": footprint}
    return Topic(
        topic="uncertainty",
        title="Phase 1 — Uncertainty-flag sensitivity",
        sections=sections,
        data=data,
    )
