# AGENTS.md

Guide for AI agents working in **voynich-data** (VCAT): data infrastructure for
computational study of the Voynich Manuscript. Two jobs live here — *building
trustworthy datasets* and *using them for analysis / code breaking*.

The repo's stance: **it does not claim to solve the manuscript.** Claims must be
falsifiable, reproducible, and stated with their uncertainty.

---

## Quick start

```bash
make venv        # uv sync --all-extras --all-groups && uv pip install -e .
make download    # scripts/fetch_sources.py -> data_sources/cache/
make build       # builders: eva_lines, metadata, mismatch_index -> output/
make corpora     # fetch_corpora.py -> data_sources/cache/corpora/ (reference baselines)
make phase0      # verify inputs + write output/translation/phase0_manifest.json
make test        # pytest (expect ~391 passed, 7 skipped)
make notebook    # jupyter lab
```

Before any PR (CI runs the same four):

```bash
ruff check . && black --check . && mypy vcat parsers builders validators hf translations && pytest tests/
```

Python 3.11+. Prefer `uv run <cmd>` over activating the venv.

---

## Layout

| Path | What it is |
| --- | --- |
| `vcat/` | Core lib: EVA charset, text processing, exceptions, logging |
| `parsers/` | `ivtff_parser.py` (IVTFF -> `Page`/`Locus`), `metadata_parser.py` |
| `builders/` | `build_eva_lines.py`, `build_metadata.py`, `build_mismatch_index.py` |
| `validators/` | Invariant checks, JSON-schema validation of outputs |
| `data_sources/` | `sources.yaml` (URLs + checksums), `cache/` raw IVTFF, `verify_sources.py` |
| `output/` | Built artifacts: `.jsonl` + `.parquet` + `SHA256SUMS` + manifests |
| `hf/`, `huggingface/` | Export code / published dataset cards |
| `translations/` | Analysis / decipherment / translation programme (plan 001). Tokenizer, strata, determinism, reference corpora, null models |
| `plans/` | Multi-phase work plans; `001_...md` carries the phase status table |
| `schemas/`, `docs/`, `notebooks/`, `scripts/`, `tests/` | as named |

Read first for context: `docs/data_model.md`, `docs/eva_alphabet.md`,
`docs/decisions.md`, `docs/charset_decisions.md`, `docs/sources.md`.

---

## Data you'll analyse

Load locally from `output/` (fast, exact) or from HF (`Ched-ai/voynich-eva`,
`voynich-manuscript-metadata`, `voynich-transcription-mismatch`).

**`eva_lines`** — 4,072 lines, ZL transcription. Key fields:
`line_id` (`f1r:1`), `page_id`, `line_number`, `text` (raw IVTFF),
`text_clean` (analysis-ready), `word_count`, `char_count`, `line_type`
(paragraph/label/circle/radius), `position`, `section`, `currier_language`
(A/B), `hand`, `quire`, `illustration_type`,
`has_uncertain|has_illegible|has_alternatives|has_high_ascii`.

**metadata** — `pages.jsonl` (226), `folios.jsonl` (102), `quires.jsonl` (18).
Contested fields use an uncertainty wrapper:
`{value, attribution, confidence, disputed, alternatives}`. Respect it.

**mismatch_index** — 4,072 rows aligning ZL/IT/CD/FG/GC per locus, with
`status`, `similarity_score`, `sources_present|missing`.

Words are `.`-separated in `text_clean` (`,` = possible boundary — decide
explicitly whether you treat it as a break, and say which you chose).

---

## Rules that keep the data honest

1. **Text processing is centralized.** All stripping/cleaning lives in
   `vcat/text_processing.py`. Import it; never re-implement regexes.
2. **The EVA charset is locked per version** (`docs/charset_decisions.md`).
   Changing it needs a decision-log entry + version bump.
3. **Data changes need provenance** — a source in `sources.yaml` (with
   checksum) or a documented decision.
4. **Source-faithful numbering.** Never renumber lines to make sources align;
   record disagreement in the mismatch index.
5. Methodology change => update the doc *and* the dataset card in the same PR.

---

## Analysis & code-breaking guidance

