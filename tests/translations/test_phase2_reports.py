"""The committed Phase 2 artifacts: candidates, reports, manifest."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from translations.config import SPECULATIVE_BANNER
from translations.phase2 import CANDIDATES, MANIFEST_PATH, REPORTS

pytestmark = pytest.mark.skipif(
    not (REPORTS / "hypothesis_scores.md").exists(),
    reason="Phase 2 not run yet; run `make decipher`",
)


@pytest.mark.parametrize("topic", ["hypothesis_scores", "synthetic_validation", "approach"])
def test_each_report_carries_the_banner(topic: str) -> None:
    assert SPECULATIVE_BANNER in (REPORTS / f"{topic}.md").read_text()
    assert json.loads((REPORTS / f"{topic}.json").read_text())["banner"] == SPECULATIVE_BANNER


def test_candidates_include_losers_and_null_runs() -> None:
    frame = pd.read_parquet(CANDIDATES)
    assert len(frame) > 20
    families = {name.rsplit("_r", 1)[0] for name in frame["corpus"].unique()}
    assert families >= {"real", "grille", "selfcite", "shuffle_chars", "markov_chars"}
    assert set(frame["split"]) == {"train", "holdout"}
    assert {"budget_spent_s", "converged", "truncated", "gain_per_token"} <= set(frame.columns)


def test_each_null_family_has_several_seeded_replicates() -> None:
    frame = pd.read_parquet(CANDIDATES)
    nulls = [name for name in frame["corpus"].unique() if name != "real"]
    for family in ("grille", "selfcite", "shuffle_chars", "markov_chars"):
        replicates = [name for name in nulls if name.startswith(family)]
        assert len(replicates) >= 3, family


def test_every_funded_hypothesis_has_a_null_distribution() -> None:
    summary = json.loads((REPORTS / "hypothesis_scores.json").read_text())["summary"]
    for name, row in summary.items():
        assert row["null"]["nulls"], name
        assert 0 < row["null"]["p_value"] <= 1


def test_held_out_pages_were_scored_once_per_hypothesis() -> None:
    frame = pd.read_parquet(CANDIDATES)
    holdout = frame[frame["split"] == "holdout"]
    assert len(holdout) == holdout["hypothesis"].nunique()


def test_synthetic_validation_recovered_its_own_keys() -> None:
    data = json.loads((REPORTS / "synthetic_validation.json").read_text())["recoveries"]
    assert {row["scheme"] for row in data} == {"substitution", "verbose", "abjad"}
    assert all(row["token_accuracy"] > 0.9 for row in data)


def test_manifest_records_the_budget_and_the_registered_grid() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["phase"] == 2
    assert len(manifest["hypotheses"]) == 10
    assert manifest["budget"]["ceiling_s"] > 0
    assert manifest["candidates"] > 20
