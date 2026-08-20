# Phase 3 — Gap analysis

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Register

| gap | blocks | remedy | cost | provenance | status |
| --- | --- | --- | --- | --- | --- |
| No token-level cross-transcription alignment | Per-token confidence weighting; every Phase 1 robustness claim was line-level | Needleman–Wunsch alignment of ZL against IT per line, substitution cost = glyph edit distance, written to `output/translation/token_alignment.parquet` with a reliability weight per token | ~3 s per run; one new module (`translations/alignment.py`) | Derived from built artifacts only (`eva_lines`, `mismatch_index`); no new source | closed |
| No illustration↔label linkage | Anchor-based gloss seeding on labels; the 115 label lines cannot be tied to the plants, stars or nymphs beside them | Ingest a published concordance (plant-ID list) as a checksummed source. No hand annotation. | Search cost only; nothing to implement without a source | Would need a `sources.yaml` entry with a checksum | open |
| Marginalia not in dataset | The best cribs (f116v, f66r, f17r) are unavailable to anchor scoring | Add a `marginalia.jsonl` source with transcription variants and explicit dispute flags | Would be small to build; the blocker is the source, not the code | Would need a checksummed transcription source | open |
| No paragraph/block segmentation | Line-as-unit versus paragraph-as-unit modelling; LAAFU effects can only be tested at line level | Plan expected derivation from `position` plus layout heuristics | ~70 lines (`translations/paragraphs.py`); no heuristics needed | Derived from the raw IVTFF text already in `eva_lines` | closed |
| Currier/v101 alphabet not mapped | Robustness checks against GC and FG stay alphabet-limited | Build and test an explicit mapping table with lossiness documented | Estimated 1–2 days: the mapping is many-to-many and needs its own validation against the images | Would need a decision-log entry per mapped glyph pair | open |
| No plant/star reference lexicons | Anchor scoring for herbal and astronomical labels | Add medieval herbal and star-name lexicons to `sources.yaml` | Star names: one entry. Plant names: no comparable source located. | `sources.yaml` entries with checksums | partially closed |
| Register-matched Latin scarce | Language-model quality for H1/H3/H4 — the herbal Latin model that scored best in Phase 2 was built on 11,638 words | Assemble a medieval-herbal Latin subcorpus; document its size limits | One multi-part `sources.yaml` entry; registry gained `urls:` support | 15 pinned files at one commit, checksum over the concatenation | closed |

3 closed, 1 partially closed, 3 open.

## What happened to each

**No token-level cross-transcription alignment** — *closed*. 33,728 ZL tokens aligned. GC/FG/CD are excluded: their alphabets differ, so a glyph edit distance against them measures the alphabet, not the scribes (Decision 13).

**No illustration↔label linkage** — *open*. No machine-readable concordance found that could be pinned. The candidates are narrative HTML pages and one application database covering three folios. §5.1's pre-committed fallback applies: label-level anchor seeding is dropped and page-level `section` / `illustration_type` is used instead.

**Marginalia not in dataset** — *open*. The readings exist only as prose discussion on HTML pages, and they are actively disputed — exactly the case where a hand transcription would smuggle one scholar's reading into the dataset as fact. Left open; the anchor catalogue stays empty and no crib enters Phase 4.

**No paragraph/block segmentation** — *closed*. 717 blocks. IVTFF marks paragraph starts (`<%>`) and ends (`<$>`) inline and the builders drop them on the way to `text_clean`; reading them back gives an annotated segmentation rather than a guessed one. 93% of blocks are opened and closed by a marker; the rest are closed by a page break.

**Currier/v101 alphabet not mapped** — *open*. Deliberately deferred. Phase 3 scoped alignment to the EVA pair, so nothing in this phase depends on the mapping; a mapping asserted without validation would create the appearance of cross-alphabet robustness without the substance.

**No plant/star reference lexicons** — *partially closed*. Star names are pinned (`iau_star_names`, 451 IAU-approved proper names, mostly Arabic- or Latin-derived and current in medieval lists). No plant-name lexicon was pinned; the nearest available route is filtering the already-pinned Whitaker's Words dictionary by its subject-area codes, which Phase 4 can do without new provenance. Neither lexicon is used in this phase: the anchor protocol only ranks finished candidates.

**Register-matched Latin scarce** — *closed*. `herbal_latin`: Isidore, *Etymologiae* IV and XVII plus Columella, *De re rustica* — 128,497 words, 11× the Clusius corpus. Size limits, stated: neither text is a *medieval herbal*; Isidore (c. 625) is encyclopaedic and Columella (1st c.) is Roman agronomy. They are the closest register match retrievable as checksummable plain text.

## What the open gaps cost the translation

Two of the three open gaps are the same problem: the manuscript's best cribs — the labels beside the drawings and the marginalia — have no checksummable transcription or concordance. Without them the translator has no anchor it is allowed to use, so Phase 4 renders under a model with no external tie-point at all. That is a hard limit on how far a gloss can be validated, and it is why the anchor catalogue in `translations/decipher/anchors.py` is still empty.

The third, the v101 mapping, costs less: it limits robustness checks to the EVA pair, and the token alignment shows the EVA pair agrees on the great majority of tokens anyway.
