"""§3.3 — distributional and lexical structure.

Zipf and Heaps behaviour, the low-frequency tail, the unusually symmetric word
length distribution, vocabulary drift through the codex, and vocabulary overlap
between strata. Every corpus-level number is computed at the same token count,
because TTR and hapax rate are strongly sample-size dependent.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from scipy import optimize, stats
from scipy.special import zeta

from translations.analysis.common import View
from translations.analysis.context import Context, hapax_rate
from translations.report import Topic, table

CURVE_POINTS: tuple[float, ...] = (0.1, 0.2, 0.4, 0.6, 0.8, 1.0)


def zipf_mle(frequencies: list[int], xmin: int = 1) -> dict[str, float]:
    """Discrete power-law MLE on word frequencies (Clauset-style), plus KS distance."""
    data = np.array([value for value in frequencies if value >= xmin], dtype=float)
    if data.size < 10:
        return {"alpha": float("nan"), "ks": float("nan"), "n": float(data.size)}

    log_sum = float(np.log(data).sum())

    def negative_log_likelihood(alpha: float) -> float:
        return float(data.size * np.log(zeta(alpha, xmin)) + alpha * log_sum)

    result = optimize.minimize_scalar(negative_log_likelihood, bounds=(1.01, 6.0), method="bounded")
    alpha = float(result.x)

    values = np.arange(xmin, int(data.max()) + 1, dtype=float)
    model_cdf = np.cumsum(values**-alpha / zeta(alpha, xmin))
    empirical = np.searchsorted(np.sort(data), values, side="right") / data.size
    return {
        "alpha": alpha,
        "ks": float(np.max(np.abs(model_cdf - empirical))),
        "n": float(data.size),
    }


def heaps_exponent(forms: list[str], points: int = 20) -> dict[str, float]:
    """Heaps' law V = K·N^β, fitted by regression over corpus prefixes."""
    sizes = np.unique(np.linspace(len(forms) // points, len(forms), points).astype(int))
    sizes = sizes[sizes > 10]
    types = np.array([len(set(forms[:size])) for size in sizes], dtype=float)
    slope, intercept, r_value, _, _ = stats.linregress(np.log(sizes), np.log(types))
    return {"beta": float(slope), "K": float(np.exp(intercept)), "r2": float(r_value**2)}


def frequency_profile(view: View) -> dict[str, float]:
    """Type/token ratio, hapax and dis-legomena shares, Zipf and Heaps fits."""
    counts = Counter(view.forms)
    frequencies = sorted(counts.values(), reverse=True)
    types = len(counts)
    return {
        "tokens": float(view.n_words),
        "types": float(types),
        "ttr": types / view.n_words if view.n_words else 0.0,
        "hapax_rate": hapax_rate(view),
        "dis_legomena_rate": (
            sum(1 for count in frequencies if count == 2) / types if types else 0.0
        ),
        **{f"zipf_{key}": value for key, value in zipf_mle(frequencies).items()},
        **{f"heaps_{key}": value for key, value in heaps_exponent(view.forms).items()},
    }


def word_length_profile(view: View) -> dict[str, object]:
    """Word length moments, and how well binomial / negative binomial fit.

    A coefficient of variation well below natural language is the "unusually
    symmetric word length" observation; the fits quantify it.
    """
    lengths = np.array([len(word) for word in view.words], dtype=float)
    if lengths.size == 0:
        return {}
    mean, variance = float(lengths.mean()), float(lengths.var(ddof=1))
    observed = np.bincount(lengths.astype(int))
    support = np.arange(observed.size)

    # Binomial by moments (variance < mean) or negative binomial (variance > mean).
    if variance < mean:
        trials: int = max(int(round(mean**2 / (mean - variance))), int(lengths.max()))
        probability = mean / trials
        expected = stats.binom.pmf(support, trials, probability) * lengths.size
        fitted = f"binomial(n={trials}, p={probability:.3f})"
    else:
        size = mean**2 / max(variance - mean, 1e-9)
        probability = size / (size + mean)
        expected = stats.nbinom.pmf(support, size, probability) * lengths.size
        fitted = f"nbinom(r={size:.2f}, p={probability:.3f})"

    keep = expected >= 5
    chi2 = float(((observed[keep] - expected[keep]) ** 2 / expected[keep]).sum())
    degrees = max(int(keep.sum()) - 3, 1)
    return {
        "mean": mean,
        "sd": float(np.sqrt(variance)),
        "cv": float(np.sqrt(variance) / mean) if mean else 0.0,
        "skew": float(stats.skew(lengths)),
        "kurtosis": float(stats.kurtosis(lengths)),
        "fit": fitted,
        "chi2_per_df": chi2 / degrees,
        "chi2_p": float(stats.chi2.sf(chi2, degrees)),
    }


def growth_curve(view: View) -> dict[str, list[float]]:
    """Types and hapax share at increasing sample sizes (for matched comparison)."""
    sizes = [int(view.n_words * fraction) for fraction in CURVE_POINTS]
    types, hapax = [], []
    for size in sizes:
        counts = Counter(view.forms[:size])
        types.append(float(len(counts)))
        hapax.append(
            sum(1 for count in counts.values() if count == 1) / len(counts) if counts else 0.0
        )
    return {"sizes": [float(size) for size in sizes], "types": types, "hapax": hapax}


def vocabulary_drift(view: View) -> dict[str, float]:
    """Does vocabulary drift through the codex? Spearman on new-type rate by page."""
    if not view.rows:
        return {}
    seen: set[str] = set()
    page_order: list[int] = []
    new_rate: list[float] = []
    index = 0
    current_page = view.rows[0].page_id
    page_forms: list[str] = []
    cursor = 0
    for line, row in zip(view.lines, view.rows, strict=True):
        forms = ["".join(word) for word in line]
        if row.page_id != current_page:
            if page_forms:
                fresh = sum(1 for form in page_forms if form not in seen)
                new_rate.append(fresh / len(page_forms))
                page_order.append(index)
                seen.update(page_forms)
                index += 1
            current_page, page_forms = row.page_id, []
        page_forms.extend(forms)
        cursor += len(forms)
    if len(new_rate) < 5:
        return {}
    correlation = stats.spearmanr(page_order, new_rate)
    return {
        "pages": float(len(new_rate)),
        "spearman_rho": float(correlation.statistic),
        "p_value": float(correlation.pvalue),
        "first_decile_new_rate": float(np.mean(new_rate[: max(len(new_rate) // 10, 1)])),
        "last_decile_new_rate": float(np.mean(new_rate[-max(len(new_rate) // 10, 1) :])),
    }


def jaccard_matrix(views: dict[str, View], sample: int) -> dict[str, dict[str, float]]:
    """Pairwise vocabulary overlap, each view cut to ``sample`` tokens first."""
    vocabularies = {name: set(view.forms[:sample]) for name, view in views.items()}
    return {
        left: {
            right: len(vocabularies[left] & vocabularies[right])
            / len(vocabularies[left] | vocabularies[right])
            for right in sorted(vocabularies)
        }
        for left in sorted(vocabularies)
    }


def run(ctx: Context) -> Topic:
    """Lexical structure of the manuscript against matched baselines."""
    views = {"voynich|base": ctx.base, **ctx.strata, **ctx.comparisons}
    profiles = {name: frequency_profile(view) for name, view in views.items()}
    lengths = {name: word_length_profile(view) for name, view in views.items()}
    curves = {
        name: growth_curve(view)
        for name, view in ({"voynich|base": ctx.base} | ctx.baselines | ctx.pseudo).items()
    }
    drift = vocabulary_drift(ctx.base)

    overlap_views = {
        name.replace("section_", ""): view
        for name, view in ctx.strata.items()
        if name.startswith("section_")
    } | {"currier_a": ctx.strata["currier_a"], "currier_b": ctx.strata["currier_b"]}
    sample = min(view.n_words for view in overlap_views.values())
    overlap = jaccard_matrix(overlap_views, sample)

    profile_table = table(
        ["view", "tokens", "types", "TTR", "hapax", "dis", "Zipf α", "Zipf KS", "Heaps β"],
        [
            [
                name,
                int(row["tokens"]),
                int(row["types"]),
                row["ttr"],
                row["hapax_rate"],
                row["dis_legomena_rate"],
                row["zipf_alpha"],
                row["zipf_ks"],
                row["heaps_beta"],
            ]
            for name, row in profiles.items()
        ],
    )
    length_table = table(
        ["view", "mean", "sd", "CV", "skew", "kurtosis", "best fit", "χ²/df", "p"],
        [
            [
                name,
                row["mean"],
                row["sd"],
                row["cv"],
                row["skew"],
                row["kurtosis"],
                row["fit"],
                row["chi2_per_df"],
                row["chi2_p"],
            ]
            for name, row in lengths.items()
            if row
        ],
    )
    overlap_names = sorted(overlap)
    overlap_table = table(
        ["view", *overlap_names],
        [[left, *[overlap[left][right] for right in overlap_names]] for left in overlap_names],
    )

    sections = [
        "## Frequency structure (Zipf, Heaps, hapax)\n\n" + profile_table,
        "## Word length distribution\n\n" + length_table,
        f"## Vocabulary overlap (Jaccard, each stratum cut to {sample:,} tokens)\n\n"
        + overlap_table,
        "## Vocabulary drift through the codex\n\n"
        + table(
            [
                "pages",
                "Spearman ρ (page order vs new-type rate)",
                "p",
                "first decile",
                "last decile",
            ],
            [
                [
                    int(drift.get("pages", 0)),
                    drift.get("spearman_rho"),
                    drift.get("p_value"),
                    drift.get("first_decile_new_rate"),
                    drift.get("last_decile_new_rate"),
                ]
            ],
        ),
    ]

    data = {
        "profiles": profiles,
        "word_length": lengths,
        "growth_curves": curves,
        "drift": drift,
        "vocabulary_overlap": overlap,
        "overlap_sample_tokens": sample,
    }
    return Topic(
        topic="lexis",
        title="Phase 1 — Lexical and distributional structure",
        sections=sections,
        data=data,
    )
