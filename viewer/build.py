"""Render the two browser-loadable HTML views of the translation output.

    uv run python -m viewer.build [--out DIR]

Both files are single, self-contained HTML documents (the only external
requests are Beinecke IIIF folio images and Google Fonts) and are byte-stable
for a given set of input artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from vcat.logging import get_logger
from viewer.data import ROOT, Payload, build_payload

logger = get_logger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
DEFAULT_OUT = ROOT / "output" / "viewer"
TEMPLATES = {
    "workbench.html": "workbench.html.j2",
    "manuscript.html": "manuscript.html.j2",
    "voynich_reading.md": "reading.md.j2",
    "voynich_clean.md": "clean.md.j2",
}


def _escape_html_only(name: str | None) -> bool:
    """Markdown templates must not be HTML-escaped."""
    return name is not None and name.endswith(".html.j2")


def render(payload: Payload, out_dir: Path) -> list[Path]:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        undefined=StrictUndefined,
        autoescape=_escape_html_only,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    payload_json = payload.as_json().replace("</", "<\\/")
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, template in TEMPLATES.items():
        path = out_dir / name
        path.write_text(
            env.get_template(template).render(
                payload_json=payload_json,
                banner=payload.banner,
                hypothesis=payload.hypothesis,
                stats=payload.stats,
                sections=payload.sections,
                pages=payload.pages,
                page_count=len(payload.pages),
            )
        )
        logger.info("Wrote view", path=str(path), kb=round(path.stat().st_size / 1024))
        written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    render(build_payload(), args.out)


if __name__ == "__main__":
    main()
