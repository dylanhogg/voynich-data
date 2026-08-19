# VCAT Decision Log

This document records significant technical and methodological decisions made during VCAT development. Each decision includes context, options considered, rationale, and consequences.

## Decision Log Format

Each decision follows this structure:

```
## Decision N: [Title]

**Date**: YYYY-MM-DD  
**Status**: [Active | Superseded | Revised]  
**Context**: What situation prompted this decision?

### Options Considered

1. **Option A** — Description
2. **Option B** — Description

### Decision

Which option was chosen.

### Rationale

Why this option was selected.

### Consequences

What follows from this decision.

### Reversibility

How difficult it would be to change this later.
```

---

## Decision 1: Primary Source Selection

**Date**: 2026-01-17  
**Status**: Active  
**Context**: Multiple transcription sources are available for the Voynich Manuscript, each with different characteristics, formats, and levels of completeness.

### Options Considered

1. **Takahashi HTML** — Original Takahashi website transcription
   - Pros: Direct from original transcriber
   - Cons: HTML format requires parsing, not actively maintained

2. **Stolfi Interlinear** — Jorge Stolfi's UNICAMP files
   - Pros: Comprehensive, historical significance
   - Cons: Older IVTFF format, less metadata

3. **LSI File** — Landini-Stolfi Interlinear
   - Pros: Multiple transcribers combined
   - Cons: Complex format, interlinear alignment issues

4. **ZL Transcription** — Zandbergen-Landini IVTFF
   - Pros: Most accurate, modern format, rich metadata, maintained
   - Cons: Single transcriber's judgment

### Decision

Use **ZL Transcription (v3b)** as the primary source for VCAT.

### Rationale

1. **Accuracy**: ZL represents the most careful, complete transcription
2. **Format**: Modern IVTFF 2.0 with rich page metadata
3. **Maintenance**: Actively maintained by René Zandbergen
4. **Community**: Widely used as reference in computational work
5. **Completeness**: All folios including foldout panels

### Consequences

- All VCAT tooling is aligned to IVTFF 2.0 format
- Parser handles ZL-specific conventions
- Other transcriptions are secondary (comparison only)
- Character set follows ZL's extended EVA

### Reversibility

Moderate. Parser could be adapted for other formats, but schema assumptions would need review.

---

## Decision 2: Stolfi Interlinear Usage

**Date**: 2026-01-17  
**Status**: Active  
**Context**: The Stolfi interlinear file contains valuable historical transcriptions but uses an older format.

### Options Considered

1. **Use as primary** — Parse Stolfi as main data source
2. **Use for comparison** — Parse for mismatch analysis only
3. **Exclude entirely** — Focus only on ZL

### Decision

Use Stolfi interlinear for **comparison and mismatch analysis**, not as a primary dataset.

### Rationale

1. Format is older (IVTFF 1.7) and less structured
2. Primary value is comparing historical transcribers (Currier, FSG)
3. ZL already incorporates Takahashi's complete transcription
4. Mismatch index captures valuable disagreement data

### Consequences

- Build mismatch index comparing ZL vs Stolfi transcribers
- Do not publish Stolfi as standalone VCAT dataset
- Document historical transcriber codes (H, C, F, L, R)

### Reversibility

Easy. Could add Stolfi as additional dataset later.

---

## Decision 3: Line Numbering Policy

**Date**: 2026-01-17  
**Status**: Active  
**Context**: Different transcription sources may number lines differently for the same page.

### Options Considered

1. **Normalize to common scheme** — Renumber all sources consistently
   - Pros: Easier cross-source comparison
   - Cons: Loses source fidelity, introduces errors

2. **Source-faithful numbering** — Preserve each source's original numbers
   - Pros: No data transformation, traceable to source
   - Cons: Harder cross-source alignment

3. **Dual numbering** — Keep both original and normalized
   - Pros: Best of both worlds
   - Cons: Schema complexity, confusion potential

### Decision

Use **source-faithful numbering**. Each dataset preserves its source's original line numbers.

### Rationale

1. Avoids introducing transformation errors
2. Makes it easy to trace back to source files
3. Mismatch index explicitly tracks numbering differences
4. Schema simplicity

### Consequences

- `line_number` field matches source exactly
- Line IDs are unique within a source (`page_id:line_number`)
- Cross-source comparison requires mismatch index
- No "canonical" line numbering exists

### Reversibility

Easy. Could add `normalized_line_number` field later without breaking schema.

---

## Decision 4: Text Cleaning Algorithm

