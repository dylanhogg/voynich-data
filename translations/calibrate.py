"""Confidence calibration on synthetic ciphertexts (plan §4.6, run in Phase 4).

    uv run python -m translations.calibrate

There is no ground truth for the manuscript, so the confidence column cannot be
calibrated against it. Instead each keyed hypothesis is given a problem whose
answer we hid ourselves: a reference corpus in the language its own model
assumes, enciphered under its own scheme at its own channel width, attacked
blind with its own search settings, then pushed through the *same* gloss stage.
Token accuracy as a function of the pipeline's own raw score is what the
isotonic map converts into a confidence.

The limitation this cannot escape, and which the reports print: the map is
valid only if the manuscript resembles the hypothesised system. It bounds
optimism about a system we can simulate; it certifies nothing about one we
cannot.
"""

from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from translations.analysis.common import View, baseline_view
from translations.config import CONFIG, PATHS
from translations.decipher.channel import CipherText, build_ciphertext, fixed_width_units
from translations.decipher.lm import ALPHABET, VOWELS, abbreviate, corpus_lm
from translations.decipher.run_hypothesis import load_hypotheses
from translations.decipher.score import NgramIndex, ngram_index
from translations.decipher.search import search_key
from translations.decipher.synthetic import true_key_array
from translations.decode import (
    CANDIDATES,
    RANKING,
    TRANSLATOR_CONFIG,
    KeyedHypothesis,
    keyed_hypotheses,
)
from translations.determinism import derived_rng
from translations.gloss import Gloss, candidates, short, specificity, specificity_of
from translations.lexicon.whitakers import Lexicon, load_lexicon
from translations.nulls.encipher import CIPHER_UNITS, Key, encipher
from vcat.logging import get_logger

logger = get_logger(__name__)

CALIBRATION_PATH = PATHS.output_dir / "calibration.json"


def transform_words(words: list[str], transform: str) -> list[str]:
    """Apply the plaintext form a hypothesis' language model assumes."""
    if transform == "abjad":
        return [kept for word in words if (kept := "".join(c for c in word if c not in VOWELS))]
    if transform == "abbrev":
        return [kept for word in words if (kept := abbreviate(word))]
    return words


def fit_alphabet(words: list[str], size: int = len(CIPHER_UNITS)) -> list[str]:
    """Drop words using letters beyond the ``size`` commonest.

    A one-glyph-per-letter channel has only as many cipher symbols as EVA has
    glyphs, and the normalised Latin corpora carry a handful of borrowed
    letters (k, w, y, z) beyond that. Dropping the words that use them is the
    honest fit: padding the cipher alphabet would simulate a channel wider than
    the one the key was searched on.
    """
    counts = Counter(character for word in words for character in word)
    keep = {letter for letter, _ in counts.most_common(size)}
    return [word for word in words if set(word) <= keep]


def raw_score(gloss: Gloss | None, specificity: float, coverage: float) -> float:
    """The pipeline's own score for one glossed token, before calibration.

    Three factors, all comparable between the manuscript, the synthetic
    ciphertext and the random-key null: how the gloss was found, how much a hit
    of that length rules out, and how much of the token the key covered with
    units it had actually seen. The transcription reliability weight is applied
    later, at the confidence, because the synthetic has nothing to match it.
    """
    if gloss is None:
        return 0.0
    return gloss.score * specificity * coverage


def _best(form: str, lexicon: Lexicon) -> Gloss | None:
    found = candidates(form, lexicon, top=1)
    return found[0] if found else None


