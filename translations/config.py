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

# Plan §7.4: meeting a kill criterion does not withdraw the artifacts, it
# re-frames them. Both strings start with "SPECULATIVE OUTPUT" so the schema
# and every downstream banner check keep working.
FAILED_VALIDATION_BANNER = (
    "SPECULATIVE OUTPUT — unvalidated rendering under a hypothesis that FAILED "
    "VALIDATION: the identical pipeline renders pseudo-Voynich, which encodes "
    "nothing, at least as well as it renders the manuscript (plan §7.4). This is "
    "model output, not a reading of the manuscript."
)


def active_banner(failed_validation: bool) -> str:
    """The banner an artifact must carry, given whether validation failed."""
    return FAILED_VALIDATION_BANNER if failed_validation else SPECULATIVE_BANNER


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
    """Transcription sources available at line level.

    ZL and IT are EVA. CD (Currier), FG (FSG) and GC (v101) use different
    alphabets, so only ``T0-char`` tokenization and alphabet-agnostic metrics
    are meaningful for them.
    """

    ZL = "zl"
    IT = "it"
    CD = "cd"
    FG = "fg"
    GC = "gc"


EVA_TRANSCRIPTIONS: tuple[Transcription, ...] = (Transcription.ZL, Transcription.IT)


@dataclass(frozen=True)
class Paths:
    """Input and output locations. All local; no URLs."""

    repo_root: Path = REPO_ROOT
    eva_lines: Path = REPO_ROOT / "output" / "eva_lines.jsonl"
    pages: Path = REPO_ROOT / "output" / "metadata" / "pages.jsonl"
    folios: Path = REPO_ROOT / "output" / "metadata" / "folios.jsonl"
    quires: Path = REPO_ROOT / "output" / "metadata" / "quires.jsonl"
    mismatch_index: Path = REPO_ROOT / "output" / "mismatch_index.jsonl"
    reports_dir: Path = REPO_ROOT / "reports" / "phase1"
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
    # Phase 1 analysis budget.
    bootstrap_resamples: int = 200
    max_ngram_order: int = 5
    # "Running prose" subset (plan §3.6): paragraph lines on pages whose
    # illustration type does not imply circular or radial writing. No line-level
    # marker for circular text exists in the data, so the rule is page-level.
    prose_exclude_illustration: tuple[str, ...] = ("A", "C")
    # Phase 2 search ceiling, allocated per hypothesis by its declared share.
    search_budget_seconds: float = 7200.0
    # Surrogate replicates per null family. The empirical p-value cannot fall
    # below 1 / (nulls + 1), so this sets the resolution of every significance
    # claim in Phase 2: 3 replicates x 4 families floors p at 0.077.
    null_replicates: int = 3
    # Phase 3 round-2 ceiling: re-characterisation plus re-scoring the funded
    # hypotheses on each improved representation.
    round2_budget_seconds: float = 14400.0
    # Phase 4 calibration: how many words of synthetic ciphertext each keyed
    # hypothesis is attacked on, and the ceiling for the whole calibration run.
    calibration_words: int = 20000
    calibration_budget_seconds: float = 14400.0
    # A token whose reliability weight falls below this is dropped from the
    # "reliable" representation (plan §5.2.6).
    reliability_floor: float = 0.5
    # Phase 5 audit (plan §7). The key-instability battery re-searches every
    # keyed hypothesis under fresh seeds and under perturbed training subsets;
    # the ceiling truncates the battery rather than the run.
    audit_seeds: int = 6
    audit_subsets: int = 3
    audit_subset_fraction: float = 0.8
    audit_permutations: int = 1000
    audit_budget_seconds: float = 7200.0
    # Gallows glyphs, and the compounds built on them (plan §3.4).
    gallows: tuple[str, ...] = ("k", "t", "p", "f", "cth", "ckh", "cph", "cfh")


PATHS = Paths()
CONFIG = Config()
