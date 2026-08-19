"""§3.4 — word-internal structure and slot grammar.

The strongest known regularity in Voynichese, quantified four ways: positional
glyph distributions, Harris entropy boundaries, an MDL slot inventory, and an
induced finite-state acceptor. The closing question is deliberately left open —
three models of word structure are scored, and the numbers are reported without
a verdict.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass

from translations.analysis import fsa
from translations.analysis.common import View
from translations.analysis.context import Context
from translations.analysis.segmentation import (
    SlotModel,
    harris_segment,
    induce_slots,
    successor_entropies,
)
from translations.analysis.stats import cohens_h
from translations.config import CONFIG
from translations.determinism import derived_rng
from translations.report import Topic, fmt, table
from translations.strata import StratumRow

MAX_POSITION = 6
END = "</w>"


def position_profile(view: View, max_position: int = MAX_POSITION) -> dict[str, dict[str, object]]:
    """Unit distribution at each word position (last bucket is "position ≥ n")."""
    buckets: dict[int, Counter[str]] = defaultdict(Counter)
    for word in view.words:
        for index, unit in enumerate(word, start=1):
            buckets[min(index, max_position)][unit] += 1

    profile: dict[str, dict[str, object]] = {}
    for position in sorted(buckets):
        counts = buckets[position]
        total = sum(counts.values())
        probabilities = [count / total for count in counts.values()]
        top = counts.most_common(3)
        label = f"{position}" if position < max_position else f"{max_position}+"
        profile[label] = {
            "n": float(total),
            "entropy": -sum(p * math.log2(p) for p in probabilities),
            "distinct": float(len(counts)),
            **{f"top{rank}_share": count / total for rank, (_, count) in enumerate(top, start=1)},
            **{f"top{rank}_unit": unit for rank, (unit, _) in enumerate(top, start=1)},
        }
    return profile


@dataclass(frozen=True)
class HarrisProfile:
    """Harris segmentation of a vocabulary."""

    mean_morphs_per_word: float
    morph_inventory: int
    top_morphs: list[tuple[str, int]]

    def as_dict(self) -> dict[str, object]:
        """JSON-friendly form."""
        return {
            "mean_morphs_per_word": self.mean_morphs_per_word,
            "morph_inventory": float(self.morph_inventory),
            "top_morphs": self.top_morphs,
        }


def harris_profile(view: View) -> HarrisProfile:
    """Harris successor/predecessor segmentation of the vocabulary."""
    words = [tuple(word) for word in view.words]
    forward = successor_entropies(words)
    backward = successor_entropies(words, reverse=True)
    segments = [harris_segment(word, forward, backward) for word in words]
    morphs = Counter("".join(piece) for word in segments for piece in word)
    return HarrisProfile(
        mean_morphs_per_word=sum(len(word) for word in segments) / len(segments),
        morph_inventory=len(morphs),
        top_morphs=morphs.most_common(15),
    )


def _train_test(
    view: View, rng: random.Random, holdout: float = 0.2
) -> tuple[list[list[str]], list[list[str]]]:
    words = list(view.words)
    rng.shuffle(words)
    cut = int(len(words) * (1 - holdout))
    return words[:cut], words[cut:]


def morph_model_bits(train: list[list[str]], test: list[list[str]], model: SlotModel) -> float:
    """Bits per word under the induced morphology (segment unigram + count)."""
    segments: Counter[str] = Counter()
    counts: Counter[int] = Counter()
    for word in train:
        pieces = model.segment(tuple(word))
        counts[len(pieces)] += 1
        segments.update("".join(piece) for piece in pieces)
    total_segments = sum(segments.values()) + len(segments) + 1
    total_counts = sum(counts.values()) + len(counts) + 1

    bits = 0.0
    for word in test:
        pieces = model.segment(tuple(word))
        bits -= math.log2((counts[len(pieces)] + 1) / total_counts)
        for piece in pieces:
            bits -= math.log2((segments["".join(piece)] + 1) / total_segments)
    return bits / len(test)


def slot_model_bits(train: list[list[str]], test: list[list[str]]) -> float:
    """Bits per word under a positional code: P(unit | position) plus length."""
    positions: dict[int, Counter[str]] = defaultdict(Counter)
    lengths: Counter[int] = Counter()
    alphabet: set[str] = set()
    for word in train:
        lengths[len(word)] += 1
        for index, unit in enumerate(word, start=1):
            positions[min(index, MAX_POSITION)][unit] += 1
            alphabet.add(unit)
    size = len(alphabet) + 1
    total_lengths = sum(lengths.values()) + len(lengths) + 1

    bits = 0.0
    for word in test:
        bits -= math.log2((lengths[len(word)] + 1) / total_lengths)
        for index, unit in enumerate(word, start=1):
            counts = positions[min(index, MAX_POSITION)]
            bits -= math.log2((counts[unit] + 1) / (sum(counts.values()) + size))
    return bits / len(test)


def chain_model_bits(train: list[list[str]], test: list[list[str]], order: int = 2) -> float:
    """Bits per word under an order-n Markov chain over units within the word."""
    contexts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    alphabet: set[str] = {END}
    for word in train:
        padded = [*word, END]
        for index, unit in enumerate(padded):
            context = tuple(padded[max(0, index - order) : index])
            contexts[context][unit] += 1
            alphabet.add(unit)
    size = len(alphabet)

    bits = 0.0
    for word in test:
        padded = [*word, END]
        for index, unit in enumerate(padded):
            context = tuple(padded[max(0, index - order) : index])
            counts = contexts.get(context, Counter())
            bits -= math.log2((counts[unit] + 1) / (sum(counts.values()) + size))
    return bits / len(test)


def model_comparison(view: View) -> dict[str, float]:
    """Held-out bits per word under morphology, slot-code and chain models.

    The morphology model is induced on this view's own training split — using
    the manuscript's affixes to score Latin would compare nothing.
    """
    train, test = _train_test(view, derived_rng(f"morphmodels-{view.name}"))
    if not test:
        return {}
    model, stats = induce_slots([tuple(word) for word in train])
    return {
        "morphology_bits": morph_model_bits(train, test, model),
        "slot_code_bits": slot_model_bits(train, test),
        "chain_bits": chain_model_bits(train, test),
        "mdl_bits_saved_per_word": stats["bits_saved"] / len(train),
        "mdl_affixes": stats["affixes"],
    }


def gallows_profile(view: View) -> dict[str, float]:
    """Where gallows glyphs sit: word-initial, line-initial word, first line."""
    gallows = set(CONFIG.gallows)
    stats = {
        "word_initial": [0, 0],
        "word_other": [0, 0],
        "line_first_word": [0, 0],
        "line_other_word": [0, 0],
        "page_first_line": [0, 0],
        "page_other_line": [0, 0],
    }
    rows: list[StratumRow | None] = list(view.rows) or [None] * len(view.lines)
    for line, row in zip(view.lines, rows, strict=True):
        first_line = bool(row and row.is_first_line_of_page)
        for word_index, word in enumerate(line):
            for unit_index, unit in enumerate(word):
                hit = unit in gallows
                key_word = "word_initial" if unit_index == 0 else "word_other"
                key_line = "line_first_word" if word_index == 0 else "line_other_word"
                key_page = "page_first_line" if first_line else "page_other_line"
                for key in (key_word, key_line, key_page):
                    stats[key][0] += int(hit)
                    stats[key][1] += 1
    rates = {key: (hits / total if total else 0.0) for key, (hits, total) in stats.items()}
    rates["h_word_initial_vs_other"] = cohens_h(rates["word_initial"], rates["word_other"])
    rates["h_line_first_vs_other"] = cohens_h(rates["line_first_word"], rates["line_other_word"])
    rates["h_page_first_vs_other"] = cohens_h(rates["page_first_line"], rates["page_other_line"])
    return rates


def _best_model(row: dict[str, float]) -> str | None:
    """Name of the model with the fewest held-out bits per word."""
    scores = {key: value for key, value in row.items() if key.endswith("_bits")}
    return min(scores, key=lambda key: scores[key]).replace("_bits", "") if scores else None


def run(ctx: Context) -> Topic:
    """Positional structure, segmentation, slot grammar and gallows behaviour."""
    focus = {
        "voynich|base": ctx.base,
        "currier_a": ctx.strata["currier_a"],
        "currier_b": ctx.strata["currier_b"],
        "vulgate_clementine": ctx.baselines["vulgate_clementine"],
        "austen_pride_prejudice": ctx.baselines["austen_pride_prejudice"],
        "finnish_bible": ctx.baselines["finnish_bible"],
        "grille": ctx.pseudo["grille"],
        "selfcite": ctx.pseudo["selfcite"],
    }

    positions = {name: position_profile(view) for name, view in focus.items()}
    harris = harris_profile(ctx.base)
    slot_model, mdl_stats = induce_slots([tuple(word) for word in ctx.base.words])
    models = {name: model_comparison(view) for name, view in focus.items()}
    gallows = {
        name: gallows_profile(view)
        for name, view in {
            "voynich|base": ctx.base,
            **{key: ctx.strata[key] for key in ("currier_a", "currier_b", "prose", "labels")},
        }.items()
    }
    automata = {
        f"{name}|k={k}": fsa.score(view.words, derived_rng(f"fsa-{name}-{k}"), k=k).as_dict()
        for name, view in focus.items()
        for k in (1, 2, 3)
    }

    position_rows = []
    for name, profile in positions.items():
        for label, row in profile.items():
            position_rows.append(
                [
                    name,
                    label,
                    int(float(row["n"])),  # type: ignore[arg-type]
                    row["entropy"],
                    row["distinct"],
                    f"{row.get('top1_unit')} {fmt(row.get('top1_share'))}",
                    f"{row.get('top2_unit')} {fmt(row.get('top2_share'))}",
                ]
            )

    sections = [
        "## Per-position glyph distributions\n\n"
        + table(["view", "position", "n", "entropy", "distinct", "top 1", "top 2"], position_rows),
        "## Harris successor/predecessor segmentation\n\n"
        + f"Mean morphs per word: {fmt(harris.mean_morphs_per_word)}; "
        + f"morph inventory {harris.morph_inventory:,}.\n\n"
        + table(["morph", "count"], harris.top_morphs),
        "## MDL slot inventory (defines `T2-slot`)\n\n"
        + f"Prefixes: `{'`, `'.join(slot_model.as_dict()['prefixes']) or '—'}`\n\n"
        + f"Suffixes: `{'`, `'.join(slot_model.as_dict()['suffixes']) or '—'}`\n\n"
        + table(
            ["initial DL (bits)", "final DL (bits)", "saved", "affixes"],
            [
                [
                    mdl_stats["initial_description_length"],
                    mdl_stats["final_description_length"],
                    mdl_stats["bits_saved"],
                    int(mdl_stats["affixes"]),
                ]
            ],
        ),
        "## Three models of word structure (held-out bits per word)\n\n"
        + table(
            [
                "view",
                "morphology",
                "positional slot code",
                "order-2 chain",
                "best",
                "MDL bits saved / word",
                "affixes",
            ],
            [
                [
                    name,
                    row.get("morphology_bits"),
                    row.get("slot_code_bits"),
                    row.get("chain_bits"),
                    _best_model(row),
                    row.get("mdl_bits_saved_per_word"),
                    int(row.get("mdl_affixes", 0)),
                ]
                for name, row in models.items()
            ],
        )
        + "\n\nReported as likelihoods, not as a verdict: the three models are not "
        + "nested and their priors differ.",
        "## Induced finite-state acceptors\n\n"
        + table(
            [
                "view|k",
                "states",
                "transitions",
                "held-out type acceptance",
                "token acceptance",
                "over-generation",
            ],
            [
                [
                    name,
                    int(row["states"]),
                    int(row["transitions"]),
                    row["heldout_type_acceptance"],
                    row["token_acceptance"],
                    row["overgeneration"],
                ]
                for name, row in automata.items()
            ],
        ),
        "## Gallows glyphs\n\n"
        + table(
            [
                "view",
                "word-initial",
                "word-other",
                "line-first word",
                "line-other",
                "page-first line",
                "page-other",
                "h (word)",
            ],
            [
                [
                    name,
                    row["word_initial"],
                    row["word_other"],
                    row["line_first_word"],
                    row["line_other_word"],
                    row["page_first_line"],
                    row["page_other_line"],
                    row["h_word_initial_vs_other"],
                ]
                for name, row in gallows.items()
            ],
        ),
    ]

    data = {
        "positions": positions,
        "harris": harris.as_dict(),
        "slot_model": slot_model.as_dict(),
        "mdl": mdl_stats,
        "model_comparison": models,
        "fsa": automata,
        "gallows": gallows,
    }
    return Topic(
        topic="morphology",
        title="Phase 1 — Word-internal structure and slot grammar",
        sections=sections,
        data=data,
    )