@dataclass(frozen=True)
class CalibrationMap:
    """Isotonic map from raw score to observed token accuracy."""

    hypothesis: str
    scores: tuple[float, ...]
    accuracy: tuple[float, ...]
    n_tokens: int
    key_accuracy: float
    token_accuracy: float
    corpus: str
    scheme: str
    diagram: tuple[dict[str, float], ...] = ()

    def __call__(self, score: float) -> float:
        """Calibrated confidence for a raw score."""
        if not self.scores:
            return 0.0
        return float(np.interp(score, self.scores, self.accuracy))

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly form."""
        return {
            "hypothesis": self.hypothesis,
            "scores": list(self.scores),
            "accuracy": list(self.accuracy),
            "n_tokens": self.n_tokens,
            "key_accuracy": self.key_accuracy,
            "token_accuracy": self.token_accuracy,
            "corpus": self.corpus,
            "scheme": self.scheme,
            "diagram": [dict(row) for row in self.diagram],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationMap:
        """Rebuild a map from its JSON form."""
        return cls(
            hypothesis=str(data["hypothesis"]),
            scores=tuple(float(value) for value in data["scores"]),
            accuracy=tuple(float(value) for value in data["accuracy"]),
            n_tokens=int(data["n_tokens"]),
            key_accuracy=float(data["key_accuracy"]),
            token_accuracy=float(data["token_accuracy"]),
            corpus=str(data["corpus"]),
            scheme=str(data["scheme"]),
            diagram=tuple(dict(row) for row in data.get("diagram", [])),
        )


def isotonic(scores: np.ndarray, outcomes: np.ndarray) -> tuple[list[float], list[float]]:
    """Pool-adjacent-violators fit of accuracy against score.

    Isotonic rather than Platt: the relation is monotone by construction but
    not remotely sigmoid — the score is a product of four bounded factors with
    heavy mass at a few values — and PAVA needs no functional assumption.
    """
    levels, inverse = np.unique(scores, return_inverse=True)
    weights = np.bincount(inverse).astype(float)
    means = np.bincount(inverse, weights=outcomes.astype(float)) / weights

    blocks: list[list[float]] = []  # value, weight, number of levels pooled
    for value, weight in zip(means, weights, strict=True):
        blocks.append([value, weight, 1.0])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            value2, weight2, span2 = blocks.pop()
            value1, weight1, span1 = blocks.pop()
            total = weight1 + weight2
            blocks.append([(value1 * weight1 + value2 * weight2) / total, total, span1 + span2])

    fitted: list[float] = []
    for value, _, span in blocks:
        fitted.extend([value] * int(span))
    return [float(level) for level in levels], fitted


DIAGRAM_BINS = 5


def reliability_diagram(
    fitted: CalibrationMap, scores: np.ndarray, correct: np.ndarray
) -> tuple[dict[str, float], ...]:
    """Predicted confidence against observed accuracy, on tokens not used to fit."""
    predicted = np.array([fitted(float(score)) for score in scores])
    edges = np.linspace(0.0, 1.0, DIAGRAM_BINS + 1)
    rows = []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (predicted >= low) & (predicted <= high if high == 1.0 else predicted < high)
        if not mask.any():
            continue
        rows.append(
            {
                "bin_low": float(low),
                "bin_high": float(high),
                "predicted": float(predicted[mask].mean()),
                "observed": float(correct[mask].mean()),
                "n": float(mask.sum()),
            }
        )
    return tuple(rows)


@dataclass(frozen=True)
class Synthetic:
    """One blind run: what the pipeline said, and what was true."""

    scores: np.ndarray
    correct: np.ndarray
    key_accuracy: float
    n_tokens: int


def run_blind(
    keyed: KeyedHypothesis,
    lexicon: Lexicon,
    n_words: int,
    iterations: int,
    restarts: int,
    rng: random.Random,
) -> Synthetic:
    """Encipher, attack blind, gloss, and score against the hidden plaintext."""
    plain = baseline_view(keyed.language, n_words, rng)
    truth = transform_words(["".join(word) for word in plain.words], keyed.transform)
    width = keyed.width
    if width is None:
        truth = fit_alphabet(truth)
    scheme = "verbose" if width else "substitution"
    ciphertext_words, hidden = encipher(truth, scheme, rng, width=width or 2)

    view = View(name=f"synthetic|{keyed.hypothesis_id}", lines=[ciphertext_words])
    ciphertext = (
        fixed_width_units(view, width, view.name, min_count=1)
        if width
        else build_ciphertext(view, view.name, min_count=1)
    )
    lm = corpus_lm(keyed.language, keyed.order, keyed.transform)
    index = ngram_index(ciphertext, lm.order)
    result = search_key(ciphertext, lm, rng, iterations, restarts, index=index)

    decoded = "".join(ALPHABET[symbol] for symbol in result.key[ciphertext.ids]).split("#")
    found = [word for word in decoded if word]
    letters = "".join(found)
    lengths = specificity(lexicon, letters or "abc", derived_rng(f"spec-{keyed.hypothesis_id}"))

    scores: list[float] = []
    correct: list[float] = []
    for guess, actual in zip(found, truth, strict=False):
        gloss = _best(guess, lexicon)
        real = _best(actual, lexicon)
        scores.append(raw_score(gloss, specificity_of(lengths, len(guess)), 1.0))
        correct.append(
            1.0
            if gloss is not None
            and real is not None
            and short(gloss.english) == short(real.english)
            else 0.0
        )

    return Synthetic(
        scores=np.array(scores),
        correct=np.array(correct),
        key_accuracy=key_accuracy(result.key, hidden, ciphertext, index),
        n_tokens=len(found),
    )


def key_accuracy(key: np.ndarray, hidden: Key, ciphertext: CipherText, index: NgramIndex) -> float:
    """Token-weighted share of cipher units the search mapped back correctly."""
    truth = true_key_array(hidden, ciphertext)
    if truth is None:
        return float("nan")
    weights = index.unit_counts[1:]
    return float((weights * (key[1:] == truth[1:])).sum() / max(weights.sum(), 1))


def calibrate(
    keyed: list[KeyedHypothesis], lexicon: Lexicon, n_words: int
) -> dict[str, CalibrationMap]:
    """Fit one map per keyed hypothesis."""
    settings = {hypothesis.hypothesis_id: hypothesis.search for hypothesis in load_hypotheses()}
    maps: dict[str, CalibrationMap] = {}
    for entry in keyed:
        search = settings.get(entry.hypothesis_id, {})
        began = time.monotonic()
        run = run_blind(
            entry,
            lexicon,
            n_words,
            int(search.get("iterations", 40000)),
            int(search.get("restarts", 4)),
            derived_rng(f"calibrate-{entry.hypothesis_id}"),
        )
        # Fit on half the synthetic tokens and diagram on the other half, so the
        # reliability diagram is a check on the map rather than a picture of it.
        fit, test = slice(0, None, 2), slice(1, None, 2)
        scores, accuracy = isotonic(run.scores[fit], run.correct[fit])
        fitted = CalibrationMap(
            hypothesis=entry.hypothesis_id,
            scores=tuple(scores),
            accuracy=tuple(accuracy),
            n_tokens=run.n_tokens,
            key_accuracy=run.key_accuracy,
            token_accuracy=float(run.correct.mean()),
            corpus=entry.language,
            scheme=entry.scheme,
        )
        maps[entry.hypothesis_id] = replace(
            fitted, diagram=reliability_diagram(fitted, run.scores[test], run.correct[test])
        )
        logger.info(
            "Calibrated",
            hypothesis=entry.hypothesis_id,
            key_accuracy=round(run.key_accuracy, 3),
            token_accuracy=round(float(run.correct.mean()), 3),
            seconds=round(time.monotonic() - began, 1),
        )
    return maps


def load_maps(path: Path | None = None) -> dict[str, CalibrationMap]:
    """Load the committed calibration maps."""
    source = path or CALIBRATION_PATH
    data = json.loads(source.read_text())
    return {name: CalibrationMap.from_dict(row) for name, row in data["maps"].items()}


def main() -> int:
    """Fit and write the calibration maps."""
    started = time.time()
    keyed = keyed_hypotheses(CANDIDATES, RANKING, TRANSLATOR_CONFIG)
    maps = calibrate(keyed, load_lexicon(), CONFIG.calibration_words)
    CALIBRATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_PATH.write_text(
        json.dumps(
            {
                "words": CONFIG.calibration_words,
                "maps": {name: value.as_dict() for name, value in sorted(maps.items())},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"Calibration written to {CALIBRATION_PATH} ({time.time() - started:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