**The transcription is not the manuscript.** Only 29.3% of lines are identical
between the two major EVA transcriptions (ZL vs IT); 16.1% differ
substantively. Any single-transcription result inherits that noise.

Do this by default:

- **Replicate across sources.** Rerun a headline result on IT (and GC/FG where
  the alphabet permits). If it survives only in ZL, it's a transcription
  artifact, not a manuscript property.
- **Split the corpus.** Currier A vs B, hand, section, and `line_type` are
  strong confounds — A/B differ enough to behave like distinct systems. Report
  per-stratum numbers, not just corpus totals.
- **Positional effects are real.** Line-initial and line-final glyph
  distributions differ from mid-line ("line as a functional unit"); labels and
  circular text are not running prose. Exclude or model them deliberately.
- **EVA is a transcription convention, not glyph ground truth.** Compounds
  (`ch`, `sh`, `cth`, `ckh`, `cph`, `cfh`) are single visual units written as
  multiple ASCII chars; `iin`/`aiin` sequences are ambiguously segmented. State
  your tokenization (char / EVA-glyph / compound-aware) — results swing on it.
- **Filter uncertainty.** Consider dropping or flagging rows with
  `has_uncertain` / `has_illegible` / `has_alternatives`; `text_clean` keeps
  only the *first* option of `[a:b]`.
- **Use null models.** Shuffled text, order-n Markov surrogates, and
  length-matched natural-language / cipher baselines. "Voynichese has property
  X" means nothing without "and random/Latin/Vulgate does not."
- **Beware multiple comparisons.** Thousands of tested substitutions will
  produce a beautiful false positive. Fix hypotheses before scanning; correct
  p-values; hold out folios for validation.
- **Known landmarks to reproduce before trusting new code:** low conditional
  entropy (~h2 well below natural language), rigid word-internal glyph
  ordering / slot structure, Zipf-like word frequency with an odd
  low-vocabulary tail, high rate of near-repeat adjacent words, Currier A/B
  divergence. If your pipeline can't reproduce these, the bug is yours.
- **Report negative results.** A cleanly falsified hypothesis is a deliverable
  here. Write it into `docs/decisions.md`.
- Exploratory work goes in `notebooks/` or `scripts/`; anything that becomes a
  dependency of a dataset moves into `builders/`/`vcat/` with tests.

Existing starting points: `scripts/quick_analysis.py` (frequencies, A/B
vocabulary), `scripts/deep_analysis.py` (compression-based entropy bounds),
`notebooks/02_sanity_statistics.ipynb`.

**Use `translations/` for new analysis** rather than re-rolling primitives:
`translations.tokenize` is the only tokenizer (T0-char / T1-glyph, comma policy
explicit), `translations.strata` gives the per-line stratum table plus the
consensus subset and the frozen held-out page split, `translations.nulls` gives
surrogates and pseudo-Voynich generators, `translations.corpora` gives
checksum-verified non-Voynich baselines with sample-size matching, and
`translations.determinism` gives seeded RNGs and run manifests. Held-out pages
(`StratumRow.is_holdout`) must not feed any key search.

---

## Python coding style — Simplicity First

- If requirements are ambiguous, **ask before implementing**.
- Write simple, clean, maintainable, minimal code.
- Don't over-complicate or over-engineer.
- If you wrote 200 lines and it could be 50, rewrite it.
- No error handling for impossible scenarios.
- No "flexibility" or "configurability" that wasn't requested.
- Self-check before finishing: *"Would a senior engineer call this
  overcomplicated?"* If yes, simplify.

Repo conventions: line length 100, `black` + `ruff` (E/W/F/I/B/C4/UP), full type
annotations (`mypy` runs with `disallow_untyped_defs`), `from __future__ import
annotations`, `pathlib` over `os.path`, dataclasses for records, module-level
`get_logger(__name__)` from `vcat.logging`, custom exceptions from
`vcat.exceptions` over bare `Exception`.

## Chat style

Extremely concise. Sacrifice grammar for concision. No preamble, no recap.

## Delegation

For coding tasks, use judgement to pick an appropriate **lower-power model** and
run it in a subagent.