**Date**: 2026-01-17  
**Status**: Active  
**Context**: Raw transcription text contains markup (comments, alternatives, markers) that must be cleaned for analysis.

### Options Considered

1. **Keep first alternative** — `[a:b]` → `a`
   - Pros: Deterministic, preserves transcriber's primary choice
   - Cons: Loses uncertainty information

2. **Keep all alternatives** — `[a:b]` → `a` OR `b`
   - Pros: Preserves full information
   - Cons: Complicates text analysis

3. **Mark alternatives** — `[a:b]` → `a?`
   - Pros: Preserves uncertainty flag
   - Cons: Non-standard, complicates analysis

### Decision

**Keep first alternative** in `text_clean`. Store raw text with markup in `text` field.

### Rationale

1. First alternative represents transcriber's best judgment
2. Raw text preserves full information for special analyses
3. Clean text enables straightforward frequency analysis
4. Both representations available to users

### Consequences

- Two text fields: `text` (raw) and `text_clean` (processed)
- Standard analyses use `text_clean`
- Users can re-process `text` with different rules
- `has_alternatives` flag indicates presence of alternatives

### Reversibility

Easy. Could add alternative `text_` fields with different processing.

---

## Decision 5: Schema Versioning (Pre-1.0)

**Date**: 2026-01-17  
**Status**: Active  
**Context**: The data model needs to support evolution while setting user expectations.

### Options Considered

1. **Start at 1.0** — Signal stability from the start
   - Pros: Looks mature
   - Cons: Locks in schema too early

2. **Use 0.x versioning** — Explicitly pre-1.0
   - Pros: Sets expectations for change, allows iteration
   - Cons: May seem less stable

### Decision

Use **0.x versioning** with explicit "pre-1.0" documentation.

### Rationale

1. Allows schema evolution based on community feedback
2. Sets honest expectations with users
3. Common practice for initial releases
4. Reaching 1.0 becomes meaningful milestone

### Consequences

- All dataset cards note "pre-1.0, schema may change"
- Breaking changes allowed in 0.x releases
- Document migration paths when possible
- Target 1.0 after community validation

### Reversibility

N/A — This is a versioning policy, not a technical decision.

---

## Decision 6: Line-Level Granularity First

**Date**: 2026-01-17  
**Status**: Active  
**Context**: The dataset could be structured at page-level, line-level, or token-level.

### Options Considered

1. **Page-level** — One record per page
   - Pros: Simple, compact
   - Cons: Harder to query individual lines

2. **Line-level** — One record per line
   - Pros: Natural unit, queryable, flexible
   - Cons: More records

3. **Token-level** — One record per word
   - Pros: Maximum granularity
   - Cons: Large dataset, loses line context

### Decision

Use **line-level granularity** as the canonical representation.

### Rationale

1. Lines are the natural transcription unit
2. Stable across tokenization choices
3. Sufficient for most Horizon 2 analyses
4. Token views can be derived later
5. Manageable dataset size (~4K records)

### Consequences

- Primary dataset is `voynich-eva:lines`
- Token-level views become derived configs
- Page-level stats computed from line aggregation
- `line_id` is the primary key

### Reversibility

Easy. Token-level config can be added without changing line-level.

---

## Decision 7: IVTFF Locus Type Preservation

**Date**: 2026-01-17  
**Status**: Active  
**Context**: IVTFF distinguishes locus types (P=paragraph, L=label, C=circle, R=radius) that may be analytically significant.

### Options Considered

1. **Ignore locus type** — Treat all text equally
2. **Filter to paragraphs** — Only include P-type loci
3. **Preserve all types** — Include with `line_type` field

### Decision

**Preserve all locus types** with `line_type` field mapping.

### Rationale

1. Labels may have different linguistic properties
2. Circular/radial text placement may be meaningful
3. Users can filter by type as needed
4. Preserves full source information

### Consequences

- `line_type` field: "paragraph", "label", "circle", "radius"
- Dataset includes all loci (4,072 total)
- Statistics can be computed per type
- Filtering available via dataset API

### Reversibility

N/A — This preserves information rather than discarding it.

---

## Decision 8: Tokenization Contract for Analysis (T0/T1 + comma policy)

**Date**: 2026-08-19  
**Status**: Active  
**Context**: EVA is a transcription convention, not glyph ground truth. Compounds
(`ch`, `sh`, `cth`, `ckh`, `cph`, `cfh`) are single visual units written as several
ASCII characters, and `,` marks an *uncertain* word break. Published Voynich results
swing on these choices, and comparing numbers across studies is impossible when the
choice is implicit.

