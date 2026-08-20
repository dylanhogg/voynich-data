"""Intermediate plaintext token -> ranked English glosses (plan §6.2).

The fallback chain is exact stem, then stem after one inflectional ending is
removed, then the best stem at edit distance 1, then nothing — in which case
the renderer prints the Voynich surface form and no English is claimed.

The distributional fallback the plan lists third is **not** implemented. It
would assign a real English word on the basis of frequency profile alone, which
manufactures the appearance of meaning; under a key that lost to a Markov model
that is the most misleading output this pipeline could emit. See
``docs/decisions.md``.

Glossing is per *type*, not per token: one Voynich type resolves to one primary
gloss corpus-wide (the consistency constraint in §6.2).
"""

from __future__ import annotations

import random
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from translations.lexicon.whitakers import Lexicon

SCORE_EXACT = 1.0
SCORE_STRIPPED = 0.75
SCORE_NEAREST = 0.45
MAX_CANDIDATES = 3
SPECIFICITY_SAMPLES = 2000
MAX_SPECIFICITY_LENGTH = 12
_SENSE_SPLIT = re.compile(r"[,/;]")


@dataclass(frozen=True)
class Gloss:
    """One English candidate for an intermediate plaintext form."""

    english: str
    lemma: str
    score: float
    source: str  # lexicon | stripped | nearest
    evidence: str

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly form."""
        return {
            "english": self.english,
            "lemma": self.lemma,
            "score": self.score,
            "source": self.source,
            "evidence": self.evidence,
        }


def short(english: str) -> str:
    """The first sense of a dictionary gloss, for use as a single English word."""
    return _SENSE_SPLIT.split(english)[0].strip() or english.strip()


def candidates(form: str, lexicon: Lexicon, top: int = MAX_CANDIDATES) -> list[Gloss]:
    """Ranked glosses for one intermediate form; empty when nothing matches.

    A strict fallback chain: the first rung that fires supplies the candidates,
    so a distance-1 neighbour never sits in the same list as an exact hit.
    """
    if not form:
        return []
    exact = lexicon.lookup(form)
    if exact is not None:
        return [
            Gloss(sense, exact.lemma, SCORE_EXACT, "lexicon", f"stem={form} pos={exact.pos}")
            for sense in exact.glosses[:top]
        ]
    stripped = lexicon.stripped(form)
    if stripped is not None:
        entry, ending = stripped
        return [
            Gloss(
                sense,
                entry.lemma,
                SCORE_STRIPPED,
                "stripped",
                f"stem={entry.lemma} ending=-{ending}",
            )
            for sense in entry.glosses[:top]
        ]
    near = lexicon.near(form)
    if near is not None:
        return [
            Gloss(sense, near.lemma, SCORE_NEAREST, "nearest", f"stem={near.lemma} d=1")
            for sense in near.glosses[:top]
        ]
    return []


def gloss_table(forms: Iterable[str], lexicon: Lexicon) -> dict[str, list[Gloss]]:
    """Gloss every distinct intermediate form once."""
    return {form: candidates(form, lexicon) for form in sorted(set(forms))}


def coverage(table: dict[str, list[Gloss]]) -> dict[str, float]:
    """Share of types resolved by each rung of the fallback chain."""
    total = max(len(table), 1)
    sources = [glosses[0].source if glosses else "none" for glosses in table.values()]
    return {
        source: sources.count(source) / total
        for source in ("lexicon", "stripped", "nearest", "none")
    }


def specificity(
    lexicon: Lexicon, letters: str, rng: random.Random, samples: int = SPECIFICITY_SAMPLES
) -> dict[int, float]:
    """How much a hit of each length is worth, measured rather than assumed.

    A two-letter string hits a 48,000-stem Latin dictionary almost whatever it
    is, so an exact match on one is close to no evidence at all. This samples
    random strings drawn from ``letters``' own frequency distribution and
    returns ``1 - hit rate`` per length: the share of the hypothesis space a hit
    of that length actually rules out.
    """
    weights = Counter(letters)
    alphabet = sorted(weights)
    counts = [weights[letter] for letter in alphabet]
    scores: dict[int, float] = {}
    for length in range(1, MAX_SPECIFICITY_LENGTH + 1):
        hits = sum(
            1
            for _ in range(samples)
            if lexicon.lookup("".join(rng.choices(alphabet, counts, k=length))) is not None
        )
        scores[length] = 1.0 - hits / samples
    return scores


def specificity_of(scores: dict[int, float], length: int) -> float:
    """Look up a length's specificity, saturating past the sampled range."""
    if not scores:
        return 1.0
    return scores.get(length, scores[max(scores)]) if length else 0.0
