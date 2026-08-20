"""The translation pipeline: manuscript lines -> glossed, hedged English rows.

Stages, each a pure function of its input (plan §6.1):

    tokenize -> represent -> decode -> gloss -> score -> calibrate -> render

Two things make the confidence column mean something more than "the lexicon
matched". First, the calibration map, fitted on ciphertext whose answer we hid
(``translations.calibrate``). Second, a **random-key null**: the same key is
permuted and the whole decode-and-gloss stage is re-run, so every token carries
an empirical p-value for "a key with no information would have glossed this at
least as well". Short tokens hit a 48,000-stem Latin dictionary whatever the
key says, and this is what makes that visible per token rather than only in the
aggregate.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from translations.alignment import TokenRow
from translations.analysis.common import View
from translations.calibrate import CalibrationMap, raw_score
from translations.decode import KeyedHypothesis
from translations.gloss import Gloss, candidates, short, specificity, specificity_of
from translations.lexicon.whitakers import Lexicon
from translations.render import RenderedToken, gated, render_line, speculative
from translations.strata import StratumRow

NULL_KEYS = 20


@dataclass
class GlossCache:
    """One gloss computation per distinct intermediate form, shared everywhere."""

    lexicon: Lexicon
    memo: dict[str, list[Gloss]] = field(default_factory=dict)

    def get(self, form: str) -> list[Gloss]:
        """Ranked glosses for a form, computed at most once."""
        if form not in self.memo:
            self.memo[form] = candidates(form, self.lexicon)
        return self.memo[form]

    def best(self, form: str) -> Gloss | None:
        """Top-ranked gloss, or ``None``."""
        found = self.get(form)
        return found[0] if found else None


@dataclass(frozen=True)
class Token:
    """One manuscript token, all the way through the pipeline."""

    surface: str
    units: tuple[str, ...]
    intermediate: str
    key_coverage: float
    reliability: float
    glosses: tuple[Gloss, ...]
    raw_score: float
    null_p: float
    confidence: float

    @property
    def english(self) -> str:
        """The chosen English word, or empty when nothing was found."""
        return short(self.glosses[0].english) if self.glosses else ""

    @property
    def rendered(self) -> RenderedToken:
        """The renderer's view of this token."""
        return RenderedToken(self.surface, self.english, self.confidence)

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly form.

        The ranked gloss candidates are *not* repeated here: they are a property
        of the type, and live once per type in ``lexicon.jsonl``. Join on
        ``surface`` to recover them.
        """
        return {
            "surface": self.surface,
            "intermediate": self.intermediate,
            "key_coverage": self.key_coverage,
            "reliability": self.reliability,
            "raw_score": self.raw_score,
            "null_p": self.null_p,
            "confidence": self.confidence,
            "band": self.rendered.band,
            "chosen": self.english,
        }


@dataclass(frozen=True)
class TranslatedLine:
    """One rendered line."""

    line_id: str
    page_id: str
    section: str
    currier_language: str
    hand: str
    line_type: str
    is_holdout: bool
    block_id: str
    text_clean: str
    tokens: tuple[Token, ...]
    english_speculative: str
    english_gated: str
    line_confidence: float

    def as_dict(self, hypothesis: KeyedHypothesis, banner: str) -> dict[str, Any]:
        """One row of ``translation_lines.jsonl``."""
        return {
            "line_id": self.line_id,
            "page_id": self.page_id,
            "section": self.section,
            "currier_language": self.currier_language,
            "hand": self.hand,
            "line_type": self.line_type,
            "is_holdout": self.is_holdout,
            "block_id": self.block_id,
            "text_clean": self.text_clean,
            "tokens": [token.as_dict() for token in self.tokens],
            "english_speculative": self.english_speculative,
            "english_gated": self.english_gated,
            "line_confidence": self.line_confidence,
            "hypothesis_id": hypothesis.hypothesis_id,
            "key_id": f"{hypothesis.representation}|{hypothesis.variant}",
            "banner": banner,
        }


def permuted_keys(key: dict[str, str], rng: random.Random, count: int) -> list[dict[str, str]]:
    """Random keys with the same letter multiset: the null this pipeline is tested against."""
    units = sorted(key)
    letters = [key[unit] for unit in units]
    keys = []
    for _ in range(count):
        shuffled = list(letters)
        rng.shuffle(shuffled)
        keys.append(dict(zip(units, shuffled, strict=True)))
    return keys


def _scores(
    words: list[list[str]],
    hypothesis: KeyedHypothesis,
    key: dict[str, str],
    cache: GlossCache,
    lengths: dict[int, float],
) -> np.ndarray:
    """Raw score of every token under one key."""
    swapped = KeyedHypothesis(
        hypothesis_id=hypothesis.hypothesis_id,
        representation=hypothesis.representation,
        variant=hypothesis.variant,
        key=key,
        gain_per_token=hypothesis.gain_per_token,
        holdout_gain_per_token=hypothesis.holdout_gain_per_token,
        converged=hypothesis.converged,
        p_value=hypothesis.p_value,
    )
    out = np.empty(len(words))
    for index, word in enumerate(words):
        decoded = swapped.decode(word)
        gloss = cache.best(decoded.plaintext)
        out[index] = raw_score(
            gloss, specificity_of(lengths, len(decoded.plaintext)), decoded.key_coverage
        )
    return out


def null_p_values(
    words: list[list[str]],
    hypothesis: KeyedHypothesis,
    real: np.ndarray,
    cache: GlossCache,
    lengths: dict[int, float],
    rng: random.Random,
    count: int = NULL_KEYS,
) -> np.ndarray:
    """Per-token empirical p-value against keys carrying no information."""
    beaten = np.zeros(len(words))
    for key in permuted_keys(hypothesis.key, rng, count):
        beaten += _scores(words, hypothesis, key, cache, lengths) >= real
    return (beaten + 1.0) / (count + 1.0)


def translate(
    view: View,
    hypothesis: KeyedHypothesis,
    cache: GlossCache,
    calibration: CalibrationMap,
    reliability: dict[tuple[str, int], float],
    blocks: dict[str, str],
    text: dict[str, str],
    rng: random.Random,
) -> list[TranslatedLine]:
    """Run every stage over a whole view and return one row per line."""
    words = view.words
    intermediates = [hypothesis.decode(word) for word in words]
    lengths = specificity(
        cache.lexicon, "".join(item.plaintext for item in intermediates) or "abc", rng
    )
    real = np.array(
        [
            raw_score(
                cache.best(item.plaintext),
                specificity_of(lengths, len(item.plaintext)),
                item.key_coverage,
            )
            for item in intermediates
        ]
    )
    nulls = null_p_values(words, hypothesis, real, cache, lengths, rng)

    lines: list[TranslatedLine] = []
    cursor = 0
    # Control corpora (pseudo-Voynich, surrogates) carry no stratum rows; they
    # still have to run through the identical pipeline, so they get synthetic
    # line ids and empty strata rather than a separate code path.
    rows: list[StratumRow | None] = list(view.rows) or [None] * len(view.lines)
    for number, (line, row) in enumerate(zip(view.lines, rows, strict=True), start=1):
        line_id = row.line_id if row else f"{view.name}:{number}"
        tokens: list[Token] = []
        for index, word in enumerate(line):
            item = intermediates[cursor]
            weight = reliability.get((line_id, index), 1.0)
            glosses = cache.get(item.plaintext)
            tokens.append(
                Token(
                    surface="".join(word),
                    units=tuple(word),
                    intermediate=item.plaintext,
                    key_coverage=item.key_coverage,
                    reliability=weight,
                    glosses=tuple(glosses),
                    raw_score=float(real[cursor]),
                    null_p=float(nulls[cursor]),
                    confidence=calibration(float(real[cursor]))
                    * (1.0 - float(nulls[cursor]))
                    * weight,
                )
            )
            cursor += 1
        rendered = [token.rendered for token in tokens]
        speculative_text, gated_text, confidence = render_line(rendered)
        lines.append(
            TranslatedLine(
                line_id=line_id,
                page_id=row.page_id if row else view.name,
                section=row.section if row else "",
                currier_language=row.currier_language if row else "",
                hand=row.hand if row else "",
                line_type=row.line_type if row else "",
                is_holdout=bool(row.is_holdout) if row else False,
                block_id=blocks.get(line_id, ""),
                text_clean=text.get(line_id, ""),
                tokens=tuple(tokens),
                english_speculative=speculative_text,
                english_gated=gated_text,
                line_confidence=confidence,
            )
        )
    return lines


def reliability_weights(rows: list[TokenRow]) -> dict[tuple[str, int], float]:
    """Per-token transcription reliability, keyed by line and position."""
    return {(row.line_id, row.token_index): row.reliability for row in rows}


__all__ = [
    "GlossCache",
    "Token",
    "TranslatedLine",
    "gated",
    "null_p_values",
    "permuted_keys",
    "reliability_weights",
    "speculative",
    "translate",
]
