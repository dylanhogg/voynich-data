"""§5.2.2 — do the induced slots behave like an inflectional paradigm?

Phase 1 showed that word-internal order is rigid and that a small affix
inventory pays for itself. That is compatible with inflection *and* with
positional generation, which is open question 4 out of Phase 1. Inflection makes
two further predictions that generation does not:

1. **Paradigm density** — the same roots recur with a *consistent* set of
   suffixes, so the root × suffix table is fuller than chance and roots cluster
   into a few paradigm classes.
2. **Contextual conditioning** — which suffix a root takes depends on the
   syntactic context, so the suffix carries mutual information with the
   neighbouring words' suffixes.

Both are measured against Latin (fusional, the H1/H3 plaintext candidate) and
Finnish (agglutinative). The plan named Turkish for the agglutinative
comparison; the cached corpora contain Finnish, which fills the same role at a
matched genre, and no Turkish text is pinned in ``sources.yaml``.

Two affix inventories are used, because they answer different questions. The
**MDL** inventory is the induced slot grammar the plan names — but at matched
sample size Latin induces no affix that pays for itself, which is the Phase 1
result restated and makes a cross-language paradigm table impossible. So the
comparison runs on a **frequency** inventory instead: the commonest word-final
unit sequences, the same number for every view. The MDL inventories are still
reported, since their sizes are the finding.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

from translations.analysis.common import View
from translations.analysis.segmentation import SlotModel, induce_slots
from translations.analysis.syntax import mutual_information, normalised_mutual_information
from translations.determinism import derived_numpy_rng
from translations.report import Topic, table

MIN_ROOT_COUNT = 5
# Phase 1 capped the MDL induction at 10 affixes for budget reasons and the
# greedy search was still paying for more. A paradigm test needs enough
# suffixes to have a paradigm at all, so the cap is raised here; the induction
# is otherwise the same and still stops as soon as an affix costs more than it
# saves.
CANDIDATES = 30
MAX_AFFIXES = 30
FREQUENCY_SUFFIXES = 12
MAX_SUFFIX_UNITS = 3


def frequency_inventory(view: View, suffixes: int = FREQUENCY_SUFFIXES) -> SlotModel:
    """The commonest word-final unit sequences, as a suffix-only slot model.

    Fixed size, so every view gets the same number of suffixes and the paradigm
    tables compare like with like.
    """
    counts: Counter[tuple[str, ...]] = Counter()
    for word in view.words:
        for size in range(1, min(MAX_SUFFIX_UNITS, len(word) - 1) + 1):
            counts[tuple(word[-size:])] += 1
    return SlotModel(
        prefixes=(), suffixes=tuple(affix for affix, _ in counts.most_common(suffixes))
    )


def mdl_inventory(view: View) -> SlotModel:
    """The induced slot grammar (Phase 1's method, with a higher affix cap)."""
    model, _ = induce_slots(
        [tuple(word) for word in view.words], candidates=CANDIDATES, max_affixes=MAX_AFFIXES
    )
    return model


def segmented(view: View, model: SlotModel) -> list[tuple[str, str, str]]:
    """Split every token of the view into prefix/root/suffix under ``model``."""
    words = [tuple(word) for word in view.words]
    rows: list[tuple[str, str, str]] = []
    for word in words:
        pieces = model.segment(word)
        prefix = "".join(pieces[0]) if len(pieces) > 1 and pieces[0] in model.prefixes else ""
        suffix = "".join(pieces[-1]) if len(pieces) > 1 and pieces[-1] in model.suffixes else ""
        start = 1 if prefix else 0
        end = len(pieces) - 1 if suffix else len(pieces)
        root = "".join("".join(piece) for piece in pieces[start:end])
        rows.append((prefix, root, suffix))
    return rows


def paradigm_density(rows: list[tuple[str, str, str]]) -> dict[str, float]:
    """How full is the root × suffix table for roots seen at least a few times?"""
    by_root: dict[str, Counter[str]] = defaultdict(Counter)
    for _, root, suffix in rows:
        by_root[root][suffix] += 1
    frequent = {
        root: counts for root, counts in by_root.items() if sum(counts.values()) >= MIN_ROOT_COUNT
    }
    if not frequent:
        return {}

    suffixes = sorted({suffix for counts in frequent.values() for suffix in counts})
    cells = len(frequent) * len(suffixes)
    filled = sum(len(counts) for counts in frequent.values())

    # Chance fill: draw each root's tokens independently from the pooled suffix
    # distribution and count how many distinct suffixes it lands on.
    pooled: Counter[str] = Counter()
    for counts in frequent.values():
        pooled.update(counts)
    total = sum(pooled.values())
    probabilities = np.array([pooled[suffix] / total for suffix in suffixes])
    expected = 0.0
    for counts in frequent.values():
        draws = sum(counts.values())
        expected += float((1.0 - (1.0 - probabilities) ** draws).sum())

    return {
        "roots": float(len(frequent)),
        "suffixes": float(len(suffixes)),
        "cells_filled": filled / cells if cells else 0.0,
        "expected_filled": expected / cells if cells else 0.0,
        "excess_over_chance": (filled - expected) / cells if cells else 0.0,
        "mean_suffixes_per_root": filled / len(frequent),
        "single_suffix_roots": sum(1 for counts in frequent.values() if len(counts) == 1)
        / len(frequent),
    }


def paradigm_classes(rows: list[tuple[str, str, str]], classes: int = 6) -> dict[str, float]:
    """Do roots fall into a few paradigm classes, or does each behave differently?

    Roots are described by their suffix distribution and clustered by k-means;
    the reported number is the share of the suffix-choice entropy that class
    membership explains.
    """
    by_root: dict[str, Counter[str]] = defaultdict(Counter)
    for _, root, suffix in rows:
        by_root[root][suffix] += 1
    frequent = {
        root: counts for root, counts in by_root.items() if sum(counts.values()) >= MIN_ROOT_COUNT
    }
    suffixes = sorted({suffix for counts in frequent.values() for suffix in counts})
    if len(frequent) < classes or len(suffixes) < 2:
        return {}

    matrix = np.array(
        [
            [counts[suffix] / sum(counts.values()) for suffix in suffixes]
            for counts in frequent.values()
        ]
    )
    rng = derived_numpy_rng("paradigm-classes")
    centres = matrix[rng.choice(matrix.shape[0], classes, replace=False)]
    assignment = np.zeros(matrix.shape[0], dtype=int)
    for _ in range(50):
        distances = ((matrix[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
        assignment = distances.argmin(axis=1)
        for index in range(classes):
            members = matrix[assignment == index]
            if members.size:
                centres[index] = members.mean(axis=0)

    def entropy(distribution: np.ndarray) -> float:
        mask = distribution > 0
        return float(-(distribution[mask] * np.log2(distribution[mask])).sum())

    weights = np.array([sum(counts.values()) for counts in frequent.values()], dtype=float)
    pooled = (matrix * weights[:, None]).sum(axis=0)
    pooled /= pooled.sum()
    within = 0.0
    for index in range(classes):
        mask = assignment == index
        if not mask.any():
            continue
        share = weights[mask].sum() / weights.sum()
        distribution = (matrix[mask] * weights[mask, None]).sum(axis=0)
        distribution /= distribution.sum()
        within += share * entropy(distribution)
    return {
        "classes": float(classes),
        "pooled_suffix_entropy": entropy(pooled),
        "within_class_entropy": within,
        "entropy_explained": (
            (entropy(pooled) - within) / entropy(pooled) if entropy(pooled) else 0.0
        ),
    }


def contextual_conditioning(rows: list[tuple[str, str, str]]) -> dict[str, float]:
    """Mutual information between a token's suffix and its neighbours' suffixes."""
    suffixes = [suffix for _, _, suffix in rows]
    roots = [root for _, root, _ in rows]
    lookup = {value: index for index, value in enumerate(sorted(set(suffixes)))}
    ids = np.array([lookup[suffix] for suffix in suffixes], dtype=np.int64)
    if ids.size < 100:
        return {}

    distribution = np.bincount(ids) / ids.size
    mask = distribution > 0
    suffix_entropy = float(-(distribution[mask] * np.log2(distribution[mask])).sum())
    return {
        "suffix_entropy": suffix_entropy,
        "mi_with_next_suffix": mutual_information(ids[:-1], ids[1:]),
        "mi_with_previous_suffix": mutual_information(ids[1:], ids[:-1]),
        "nmi_with_own_root": normalised_mutual_information(roots, suffixes),
        "conditioned_share": (
            mutual_information(ids[:-1], ids[1:]) / suffix_entropy if suffix_entropy else 0.0
        ),
    }


def run(views: dict[str, View]) -> Topic:
    """Paradigm density and contextual conditioning, Voynich against baselines."""
    results: dict[str, dict[str, object]] = {}
    for name, view in views.items():
        rows = segmented(view, frequency_inventory(view))
        induced = mdl_inventory(view)
        results[name] = {
            "frequency_inventory": frequency_inventory(view).as_dict(),
            "mdl_inventory": induced.as_dict(),
            "mdl_affixes": float(len(induced.prefixes) + len(induced.suffixes)),
            "density": paradigm_density(rows),
            "classes": paradigm_classes(rows),
            "conditioning": contextual_conditioning(rows),
        }

    def cell(name: str, group: str, key: str) -> float | None:
        block = results[name][group]
        if not isinstance(block, dict):
            return None
        value = block.get(key)
        return float(value) if isinstance(value, (int, float)) else None

    sections = [
        "## Paradigm density\n\n"
        + table(
            [
                "view",
                "roots (≥5 tokens)",
                "suffixes",
                "cells filled",
                "expected by chance",
                "excess",
                "single-suffix roots",
            ],
            [
                [
                    name,
                    cell(name, "density", "roots"),
                    cell(name, "density", "suffixes"),
                    cell(name, "density", "cells_filled"),
                    cell(name, "density", "expected_filled"),
                    cell(name, "density", "excess_over_chance"),
                    cell(name, "density", "single_suffix_roots"),
                ]
                for name in results
            ],
        )
        + "\n\nChance is the fill a root would reach by drawing its tokens "
        + "independently from the pooled suffix distribution. An inflectional "
        + "paradigm fills *fewer* cells than chance in a fusional language (roots "
        + "select a declension) and more in an agglutinative one.",
        "## Paradigm classes\n\n"
        + table(
            ["view", "pooled suffix entropy", "within-class entropy", "explained by class"],
            [
                [
                    name,
                    cell(name, "classes", "pooled_suffix_entropy"),
                    cell(name, "classes", "within_class_entropy"),
                    cell(name, "classes", "entropy_explained"),
                ]
                for name in results
            ],
        )
        + "\n\nSix classes, k-means on each root's suffix distribution. A language "
        + "with declensions concentrates suffix choice inside a class.",
        "## Is suffix choice conditioned by context?\n\n"
        + table(
            [
                "view",
                "suffix entropy",
                "MI with next suffix",
                "NMI with own root",
                "share explained",
            ],
            [
                [
                    name,
                    cell(name, "conditioning", "suffix_entropy"),
                    cell(name, "conditioning", "mi_with_next_suffix"),
                    cell(name, "conditioning", "nmi_with_own_root"),
                    cell(name, "conditioning", "conditioned_share"),
                ]
                for name in results
            ],
        )
        + "\n\nAgreement and government make a suffix predictable from its "
        + "neighbours. Positional generation does not: the suffix is decided "
        + "inside the word and owes nothing to the word before it.",
        "## Induced inventories, for reference\n\n"
        + table(
            ["view", "MDL affixes", "MDL suffixes"],
            [
                [
                    name,
                    results[name]["mdl_affixes"],
                    ", ".join(results[name]["mdl_inventory"]["suffixes"]) or "—",  # type: ignore[index]
                ]
                for name in results
            ],
        )
        + f"\n\nThe tables above use the frequency inventory ({FREQUENCY_SUFFIXES} "
        + "commonest word-final sequences per view) so the columns are comparable. "
        + "This table is the MDL induction the plan names, and its point is the "
        + "asymmetry: affixes pay for themselves on the manuscript and largely do "
        + "not on size-matched natural language.",
    ]
    return Topic(
        topic="paradigms",
        title="Phase 3 — Slot-to-function mapping",
        sections=sections,
        data={"views": results},
    )
