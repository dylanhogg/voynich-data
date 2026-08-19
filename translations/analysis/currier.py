"""§3.7 — Currier A versus B.

A and B differ enough to behave like two systems. This module measures the
difference at matched sample size, asks whether B is reachable from A by a
simple systematic transformation, and separates the language factor from hand,
section and quire.
"""

from __future__ import annotations

import random
from collections import Counter

import numpy as np

from translations.analysis.common import View, encode_units
from translations.analysis.context import Context, hapax_rate, mean_word_length
from translations.analysis.stats import conditional_entropy
from translations.analysis.syntax import near_repeats
from translations.config import CONFIG
from translations.determinism import derived_rng
from translations.report import Topic, table

AFFIXES: tuple[str, ...] = ("qo", "ch", "sh", "o", "y", "d", "l", "r", "ol", "dy", "aiin", "ain")
FACTORS: tuple[str, ...] = ("currier_language", "hand", "section", "quire_id")


def match_size(view: View, n_words: int, rng: random.Random) -> View:
    """Subsample whole lines until the token budget is met (order preserved)."""
    if view.n_words <= n_words:
        return view
    order = list(range(len(view.lines)))
    rng.shuffle(order)
    chosen: list[int] = []
    total = 0
    for index in order:
        if total >= n_words:
            break
        chosen.append(index)
        total += len(view.lines[index])
    keep = sorted(chosen)
    return View(name=f"{view.name}|matched", lines=[view.lines[index] for index in keep])


def battery(view: View) -> dict[str, float]:
    """The per-language metric battery."""
    sequence = encode_units(view)
    counts = Counter(view.forms)
    return {
        "tokens": float(view.n_words),
        "types": float(len(counts)),
        "ttr": len(counts) / view.n_words if view.n_words else 0.0,
        "hapax_rate": hapax_rate(view),
        "mean_word_length": mean_word_length(view),
        "h1": conditional_entropy(sequence, 1),
        "h2": conditional_entropy(sequence, 2),
        "h3": conditional_entropy(sequence, 3),
        "near_repeat_within_2": near_repeats(view)["within_2"],
        "gallows_rate": sum(unit in set(CONFIG.gallows) for unit in view.units) / view.n_units,
    }


def transformation_search(source: View, target: View, top: int = 10) -> list[dict[str, object]]:
    """Can B be reached from A by one systematic change? Report the best tries.

    Candidates are single-glyph substitutions and affix additions/removals. The
    score is the share of transformed source *types* that exist in the target
    vocabulary, minus the share before transformation.
    """
    source_types = sorted(set(source.forms))
    target_types = set(target.forms)
    baseline = sum(form in target_types for form in source_types) / len(source_types)

    units = sorted({unit for word in source.words for unit in word})
    results: list[dict[str, object]] = []

    def score(transformed: list[str]) -> float:
        return sum(form in target_types for form in transformed) / len(transformed)

    for left in units:
        for right in units:
            if left == right:
                continue
            candidate = [form.replace(left, right) for form in source_types]
            results.append(
                {"kind": "substitute", "detail": f"{left}→{right}", "coverage": score(candidate)}
            )

    for affix in AFFIXES:
        results.append(
            {
                "kind": "add prefix",
                "detail": affix,
                "coverage": score([affix + form for form in source_types]),
            }
        )
        results.append(
            {
                "kind": "drop prefix",
                "detail": affix,
                "coverage": score(
                    [
                        form[len(affix) :] if form.startswith(affix) else form
                        for form in source_types
                    ]
                ),
            }
        )
        results.append(
            {
                "kind": "add suffix",
                "detail": affix,
                "coverage": score([form + affix for form in source_types]),
            }
        )
        results.append(
            {
                "kind": "drop suffix",
                "detail": affix,
                "coverage": score(
                    [form[: -len(affix)] if form.endswith(affix) else form for form in source_types]
                ),
            }
        )

    for row in results:
        row["gain"] = float(str(row["coverage"])) - baseline
    ranked = sorted(results, key=lambda row: float(str(row["gain"])), reverse=True)[:top]
    return [{"baseline_coverage": baseline, **row} for row in ranked]


