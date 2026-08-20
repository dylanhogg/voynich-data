"""Glyph units -> intermediate plaintext, under a key Phase 2/3 committed to.

A key is a mapping from *channel units* to plaintext letters. Which units a
channel has depends on the hypothesis: the ``plain`` channel's units are the
representation's own units, while ``fixed-width-N`` groups them in Ns, so the
same key file means nothing without the channel it was searched on. Both are
recovered from the candidate's variant string, which is where the search
recorded them.

Units the search never saw are folded to the rare symbol ``?``, exactly as
:func:`translations.decipher.channel.build_ciphertext` did during the search —
and counted, so a token decoded mostly from rare units can be marked as such.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from translations.config import PATHS
from translations.decipher.channel import RARE
from translations.decipher.lm import BOUNDARY

CANDIDATES = PATHS.repo_root / "output" / "decipher" / "round2_candidates.parquet"
RANKING = PATHS.repo_root / "reports" / "phase3" / "rescoring.json"
TRANSLATOR_CONFIG = PATHS.output_dir / "phase3_translator_config.json"

FIXED_WIDTH = re.compile(r"fixed-width-(\d+)")
LM_ORDER = re.compile(r"-o\d+$")

# Which encipherment the calibration harness must reproduce for a hypothesis.
# H3 strips vowels, H2 spells one letter with several glyphs, the rest are
# one-glyph-per-letter substitutions.
SCHEMES: dict[str, str] = {
    "H1": "substitution",
    "H2": "verbose",
    "H3": "abjad",
    "H4": "substitution",
    "H7": "substitution",
}


@dataclass(frozen=True)
class Decoded:
    """One token's intermediate plaintext plus how much of it was guessed."""

    plaintext: str
    n_units: int
    n_rare: int
    n_deleted: int

    @property
    def key_coverage(self) -> float:
        """Share of the token's units that had a key entry of their own."""
        return (self.n_units - self.n_rare) / self.n_units if self.n_units else 0.0


@dataclass(frozen=True)
class KeyedHypothesis:
    """A committed key, with the channel and the scores it was committed under."""

    hypothesis_id: str
    representation: str
    variant: str
    key: dict[str, str]
    gain_per_token: float
    holdout_gain_per_token: float
    converged: bool
    p_value: float

    @property
    def width(self) -> int | None:
        """Channel width, or ``None`` for the plain channel."""
        match = FIXED_WIDTH.search(self.variant)
        return int(match.group(1)) if match else None

    @property
    def channel(self) -> str:
        """Channel name as it appears in the variant string."""
        return f"fixed-width-{self.width}" if self.width else "plain"

    @property
    def scheme(self) -> str:
        """The encipherment the calibration harness reproduces for this key."""
        return SCHEMES[self.hypothesis_id]

    @property
    def order(self) -> int:
        """Language-model order the search used."""
        match = LM_ORDER.search(self.variant.split("|")[0])
        return int(match.group(0)[2:]) if match else 3

    @property
    def transform(self) -> str:
        """Plaintext form the language model assumed: plain, abjad or abbrev."""
        parts = self.variant.split("|")[0].split("-")
        return parts[-2] if len(parts) > 1 and parts[-2] in ("abjad", "abbrev") else "plain"

    @property
    def language(self) -> str:
        """The reference corpus whose language model the search used."""
        name = self.variant.split("|")[0]
        name = LM_ORDER.sub("", name)
        return name[: -len(self.transform) - 1] if self.transform != "plain" else name

    def units(self, word: list[str]) -> list[str]:
        """Channel units of one word."""
        width = self.width
        if width is None:
            return word
        return ["".join(word[start : start + width]) for start in range(0, len(word), width)]

    def decode(self, word: list[str]) -> Decoded:
        """Decode one word to its intermediate plaintext."""
        units = self.units(word)
        letters: list[str] = []
        rare = deleted = 0
        for unit in units:
            letter = self.key.get(unit)
            if letter is None:
                rare += 1
                letter = self.key.get(RARE, BOUNDARY)
            if letter == BOUNDARY:
                deleted += 1
                continue
            letters.append(letter)
        return Decoded("".join(letters), len(units), rare, deleted)


def parse_key(text: str) -> dict[str, str]:
    """Parse a key as the search recorded it (a Python dict repr)."""
    parsed = ast.literal_eval(text)
    return {str(unit): str(letter) for unit, letter in parsed.items()}


def keyed_hypotheses(
    candidates: Path, ranking: Path, translator_config: Path
) -> list[KeyedHypothesis]:
    """Every ranked hypothesis that committed to a key, the chosen one first.

    ``best_by_hypothesis`` — one row per hypothesis, with the significance the
    Phase 3 report published — is the source of truth for *which* variant each
    hypothesis is represented by; the candidate table supplies its key. Nothing
    is re-derived here, so the scores printed beside a translation are the same
    numbers `reports/phase3/rescoring.md` prints.
    """
    frame = pd.read_parquet(candidates)
    keys = {
        (str(row["hypothesis"]), str(row["representation"]), str(row["variant"])): str(row["key"])
        for _, row in frame[(frame["corpus"] == "real") & (frame["split"] == "train")].iterrows()
    }
    rows = json.loads(ranking.read_text())["best_by_hypothesis"].values()
    primary = str(json.loads(translator_config.read_text())["chosen"]["hypothesis"])

    keyed = []
    for row in rows:
        key = keys.get((row["hypothesis"], row["representation"], row["variant"]), "")
        if len(key) <= 2:  # generative hypotheses commit to no key
            continue
        keyed.append(
            KeyedHypothesis(
                hypothesis_id=str(row["hypothesis"]),
                representation=str(row["representation"]),
                variant=str(row["variant"]),
                key=parse_key(key),
                gain_per_token=float(row["gain_per_token"]),
                holdout_gain_per_token=float(row["holdout_gain_per_token"]),
                converged=bool(row["converged"]),
                p_value=float(row["p_value"]),
            )
        )
    return sorted(keyed, key=lambda entry: (entry.hypothesis_id != primary, entry.hypothesis_id))
