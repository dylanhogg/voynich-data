# Getting Started

A guide for developers and code crackers joining `voynich-data`.

Read this first, then `docs/data_model.md` and `docs/decisions.md`.

---

## 1. What this repo does

`voynich-data` is the **data layer** of the Voynich Computational Analysis
Toolkit (VCAT). It turns scholarly transcriptions of the Voynich Manuscript
(Beinecke MS 408) into **versioned, checksummed, schema-validated datasets**
that anyone can load and analyse reproducibly.

It does four things:

1. **Fetches** transcription source files from their canonical URLs and pins
   them by SHA256.
2. **Parses** them (IVTFF format) into structured page / line records.
3. **Builds** three published datasets from those records.
4. **Validates** everything — JSON Schema, EVA charset rules, and build
   invariants — before anything ships.

The headline product is a corpus of **4,072 EVA transcription lines across 226
pages**, plus codicological metadata and a cross-transcription disagreement
index.

The repo takes an explicit position, stated in the README and worth repeating:
*it does not claim to solve the manuscript.* Its job is to make sure that when
you do run an analysis, you know exactly which bytes you ran it on.

---

## 2. Datasets

### 2.1 Source transcriptions (inputs)

Five independent scholarly transcriptions, defined in
`data_sources/sources.yaml`, downloaded to `data_sources/cache/`, and hash-pinned
in `data_sources/checksums_all.txt`:

| Code | Transcriber | Alphabet | Lines | Role |
|------|-------------|----------|-------|------|
| **ZL** | Zandbergen–Landini | EVA | 4,072 | **Primary reference** — most complete, IVTFF 2.0, actively maintained |
| **IT** | Takeshi Takahashi | EVA | 4,069 | Secondary EVA, used for the mismatch comparison |
| **CD** | Currier / D'Imperio | Currier | 2,154 | Historical, partial |
| **FG** | First Study Group (Friedman) | FSG | 3,980 | 1940s punch-card transcription |
| **GC** | Glen Claston | v101 | 4,070 | Higher glyph granularity than EVA |

ZL was chosen as primary in `docs/decisions.md` (Decision 1). Everything else is
comparison material.

### 2.2 Built datasets (outputs)

Written to `output/` as both JSONL (canonical, hash-guaranteed) and Parquet
(content-equivalent convenience copy), and published to Hugging Face under
`Ched-ai/`:

| Dataset | Records | What it is |
|---------|---------|------------|
| `voynich-eva` | 4,072 lines | Line-level EVA transcription from ZL. Schema: `schemas/transcription_lines.schema.json` |
| `voynich-manuscript-metadata` | 226 pages / 102 folios / 18 quires | Codicological structure: section, Currier language, hand, illustration type, quire, foldout panels |
| `voynich-transcription-mismatch` | 4,072 records | Line-by-line comparison across all five sources. Schema: `schemas/mismatch_index.schema.json` |

A line record looks like this:

```json
{
  "line_id": "f1r:1", "page_id": "f1r", "line_number": 1, "line_index": 1,
  "text": "<%>fachys.ykal.ar.ataiin.shol.shory.[cth:oto]res.y.kor.sholdy<!@254;>",
  "text_clean": "fachys.ykal.ar.ataiin.shol.shory.cthres.y.kor.sholdy",
  "line_type": "paragraph", "position": "@", "quire": "A", "section": "text_only",
  "currier_language": "A", "hand": "1", "illustration_type": "T",
  "source": "zandbergen_landini", "source_version": "bf5b6d4ac1e3",
  "char_count": 43, "word_count": 10,
  "has_uncertain": false, "has_illegible": false,
  "has_alternatives": true, "has_high_ascii": true
}
```

Two fields deserve attention before you write any analysis:

- **`text` vs `text_clean`.** `text` is source-faithful, markup and all.
  `text_clean` has IVTFF markup stripped by
  `vcat/text_processing.py:strip_ivtff_markup` — the single source of truth,
  shared by builders and validators so they can never diverge. Analyse
  `text_clean`; cite `text`.
- **The `has_*` flags.** They tell you where the transcriber was unsure. Filtering
  on them is usually the difference between a result and an artefact.

### 2.3 The disagreement problem

The mismatch dataset exists because **the two major EVA transcriptions do not
agree**:

| Category | Lines | Share |
|----------|-------|-------|
| Exact match | 901 | 22.1% |
| Match after normalisation | 293 | 7.2% |
| High similarity (≥95%, not identical) | 2,220 | 54.6% |
| Substantive disagreement (<95%) | 655 | 16.1% |

Only **29.3%** of lines are identical even after stripping uncertainty markup.
Any single-transcription result inherits that noise floor. If your finding
disappears when you re-run it against IT instead of ZL, it was never a finding.

---

## 3. Scope

**In scope:**

- Source acquisition, verification, and checksum pinning
- IVTFF and metadata parsing
- Dataset construction, schema validation, invariant checking
- Hugging Face export, dataset cards, provenance and licensing documentation
- Sanity statistics and exploratory scripts (`scripts/`, `notebooks/`)

