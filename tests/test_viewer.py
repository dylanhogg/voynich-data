"""The two rendered HTML views: payload integrity, banner, determinism."""

from __future__ import annotations

import json

import pytest

from viewer.build import TEMPLATES, render
from viewer.data import BANDS, GATE, LINES_PATH, build_payload
from viewer.iiif import image_url, load_map

pytestmark = pytest.mark.skipif(
    not LINES_PATH.exists(), reason="Phase 4 not run yet; run `make calibrate && make translate`"
)


@pytest.fixture(scope="module")
def payload():
    return build_payload()


def test_payload_covers_every_line(payload):
    assert sum(len(page["lines"]) for page in payload.pages) == 4072
    assert payload.stats["declared_unsuccessful"] is True


def test_gate_matches_the_committed_coverage(payload):
    tokens = [tok for page in payload.pages for line in page["lines"] for tok in line[6]]
    gated = sum(1 for tok in tokens if tok[3] >= GATE) / len(tokens)
    assert gated == pytest.approx(payload.stats["overall"]["gated_coverage"], abs=5e-4)


def test_bands_are_the_pipeline_bands():
    assert BANDS == {"none": 0, "low": 1, "medium": 2, "high": 3}


def test_every_page_resolves_to_a_folio_image(payload):
    assert all(page["plate"] for page in payload.pages)
    assert image_url(load_map(), "f68r2", 400).endswith("/full/!400,400/0/default.jpg")


def test_views_are_self_contained_and_bannered(payload, tmp_path):
    written = render(payload, tmp_path)
    assert {path.name for path in written} == set(TEMPLATES)
    for path in written:
        html = path.read_text()
        assert "FAILED VALIDATION" in html
        assert "</script" not in html.split('id="payload"')[1].split("</script>")[0]
        assert (
            json.loads(
                html.split('type="application/json">')[1]
                .split("</script>")[0]
                .replace("<\\/", "</")
            )["stats"]["control_ratio"]
            > 1
        )


def test_render_is_byte_stable(payload, tmp_path):
    first = [path.read_bytes() for path in render(payload, tmp_path / "a")]
    second = [path.read_bytes() for path in render(build_payload(), tmp_path / "b")]
    assert first == second
