"""The committed Phase 4 artifacts: rows, reports, calibration, determinism."""

from __future__ import annotations

import hashlib
import json
import random

import pandas as pd
import pytest

from translations.analysis.common import View
from translations.calibrate import CALIBRATION_PATH, CalibrationMap, load_maps
from translations.config import FAILED_VALIDATION_BANNER, active_banner
from translations.decode import CANDIDATES, RANKING, TRANSLATOR_CONFIG, keyed_hypotheses
from translations.lexicon import whitakers
from translations.phase4 import (
    LEXICON_PATH,
    LINES_JSONL,
    LINES_PARQUET,
    MANIFEST_PATH,
    REPORTS,
    SUMS_PATH,
)
from translations.pipeline import GlossCache, translate
from translations.render import GATED_MASK

pytestmark = pytest.mark.skipif(
    not LINES_JSONL.exists(), reason="Phase 4 not run yet; run `make calibrate && make translate`"
)


@pytest.fixture(scope="module")
def banner() -> str:
    """The banner this run's own control verdict requires (plan §7.4)."""
    verdict = json.loads((REPORTS / "coverage.json").read_text())
    return active_banner(bool(verdict["validation_failed"]))


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    """The committed translation rows."""
    return [json.loads(line) for line in LINES_JSONL.read_text().splitlines() if line.strip()]


def test_every_manuscript_line_is_rendered(rows: list[dict], banner: str) -> None:
    assert len(rows) == 4072
    assert all(row["english_speculative"] for row in rows if row["tokens"])
    assert all(row["banner"] == banner for row in rows)


def test_gated_view_masks_everything_below_the_medium_band(rows: list[dict]) -> None:
    for row in rows:
        expected = [
            (
                token["chosen"]
                if token["band"] in ("high", "medium") and token["chosen"]
                else GATED_MASK
            )
            for token in row["tokens"]
        ]
        assert row["english_gated"] == " ".join(expected)


def test_every_token_traces_back_to_a_glyph_sequence(rows: list[dict]) -> None:
    tokens = [token for row in rows for token in row["tokens"]]
    assert len(tokens) == 33728
    assert all(token["surface"] for token in tokens)
    assert all(0.0 <= token["confidence"] <= 1.0 for token in tokens)
    assert all(token["null_p"] >= 1 / 21 for token in tokens)


def test_parquet_carries_every_keyed_hypothesis() -> None:
    frame = pd.read_parquet(LINES_PARQUET)
    assert set(frame["hypothesis_id"]) == {"H1", "H2", "H3", "H4", "H7"}
    assert len(frame) == 4072 * 5


def test_lexicon_holds_the_candidates_the_rows_omit(banner: str) -> None:
    entries = [json.loads(line) for line in LEXICON_PATH.read_text().splitlines() if line.strip()]
    assert entries
    assert all(
        {"voynich_type", "intermediate", "glosses", "support"} <= set(row) for row in entries
    )
    assert all(row["banner"] == banner for row in entries)


@pytest.mark.parametrize("topic", ["coverage", "calibration"])
def test_each_report_carries_the_banner(topic: str, banner: str) -> None:
    assert banner in (REPORTS / f"{topic}.md").read_text()
    assert json.loads((REPORTS / f"{topic}.json").read_text())["banner"] == banner


def test_folio_readings_repeat_the_banner_on_every_page(banner: str) -> None:
    text = (REPORTS / "folio_readings.md").read_text()
    assert text.count("## f") == text.count(banner) - 1  # one banner at the top


def test_coverage_report_leads_with_the_control_comparison() -> None:
    data = json.loads((REPORTS / "coverage.json").read_text())
    assert set(data["controls"]) == {"real", "grille", "selfcite"}
    body = (REPORTS / "coverage.md").read_text()
    assert body.index("Pseudo-Voynich control") < body.index("Every keyed hypothesis")


def test_manifest_carries_no_wall_clock() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["phase"] == 4
    assert "timestamp" not in manifest and "elapsed" not in manifest
    assert manifest["inputs"]


def test_checksums_match_the_artifacts_on_disk() -> None:
    for line in SUMS_PATH.read_text().splitlines():
        digest, name = line.split("  ")
        path = SUMS_PATH.parent / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name


def test_calibration_covers_every_rendered_hypothesis() -> None:
    maps = load_maps()
    keyed = keyed_hypotheses(CANDIDATES, RANKING, TRANSLATOR_CONFIG)
    assert {entry.hypothesis_id for entry in keyed} <= set(maps)
    assert all(isinstance(value, CalibrationMap) for value in maps.values())
    assert all(list(value.accuracy) == sorted(value.accuracy) for value in maps.values())


def test_calibration_reliability_diagram_tracks_the_map() -> None:
    for value in load_maps().values():
        for row in value.diagram:
            assert abs(row["predicted"] - row["observed"]) < 0.1


def test_the_run_is_byte_stable() -> None:
    """Two runs of the pipeline on the same input produce identical rows."""
    lexicon = whitakers.build_lexicon([whitakers.Entry("ab", ("ab",), "N", "A", ("thing",))])
    entry = keyed_hypotheses(CANDIDATES, RANKING, TRANSLATOR_CONFIG)[0]
    view = View(name="t", lines=[[list("xy"), list("yx")]])
    fitted = CalibrationMap("H1", (0.0, 1.0), (0.0, 1.0), 4, 1.0, 1.0, "latin", "substitution")
    runs = [
        [
            line.as_dict(entry, FAILED_VALIDATION_BANNER)
            for line in translate(
                view, entry, GlossCache(lexicon), fitted, {}, {}, {}, random.Random(11)
            )
        ]
        for _ in range(2)
    ]
    assert json.dumps(runs[0], sort_keys=True) == json.dumps(runs[1], sort_keys=True)


def test_calibration_file_records_the_sample_size() -> None:
    data = json.loads(CALIBRATION_PATH.read_text())
    assert data["words"] > 0
    assert set(data["maps"]) >= {"H1", "H2", "H3", "H4", "H7"}
