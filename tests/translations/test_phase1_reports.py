"""The committed Phase 1 artifacts: present, banner-carrying, gate green."""

from __future__ import annotations

import json

import pytest

from translations.config import PATHS, SPECULATIVE_BANNER
from translations.phase1 import MANIFEST_PATH, SLOT_MODEL_PATH, TOPICS

TOPIC_NAMES = [module.__name__.rsplit(".", 1)[-1] for module in TOPICS] + ["landmarks"]

pytestmark = pytest.mark.skipif(
    not (PATHS.reports_dir / "summary.md").exists(),
    reason="Phase 1 not run yet; run `make analyse1`",
)


@pytest.mark.parametrize("topic", TOPIC_NAMES)
def test_each_topic_has_both_artifacts(topic: str) -> None:
    markdown = PATHS.reports_dir / f"{topic}.md"
    payload = PATHS.reports_dir / f"{topic}.json"
    assert SPECULATIVE_BANNER in markdown.read_text()
    assert json.loads(payload.read_text())["banner"] == SPECULATIVE_BANNER


def test_landmark_gate_is_green() -> None:
    data = json.loads((PATHS.reports_dir / "landmarks.json").read_text())
    assert data["passed"] is True
    assert len(data["landmarks"]) == 6


def test_manifest_records_inputs_and_tuning() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["phase"] == 1
    assert "output/eva_lines.jsonl" in manifest["inputs"]
    assert manifest["pseudo_tuning"]["grille"]["name"].startswith("pseudo|grille")
    assert "time" not in json.dumps(manifest)


def test_slot_model_is_recorded_for_t2() -> None:
    model = json.loads(SLOT_MODEL_PATH.read_text())
    assert model["prefixes"] or model["suffixes"]
    assert model["source_view"] == "voynich|base"
