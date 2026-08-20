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


def test_prose_keeps_every_gated_gloss_in_order(payload):
    """Paragraph blocks in block order, then the label lines; nothing added or dropped."""
    for page in payload.pages:
        ordered = [line for line in page["lines"] if not line[4]] + [
            line for line in page["lines"] if line[4]
        ]
        glosses = [
            token[2] for line in ordered for token in line[6] if token[3] >= GATE and token[2]
        ]
        spans = [run for block in page["prose"] for run in block["runs"] if isinstance(run, str)]
        assert " ".join(spans).lower() == " ".join(glosses).lower()


def test_html_views_are_self_contained_and_bannered(payload, tmp_path):
    written = {path.name: path for path in render(payload, tmp_path)}
    assert set(written) == set(TEMPLATES)
    for name in ("workbench.html", "manuscript.html"):
        html = written[name].read_text()
        assert "FAILED VALIDATION" in html
        blob = html.split('type="application/json">')[1].split("</script>")[0]
        assert "</script" not in blob
        assert json.loads(blob.replace("<\\/", "</"))["stats"]["control_ratio"] > 1


def test_markdown_views_carry_the_notice_and_the_right_scaffolding(payload, tmp_path):
    written = {path.name: path for path in render(payload, tmp_path)}
    reading = written["voynich_reading.md"].read_text()
    clean = written["voynich_clean.md"].read_text()
    assert payload.banner in reading
    assert "75.1%" in reading and "75.1%" in clean
    assert reading.count("\n## Folio ") == len(payload.pages)
    assert "**Illustration:**" in reading and "[…×" in reading
    assert "## Folio" not in clean and "[…" not in clean and "**Label:**" not in clean
    assert "…" in clean


def test_render_is_byte_stable(payload, tmp_path):
    first = [path.read_bytes() for path in render(payload, tmp_path / "a")]
    second = [path.read_bytes() for path in render(build_payload(), tmp_path / "b")]
    assert first == second
