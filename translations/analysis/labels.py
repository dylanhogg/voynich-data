"""§5.2.5 — the 115 label lines as a nomenclature.

Labels sit beside plants, stars and nymphs, so if any part of the manuscript is
a list of names, it is this one. Names behave differently from running text:
they are morphologically plainer, they repeat less, and within one page they
resemble each other more than random text does (a page of star labels is a
paradigm of one kind of thing).

Everything is compared against a size-matched random sample of paragraph tokens
drawn with a seeded RNG, because labels are ~2% of the corpus and every one of
these statistics moves with sample size.
"""

from __future__ import annotations

from collections import Counter

from translations.analysis.common import View
from translations.analysis.paradigms import frequency_inventory
from translations.analysis.syntax import edit_within
from translations.config import CONFIG
from translations.determinism import derived_rng
from translations.report import Topic, table

PAIR_SAMPLE = 2000


def matched_sample(prose: View, size: int, salt: str) -> list[list[str]]:
    """A random sample of ``size`` prose tokens."""
    rng = derived_rng(f"labels-{salt}")
    words = list(prose.words)
    if size >= len(words):
        return words
    return rng.sample(words, size)


def shape(words: list[list[str]], suffixes: tuple[tuple[str, ...], ...]) -> dict[str, float]:
    """Length, affix use and repetition profile of a bag of tokens."""
    if not words:
        return {}
    forms = ["".join(word) for word in words]
    counts = Counter(forms)
    lengths = [len(word) for word in words]
    mean = sum(lengths) / len(lengths)
    variance = sum((value - mean) ** 2 for value in lengths) / max(len(lengths) - 1, 1)
    gallows = set(CONFIG.gallows)
    with_suffix = sum(
        1
        for word in words
        if any(len(word) > len(affix) and tuple(word[-len(affix) :]) == affix for affix in suffixes)
    )
    return {
        "tokens": float(len(words)),
        "types": float(len(counts)),
        "ttr": len(counts) / len(words),
        "hapax_rate": sum(1 for count in counts.values() if count == 1) / len(counts),
        "mean_length": mean,
        "cv_length": (variance**0.5) / mean if mean else 0.0,
        "suffix_rate": with_suffix / len(words),
        "gallows_initial_rate": sum(1 for word in words if word and word[0] in gallows)
        / len(words),
    }


def internal_similarity(groups: list[list[list[str]]], salt: str) -> dict[str, float]:
    """Mean pairwise edit distance inside a group versus across groups.

    A list of like things (star names, plant parts) should be tighter than the
    same tokens shuffled between pages.
    """
    rng = derived_rng(f"labels-similarity-{salt}")
    within: list[int] = []
    for group in groups:
        for _ in range(min(PAIR_SAMPLE // max(len(groups), 1), 200)):
            if len(group) < 2:
                break
            left, right = rng.sample(group, 2)
            within.append(edit_within(left, right, max(len(left), len(right))))

    pooled = [word for group in groups for word in group]
    across: list[int] = []
    for _ in range(len(within)):
        if len(pooled) < 2:
            break
        left, right = rng.sample(pooled, 2)
        across.append(edit_within(left, right, max(len(left), len(right))))

    if not within or not across:
        return {}
    return {
        "pairs": float(len(within)),
        "within_group_distance": sum(within) / len(within),
        "across_group_distance": sum(across) / len(across),
        "tightening": (sum(across) / len(across)) - (sum(within) / len(within)),
    }


def overlap(labels: View, prose: View) -> dict[str, float]:
    """How much label vocabulary is shared with running text."""
    label_types = {"".join(word) for word in labels.words}
    prose_types = {"".join(word) for word in prose.words}
    shared = label_types & prose_types
    return {
        "label_types": float(len(label_types)),
        "shared_with_prose": len(shared) / len(label_types) if label_types else 0.0,
        "label_only_types": float(len(label_types - prose_types)),
        "repeated_label_types": (
            sum(
                1
                for _, count in Counter("".join(word) for word in labels.words).items()
                if count > 1
            )
            / len(label_types)
            if label_types
            else 0.0
        ),
    }


def run(labels: View, prose: View) -> Topic:
    """Labels against a size-matched prose sample."""
    suffixes = frequency_inventory(prose).suffixes
    sample = matched_sample(prose, labels.n_words, "matched")

    label_groups: list[list[list[str]]] = []
    if labels.rows:
        by_page: dict[str, list[list[str]]] = {}
        for line, row in zip(labels.lines, labels.rows, strict=True):
            by_page.setdefault(row.page_id, []).extend(line)
        label_groups = [words for words in by_page.values() if len(words) > 1]

    prose_groups: list[list[list[str]]] = []
    if prose.rows:
        by_page_prose: dict[str, list[list[str]]] = {}
        for line, row in zip(prose.lines, prose.rows, strict=True):
            by_page_prose.setdefault(row.page_id, []).extend(line)
        prose_groups = [words[: len(words)] for words in by_page_prose.values() if len(words) > 1]

    rows = {
        "labels": shape(labels.words, suffixes),
        "prose (matched sample)": shape(sample, suffixes),
        "prose (all)": shape(prose.words, suffixes),
    }
    similarity = {
        "labels": internal_similarity(label_groups, "labels"),
        "prose": internal_similarity(prose_groups, "prose"),
    }
    shared = overlap(labels, prose)

    keys = [
        "tokens",
        "types",
        "ttr",
        "hapax_rate",
        "mean_length",
        "cv_length",
        "suffix_rate",
        "gallows_initial_rate",
    ]
    sections = [
        "## Are labels morphologically simpler?\n\n"
        + table(
            ["view", *keys],
            [[name, *[row.get(key) for key in keys]] for name, row in rows.items()],
        )
        + "\n\nThe matched sample is the row to read against: labels are ~2% of the "
        + "corpus and every one of these numbers moves with sample size. Suffix rate "
        + "uses the frequency inventory induced on prose, so it asks whether labels "
        + "carry the endings running text uses.",
        "## Do labels on a page resemble each other?\n\n"
        + table(
            ["view", "pairs", "within-page distance", "across-page distance", "tightening"],
            [
                [
                    name,
                    row.get("pairs"),
                    row.get("within_group_distance"),
                    row.get("across_group_distance"),
                    row.get("tightening"),
                ]
                for name, row in similarity.items()
            ],
        )
        + "\n\nGlyph edit distance between random pairs of tokens on the same page "
        + "versus random pairs from anywhere. Positive tightening means a page's "
        + "labels are more like each other than like the label vocabulary at large — "
        + "which is what a list of one kind of thing looks like.",
        "## Label vocabulary against running text\n\n"
        + table(
            ["quantity", "value"],
            [
                ["label types", shared["label_types"]],
                ["share also seen in prose", shared["shared_with_prose"]],
                ["label-only types", shared["label_only_types"]],
                ["label types used more than once", shared["repeated_label_types"]],
            ],
        )
        + "\n\nA nomenclature drawn from the same language as the text shares "
        + "vocabulary with it; a separate naming system does not. Nothing here "
        + "identifies what is being named — that needs the illustration↔label "
        + "concordance the gap analysis leaves open.",
    ]
    return Topic(
        topic="labels",
        title="Phase 3 — Labels as a nomenclature",
        sections=sections,
        data={"shape": rows, "similarity": similarity, "overlap": shared},
    )
