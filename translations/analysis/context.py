"""The Phase 1 run context: every view the analysis modules share, built once.

Also home to the pseudo-Voynich tuning promised in §2.5. The grille and autocopy
generators are fitted to the manuscript's own h2, mean word length and hapax
rate, because an untuned pseudo-Voynich is a strawman and the Phase 5 audit
rests on this control being hard to beat.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from translations.analysis.common import (
    NULL_KINDS,
    View,
    baseline_view,
    encode_units,
    grille_view,
    is_prose,
    null_view,
    selfcite_view,
    voynich_view,
)
from translations.analysis.stats import conditional_entropy
from translations.config import CommaPolicy, Tokenizer, Transcription
from translations.corpora import available
from translations.determinism import derived_rng
from translations.strata import StratumRow
from vcat.logging import get_logger

logger = get_logger(__name__)

GRILLE_SIZES: tuple[int, ...] = (24, 48, 96)
GRILLE_COUNTS: tuple[int, ...] = (4, 8, 16)
SELFCITE_WINDOWS: tuple[int, ...] = (5, 10, 20, 40, 100)
SELFCITE_RATES: tuple[float, ...] = (0.05, 0.1, 0.2, 0.3, 0.5)
SECTION_VIEWS: tuple[str, ...] = ("herbal", "stars", "biological", "pharmaceutical", "text_only")


def hapax_rate(view: View) -> float:
    """Share of word types occurring exactly once."""
    counts: dict[str, int] = {}
    for form in view.forms:
        counts[form] = counts.get(form, 0) + 1
    return sum(1 for count in counts.values() if count == 1) / len(counts) if counts else 0.0


def mean_word_length(view: View) -> float:
    """Mean units per word."""
    return view.n_units / view.n_words if view.n_words else 0.0


def profile(view: View) -> tuple[float, float, float]:
    """The three quantities the pseudo-Voynich generators are tuned against."""
    return conditional_entropy(encode_units(view), 2), mean_word_length(view), hapax_rate(view)


def _distance(candidate: tuple[float, float, float], target: tuple[float, float, float]) -> float:
    return sum(((value - goal) / goal) ** 2 for value, goal in zip(candidate, target, strict=True))


def tune_pseudo(base: View) -> tuple[View, View, dict[str, Any]]:
    """Fit grille and selfcite parameters to the manuscript's own profile."""
    target = profile(base)

    grilles = [
        (
            grille_view(base, derived_rng(f"grille-{size}-{count}"), size, count),
            {"table_size": size, "n_grilles": count},
        )
        for size in GRILLE_SIZES
        for count in GRILLE_COUNTS
    ]
    selfcites = [
        (
            selfcite_view(base, derived_rng(f"selfcite-{window}-{rate}"), window, rate),
            {"window": window, "mutation_rate": rate},
        )
        for window in SELFCITE_WINDOWS
        for rate in SELFCITE_RATES
    ]
    best_grille, grille_params = min(grilles, key=lambda item: _distance(profile(item[0]), target))
    best_selfcite, selfcite_params = min(
        selfcites, key=lambda item: _distance(profile(item[0]), target)
    )

    parameters = {
        "target": dict(zip(("h2", "mean_word_length", "hapax_rate"), target, strict=True)),
        "grille": {
            "name": best_grille.name,
            "params": grille_params,
            "profile": profile(best_grille),
            "distance": _distance(profile(best_grille), target),
        },
        "selfcite": {
            "name": best_selfcite.name,
            "params": selfcite_params,
            "profile": profile(best_selfcite),
            "distance": _distance(profile(best_selfcite), target),
        },
    }
    logger.info("Tuned pseudo-Voynich", grille=best_grille.name, selfcite=best_selfcite.name)
    return best_grille, best_selfcite, parameters


@dataclass
class Context:
    """Everything the Phase 1 analyses share."""

    base: View
    grid: dict[str, View]
    strata: dict[str, View]
    baselines: dict[str, View]
    nulls: dict[str, View]
    pseudo: dict[str, View]
    pseudo_parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def comparisons(self) -> dict[str, View]:
        """Baselines, nulls and pseudo-Voynich together, in sorted key order."""
        merged = {**self.baselines, **self.nulls, **self.pseudo}
        return {key: merged[key] for key in sorted(merged)}


def _has_section(name: str) -> Callable[[StratumRow], bool]:
    def keep(row: StratumRow) -> bool:
        return row.section == name

    return keep


def build_context() -> Context:
    """Build every view Phase 1 needs. Deterministic: all RNGs are seed-derived."""
    base = voynich_view("voynich|base")

    grid = {
        f"{tokenizer}|{comma}|{transcription}": voynich_view(
            f"voynich|{tokenizer}|{comma}|{transcription}", tokenizer, comma, transcription
        )
        for tokenizer in (Tokenizer.T0_CHAR, Tokenizer.T1_GLYPH)
        for comma in (CommaPolicy.BREAK, CommaPolicy.JOIN)
        for transcription in (Transcription.ZL, Transcription.IT)
    }

    strata = {
        "currier_a": voynich_view(
            "voynich|currier_a", keep=lambda row: row.currier_language == "A"
        ),
        "currier_b": voynich_view(
            "voynich|currier_b", keep=lambda row: row.currier_language == "B"
        ),
        "consensus": voynich_view("voynich|consensus", keep=lambda row: row.in_consensus),
        "prose": voynich_view("voynich|prose", keep=is_prose),
        "labels": voynich_view("voynich|labels", keep=lambda row: row.line_type == "label"),
    } | {
        f"section_{name}": voynich_view(f"voynich|section={name}", keep=_has_section(name))
        for name in SECTION_VIEWS
    }

    baselines = {
        spec.corpus_id: baseline_view(
            spec.corpus_id, base.n_words, derived_rng(f"baseline-{spec.corpus_id}")
        )
        for spec in available()
    }

    nulls: dict[str, View] = {}
    for kind in NULL_KINDS:
        orders = (1, 2, 3) if kind == "markov_chars" else (1, 2) if kind == "markov_words" else (2,)
        for order in orders:
            view = null_view(kind, base, derived_rng(f"null-{kind}-{order}"), order=order)
            nulls[view.name.split("|", 1)[1]] = view

    grille, selfcite, parameters = tune_pseudo(base)
    logger.info("Context built", words=base.n_words, baselines=len(baselines), nulls=len(nulls))
    return Context(
        base=base,
        grid=grid,
        strata=strata,
        baselines=baselines,
        nulls=nulls,
        pseudo={"grille": grille, "selfcite": selfcite},
        pseudo_parameters=parameters,
    )