**Out of scope (deliberately):**

- Decipherment claims, proposed plaintexts, or translations
- Statistical analysis tooling → planned repo **`voynich-analysis`**
- Hypothesis-testing frameworks → planned repo **`voynich-hypotheses`**
- Manuscript images (the Beinecke IIIF manifest is referenced, not mirrored)

The repo tracks its own maturity as "Horizon 1", which is **complete**: all three
datasets are built, validated, and published. `docs/progress.md` has the full
definition-of-done. Anything analytical belongs downstream.

**Three ground rules** (from `CONTRIBUTING.md`) that PRs are held to:

1. **Data changes need provenance.** Trace to a source in `sources.yaml` (with
   checksum) or a documented decision in `docs/decisions.md`.
2. **Text processing is centralised.** All cleaning lives in
   `vcat/text_processing.py`. Never duplicate it.
3. **The EVA charset is locked** per version (`docs/charset_decisions.md`).
   Changing it requires a decision-log entry *and* a version bump.

---

## 4. Architecture

Data flows one way, left to right:

```
sources.yaml + checksums
        │  scripts/fetch_sources.py  (download, verify SHA256, fail hard)
        ▼
data_sources/cache/*.txt        ZL3b-n, IT_ivtff_1a, CD2a-n, FG2a-n, GC2a-n
        │  parsers/
        ▼
Page / Locus / PageVariables    ivtff_parser.py
PageRecord / FolioRecord /      metadata_parser.py
QuireRecord
        │  builders/            (uses vcat/ for charset + text cleaning)
        ▼
output/*.jsonl + *.parquet + build reports + SHA256SUMS
        │  validators/          (schema, invariants, release checks)
        ▼
hf/export.py → huggingface/    → Hugging Face Hub
```

### Package map

| Package | Responsibility | Key entry points |
|---------|----------------|------------------|
| `vcat/` | Core library. Charset definitions, text processing, exceptions, logging. Imported by everything else. | `charset.py` (locked charset — single source of truth), `text_processing.py` (`strip_ivtff_markup`, `clean_text_for_analysis`, `compute_flags`), `eva_charset.py` (`validate_eva_text`), `exceptions.py` (`VCATError` hierarchy) |
| `parsers/` | Format → structured records. No I/O policy, no export. | `IVTFFParser.parse_file()` → `Iterator[Page]`; `MetadataParser.extract_pages/folios/quires()` |
| `builders/` | Records → datasets. Each builder is runnable as `python -m`. | `build_eva_lines`, `build_metadata`, `build_mismatch_index` |
| `validators/` | Independent verification. Deliberately re-derives results rather than trusting the builder. | `schema.py`, `verify_invariants.py`, `validate_phase1_outputs.py` |
| `schemas/` | JSON Schema (Draft 7) contracts for published records. | `transcription_lines.schema.json`, `mismatch_index.schema.json` |
| `hf/` | Hugging Face export and dataset-card generation. | `export.py` |
| `data_sources/` | Source config, checksums, cached downloads, verification script. | `sources.yaml`, `verify_sources.py` (also installed as `vcat-verify`) |
| `scripts/` | Operational and exploratory scripts. | `fetch_sources.py`, `analyze_charset.py`, `quick_analysis.py`, `deep_analysis.py` |
| `tests/` | 343 passing / 7 skipped, ~100% coverage on core packages. | `pytest tests/` |
| `notebooks/` | Worked examples: source verification, loading from HF, sanity statistics. | |
| `docs/` | Data model, sources, decisions, charset covenant, publishing. | |

### Design invariants worth internalising

- **Builders and validators share the same stripping code.** This is the reason
  `vcat/text_processing.py` exists as a separate module and carries a warning in
  its docstring. Do not inline a regex.
- **Line-level is the canonical granularity** (Decision 6). `line_id` (`f1r:1`)
  is the primary key joining every dataset. Token views are derived, not stored.
- **All locus types are preserved** (Decision 7) — `line_type` is one of
  `paragraph`, `label`, `circle`, `radius`. Labels behave differently from
  running text; filter, don't assume.
- **Reproducibility scope is JSONL only.** Parquet is content-equivalent but not
  hash-guaranteed. `output/SHA256SUMS` covers the JSONL.
- **Uncertainty is a first-class field**, not a footnote — see `UncertainValue`
  in the metadata records (`section` carries `confidence` and `disputed`).

---

## 5. Set-up

Requires Python 3.11+.

```bash
git clone https://github.com/dylanhogg/voynich-data.git
cd voynich-data
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Download and hash-verify the five source transcriptions
python scripts/fetch_sources.py

# Rebuild everything from source
python -m builders.build_eva_lines
python -m builders.build_metadata
python -m builders.build_mismatch_index

# Verify
python -m validators.verify_invariants --output-dir ./output
python -m validators.validate_phase1_outputs
```

Before opening a PR, all four of these must pass — CI runs the same checks:

```bash
ruff check .
black --check .
mypy vcat parsers builders validators hf
pytest tests/            # expect 343 passed, 7 skipped
```

### Load the data without building it