def factor_model(view: View, response: str = "mean_word_length") -> dict[str, float]:
    """Partial R² of language, hand, section and quire on a per-line response."""
    if not view.rows:
        return {}
    rows = [row for row, line in zip(view.rows, view.lines, strict=True) if line]
    lines = [line for line in view.lines if line]
    if response == "gallows_rate":
        gallows = set(CONFIG.gallows)
        values = np.array(
            [
                sum(unit in gallows for word in line for unit in word)
                / max(sum(len(word) for word in line), 1)
                for line in lines
            ]
        )
    else:
        values = np.array([float(np.mean([len(word) for word in line])) for line in lines])

    def design(factors: tuple[str, ...]) -> np.ndarray:
        columns = [np.ones(len(rows))]
        for factor in factors:
            levels = sorted({str(getattr(row, factor)) for row in rows})[1:]
            columns += [
                np.array([1.0 if str(getattr(row, factor)) == level else 0.0 for row in rows])
                for level in levels
            ]
        return np.column_stack(columns)

    def r_squared(factors: tuple[str, ...]) -> float:
        matrix = design(factors)
        coefficients, *_ = np.linalg.lstsq(matrix, values, rcond=None)
        residual = values - matrix @ coefficients
        total = ((values - values.mean()) ** 2).sum()
        return float(1 - (residual**2).sum() / total) if total else 0.0

    full = r_squared(FACTORS)
    return {
        "response": response,  # type: ignore[dict-item]
        "r2_full": full,
        **{
            f"partial_r2_{factor}": full - r_squared(tuple(f for f in FACTORS if f != factor))
            for factor in FACTORS
        },
    }


def run(ctx: Context) -> Topic:
    """A/B comparison at matched size, transformation search and factor model."""
    language_a = ctx.strata["currier_a"]
    language_b = ctx.strata["currier_b"]
    budget = min(language_a.n_words, language_b.n_words)
    matched = {
        "currier_a": match_size(language_a, budget, derived_rng("match-a")),
        "currier_b": match_size(language_b, budget, derived_rng("match-b")),
    }

    batteries = {
        "currier_a (full)": battery(language_a),
        "currier_b (full)": battery(language_b),
        "currier_a (matched)": battery(matched["currier_a"]),
        "currier_b (matched)": battery(matched["currier_b"]),
    }

    types_a = set(matched["currier_a"].forms)
    types_b = set(matched["currier_b"].forms)
    vocabulary = {
        "matched_tokens": float(budget),
        "types_a": float(len(types_a)),
        "types_b": float(len(types_b)),
        "shared": float(len(types_a & types_b)),
        "a_only": float(len(types_a - types_b)),
        "b_only": float(len(types_b - types_a)),
        "jaccard": len(types_a & types_b) / len(types_a | types_b),
    }

    transformations = transformation_search(matched["currier_a"], matched["currier_b"])
    factors = {
        response: factor_model(ctx.base, response)
        for response in ("mean_word_length", "gallows_rate")
    }

    metric_names = [
        "tokens",
        "types",
        "ttr",
        "hapax_rate",
        "mean_word_length",
        "h1",
        "h2",
        "h3",
        "near_repeat_within_2",
        "gallows_rate",
    ]
    sections = [
        "## Metric battery, full and sample-size matched\n\n"
        + table(
            ["view", *metric_names],
            [[name, *[row[metric] for metric in metric_names]] for name, row in batteries.items()],
        ),
        "## Vocabulary at matched size\n\n"
        + table(
            ["matched tokens", "A types", "B types", "shared", "A only", "B only", "Jaccard"],
            [
                [
                    int(vocabulary["matched_tokens"]),
                    int(vocabulary["types_a"]),
                    int(vocabulary["types_b"]),
                    int(vocabulary["shared"]),
                    int(vocabulary["a_only"]),
                    int(vocabulary["b_only"]),
                    vocabulary["jaccard"],
                ]
            ],
        ),
        "## Is B reachable from A by one systematic transformation?\n\n"
        + f"Baseline: {transformations[0]['baseline_coverage']:.3f} of A types already occur in B.\n\n"
        + table(
            ["transformation", "detail", "coverage", "gain"],
            [[row["kind"], row["detail"], row["coverage"], row["gain"]] for row in transformations],
        )
        + "\n\nA single-step transformation that mattered would show a large positive gain.",
        "## Language versus hand, section and quire (partial R² on per-line responses)\n\n"
        + table(
            ["response", "R² full", *[f"partial R² {factor}" for factor in FACTORS]],
            [
                [
                    response,
                    row["r2_full"],
                    *[row[f"partial_r2_{factor}"] for factor in FACTORS],
                ]
                for response, row in factors.items()
            ],
        ),
    ]

    data = {
        "battery": batteries,
        "vocabulary": vocabulary,
        "transformations": transformations,
        "factors": factors,
    }
    return Topic(
        topic="currier", title="Phase 1 — Currier A versus B", sections=sections, data=data
    )
