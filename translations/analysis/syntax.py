"""§3.5 — word order, long-range structure and topic organisation.

Four questions: does word order carry information, does mutual information decay
with distance the way it does in language, how much of the text is near-repeat
of what precedes it, and do page-level word distributions line up with the
illustrations.
"""

from __future__ import annotations

import math
from collections import Counter

import numpy as np

from translations.analysis.common import View
from translations.analysis.context import Context
from translations.determinism import derived_numpy_rng, derived_rng
from translations.report import Topic, fmt, table

DISTANCES: tuple[int, ...] = (1, 2, 3, 5, 8, 12, 20, 30, 50)
TOP_WORDS = 500
NEAR_REPEAT_WINDOW = 20
TOPICS = 7


def _ids(view: View, top: int = TOP_WORDS) -> np.ndarray:
    """Map word forms to ids, pooling everything outside the top ``top`` as OOV."""
    common = [form for form, _ in Counter(view.forms).most_common(top)]
    lookup = {form: index for index, form in enumerate(sorted(common))}
    oov = len(lookup)
    return np.fromiter(
        (lookup.get(form, oov) for form in view.forms), dtype=np.int64, count=view.n_words
    )


def mutual_information(left: np.ndarray, right: np.ndarray) -> float:
    """Plug-in mutual information of paired id arrays, in bits."""
    if left.size == 0:
        return 0.0
    size = int(max(left.max(), right.max())) + 1
    joint = np.bincount(left * size + right, minlength=size * size).reshape(size, size)
    total = joint.sum()
    probabilities = joint / total
    marginal_left = probabilities.sum(axis=1, keepdims=True)
    marginal_right = probabilities.sum(axis=0, keepdims=True)
    expected = marginal_left * marginal_right
    mask = probabilities > 0
    return float((probabilities[mask] * np.log2(probabilities[mask] / expected[mask])).sum())


def mi_curve(view: View, within_lines: bool) -> dict[int, dict[str, float]]:
    """MI at increasing word distance, with a shuffled control at each distance."""
    ids = _ids(view)
    line_of = np.concatenate(
        [np.full(len(line), index) for index, line in enumerate(view.lines) if line]
    )
    rng = derived_numpy_rng(f"mi-{view.name}")
    shuffled = rng.permutation(ids)

    curve: dict[int, dict[str, float]] = {}
    for distance in DISTANCES:
        left, right = ids[:-distance], ids[distance:]
        if within_lines:
            same = line_of[:-distance] == line_of[distance:]
            left, right = left[same], right[same]
        if left.size < 100:
            continue
        observed = mutual_information(left, right)
        control = mutual_information(shuffled[: left.size], rng.permutation(shuffled)[: left.size])
        curve[distance] = {
            "mi": observed,
            "shuffled_mi": control,
            "excess": observed - control,
            "pairs": float(left.size),
        }
    return curve


def bigram_bits(view: View, shuffled: bool = False) -> float:
    """Held-out bits per word under a word-bigram model (add-1 smoothed)."""
    forms = list(view.forms)
    if shuffled:
        rng = derived_rng(f"bigram-{view.name}")
        rng.shuffle(forms)
    cut = int(len(forms) * 0.8)
    train, test = forms[:cut], forms[cut:]
    if not test:
        return 0.0
    unigram = Counter(train)
    bigram = Counter(zip(train, train[1:], strict=False))
    vocabulary = len(unigram) + 1

    bits = 0.0
    for previous, current in zip(test, test[1:], strict=False):
        numerator = bigram[(previous, current)] + 1
        denominator = unigram[previous] + vocabulary
        bits -= math.log2(numerator / denominator)
    return bits / max(len(test) - 1, 1)


def edit_within(left: list[str], right: list[str], limit: int) -> int:
    """Levenshtein distance, capped at ``limit`` (returns ``limit + 1`` beyond)."""
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous = list(range(len(right) + 1))
    for i, unit in enumerate(left, start=1):
        current = [i]
        for j, other in enumerate(right, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (unit != other),
                )
            )
        if min(current) > limit:
            return limit + 1
        previous = current
    return previous[-1]


