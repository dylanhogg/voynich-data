"""Phase 0 entrypoint: verify inputs, summarise the corpus, write a run manifest.

Run twice, the emitted manifest must be byte-identical — that is the
determinism acceptance test for Phase 0 (plan §2.2, §2.6).

    uv run python -m translations.phase0
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from typing import Any

from translations.config import CONFIG, PATHS, CommaPolicy, Tokenizer, Transcription
from translations.corpora import load_corpus, load_specs
from translations.determinism import sha256_file, write_manifest
from translations.io import load_lines, load_mismatches, transcription_text
from translations.strata import StratumRow, build_strata, group_by
from translations.tokenize import split_words, unit_stream
from vcat.logging import get_logger

logger = get_logger(__name__)

MANIFEST_PATH = PATHS.output_dir / "phase0_manifest.json"

# The reporting grid: no headline number is ever a single number (plan §2.3).
GRID: tuple[tuple[Tokenizer, CommaPolicy, Transcription], ...] = tuple(
    (tokenizer, comma, transcription)
    for tokenizer in (Tokenizer.T0_CHAR, Tokenizer.T1_GLYPH)
    for comma in (CommaPolicy.BREAK, CommaPolicy.JOIN)
    for transcription in (Transcription.ZL, Transcription.IT)
)


def corpus_grid() -> dict[str, dict[str, int]]:
    """Token and unit counts for every cell of the tokenization grid."""
    lines = load_lines()
    mismatches = load_mismatches()
    grid: dict[str, dict[str, int]] = {}
    for tokenizer, comma, transcription in GRID:
        texts = [
            text
            for line in lines
            if (text := transcription_text(line, mismatches.get(line.line_id), transcription))
        ]
        grid[f"{tokenizer}|{comma}|{transcription}"] = {
            "lines": len(texts),
            "words": sum(len(split_words(text, comma)) for text in texts),
            "units": sum(len(unit_stream(text, tokenizer, comma)) for text in texts),
        }
    return grid


def strata_summary(rows: list[StratumRow]) -> dict[str, Any]:
    """Line counts per stratum, plus the consensus and held-out subsets."""
    summary: dict[str, Any] = {
        field: {key: len(group) for key, group in group_by(rows, field).items()}
        for field in ("currier_language", "section", "line_type", "hand", "quire_id")
    }
    summary["consensus_lines"] = sum(row.in_consensus for row in rows)
    summary["holdout_lines"] = sum(row.is_holdout for row in rows)
    summary["holdout_pages"] = len({row.page_id for row in rows if row.is_holdout})
    summary["pages"] = len({row.page_id for row in rows})
    summary["mismatch_status"] = dict(sorted(Counter(row.mismatch_status for row in rows).items()))
    return summary


def corpora_summary() -> dict[str, Any]:
    """Per-corpus checksum status and normalised size."""
    summary: dict[str, Any] = {}
    for spec in load_specs():
        present = spec.path.exists()
        entry: dict[str, Any] = {
            "group": spec.group,
            "language": spec.language,
            "kind": spec.kind,
            "present": present,
            "checksum_ok": present and sha256_file(spec.path) == spec.sha256,
        }
        if present and entry["checksum_ok"] and spec.is_text:
            corpus = load_corpus(spec.corpus_id)
            entry["words"] = corpus.n_words
            entry["chars"] = corpus.n_chars
        summary[spec.corpus_id] = entry
    return summary


def main() -> int:
    """Write the Phase 0 manifest; non-zero exit if a corpus failed verification."""
    PATHS.output_dir.mkdir(parents=True, exist_ok=True)
    corpora = corpora_summary()
    rows = build_strata()

    manifest = write_manifest(
        MANIFEST_PATH,
        inputs=[PATHS.eva_lines, PATHS.pages, PATHS.mismatch_index, PATHS.sources_yaml],
        extra={
            "phase": 0,
            "defaults": {
                "tokenizer": str(CONFIG.default_tokenizer),
                "comma_policy": str(CONFIG.default_comma_policy),
                "transcription": str(CONFIG.default_transcription),
            },
            "tokenization_grid": corpus_grid(),
            "strata": strata_summary(rows),
            "corpora": corpora,
        },
    )
    print(json.dumps(manifest["strata"], indent=2, sort_keys=True))
    print(f"\nManifest: {MANIFEST_PATH}")

    unverified = sorted(
        corpus_id for corpus_id, entry in corpora.items() if not entry["checksum_ok"]
    )
    if unverified:
        print(f"Corpora missing or failing checksum: {', '.join(unverified)} (run `make corpora`)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
