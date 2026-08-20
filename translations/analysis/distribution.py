"""§5.2.3–§5.2.4 — function-word discovery and the semantic-field probe.

Two questions about the *distribution* of word types rather than their shape.

**Function words.** Every natural language has a small closed class that is
frequent, context-promiscuous and spread evenly over the whole text. If
Voynichese has one, its members are the first things a translator can try to
gloss, and their absence is itself evidence about what the text is. Each type is
scored on three axes — frequency share, context entropy, dispersion across pages
— and the same scoring runs on the baselines, where the answer is known.

**Semantic fields.** If the herbal pages really are about herbs, herbal-only
vocabulary should exist beyond what page-topic frequency alone predicts. Section
specificity is measured as the KL divergence of a type's section distribution
from the corpus-wide one, and tested against a permutation null that reassigns
whole *pages* to sections, preserving page sizes and within-page vocabulary.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any

from translations.analysis.common import View
from translations.determinism import derived_rng
from translations.report import Topic, table

TOP_TYPES = 200
# Reference corpora have no pages. Blocks of this many pseudo-lines stand in for
# them, chosen so a baseline gets about as many blocks as the manuscript has
# pages (206), which is what makes the dispersion column comparable at all.
LINES_PER_BLOCK = 20
REPORT_TYPES = 20
MIN_TYPE_COUNT = 20
PERMUTATIONS = 200


def _entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def function_word_scores(view: View) -> list[dict[str, float | str]]:
    """Score the commonest types on frequency, context promiscuity and spread."""
    counts = Counter(view.forms)
    common = [form for form, _ in counts.most_common(TOP_TYPES)]
    ranked = set(common)

    left: dict[str, Counter[str]] = defaultdict(Counter)
    right: dict[str, Counter[str]] = defaultdict(Counter)
    pages: dict[str, Counter[str]] = defaultdict(Counter)
    units = {form: len(word) for form, word in zip(view.forms, view.words, strict=True)}
    rows = view.rows or []
    for index, line in enumerate(view.lines):
        page = rows[index].page_id if index < len(rows) else f"block{index // LINES_PER_BLOCK}"
        forms = ["".join(word) for word in line]
        for position, form in enumerate(forms):
            if form not in ranked:
                continue
            left[form][forms[position - 1] if position else "#"] += 1
            right[form][forms[position + 1] if position + 1 < len(forms) else "#"] += 1
            pages[form][page] += 1

    total = view.n_words
    page_count = max(len({page for counts in pages.values() for page in counts}), 1)
    scores: list[dict[str, float | str]] = []
    for form in common:
        occurrences = counts[form]
        dispersion = _entropy(pages[form]) / math.log2(page_count) if page_count > 1 else 0.0
        scores.append(
            {
                "form": form,
                "count": float(occurrences),
                "share": occurrences / total,
                "left_entropy": _entropy(left[form]),
                "right_entropy": _entropy(right[form]),
                "context_entropy": (_entropy(left[form]) + _entropy(right[form])) / 2,
                "dispersion": dispersion,
                "length": float(units[form]),
            }
        )
    return scores


def function_word_summary(scores: list[dict[str, float | str]]) -> dict[str, float]:
    """Corpus-level shape of the function-word axes."""
    if not scores:
        return {}
    top = scores[:REPORT_TYPES]
    return {
        "top20_token_share": sum(float(row["share"]) for row in top),
        "top20_mean_context_entropy": sum(float(row["context_entropy"]) for row in top) / len(top),
        "top20_mean_dispersion": sum(float(row["dispersion"]) for row in top) / len(top),
        "top20_mean_length": sum(float(row["length"]) for row in top) / len(top),
        "all_mean_context_entropy": sum(float(row["context_entropy"]) for row in scores)
        / len(scores),
        "all_mean_length": sum(float(row["length"]) for row in scores) / len(scores),
    }


def section_specificity(view: View) -> dict[str, Any]:
    """Do word types concentrate in sections beyond what page topics predict?"""
    if not view.rows:
        return {}
    page_section: dict[str, str] = {}
    page_types: dict[str, Counter[str]] = defaultdict(Counter)
    for line, row in zip(view.lines, view.rows, strict=True):
        page_section[row.page_id] = row.section
        page_types[row.page_id].update("".join(word) for word in line)

    totals = Counter[str]()
    for counts in page_types.values():
        totals.update(counts)
    frequent = sorted(form for form, count in totals.items() if count >= MIN_TYPE_COUNT)

    def divergence_mean(assignment: dict[str, str]) -> float:
        by_type: dict[str, Counter[str]] = defaultdict(Counter)
        section_totals = Counter[str]()
        for page, counts in page_types.items():
            section = assignment[page]
            section_totals[section] += sum(counts.values())
            for form in frequent:
                if counts[form]:
                    by_type[form][section] += counts[form]
        grand = sum(section_totals.values())
        background = {section: count / grand for section, count in section_totals.items()}
        total = 0.0
        for form in frequent:
            counts = by_type[form]
            observed = sum(counts.values())
            total += sum(
                (count / observed) * math.log2((count / observed) / background[section])
                for section, count in counts.items()
                if count
            )
        return total / len(frequent) if frequent else 0.0

    identity = dict(page_section)
    observed_mean = divergence_mean(identity)

    # Null: reassign whole pages to sections, keeping each page's vocabulary and
    # size. This removes any real section-vocabulary link but keeps the fact that
    # a page repeats its own words.
    pages = sorted(page_section)
    labels = [page_section[page] for page in pages]
    rng = derived_rng(f"section-null-{view.name}")
    null_means: list[float] = []
    for _ in range(PERMUTATIONS):
        shuffled = list(labels)
        rng.shuffle(shuffled)
        null_means.append(divergence_mean(dict(zip(pages, shuffled, strict=True))))

    beaten = sum(1 for value in null_means if value >= observed_mean)

    by_section: dict[str, Counter[str]] = defaultdict(Counter)
    for page, counts in page_types.items():
        by_section[page_section[page]].update(counts)
    top_by_section: dict[str, list[str]] = {}
    for section, counts in sorted(by_section.items()):
        share = [
            (counts[form] / totals[form], form)
            for form in frequent
            if counts[form] >= MIN_TYPE_COUNT
        ]
        top_by_section[section] = [
            form for _, form in sorted(share, reverse=True)[: REPORT_TYPES // 2]
        ]

    return {
        "types_tested": len(frequent),
        "observed_mean_divergence": observed_mean,
        "null_mean_divergence": sum(null_means) / len(null_means) if null_means else 0.0,
        "null_max_divergence": max(null_means) if null_means else 0.0,
        "p_value": (beaten + 1) / (len(null_means) + 1),
        "permutations": len(null_means),
        "top_by_section": top_by_section,
    }


def run(views: dict[str, View], voynich: str) -> Topic:
    """Function-word candidates and section specificity, against the baselines."""
    scores = {name: function_word_scores(view) for name, view in views.items()}
    summaries = {name: function_word_summary(rows) for name, rows in scores.items()}
    specificity = section_specificity(views[voynich])
    by_section: dict[str, list[str]] = dict(specificity.get("top_by_section") or {})

    sections = [
        "## Function-word axes, by corpus\n\n"
        + table(
            [
                "view",
                "top-20 token share",
                "mean context entropy",
                "mean dispersion",
                "mean length",
            ],
            [
                [
                    name,
                    summaries[name].get("top20_token_share"),
                    summaries[name].get("top20_mean_context_entropy"),
                    summaries[name].get("top20_mean_dispersion"),
                    summaries[name].get("top20_mean_length"),
                ]
                for name in scores
            ],
        )
        + "\n\nA function-word class shows up as a top of the frequency list that is "
        + "short, maximally promiscuous in its contexts and evenly dispersed. "
        + "Dispersion is the page distribution's entropy over log2(pages), so 1.0 "
        + "means present everywhere; reference corpora have no pages, so blocks of "
        + f"{LINES_PER_BLOCK} pseudo-lines stand in for them.",
        f"## Candidate function words in {voynich}\n\n"
        + table(
            ["form", "count", "share", "context entropy", "dispersion", "units"],
            [
                [
                    row["form"],
                    row["count"],
                    row["share"],
                    row["context_entropy"],
                    row["dispersion"],
                    row["length"],
                ]
                for row in scores[voynich][:REPORT_TYPES]
            ],
        )
        + "\n\nThese are candidates by distribution alone. Nothing here says what "
        + "they mean, and a generated text with a frequency skew produces the same "
        + "table.",
        "## Semantic-field probe\n\n"
        + table(
            ["quantity", "value"],
            [
                ["types tested (≥20 tokens)", specificity.get("types_tested")],
                ["mean section divergence (bits)", specificity.get("observed_mean_divergence")],
                ["null mean", specificity.get("null_mean_divergence")],
                ["null max", specificity.get("null_max_divergence")],
                ["permutations", specificity.get("permutations")],
                ["p", specificity.get("p_value")],
            ],
        )
        + "\n\nThe null reassigns whole pages to sections, so it keeps every page's "
        + "own repetitiveness and destroys only the link between a section and its "
        + "vocabulary. A low p means section-specific vocabulary exists beyond page "
        + "topic frequency — which is what would make herbal-only and pharma-only "
        + "subsets the most translatable parts of the manuscript.",
        "## Most section-specific types\n\n"
        + table(
            ["section", "types"],
            [[section, ", ".join(forms) or "—"] for section, forms in sorted(by_section.items())],
        ),
    ]
    return Topic(
        topic="distribution",
        title="Phase 3 — Function words and semantic fields",
        sections=sections,
        data={
            "function_word_summaries": summaries,
            "function_word_candidates": {
                name: rows[:REPORT_TYPES] for name, rows in scores.items()
            },
            "section_specificity": specificity,
        },
    )