def near_repeats(view: View) -> dict[str, float]:
    """Adjacent near-repeat rates and the longest run of identical words."""
    words = view.words
    counts: Counter[int] = Counter()
    for left, right in zip(words, words[1:], strict=False):
        counts[edit_within(left, right, 2)] += 1
    pairs = max(sum(counts.values()), 1)

    longest, current = 1, 1
    for form, following in zip(view.forms, view.forms[1:], strict=False):
        current = current + 1 if form == following else 1
        longest = max(longest, current)

    return {
        "exact": counts[0] / pairs,
        "distance_1": counts[1] / pairs,
        "distance_2": counts[2] / pairs,
        "within_2": (counts[0] + counts[1] + counts[2]) / pairs,
        "longest_identical_run": float(longest),
    }


def self_citation(view: View, window: int = NEAR_REPEAT_WINDOW) -> dict[str, float]:
    """How close is each word to the most similar of the preceding ``window``?"""
    words = view.words
    buckets = Counter[int]()
    for index in range(1, len(words)):
        best = 3
        for previous in words[max(0, index - window) : index]:
            best = min(best, edit_within(words[index], previous, 2))
            if best == 0:
                break
        buckets[best] += 1
    total = max(sum(buckets.values()), 1)
    return {
        "identical_in_window": buckets[0] / total,
        "distance_1_in_window": buckets[1] / total,
        "distance_2_in_window": buckets[2] / total,
        "novel_in_window": buckets[3] / total,
    }


def nmf(
    matrix: np.ndarray, components: int, iterations: int = 200
) -> tuple[np.ndarray, np.ndarray]:
    """Non-negative matrix factorisation by multiplicative updates."""
    rng = derived_numpy_rng("nmf")
    weights = rng.random((matrix.shape[0], components)) + 0.1
    features = rng.random((components, matrix.shape[1])) + 0.1
    for _ in range(iterations):
        features *= (weights.T @ matrix) / (weights.T @ weights @ features + 1e-9)
        weights *= (matrix @ features.T) / (weights @ features @ features.T + 1e-9)
    return weights, features


def normalised_mutual_information(left: list[str], right: list[str]) -> float:
    """NMI between two labellings of the same items."""
    joint = Counter(zip(left, right, strict=True))
    total = len(left)
    left_counts, right_counts = Counter(left), Counter(right)

    def entropy(counts: Counter[str]) -> float:
        return -sum((count / total) * math.log2(count / total) for count in counts.values())

    mutual = sum(
        (count / total)
        * math.log2((count / total) / ((left_counts[a] / total) * (right_counts[b] / total)))
        for (a, b), count in joint.items()
    )
    denominator = math.sqrt(entropy(left_counts) * entropy(right_counts))
    return mutual / denominator if denominator else 0.0


def page_topics(view: View, components: int = TOPICS) -> dict[str, float]:
    """NMF over the page × word matrix; does the induced structure track sections?"""
    if not view.rows:
        return {}
    pages = sorted({row.page_id for row in view.rows})
    page_index = {page: index for index, page in enumerate(pages)}
    vocabulary = [form for form, _ in Counter(view.forms).most_common(1000)]
    word_index = {form: index for index, form in enumerate(sorted(vocabulary))}

    matrix = np.zeros((len(pages), len(word_index)))
    for line, row in zip(view.lines, view.rows, strict=True):
        for word in line:
            column = word_index.get("".join(word))
            if column is not None:
                matrix[page_index[row.page_id], column] += 1

    weights, _ = nmf(matrix, components)
    assignments = [f"topic{index}" for index in weights.argmax(axis=1)]
    sections = {row.page_id: row.section for row in view.rows}
    illustrations = {row.page_id: row.illustration_type for row in view.rows}
    labels_section = [sections[page] for page in pages]
    labels_illustration = [illustrations[page] for page in pages]

    purity = sum(
        Counter(
            label
            for label, topic in zip(labels_section, assignments, strict=True)
            if topic == cluster
        ).most_common(1)[0][1]
        for cluster in sorted(set(assignments))
    ) / len(pages)

    return {
        "components": float(components),
        "pages": float(len(pages)),
        "nmi_section": normalised_mutual_information(assignments, labels_section),
        "nmi_illustration": normalised_mutual_information(assignments, labels_illustration),
        "purity_section": purity,
    }


