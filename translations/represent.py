"""Representations of the manuscript carried into Phase 3 (plan §5.2.1, §5.2.8).

Phase 1 and Phase 2 both worked on one representation: ``T1-glyph`` words of
the ZL transcription. Phase 3 asks whether the Phase 2 shortlist changes the
picture, which means re-running the analysis on the *representations those
hypotheses imply*:

``raw``
    the Phase 1/2 representation, kept as the control.
``merged``
    ``T3-merge``: the converged merge partition H2 found. If verbose encipherment
    is real, this is closer to the plaintext's unit stream than ``raw`` is.
``reliable``
    the same units, with tokens the alignment model distrusts dropped. If a
    landmark is an artifact of transcription noise, it should move here.

A representation is just a ``View -> View`` function plus provenance, so any
Phase 1 estimator or Phase 2 search runs on it unchanged.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from translations.alignment import TokenRow
from translations.analysis.common import View
from translations.config import CONFIG, PATHS
from translations.tokenize import Merges, apply_merges, glyphs
from vcat.exceptions import ConfigurationError

CANDIDATES = PATHS.repo_root / "output" / "decipher" / "candidates.parquet"


@dataclass(frozen=True)
class Representation:
    """A named re-tokenisation of a view, with the provenance of its induction."""

    name: str
    transform: Callable[[View], View]
    origin: str
    detail: dict[str, Any] = field(default_factory=dict)

    def __call__(self, view: View) -> View:
        """Apply the representation to a view."""
        return self.transform(view)


def identity() -> Representation:
    """The Phase 1/2 representation, unchanged."""
    return Representation(
        name="raw",
        transform=lambda view: view,
        origin="Phase 1 tokenization contract (T1-glyph, CB=break, ZL)",
    )


def merged(merges: Merges, origin: str, detail: dict[str, Any] | None = None) -> Representation:
    """``T3-merge``: glyph groups treated as single units."""

    def transform(view: View) -> View:
        lines = [[apply_merges(word, merges) for word in line] for line in view.lines]
        return View(name=f"{view.name}|merged", lines=lines, rows=view.rows)

    return Representation(
        name="merged",
        transform=transform,
        origin=origin,
        detail={"merges": ["".join(merge) for merge in merges], **(detail or {})},
    )


def reliable(rows: list[TokenRow], threshold: float = CONFIG.reliability_floor) -> Representation:
    """Drop tokens whose reliability weight falls below ``threshold``.

    Filtering is by ``(line_id, token_index)``, so it applies to any view that
    still carries its stratum rows; views without them are passed through
    unchanged rather than silently mis-filtered.
    """
    drop = {(row.line_id, row.token_index) for row in rows if row.reliability < threshold}

    def transform(view: View) -> View:
        if not view.rows:
            return view
        lines = [
            [word for index, word in enumerate(line) if (row.line_id, index) not in drop]
            for line, row in zip(view.lines, view.rows, strict=True)
        ]
        keep = [(line, row) for line, row in zip(lines, view.rows, strict=True) if line]
        return View(
            name=f"{view.name}|reliable",
            lines=[line for line, _ in keep],
            rows=[row for _, row in keep],
        )

    return Representation(
        name="reliable",
        transform=transform,
        origin="Phase 3 token reliability model (translations/alignment.py)",
        detail={"threshold": threshold, "tokens_dropped": len(drop)},
    )


def phase2_merges(candidates_path: Path | None = None) -> tuple[Merges, dict[str, Any]]:
    """The best *converged* merge partition Phase 2 committed to.

    Phase 2's top-scoring H2 variants were the wide fixed-width channels, which
    are large codebooks and did not converge across restarts (plan 001, Phase 2
    delta 13). A partition nobody converged on is not a representation worth
    carrying, so the choice here is the best converged searched-merge run.
    """
    import pandas as pd

    frame = pd.read_parquet(candidates_path or CANDIDATES)
    subset = frame[
        (frame["hypothesis"] == "H2")
        & (frame["corpus"] == "real")
        & (frame["split"] == "train")
        & frame["variant"].str.contains("searched-merges")
        & frame["converged"]
    ]
    if subset.empty:
        raise ConfigurationError("No converged H2 merge run", {"path": str(candidates_path)})
    best = subset.loc[subset["gain_per_token"].idxmax()]
    forms = json.loads(str(best["merges"]).replace("'", '"'))
    return tuple(tuple(glyphs(form)) for form in forms), {
        "variant": str(best["variant"]),
        "gain_per_token": float(best["gain_per_token"]),
        "n_merges": len(forms),
    }
