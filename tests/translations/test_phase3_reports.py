"""The committed Phase 3 artifacts: reports, alignment table, manifest, config."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from translations.alignment import ALIGNMENT_PATH
from translations.config import SPECULATIVE_BANNER
from translations.phase3 import CANDIDATES, MANIFEST_PATH, REPORTS, TRANSLATOR_CONFIG

ANALYSIS_TOPICS = (
    "gap_analysis",
    "reliability",
    "recharacterise",
    "paradigms",
    "distribution",
    "labels",
)

pytestmark = pytest.mark.skipif(
    not (REPORTS / "gap_analysis.md").exists(),
    reason="Phase 3 not run yet; run `make analyse2`",
)


@pytest.mark.parametrize("topic", ANALYSIS_TOPICS)
def test_each_report_carries_the_banner(topic: str) -> None:
    assert SPECULATIVE_BANNER in (REPORTS / f"{topic}.md").read_text()
    assert json.loads((REPORTS / f"{topic}.json").read_text())["banner"] == SPECULATIVE_BANNER


def test_alignment_table_has_one_row_per_zl_token() -> None:
    frame = pd.read_parquet(ALIGNMENT_PATH)
    assert len(frame) == 33728
    assert {"line_id", "token_index", "agreement", "reliability"} <= set(frame.columns)
    assert frame["reliability"].between(0.0, 1.0).all()


def test_gap_register_records_open_gaps_as_well_as_closed() -> None:
    data = json.loads((REPORTS / "gap_analysis.json").read_text())
    assert data["counts"]["closed"] >= 3
    assert data["counts"]["open"] >= 1
    assert all(
        {"gap", "remedy", "cost", "provenance", "status"} <= set(row) for row in data["gaps"]
    )


def test_recharacterisation_compares_every_representation() -> None:
    data = json.loads((REPORTS / "recharacterise.json").read_text())
    assert set(data["inside_counts"]) == {"raw", "merged", "reliable"}
    metrics = {row["metric"] for row in data["verdicts"]}
    assert metrics == set(data["natural_band"])
    # Every representation is scored on every metric, not only where it looks good.
    assert all({"raw", "merged", "reliable"} <= set(row) for row in data["verdicts"])


@pytest.mark.skipif(not CANDIDATES.exists(), reason="re-scoring skipped (--analysis-only)")
def test_round2_candidates_record_the_representation() -> None:
    frame = pd.read_parquet(CANDIDATES)
    assert set(frame["representation"]) == {"merged", "reliable"}
    assert set(frame["split"]) == {"train", "holdout"}


@pytest.mark.skipif(not MANIFEST_PATH.exists(), reason="Phase 3 manifest missing")
def test_manifest_carries_no_wall_clock() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["phase"] == 3
    assert "timestamp" not in manifest and "elapsed" not in manifest
    assert manifest["inputs"]


@pytest.mark.skipif(not TRANSLATOR_CONFIG.exists(), reason="translator config missing")
def test_translator_config_states_that_the_model_lost() -> None:
    configuration = json.loads(TRANSLATOR_CONFIG.read_text())
    assert configuration["anchors"] == []
    assert "losing model" in configuration["warning"]
    assert configuration["best_scoring"]["beat_every_null"] is False


def test_translator_config_chooses_a_converged_candidate_with_a_key() -> None:
    chosen = json.loads(TRANSLATOR_CONFIG.read_text())["chosen"]
    assert chosen is not None
    assert chosen["gain_per_token"] < 0
    assert chosen["key"].startswith("{")