def run(ctx: Context) -> Topic:
    """Order, repetition and topic structure against baselines and surrogates."""
    focus = {
        "voynich|base": ctx.base,
        **{name: ctx.baselines[name] for name in ("vulgate_clementine", "austen_pride_prejudice")},
        **ctx.pseudo,
        **{name: ctx.nulls[name] for name in ("shuffle_word_order", "markov_words|n=1")},
    }

    repeats = {name: near_repeats(view) for name, view in focus.items()}
    citation = {name: self_citation(view) for name, view in focus.items()}
    order_bits = {
        name: {"real": bigram_bits(view), "word_shuffled": bigram_bits(view, shuffled=True)}
        for name, view in focus.items()
    }
    curves = {
        "voynich|within_lines": mi_curve(ctx.base, within_lines=True),
        "voynich|across_lines": mi_curve(ctx.base, within_lines=False),
        "vulgate_clementine": mi_curve(ctx.baselines["vulgate_clementine"], within_lines=False),
        "grille": mi_curve(ctx.pseudo["grille"], within_lines=False),
        "selfcite": mi_curve(ctx.pseudo["selfcite"], within_lines=False),
    }
    topics = page_topics(ctx.base)

    sections = [
        "## Adjacent near-repeats\n\n"
        + table(
            ["view", "exact", "distance 1", "distance 2", "within 2", "longest identical run"],
            [
                [
                    name,
                    row["exact"],
                    row["distance_1"],
                    row["distance_2"],
                    row["within_2"],
                    int(row["longest_identical_run"]),
                ]
                for name, row in repeats.items()
            ],
        ),
        f"## Self-citation within {NEAR_REPEAT_WINDOW} preceding words\n\n"
        + table(
            ["view", "identical", "distance 1", "distance 2", "novel"],
            [
                [
                    name,
                    row["identical_in_window"],
                    row["distance_1_in_window"],
                    row["distance_2_in_window"],
                    row["novel_in_window"],
                ]
                for name, row in citation.items()
            ],
        ),
        "## Does word order carry information? (bits/word under a word bigram model)\n\n"
        + table(
            ["view", "real", "word order shuffled", "gain from order"],
            [
                [name, row["real"], row["word_shuffled"], row["word_shuffled"] - row["real"]]
                for name, row in order_bits.items()
            ],
        ),
        "## Mutual information decay\n\n"
        + table(
            ["view", *[f"d={distance}" for distance in DISTANCES]],
            [
                [name, *[fmt(curve.get(distance, {}).get("excess")) for distance in DISTANCES]]
                for name, curve in curves.items()
            ],
        )
        + "\n\nValues are excess MI over a permuted control at the same sample size; "
        + "plug-in MI at this vocabulary size is badly biased and only the excess is readable.",
        "## Page topic structure (NMF)\n\n"
        + table(
            ["components", "pages", "NMI vs section", "NMI vs illustration", "purity vs section"],
            [
                [
                    int(topics.get("components", 0)),
                    int(topics.get("pages", 0)),
                    topics.get("nmi_section"),
                    topics.get("nmi_illustration"),
                    topics.get("purity_section"),
                ]
            ],
        ),
    ]

    data = {
        "near_repeats": repeats,
        "self_citation": citation,
        "order_bits": order_bits,
        "mi_curves": {
            name: {str(k): v for k, v in curve.items()} for name, curve in curves.items()
        },
        "page_topics": topics,
    }
    return Topic(
        topic="syntax",
        title="Phase 1 — Word order, repetition and topic structure",
        sections=sections,
        data=data,
    )
