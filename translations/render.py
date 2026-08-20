"""Line rendering: glossed tokens -> two English strings (plan §6.3).

``english_speculative`` renders every token, marking how much to believe each
one. ``english_gated`` masks everything below the medium band with ``UNKNOWN``
and is the view the coverage statistics use.

Word order is the manuscript's own. The plan called for reordering under an
induced syntactic grammar, but Phase 1 found no word-order grammar to induce
(``reports/phase1/syntax.md``) and Phase 3 did not change that, so reordering
would be invention. No function words are inserted for the same reason.
"""

from __future__ import annotations

from dataclasses import dataclass

HIGH = 0.7
MEDIUM = 0.4
LOW = 0.15
GATED_MASK = "UNKNOWN"


@dataclass(frozen=True)
class RenderedToken:
    """One token as the renderer sees it."""

    surface: str
    english: str
    confidence: float

    @property
    def band(self) -> str:
        """Confidence band per plan §6.3."""
        if self.confidence >= HIGH:
            return "high"
        if self.confidence >= MEDIUM:
            return "medium"
        if self.confidence >= LOW:
            return "low"
        return "none"


def transliteration(surface: str) -> str:
    """The Voynich surface form, marked as untranslated."""
    return f"⟨{surface}⟩"


def speculative(token: RenderedToken) -> str:
    """Full-coverage rendering: every token produces something, marked by band."""
    band = token.band
    if not token.english:
        return transliteration(token.surface)
    if band == "high":
        return token.english
    if band == "medium":
        return f"*{token.english}*"
    if band == "low":
        return f"?{token.english}?"
    return f"{transliteration(token.surface)}(≈{token.english})"


def gated(token: RenderedToken) -> str:
    """Honest diagnostic view: anything below the medium band is masked."""
    return token.english if token.band in ("high", "medium") and token.english else GATED_MASK


def render_line(tokens: list[RenderedToken]) -> tuple[str, str, float]:
    """Render one line: speculative text, gated text and mean confidence."""
    if not tokens:
        return "", "", 0.0
    confidence = sum(token.confidence for token in tokens) / len(tokens)
    return (
        " ".join(speculative(token) for token in tokens),
        " ".join(gated(token) for token in tokens),
        confidence,
    )


def gated_coverage(tokens: list[RenderedToken]) -> float:
    """Share of tokens the gated view actually renders."""
    if not tokens:
        return 0.0
    return sum(1 for token in tokens if gated(token) != GATED_MASK) / len(tokens)
