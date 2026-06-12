# Contributing to voynich-data

Thanks for your interest! This project aims to be boring in the best way:
reproducible builds, validated data, documented decisions.

## Getting set up

```bash
git clone https://github.com/noah-chelednik/voynich-data.git
cd voynich-data
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/fetch_sources.py
```

## Before submitting a PR

```bash
ruff check .          # lint
black --check .       # formatting
mypy vcat parsers builders validators hf   # types
pytest tests/         # tests (expect 343 passed, 7 skipped)
```

All four must pass — CI runs the same checks.

## Ground rules

- **Data changes need provenance.** Any change to dataset content must trace
  back to a source file in `data_sources/sources.yaml` (with checksum) or a
  documented decision in `docs/decisions.md`.
- **Text processing is centralized.** All cleaning/stripping logic lives in
  `vcat/text_processing.py`. Do not duplicate it — builders and validators
  must use identical rules.
- **The EVA charset is locked** (see `docs/charset_decisions.md`). Charset
  changes require a decision-log entry and a version bump.
- **Methodology changes get documented.** If you change how something is
  computed (e.g., the mismatch categories), update the relevant doc and
  dataset card in the same PR.

## Reporting issues

- Data errors: include the `line_id` (e.g., `f1r:5`) and the source you
  checked against.
- Licensing/attribution concerns: see
  [docs/SOURCES_LICENSE.md](docs/SOURCES_LICENSE.md) — these are acted on
  promptly.