```python
from datasets import load_dataset

eva      = load_dataset("Ched-ai/voynich-eva")
pages    = load_dataset("Ched-ai/voynich-manuscript-metadata", "pages")
mismatch = load_dataset("Ched-ai/voynich-transcription-mismatch")
```

Or straight from local Parquet:

```python
import pandas as pd
df = pd.read_parquet("output/eva_lines.parquet")
```

### A first look

```bash
python scripts/quick_analysis.py    # word frequencies, basic counts
python scripts/deep_analysis.py     # entropy, bigrams, hapax, Currier A/B
jupyter notebook notebooks/02_sanity_statistics.ipynb
```

---

## 6. Possible next steps toward decoding

Nothing below is a solution. These are tractable, falsifiable directions the
current datasets already support. The value of this repo is that each one can be
run twice — once on ZL, once on IT — and disagreement between the two runs is
measurable rather than invisible.

**Start here: replicate before you innovate.**
`scripts/deep_analysis.py` already computes conditional entropy, word-position
entropy, bigram transition ratios, hapax rates, and Currier A/B comparisons.
Bowern (2021) reports h₂ ≈ 2.0 bits/char for Voynich against 3.0–4.0 for natural
language. Reproduce that number on this corpus first. If you can't reproduce a
known result, you can't trust a novel one.

### Structural questions (data is ready today)

1. **Slot grammar.** Word-position entropy is strikingly non-uniform — position
   1 and final positions are heavily constrained. Formalise this as a finite-state
   grammar over EVA glyphs and measure what fraction of the 4,072 lines it
   generates. A high-coverage slot grammar constrains what the encoding *can* be.
2. **Currier A vs B.** They show different entropies. Are they two languages, two
   scribes, two registers, or one system with two vocabularies? Join
   `eva_lines` to `pages` on `page_id` and test A/B against `hand`,
   `section`, and `quire` — the metadata dataset makes this a one-liner.
3. **Line as a unit.** Line-initial and line-final glyph distributions differ
   from line-medial. If lines are meaningful units rather than arbitrary wraps,
   that rules out several cipher families. Test whether the effect survives
   controlling for `line_type` and paragraph position.
4. **Labels vs running text.** 115 label loci sit next to illustrations. If any
   part of the manuscript is decodable by context, it's the labels — they have
   external referents (plants, stars, figures). Slice on
   `line_type == "label"` and join to `illustration_type`.

### Method questions

5. **Transcription-robust results only.** Adopt a house rule: every claim gets
   re-run on IT and reported with a stability figure from the mismatch dataset.
   Restricting to the 901 exactly-matching lines gives a high-confidence
   sub-corpus; the 655 substantive disagreements are a useful adversarial set.
6. **Glyph granularity.** EVA may over- or under-split glyphs. GC's v101 encodes
   more visual distinctions. Re-run entropy measures on the GC text from the
   mismatch dataset — if key statistics move, EVA's segmentation is doing work
   that the manuscript itself may not support.
7. **Null models.** Before claiming "language-like", state what would falsify it.
   Compare against shuffled text, an order-2 Markov generator trained on the
   corpus, and a Cardan-grille / table-lookup generator. A hypothesis that no
   null model can fail is not a hypothesis.

### Infrastructure that would unlock more

8. **Token-level view.** Decision 6 leaves this as a derived config —
   straightforward to add, and prerequisite for most morphological work.
9. **Image/IIIF alignment.** The Beinecke IIIF manifest is referenced in
   `sources.yaml`. Line-to-image-region alignment would let layout, glyph
   variants, and ink evidence enter the analysis.
10. **A hypothesis registry.** Pre-register the prediction, the test, and the
    falsification criterion before running it. This is the intended job of the
    planned `voynich-hypotheses` repo, and it's the single biggest defence
    against the failure mode that has claimed most Voynich "solutions":
    a flexible enough method fits noise, and 4,072 lines contain a great deal of
    noise.

### Where analysis code belongs

Exploratory work is welcome in `scripts/` and `notebooks/`. Anything that
becomes a reusable method belongs in `voynich-analysis`, not here — this repo
stays boring on purpose.

---

## Further reading

| Document | Covers |
|----------|--------|
| `docs/data_model.md` | Identifier formats, normalisation rules, entity relationships |
| `docs/sources.md` | Full source documentation and attribution |
| `docs/decisions.md` | Decision log with rationale and reversibility |
| `docs/eva_alphabet.md` | EVA character set reference |
| `docs/charset_decisions.md` | The charset covenant |
| `docs/SOURCES_LICENSE.md` | Provenance and licensing of the underlying transcriptions |
| `docs/PUBLISHING.md` | Hugging Face publishing procedure |
| `docs/progress.md` | Horizon 1 status and definition of done |
| `CONTRIBUTING.md` | Setup, required checks, ground rules |

Code is MIT. The underlying scholarly transcriptions carry no formal licence —
read `docs/SOURCES_LICENSE.md` before redistributing, and credit the
transcribers listed in the README's acknowledgments. Decades of somebody else's
careful work is what makes any of this possible.
