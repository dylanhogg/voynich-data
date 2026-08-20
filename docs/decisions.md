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

## Decision 11: Entropy Estimation and Bootstrap Protocol

**Date**: 2026-08-19  
**Status**: Active  
**Context**: Plug-in entropy on ~170k glyphs overestimates order-3+ structure. The plan
(§3.2) required Miller–Madow and, "where feasible", NSB, plus bootstrap CIs.

### Options Considered

1. Plug-in only, with a caveat in the text.
2. Miller–Madow plus a second estimator, with a block bootstrap over lines.
3. Full NSB / Bayesian estimation.

### Decision

Option 2. `translations/analysis/stats.py` reports Miller–Madow as the headline
estimator, offers Chao–Shen as a cross-check, and computes 95% CIs by a block bootstrap
that resamples *lines* (200 resamples; 50 for metrics that require rebuilding a view).
NSB was **not** implemented.

### Rationale

Miller–Madow and Chao–Shen disagree by less than the bootstrap CI at orders 1–3, which is
the range every claim in Phase 1 rests on. NSB's advantage appears where both are already
unreliable (orders 4+), so it would have bought precision only where no claim is made.
Resampling lines rather than glyphs preserves within-line structure, which is itself one
of the objects of study.

### Consequences

Orders 4 and 5 are reported but never used for a claim. If Phase 2 needs h4/h5 as evidence,
NSB (or a Bayesian estimator) has to be added first.

### Reversibility

Easy — one module, one estimator function to add.

---

## Decision 12: Definition of the "Running Prose" Subset

**Date**: 2026-08-19  
**Status**: Active  
**Context**: §3.6 requires excluding circular and radial text from prose statistics, but
the built data has no line-level marker for it: `line_type` is only `paragraph` or `label`.

### Options Considered

1. Skip the exclusion and note the limitation.
2. Exclude by page-level illustration type.
3. Hand-annotate circular lines.

### Decision

Option 2. Running prose = paragraph lines on pages whose `illustration_type` is not
`A` (astronomical) or `C` (cosmological), configured as `CONFIG.prose_exclude_illustration`.
Hand annotation is out of scope by the plan's own rule (§0.3, fully automated).

### Rationale

Circular and radial writing is concentrated on astronomical and cosmological pages. The
rule is coarse — some circular text on biological pages survives it — but it is
reproducible from the data, which hand annotation would not be.

### Consequences

The subset costs 170 lines (4.2%) and 587 tokens (1.7%), and moves h2 by 0.006 bits. Layout
effects are therefore real but not what drives the headline numbers. A finer rule needs
either glyph coordinates or page images, both of which are open data gaps.

### Reversibility

Easy — one config tuple.

---

## Decision 13: Cross-Transcription Stability Is Judged on the EVA Pair Only

**Date**: 2026-08-19  
**Status**: Active  
**Context**: §3.8 asks for a per-metric stability score across transcriptions. CD, FG and GC
use different alphabets (Currier, FSG, v101), so their metric differences mix alphabet
choice with transcription disagreement.

### Options Considered

1. Pool all five sources into one stability score.
2. Score stability on ZL vs IT (both EVA) and report the others as context.

### Decision

Option 2. The `robust` verdict uses the ZL/IT paired difference against the metric's own
bootstrap CI; CD/FG/GC deltas are reported in the same table but explicitly labelled as
alphabet-plus-transcription.

### Rationale

Pooling made every metric "transcription-limited", which is true only in the trivial sense
that different alphabets count different things. The EVA-only comparison answers the
question actually being asked: would this number change if we had used the other EVA
transcription?

### Consequences

h2, hapax rate and near-repeat rate are robust within EVA; TTR and mean word length are
not, and cannot by themselves support a decipherment claim.

### Reversibility

Easy.

---

## Decision 14: Currier B Is Not Reachable from A by a Single Systematic Transformation

**Date**: 2026-08-19  
**Status**: Active (negative result)  
**Context**: §3.7 asks whether B is derivable from A by a systematic glyph- or affix-level
mapping. A positive result would have been a major structural finding.

### Test

At matched sample size (10,774 tokens each), 24.3% of A word types already occur in B.
Every single-glyph substitution (all ordered pairs over the glyph inventory) and every
addition or removal of twelve common affixes was applied to the A vocabulary and scored by
coverage of the B vocabulary.

### Result

**Falsified.** The best single transformation ("drop prefix `d`") raises coverage from
0.243 to 0.266 — a 2.3 point gain, in the range expected from chance overlap of short
strings. Vocabulary Jaccard between A and B at matched size is 0.151.

### Consequences

Phase 2 must treat A and B as separate systems with separate keys rather than assuming one
is a transform of the other. Compound transformations (two or more simultaneous changes)
were not searched, so the negative result covers single-step transformations only.

### Reversibility

n/a — recorded as a falsified hypothesis.

---

