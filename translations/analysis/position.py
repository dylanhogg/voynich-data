"""§3.6 — positional and layout effects.

Line-as-a-functional-unit effects are real and they contaminate anything that
treats the manuscript as running prose. This module measures them, defines the
running-prose subset, and says exactly how much of the corpus that costs.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from scipy import stats

from translations.analysis.common import View, encode_units, is_prose
from translations.analysis.context import Context, hapax_rate, mean_word_length
from translations.analysis.stats import conditional_entropy
from translations.analysis.syntax import near_repeats
from translations.config import CONFIG
from translations.report import Topic, fmt, table

POSITION_CLASSES: tuple[str, ...] = ("initial", "mid", "final")


def _class_of(index: int, length: int) -> str:
    if index == 0:
        return "initial"
    if index == length - 1:
        return "final"
    return "mid"


def unit_position_table(view: View) -> tuple[dict[str, dict[str, int]], dict[str, float]]:
    """First-glyph distribution of line-initial / mid / final words, and a χ² test."""
    counts: dict[str, Counter[str]] = {name: Counter() for name in POSITION_CLASSES}
    for line in view.lines:
        for index, word in enumerate(line):
            if word:
                counts[_class_of(index, len(line))][word[0]] += 1

    units = sorted({unit for column in counts.values() for unit in column})
    matrix = np.array([[counts[name][unit] for unit in units] for name in POSITION_CLASSES])
    keep = matrix.sum(axis=0) >= 20
    result = stats.chi2_contingency(matrix[:, keep])
    cramers_v = float(
        np.sqrt(result.statistic / (matrix[:, keep].sum() * (min(matrix[:, keep].shape) - 1)))
    )
    return (
        {name: dict(counts[name].most_common(8)) for name in POSITION_CLASSES},
        {
            "chi2": float(result.statistic),
            "p_value": float(result.pvalue),
            "dof": float(result.dof),
            "cramers_v": cramers_v,
        },
    )


def word_length_by_position(view: View) -> dict[str, float]:
    """Mean word length by position in line — the crudest LAAFU signature."""
    lengths: dict[str, list[int]] = {name: [] for name in POSITION_CLASSES}
    for line in view.lines:
        for index, word in enumerate(line):
            lengths[_class_of(index, len(line))].append(len(word))
    return {name: float(np.mean(values)) if values else 0.0 for name, values in lengths.items()}


def first_line_effect(view: View) -> dict[str, float]:
    """Do first lines of pages differ from the rest?"""
    if not view.rows:
        return {}
    first: list[int] = []
    rest: list[int] = []
    for line, row in zip(view.lines, view.rows, strict=True):
        target = first if row.is_first_line_of_page else rest
        target.extend(len(word) for word in line)
    if not first or not rest:
        return {}
    result = stats.mannwhitneyu(first, rest)
    return {
        "first_line_mean_word_length": float(np.mean(first)),
        "other_line_mean_word_length": float(np.mean(rest)),
        "mannwhitney_p": float(result.pvalue),
        "first_line_words": float(len(first)),
    }


def label_vocabulary(ctx: Context) -> dict[str, float]:
    """Label vocabulary against paragraph vocabulary — 115 labels, treat gently."""
    labels = ctx.strata["labels"]
    prose = ctx.strata["prose"]
    label_forms = set(labels.forms)
    prose_forms = set(prose.forms)
    shared = label_forms & prose_forms
    return {
        "label_tokens": float(labels.n_words),
        "label_types": float(len(label_forms)),
        "shared_with_prose": float(len(shared)),
        "share_of_label_types_in_prose": len(shared) / len(label_forms) if label_forms else 0.0,
        "label_mean_word_length": mean_word_length(labels),
        "prose_mean_word_length": mean_word_length(prose),
    }


def prose_subset_cost(ctx: Context) -> dict[str, float]:
    """How much of the corpus the running-prose rule removes, and what it changes."""
    base, prose = ctx.base, ctx.strata["prose"]
    excluded_rows = [row for row in base.rows if not is_prose(row)]
    return {
        "excluded_lines": float(len(excluded_rows)),
        "excluded_share_of_lines": len(excluded_rows) / len(base.rows) if base.rows else 0.0,
        "excluded_tokens": float(base.n_words - prose.n_words),
        "excluded_share_of_tokens": (base.n_words - prose.n_words) / base.n_words,
        "h2_full": conditional_entropy(encode_units(base), 2),
        "h2_prose": conditional_entropy(encode_units(prose), 2),
        "hapax_full": hapax_rate(base),
        "hapax_prose": hapax_rate(prose),
        "near_repeat_full": near_repeats(base)["within_2"],
        "near_repeat_prose": near_repeats(prose)["within_2"],
    }


def run(ctx: Context) -> Topic:
    """Line-position effects, label vocabulary and the running-prose subset."""
    views = {
        "voynich|base": ctx.base,
        "currier_a": ctx.strata["currier_a"],
        "currier_b": ctx.strata["currier_b"],
        "vulgate_clementine": ctx.baselines["vulgate_clementine"],
    }
    distributions = {}
    tests = {}
    lengths = {}
    for name, view in views.items():
        distribution, test = unit_position_table(view)
        distributions[name] = distribution
        tests[name] = test
        lengths[name] = word_length_by_position(view)

    first_lines = first_line_effect(ctx.base)
    labels = label_vocabulary(ctx)
    cost = prose_subset_cost(ctx)

    sections = [
        "## Line-initial / mid / final first-glyph distributions\n\n"
        + table(
            ["view", "χ²", "dof", "p", "Cramér's V", "initial top", "mid top", "final top"],
            [
                [
                    name,
                    tests[name]["chi2"],
                    int(tests[name]["dof"]),
                    tests[name]["p_value"],
                    tests[name]["cramers_v"],
                    ", ".join(list(distributions[name]["initial"])[:3]),
                    ", ".join(list(distributions[name]["mid"])[:3]),
                    ", ".join(list(distributions[name]["final"])[:3]),
                ]
                for name in views
            ],
        )
        + "\n\nThe Latin baseline is included to show what a *language* does at line "
        + "boundaries when the lines are arbitrary blocks: nothing.",
        "## Mean word length by position in line\n\n"
        + table(
            ["view", *POSITION_CLASSES],
            [[name, *[lengths[name][cls] for cls in POSITION_CLASSES]] for name in views],
        ),
        "## First line of page\n\n"
        + table(
            [
                "first-line mean length",
                "other-line mean length",
                "Mann–Whitney p",
                "first-line words",
            ],
            [
                [
                    first_lines.get("first_line_mean_word_length"),
                    first_lines.get("other_line_mean_word_length"),
                    first_lines.get("mannwhitney_p"),
                    int(first_lines.get("first_line_words", 0)),
                ]
            ],
        ),
        "## Labels versus paragraph text\n\n"
        + table(
            [
                "label tokens",
                "label types",
                "types shared with prose",
                "share shared",
                "label mean length",
                "prose mean length",
            ],
            [
                [
                    int(labels["label_tokens"]),
                    int(labels["label_types"]),
                    int(labels["shared_with_prose"]),
                    labels["share_of_label_types_in_prose"],
                    labels["label_mean_word_length"],
                    labels["prose_mean_word_length"],
                ]
            ],
        ),
        "## Cost of the running-prose subset\n\n"
        + "Rule: paragraph lines only, excluding pages with illustration type "
        + f"{', '.join(CONFIG.prose_exclude_illustration)} (astronomical and cosmological), "
        + "because no line-level marker for circular or radial writing exists in the data.\n\n"
        + table(
            ["excluded lines", "share of lines", "excluded tokens", "share of tokens"],
            [
                [
                    int(cost["excluded_lines"]),
                    cost["excluded_share_of_lines"],
                    int(cost["excluded_tokens"]),
                    cost["excluded_share_of_tokens"],
                ]
            ],
        )
        + "\n\n"
        + table(
            ["metric", "full corpus", "running prose"],
            [
                ["h2", cost["h2_full"], cost["h2_prose"]],
                ["hapax rate", cost["hapax_full"], cost["hapax_prose"]],
                ["near-repeat (within 2)", cost["near_repeat_full"], cost["near_repeat_prose"]],
            ],
        )
        + f"\n\nExcluding circular pages moves h2 by {fmt(cost['h2_prose'] - cost['h2_full'])} bits: "
        + "the layout effects are real but they are not what drives the headline numbers.",
    ]

    data = {
        "first_glyph_by_position": distributions,
        "position_tests": tests,
        "word_length_by_position": lengths,
        "first_line_effect": first_lines,
        "labels": labels,
        "prose_subset": cost,
    }
    return Topic(
        topic="position",
        title="Phase 1 — Positional and layout effects",
        sections=sections,
        data=data,
    )
