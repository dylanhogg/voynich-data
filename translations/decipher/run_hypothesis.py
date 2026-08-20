"""The hypothesis runner (plan §4.3.5).

Takes a pre-registered hypothesis record, executes its declared grid, and
returns one row per candidate — **including losers**, including the runs on the
null corpora, each row carrying what it cost and whether it was truncated.

Design choices worth stating:

- searches run on the training pages only; the held-out pages are scored once,
  at the end, with the key the search already committed to;
- the null runs use the identical search settings, but only for the best variant
  of a hypothesis: running every language against every null would multiply the
  budget by four for no extra discrimination.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.optimize import linear_sum_assignment

from translations.analysis.common import View
from translations.config import REPO_ROOT
from translations.decipher import generative
from translations.decipher.budget import Deadline
from translations.decipher.channel import (
    Merge,
    build_ciphertext,
    fixed_width_units,
    key_as_dict,
    merge_units,
)
from translations.decipher.lm import ALPHABET, CharLM, corpus_lm
from translations.decipher.priors import merge_pool, morph_merges
from translations.decipher.score import (
    Description,
    gain_per_token,
    markov_description,
    ngram_index,
    substitution_description,
)
from translations.decipher.search import merge_search, search_key
from vcat.logging import get_logger

logger = get_logger(__name__)

HYPOTHESIS_DIR = REPO_ROOT / "translations" / "hypotheses"
GENERATIVE_KINDS = {
    "grille": generative.grille_description,
    "selfcite": generative.selfcite_description,
    "morphology": generative.morphology_description,
    "slot_grammar": generative.slot_grammar_description,
}


@dataclass(frozen=True)
class Hypothesis:
    """A pre-registered hypothesis record."""

    hypothesis_id: str
    title: str
    family: str
    funded: bool
    budget_share: float
    search: dict[str, Any]
    nulls: tuple[str, ...]
    record: dict[str, Any]

    @property
    def kind(self) -> str:
        """Which search the runner dispatches to."""
        return str(self.search.get("kind", "none"))


def load_hypotheses(directory: Path | None = None) -> list[Hypothesis]:
    """Load every registered hypothesis, ordered by id."""
    folder = directory or HYPOTHESIS_DIR
    hypotheses = []
    for path in sorted(folder.glob("*.yaml")):
        record = yaml.safe_load(path.read_text())
        hypotheses.append(
            Hypothesis(
                hypothesis_id=record["id"],
                title=record["title"],
                family=record["family"],
                funded=bool(record["funded"]),
                budget_share=float(record["budget_share"]),
                search=record.get("search", {}),
                nulls=tuple(record.get("nulls", ())),
                record=record,
            )
        )
    return hypotheses


def _row(
    hypothesis: Hypothesis,
    variant: str,
    corpus: str,
    split: str,
    description: Description,
    baseline: Description,
    seconds: float,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "hypothesis": hypothesis.hypothesis_id,
        "variant": variant,
        "corpus": corpus,
        "split": split,
        "total_bits": description.total_bits,
        "model_bits": description.model_bits,
        "bits_per_token": description.bits_per_token,
        "baseline_bits_per_token": baseline.bits_per_token,
        "gain_per_token": gain_per_token(description, baseline),
        "n_tokens": description.n_tokens,
        "detail": description.detail,
        "budget_spent_s": seconds,
        "converged": True,
        "truncated": False,
        **extra,
    }


def _language_models(hypothesis: Hypothesis) -> list[CharLM]:
    transform = (
        "abjad"
        if hypothesis.search.get("strip_vowels")
        else "abbrev" if hypothesis.search.get("abbreviate") else "plain"
    )
    order = int(hypothesis.search.get("lm_order", 3))
    return [
        corpus_lm(language, order, transform) for language in hypothesis.search.get("languages", [])
    ]


def _substitution_variant(
    hypothesis: Hypothesis,
    view: View,
    lm: CharLM,
    rng: random.Random,
    width: int | None = None,
    merges: tuple[Merge, ...] = (),
) -> tuple[Description, np.ndarray, dict[str, Any], float]:
    """Run one substitution search and describe the result."""
    started = time.monotonic()
    if width:
        ciphertext = fixed_width_units(view, width, f"{view.name}|w{width}")
    elif merges:
        ciphertext = merge_units(view, merges, f"{view.name}|merged")
    else:
        ciphertext = build_ciphertext(view)
    index = ngram_index(ciphertext, lm.order)
    result = search_key(
        ciphertext,
        lm,
        rng,
        int(hypothesis.search.get("iterations", 40000)),
        int(hypothesis.search.get("restarts", 4)),
        index=index,
    )
    description = substitution_description(
        result.key, index, lm, ciphertext, hypothesis.hypothesis_id, merges=merges
    )
    meta = {
        "converged": result.converged,
        "iterations": result.iterations,
        "restarts": result.restarts,
        "evaluations": result.evaluations,
        "key": str(key_as_dict(result.key, ciphertext)),
        "merges": str(["".join(merge) for merge in merges]),
    }
    return description, result.key, meta, time.monotonic() - started


def _assignment_variant(
    hypothesis: Hypothesis, view: View, lm: CharLM
) -> tuple[Description, np.ndarray, dict[str, Any], float]:
    """H7: with an order-1 model the optimal key is an exact assignment problem."""
    started = time.monotonic()
    ciphertext = build_ciphertext(view)
    index = ngram_index(ciphertext, 1)
    unigram = lm.table
    for _ in range(lm.order - 1):
        unigram = unigram.mean(axis=0)
    cost = -np.outer(index.unit_counts, unigram)
    rows, columns = linear_sum_assignment(cost)
    key = np.zeros(ciphertext.size, dtype=np.int64)
    for unit, letter in zip(rows, columns, strict=True):
        if unit:
            key[unit] = letter
    description = substitution_description(key, index, lm, ciphertext, hypothesis.hypothesis_id)
    meta = {
        "converged": True,
        "iterations": 1,
        "restarts": 1,
        "evaluations": 1,
        "key": str(key_as_dict(key, ciphertext)),
        "merges": "[]",
    }
    return description, key, meta, time.monotonic() - started


def _generative_rows(
    hypothesis: Hypothesis,
    corpora: dict[str, View],
    holdout: View,
    baselines: dict[str, Description],
) -> list[dict[str, Any]]:
    describe = GENERATIVE_KINDS[hypothesis.kind]
    rows = []
    for corpus, view in corpora.items():
        started = time.monotonic()
        description = describe(view)
        rows.append(
            _row(
                hypothesis,
                hypothesis.kind,
                corpus,
                "train",
                description,
                baselines[corpus],
                time.monotonic() - started,
                key="",
                merges="[]",
                iterations=1,
                restarts=1,
                evaluations=1,
            )
        )
    started = time.monotonic()
    rows.append(
        _row(
            hypothesis,
            hypothesis.kind,
            "real",
            "holdout",
            describe(holdout),
            baselines["holdout"],
            time.monotonic() - started,
            key="",
            merges="[]",
            iterations=1,
            restarts=1,
            evaluations=1,
        )
    )
    return rows


def run_hypothesis(
    hypothesis: Hypothesis,
    corpora: dict[str, View],
    holdout: View,
    baselines: dict[str, Description],
    rng: random.Random,
    deadline: Deadline,
) -> list[dict[str, Any]]:
    """Execute one hypothesis' declared grid and return every candidate row."""
    if not hypothesis.funded:
        return []
    if hypothesis.kind in GENERATIVE_KINDS:
        return _generative_rows(hypothesis, corpora, holdout, baselines)

    real = corpora["real"]
    models = _language_models(hypothesis)
    rows: list[dict[str, Any]] = []
    best: tuple[float, str, CharLM, np.ndarray, tuple[Merge, ...], int | None] | None = None

    for lm in models:
        variants: list[tuple[str, int | None, tuple[Merge, ...]]] = [("plain", None, ())]
        if hypothesis.kind == "merge":
            widths: list[tuple[str, int | None, tuple[Merge, ...]]] = [
                (f"fixed-width-{width}", int(width), ())
                for width in hypothesis.search.get("fixed_widths", [])
            ]
            variants = [*widths, ("plain", None, ())]

        for label, width, merges in variants:
            if hypothesis.kind == "assignment":
                description, key, meta, seconds = _assignment_variant(hypothesis, real, lm)
            else:
                description, key, meta, seconds = _substitution_variant(
                    hypothesis, real, lm, rng, width, merges
                )
            variant = f"{lm.name}|{label}"
            rows.append(
                _row(
                    hypothesis,
                    variant,
                    "real",
                    "train",
                    description,
                    baselines["real"],
                    seconds,
                    **meta,
                )
            )
            gain = gain_per_token(description, baselines["real"])
            if best is None or gain > best[0]:
                best = (gain, variant, lm, key, merges, width)

        if hypothesis.kind == "merge":
            settings = hypothesis.search.get("merge", {})
            started = time.monotonic()
            pool = merge_pool(build_ciphertext(real), int(settings.get("pool", 40)))
            initial = morph_merges() if settings.get("seed_with_phase1_morphs") else ()
            result = merge_search(
                real,
                lm,
                rng,
                pool=pool,
                outer_steps=int(settings.get("outer_steps", 10)),
                inner_iterations=int(settings.get("inner_iterations", 10000)),
                inner_restarts=int(settings.get("inner_restarts", 3)),
                width=int(settings.get("width", 6)),
                initial=tuple(merge for merge in initial if merge in pool),
                deadline=deadline,
            )
            index = ngram_index(result.ciphertext, lm.order)
            description = substitution_description(
                result.key,
                index,
                lm,
                result.ciphertext,
                hypothesis.hypothesis_id,
                merges=result.merges,
            )
            variant = f"{lm.name}|searched-merges"
            rows.append(
                _row(
                    hypothesis,
                    variant,
                    "real",
                    "train",
                    description,
                    baselines["real"],
                    time.monotonic() - started,
                    key=str(key_as_dict(result.key, result.ciphertext)),
                    merges=str(["".join(merge) for merge in result.merges]),
                    iterations=result.outer_steps,
                    restarts=int(settings.get("inner_restarts", 3)),
                    evaluations=result.evaluations,
                    converged=not result.truncated,
                    truncated=result.truncated,
                )
            )
            gain = gain_per_token(description, baselines["real"])
            if best is None or gain > best[0]:
                best = (gain, variant, lm, result.key, result.merges, None)

    assert best is not None
    _, variant, lm, key, merges, width = best

    # The nulls, run with identical settings on the best variant only.
    for corpus, view in corpora.items():
        if corpus == "real":
            continue
        if hypothesis.kind == "assignment":
            description, _, meta, seconds = _assignment_variant(hypothesis, view, lm)
        else:
            description, _, meta, seconds = _substitution_variant(
                hypothesis, view, lm, rng, width, merges
            )
        rows.append(
            _row(
                hypothesis,
                variant,
                corpus,
                "train",
                description,
                baselines[corpus],
                seconds,
                **meta,
            )
        )

    # Held-out pages, scored once, with the key the search already committed to.
    started = time.monotonic()
    if width:
        held = fixed_width_units(holdout, width, f"{holdout.name}|w{width}")
    elif merges:
        held = merge_units(holdout, merges, f"{holdout.name}|merged")
    else:
        held = build_ciphertext(holdout)
    held_index = ngram_index(held, lm.order)
    held_key = np.zeros(held.size, dtype=np.int64)
    train_cipher = (
        fixed_width_units(corpora["real"], width, "train")
        if width
        else (
            merge_units(corpora["real"], merges, "train")
            if merges
            else build_ciphertext(corpora["real"])
        )
    )
    train_mapping = key_as_dict(key, train_cipher)
    letters = {letter: index for index, letter in enumerate(ALPHABET)}
    for position, unit in enumerate(held.units):
        if position:
            held_key[position] = letters.get(train_mapping.get(unit, ""), 0)
    description = substitution_description(
        held_key, held_index, lm, held, hypothesis.hypothesis_id, merges=merges
    )
    rows.append(
        _row(
            hypothesis,
            variant,
            "real",
            "holdout",
            description,
            baselines["holdout"],
            time.monotonic() - started,
            key=str(train_mapping),
            merges=str(["".join(merge) for merge in merges]),
            iterations=0,
            restarts=0,
            evaluations=0,
        )
    )
    return rows


def markov_baselines(corpora: dict[str, View], holdout: View) -> dict[str, Description]:
    """The order-2 glyph Markov baseline for every corpus in play."""
    baselines = {name: markov_description(build_ciphertext(view)) for name, view in corpora.items()}
    baselines["holdout"] = markov_description(build_ciphertext(holdout))
    return baselines