## Decision 15: `[a:b]` Alternative Selection Is a Parameter, Not a Hard-Coded Convention

**Date**: 2026-08-19  
**Status**: Active  
**Context**: `vcat/text_processing.py` kept the first option of every `[a:b]` alternative
reading. §3.9 requires quantifying what that convention decides, which needs the second
reading — and the repo rule is that all stripping lives in that one module.

### Decision

`strip_ivtff_markup` and `clean_text_for_analysis` take an `alternative: int = 0` argument
selecting which option to keep. The default is unchanged, so every built dataset is
byte-identical; the Phase 1 uncertainty analysis passes `alternative=1`.

### Rationale

The alternative was re-implementing the regex inside `translations/`, which the repo rule
forbids for good reason: the builder and the verifier would then be able to drift apart.

### Consequences

584 lines carry alternatives; the second reading changes 627 tokens (1.9%) and moves every
headline metric by less than 0.3%. The first-option convention is therefore not load-bearing.

### Reversibility

Easy — the parameter defaults to the old behaviour.

---

## Decision 16: One Description-Length Scale for Every Hypothesis

**Date**: 2026-08-20  
**Status**: Active  
**Context**: Phase 2 has to compare "enciphered Latin" against "meaningless table-generated
text" (plan §4.2 requires H6a/H6b to be scored on the same scale as H1–H9). Likelihoods
under different model families are not comparable, and an unconstrained key fits anything.

### Options Considered

1. Compare LM likelihoods of the decoded text, penalised ad hoc.
2. Score every hypothesis as a **code**: total bits to reconstruct the observed glyph
   stream, model plus data.
3. Score cipher hypotheses by likelihood and generative rivals by a separate criterion.

### Decision

Option 2. A hypothesis' score is `model_bits + data_bits`, where model bits pay for the key,
merge partition, syllable table or automaton, and data bits pay for the manuscript under it.
Reported **gain** is bits per token saved against an order-2 Markov model of the glyph
stream itself (parameters priced at ½·log2 N). Two costs are charged explicitly:
**ambiguity bits** (`log2` of the number of glyphs sharing a plaintext letter, per
occurrence) and the key description.

### Rationale

MDL is the plan's own complexity penalty (§4.1) and it makes the rivals commensurable.
Without ambiguity bits every search collapses the key onto the most frequent letter, which
is a decode that cannot be inverted and therefore is not a description of the manuscript.
The order-2 Markov reference knows nothing about language, so beating it is the minimum bar
for "this hypothesis explains something".

### Consequences

All scores are negative in this run — no hypothesis, cipher or generative, describes the
manuscript better than its own local statistics. The comparison that carries the evidence is
therefore the null-relative one (same search on pseudo-Voynich), not the absolute score.

### Reversibility

Easy in principle, but a rescoring invalidates every Phase 2 number, so it needs a new
decision entry.

---

## Decision 17: Annealing with Restarts Instead of Gibbs Decipherment

**Date**: 2026-08-20  
**Status**: Active  
**Context**: §4.3.3 lists EM (Knight et al.) and Bayesian/Gibbs decipherment (Ravi & Knight)
as the search workhorses.

### Decision

Implemented: frequency-matched initialisation (the cheap end of EM), simulated annealing with
multi-restart, exact linear assignment where the model is order-1, and a stochastic
steepest-descent search over glyph-merge partitions. **Not** implemented: Gibbs sampling with
sparse priors.

### Rationale

The cipher alphabet is 25 units. Annealing reaches the same optimum from independent restarts
well inside budget — verified on synthetic ciphers, where it recovers hidden keys at 100%
token accuracy. Gibbs earns its keep on key spaces an order of magnitude larger, which is the
slot-conditioned hypothesis H5, and H5 is registered unfunded for exactly that reason.

### Consequences

If H5 is ever funded, the sampler has to be written first. Recorded so that "we used
annealing" is a choice on the record rather than an omission.

### Reversibility

Easy — one module.

---

## Decision 18: The H4 Abbreviation Transform Is a Crude Proxy

**Date**: 2026-08-20  
**Status**: Active  
**Context**: H4 (medieval Latin scribal abbreviation) needs an abbreviated-Latin language
model, and this plan forbids hand annotation (§0.3), so the abbreviation has to be generated
by rule.

### Decision

`translations.decipher.lm.abbreviate` applies a deterministic transform: suspension of the
commonest endings (`-orum -arum -ibus -us -um -is -em`), nasal contraction before a
consonant, and `-que` written as one sign. H4 is funded at a 6% share on top of the four
hypotheses named in the session scope, because it reuses the H3 machinery unchanged.

### Rationale

Real scribal abbreviation is irregular, context-dependent and scribe-specific. A rule-based
proxy is the only automatable option, and it is better than not testing the hypothesis at all
— provided the limitation is stated wherever the result is.

### Consequences