### Options Considered

1. **Pick one tokenization** (e.g. characters) and use it everywhere.
2. **Make tokenization an explicit experimental factor** reported as a grid.

### Decision

Option 2. `translations/tokenize.py` is the only tokenizer for the analysis
programme. It implements `T0-char` (characters as-is) and `T1-glyph`
(compound-aware; `@NNN;` high-ASCII tokens are single opaque units; the ligature
connector `'` is dropped as it marks how glyphs join rather than being a glyph).
`T2-slot` and `T3-merge` are declared but raise `NotImplementedError` until the
Phase 1 morphology induction and Phase 2 merge search produce them. Orthogonally,
the comma policy (`CB=break` / `CB=join`) is explicit at every call site; `CB=break`
is the default for headline numbers.

### Rationale

Every headline metric is then reported over `{T0,T1} × {break,join} × {ZL,IT}`,
so a result that only exists under one tokenization is visible as such.

### Consequences

Analysis code never re-implements word splitting. Numbers in reports carry their
grid cell. Dropping `'` loses 24 corpus-wide markers; that loss is recorded here
rather than hidden in a regex.

### Reversibility

Easy — one module, fully unit-tested against hand-checked lines from f1r, f68r1
and f66r.

---

## Decision 9: Reference Corpora Are Fetched, Not Vendored

**Date**: 2026-08-19  
**Status**: Active  
**Context**: Phase 0 of plan 001 needs non-Voynich baselines (Latin, Romance,
Germanic, agglutinative, English) plus a Latin→English lexicon. Together these are
~26 MB and carry mixed provenance.

### Options Considered

1. **Vendor into git** alongside the transcriptions in `data_sources/cache/`.
2. **Fetch and verify by checksum**, keeping the cache git-ignored.

### Decision

Option 2. Declarations live in `data_sources/sources.yaml` under
`reference_corpora:` (URL, licence, SHA256, retrieval date, extractor format);
`scripts/fetch_corpora.py` (`make corpora`) fetches and verifies; a mismatch is
fatal. GitHub-hosted sources are pinned to a commit SHA rather than a branch.

### Rationale

Keeps the repository small, avoids redistributing third-party text, and makes
upstream drift a loud failure instead of a silent change in results.

### Consequences

`make corpora` is required before baseline analysis; tests that need corpora skip
cleanly when the cache is absent (so CI stays offline). Project Gutenberg
occasionally regenerates its files, which will surface as a checksum failure and a
deliberate re-pin.

### Reversibility

Easy.

---

## Decision 10: Frozen Held-Out Page Split

**Date**: 2026-08-19  
**Status**: Active  
**Context**: Any search over thousands of candidate substitutions will find a
beautiful false positive. Without held-out data, there is nothing left to falsify it.

### Options Considered

1. Line-level random split.
2. Page-level seeded split, frozen in config.
3. No split; rely on significance testing.

### Decision

Option 2. `translations/config.py` fixes the global seed (20260819) and the 20%
fraction; `translations.strata.holdout_pages` derives the split deterministically
from the sorted page list. 41 of 206 pages (698 lines) are held out. Held-out pages
are illegal inputs to any key search and are only read at the Phase 4 validation gate.

### Rationale

Lines from the same page share hand, section, language and vocabulary, so a
line-level split leaks. The split must be reproducible from the seed alone, never
stored as a data file that could drift.

### Consequences

Search phases operate on ~80% of the corpus. Changing the seed or fraction
invalidates every validation number produced so far and requires a new decision entry.

### Reversibility

Hard by design.

---

## Template for Future Decisions

Copy this template for new decisions:

```markdown
## Decision N: [Title]

**Date**: YYYY-MM-DD  
**Status**: Active  
**Context**: [What situation prompted this decision?]

### Options Considered

1. **Option A** — Description
2. **Option B** — Description

### Decision

[Which option was chosen]

### Rationale

[Why this option]

### Consequences

[What follows]

### Reversibility

[How hard to change]
```

---

## Index by Topic

| Topic | Decisions |
|-------|-----------|
| Data Sources | 1, 2, 9 |
| Schema Design | 5, 6 |
| Text Processing | 3, 4, 8 |
| Content Inclusion | 7 |
| Analysis Methodology | 8, 10 |

---

*This decision log is part of VCAT v0.1.0. Last updated: 2026-01-17*
