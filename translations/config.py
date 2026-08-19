"""Frozen configuration for the translation programme.

One place for paths, the global seed, the tokenization contract and the
held-out split. Nothing here is read from the environment: a run is defined by
this module plus the input file checksums (see :mod:`translations.determinism`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SPECULATIVE_BANNER = (
    "SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript "
    "exists. This is model output under a stated hypothesis, not a reading of "
    "the manuscript."
)


class Tokenizer(StrEnum):
    """Tokenization variants (plan §2.3).

    ``T2_SLOT`` and ``T3_MERGE`` depend on inductions produced in Phase 1.4 and
    Phase 2 respectively and are not implemented yet.
    """

    T0_CHAR = "T0-char"
    T1_GLYPH = "T1-glyph"
    T2_SLOT = "T2-slot"
    T3_MERGE = "T3-merge"


class CommaPolicy(StrEnum):
    """How the uncertain word separator ``,`` is treated."""

    BREAK = "CB=break"
    JOIN = "CB=join"


class Transcription(StrEnum):
    """Transcription sources available at line level."""

    ZL = "zl"
    IT = "it"


@dataclass(frozen=True)
class Paths:
    """Input and output locations. All local; no URLs."""

    repo_root: Path = REPO_ROOT
    eva_lines: Path = REPO_ROOT / "output" / "eva_lines.jsonl"
    pages: Path = REPO_ROOT / "output" / "metadata" / "pages.jsonl"
    folios: Path = REPO_ROOT / "output" / "metadata" / "folios.jsonl"
    quires: Path = REPO_ROOT / "output" / "metadata" / "quires.jsonl"
    mismatch_index: Path = REPO_ROOT / "output" / "mismatch_index.jsonl"
    sources_yaml: Path = REPO_ROOT / "data_sources" / "sources.yaml"
    corpora_cache: Path = REPO_ROOT / "data_sources" / "cache" / "corpora"
    output_dir: Path = REPO_ROOT / "output" / "translation"


@dataclass(frozen=True)
class Config:
    """The experiment configuration. Changing any field changes the run hash."""

    seed: int = 20260819
    holdout_fraction: float = 0.2
    default_tokenizer: Tokenizer = Tokenizer.T1_GLYPH
    default_comma_policy: CommaPolicy = CommaPolicy.BREAK
    default_transcription: Transcription = Transcription.ZL
    # Mismatch-index statuses that make up the consensus subset (plan §3.1).
    consensus_statuses: tuple[str, ...] = ("exact_match", "normalized_match", "high_similarity")


PATHS = Paths()
CONFIG = Config()