A negative H4 result is weaker than a negative H1 result: it falsifies "this abbreviation
model", not "abbreviated Latin". The hypothesis record says so, and so does the report.

### Reversibility

Easy — a checksummed corpus of genuinely abbreviated Latin would replace the transform.

---

## Decision 19: H5 Is Registered Unfunded, Not Falsified

**Date**: 2026-08-20  
**Status**: Active  
**Context**: H5 (homophonic / slot-conditioned polyalphabetic) has a key space of
slots × alphabet rather than alphabet, needing a sampler and a budget beyond this run's.

### Decision

H5 is registered in full — prediction, falsifier, grid, iteration counts — with
`funded: false` and a written rationale, and appears in the report under "unfunded".

### Rationale

The plan's own rule (§4.3.6) is that a truncated or unfunded hypothesis is *inconclusive*,
never falsified. Silently dropping it would have been the dishonest option; scoring it with a
budget it cannot use would have been worse.

### Consequences

Any future claim that "slot-conditioned ciphers were ruled out" is unsupported by this work.

### Reversibility

n/a — H5 runs unchanged when the budget exists.

---

## Decision 20: Every Funded Phase 2 Hypothesis Was Falsified by Its Own Criterion

**Date**: 2026-08-20  
**Status**: Active (negative results)  
**Context**: Nine hypotheses were pre-registered with an explicit falsifier before any search
ran (`translations/hypotheses/*.yaml`). Phase 2 executed the eight funded ones, each against
12 independently seeded surrogate corpora, with the held-out pages scored once at the end.

### Test

Each hypothesis is scored as a code for the manuscript (Decision 16), and its **gain** is
bits per token saved against an order-2 Markov model of the glyph stream itself. Every
falsifier in the registered records reduces to: *does the hypothesis beat that baseline, and
does the same search do better on the manuscript than on surrogate text?*

### Result — falsified

| id | best variant | gain (bits/token) | held-out | nulls beating it | verdict |
|----|--------------|-------------------|----------|------------------|---------|
| H2 verbose cipher | fixed-width-3, herbal Latin | −4.23 | −2.37 | 6 of 12 | falsified; widest variant unconverged |
| H8 affixal morphology | MDL slot inventory | −5.39 | −5.38 | 6 of 12 | falsified |
| H7 transposition | Latin unigram, exact assignment | −9.66 | −8.70 | 3 of 12 | falsified |
| H1 monoalphabetic | herbal Latin (Clusius) | −10.28 | −9.07 | **0 of 12** | falsified against baseline |
| H4 abbreviated Latin | abbreviation proxy | −10.38 | −9.34 | 1 of 12 | falsified (this model, not the idea) |
| H3 abjad | vowel-stripped Latin | −11.01 | −10.03 | 4 of 12 | falsified |
| H6b autocopying | copy-plus-edit code | −13.02 | −10.36 | 9 of 12 | falsified |
| H9 ars combinatoria | k=2 slot grammar | −15.20 | −13.93 | 7 of 12 | falsified |
| H6a Rugg grille | fitted table + grilles | −23.92 | −18.22 | 11 of 12 | falsified |

Not one hypothesis — cipher or "no plaintext" — describes the manuscript in fewer bits than
its own order-2 glyph statistics. The two rival generative models lose by more than the
cipher hypotheses do, so this is not a result in favour of meaninglessness either.

### The one residual signal

H1 on the herbal-Latin model is the only hypothesis whose real score beat **all twelve**
surrogates (p at the 0.077 floor, q = 0.69 after correction). The margin is 0.16 bits/token
and it is not significant at any conventional threshold. It is recorded because it is the
only asymmetry in the table, not because it supports monoalphabetic Latin — which its own
falsifier rejects.

### Consequences

- Phase 4 will render English under a **losing** model, and every artifact must carry that
  label (plan §0.4, §6.3).
- The Phase 4 shortlist is H2, H8, H1 and H6b (as the rival control) — carried as least-bad,
  not as supported.
- H2 is the one hypothesis whose *best* variant did not converge across restarts (263 cipher
  units against 26 letters). Its converged variants — fixed-width-2 and the searched merge
  partition — met the falsifier independently, so the verdict stands, but the wide-alphabet
  corner of H2's space is properly described as inconclusive.
- These are results about *these* models at *this* budget on the ZL transcription. They do
  not show the manuscript is meaningless, and they do not exclude H5, which was never run.

### Reversibility

n/a — recorded as falsified hypotheses. Re-running a record unchanged with a larger budget is
the intended way to revisit any of them.

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
| Text Processing | 3, 4, 8, 15 |
| Content Inclusion | 7 |
| Analysis Methodology | 8, 10, 11, 12, 13, 16, 17 |
| Decipherment | 16, 17, 18, 19 |
| Falsified Hypotheses | 14, 20 |

---

*This decision log is part of VCAT v0.1.0. Last updated: 2026-01-17*
