"""The audit harness: one loaded pipeline, re-run over whatever a test asks for.

Every Phase 5 test is the same shape — build a view, push it through the Phase 4
pipeline unchanged, and compare a headline number against a null. Sharing the
lexicon cache, the calibration maps and the committed keys across all of them is
what keeps the battery to minutes rather than hours, and it also guarantees that
a control is measured by the *identical* code path as the manuscript, which is
the only reason the comparison means anything (plan §7.2.1).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from translations.alignment import build_rows
from translations.analysis.common import View, voynich_view
from translations.calibrate import CalibrationMap, load_maps
from translations.decode import CANDIDATES, RANKING, TRANSLATOR_CONFIG, KeyedHypothesis
from translations.decode import keyed_hypotheses as load_keyed
from translations.determinism import derived_rng
from translations.io import load_lines
from translations.lexicon.whitakers import load_lexicon
from translations.paragraphs import build_blocks
from translations.pipeline import GlossCache, TranslatedLine, reliability_weights, translate
from translations.render import GATED_MASK, gated
from translations.represent import Representation, merged, phase2_merges
from translations.tokenize import Merges

# A finding either raises confidence in the rendering, lowers it, or cannot say.
SUPPORTS = "supports"
UNDERMINES = "undermines"
NEUTRAL = "neutral"
VACUOUS = "vacuous"
NOT_RUN = "not run"


@dataclass(frozen=True)
class Finding:
    """One audit test, reduced to a row of the report's evidence table."""

    test: str
    metric: str
    value: Any
    null: Any
    verdict: str
    implication: str

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly form."""
        return {
            "test": self.test,
            "metric": self.metric,
            "value": self.value,
            "null": self.null,
            "verdict": self.verdict,
            "implication": self.implication,
        }


@dataclass(frozen=True)
class Check:
    """A finding, the markdown that shows its working, and its raw numbers."""

    finding: Finding
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Harness:
    """Everything a Phase 5 test needs to re-run the Phase 4 pipeline."""

    keyed: list[KeyedHypothesis]
    maps: dict[str, CalibrationMap]
    cache: GlossCache
    representation: Representation
    merges: Merges
    base: View
    weights: dict[tuple[str, int], float]
    blocks: dict[str, str]
    text: dict[str, str]
    provenance: dict[str, Any]

    @property
    def primary(self) -> KeyedHypothesis:
        """The hypothesis the Phase 4 artifacts are rendered under."""
        return self.keyed[0]

    def render(
        self,
        salt: str,
        view: View,
        hypothesis: KeyedHypothesis | None = None,
        reliability: bool = True,
    ) -> list[TranslatedLine]:
        """Run the full Phase 4 pipeline over one view.

        ``salt`` seeds the random-key null, so passing
        :func:`translations.phase4.render_salt` reproduces a committed rendering
        exactly and anything else deliberately draws a fresh null.
        """
        entry = hypothesis or self.primary
        return translate(
            view,
            entry,
            self.cache,
            self.maps[entry.hypothesis_id],
            self.weights if reliability else {},
            self.blocks,
            self.text,
            derived_rng(salt),
        )

    def chosen(self, view: View, hypothesis: KeyedHypothesis) -> list[str]:
        """Just the glosses, skipping scoring: what each token decodes to.

        The key-instability battery compares dozens of keys, and the confidence
        stages (twenty permuted keys per rendering) cost far more than the
        question needs. Two keys that gloss every token identically are the same
        key for every purpose this report cares about.
        """
        out = []
        for word in view.words:
            gloss = self.cache.best(hypothesis.decode(word).plaintext)
            out.append(gloss.english if gloss else "")
        return out

    def rng(self, salt: str) -> random.Random:
        """A seeded generator, so every test is reproducible on its own."""
        return derived_rng(f"phase5-{salt}")


def build_harness() -> Harness:
    """Load the Phase 4 pipeline exactly as `make translate` builds it."""
    merges, provenance = phase2_merges()
    representation = merged(merges, origin="Phase 3 translator configuration", detail=provenance)
    return Harness(
        keyed=load_keyed(CANDIDATES, RANKING, TRANSLATOR_CONFIG),
        maps=load_maps(),
        cache=GlossCache(load_lexicon()),
        representation=representation,
        merges=merges,
        base=voynich_view(),
        weights=reliability_weights(build_rows()),
        blocks={line_id: block.block_id for block in build_blocks() for line_id in block.line_ids},
        text={line.line_id: line.text_clean for line in load_lines()},
        provenance=provenance,
    )


def gated_coverage(lines: list[TranslatedLine]) -> float:
    """Share of tokens the gated view renders."""
    tokens = [token for line in lines for token in line.tokens]
    if not tokens:
        return 0.0
    return sum(1 for token in tokens if gated(token.rendered) != GATED_MASK) / len(tokens)


def mean_confidence(lines: list[TranslatedLine]) -> float:
    """Mean per-token confidence."""
    tokens = [token for line in lines for token in line.tokens]
    return sum(token.confidence for token in tokens) / len(tokens) if tokens else 0.0


def gated_words(lines: list[TranslatedLine]) -> list[str]:
    """Every English word the gated view actually prints, in order."""
    return [
        word
        for line in lines
        for token in line.tokens
        if (word := gated(token.rendered)) != GATED_MASK
    ]


def agreement(left: list[str], right: list[str]) -> float:
    """Share of positions where two gloss sequences say the same thing."""
    pairs = list(zip(left, right, strict=False))
    if not pairs:
        return 0.0
    return sum(1 for a, b in pairs if a == b) / len(pairs)
