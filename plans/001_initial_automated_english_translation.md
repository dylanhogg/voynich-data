# Plan 001 — Initial Automated English Translation

**Status**: Phases 0–4 complete (landmark gate green; no hypothesis beat its null on
any representation; the pseudo-Voynich control renders *more* than the manuscript does);
Phase 5 not started
**Author**: VCAT / agent-assisted
**Date**: 2026-08-19 (Phases 0–1 implemented 2026-08-19, Phases 2–4 on 2026-08-20)
**Scope**: Extend voynich-data (VCAT) from dataset building into analysis, code
breaking, and a best-efforts automated English translation.

---

## Phase status

| Phase | State | Evidence |
| --- | --- | --- |
| 0 — Foundations | **Complete** | `translations/` package (config, determinism, io, tokenize, strata, corpora, nulls, phase0), 10 checksum-pinned reference corpora, 48 new tests (391 passed / 7 skipped total), `output/translation/phase0_manifest.json` byte-identical across runs |
| 1 — Analysis round 1 | **Complete** | `translations/analysis/` (12 modules), `reports/phase1/` (9 topic reports + `summary.md`), landmark gate **GREEN** (6/6), 64 new tests (455 passed / 7 skipped total), `make analyse1` ≈100 s and byte-stable across runs |
| 2 — Hypothesis space + search | **Complete** | 10 pre-registered records in `translations/hypotheses/`, `translations/decipher/` (11 modules), `reports/phase2/` (scores, approach, synthetic validation), 143 candidates in `output/decipher/candidates.parquet`, engine validated at ~100% key recovery on self-built ciphers, all 8 funded hypotheses falsified by their own criteria (Decision 20), 47 new tests (504 passed / 7 skipped) |
| 3 — Analysis round 2 | **Complete** | `reports/phase3/` (gap register, `round2_findings.md`, `rescoring.md` + 5 topic reports), 3 of 7 gaps closed and 1 partially, `output/translation/token_alignment.parquet` (33,728 tokens, 86.2% ZL/IT exact agreement), 717 paragraph blocks, 2 new checksummed corpora, `T3-merge` implemented, 286 round-2 candidates in `output/decipher/round2_candidates.parquet`, 48 new tests (552 passed / 7 skipped), `make analyse2` ≈2 h 6 min |
| 4 — Translation pipeline | **Complete** | `translations/` +6 modules (`decode`, `gloss`, `lexicon/whitakers`, `render`, `pipeline`, `calibrate`, `phase4`), all 4,072 lines rendered under 5 keyed hypotheses, `output/translation/translation_lines.jsonl` + `.parquet` + `lexicon.jsonl` + `calibration.json` + `SHA256SUMS`, `reports/translation/` (coverage, calibration, folio readings), schema + validator, 49 new tests (601 passed / 7 skipped), `make calibrate` ≈2 min + `make translate` ≈35 s, byte-identical across runs. **Gate §6.6 met; the `grille` control renders 75.1% of tokens against the manuscript's 61.1%** (Decision 29) |
| 5 — Audit + honesty gate | Not started | — |

**Run Phases 0–4:**

```bash
make corpora   # fetch + SHA256-verify reference corpora into data_sources/cache/corpora/
make phase0    # verify inputs, summarise strata, write output/translation/phase0_manifest.json
make analyse1  # Phase 1 suite -> reports/phase1/ (~100 s; non-zero exit if the gate is red)
make decipher  # Phase 2 hypothesis search -> reports/phase2/ (budgeted; ~50 min at current grids)
make analyse2  # Phase 3 remediation + round 2 + re-scoring -> reports/phase3/ (~2 h; --analysis-only skips the search)
make calibrate # Phase 4 blind search on synthetic ciphertext -> output/translation/calibration.json (~2 min)
make translate # Phase 4 pipeline + validators -> output/translation/, reports/translation/ (~35 s)
make test      # 601 passed, 7 skipped
```

Start reading at `reports/phase1/summary.md` (findings table, landmark gate, and
the "what we still cannot tell" list), then `reports/phase2/hypothesis_scores.md`
(ranked hypotheses, null-relative significance, held-out scores), then
`reports/phase3/round2_findings.md` (what remediation changed) with
`reports/phase3/gap_analysis.md` for what could not be sourced, and finally
`reports/translation/coverage.md`, whose first table — the pseudo-Voynich control — is the
verdict on everything downstream of it. `docs/translation_method.md` is the Phase 4 method.

### Phase 0 as built (deltas from the plan below)

1. **No new runtime dependencies.** Everything in Phase 0 is stdlib plus the
   existing `pyyaml`. numpy/scipy/torch are deferred to Phase 1, where they are
   first actually needed.
2. **`line_type` has only two values** in the built data — `paragraph` (3,957)
   and `label` (115). There is no `circle`/`radius` value, contrary to §2.6 and
   the assumption behind §3.6: circular and radial text is *not* distinguishable
   at line level. Astronomical/cosmological pages (f68r1–3, f57v, f67r…) are typed
   `paragraph`. Excluding circular text therefore needs a page-level or
   illustration-type rule, which Phase 1 must define explicitly.
3. **Tokenizer exit-gate lines changed accordingly.** f100r has no label lines;
   labels concentrate on f66r (49) and f49v (26). The hand-checked test lines are
   f1r:1 (prose), f1r:2 (comma), f1r:19 (high-ASCII), f2r:10 (ligature),
   f68r1:1 (circular page), f66r:1 (label).
4. **`text_clean` is not pure EVA letters.** It contains 80 high-ASCII tokens
   (`@NNN;`) and 24 ligature connectors (`'`). `T1-glyph` treats `@NNN;` as one
   opaque unit and drops `'`; both choices are recorded in `docs/decisions.md`
   (Decision 8).
5. **The comma policy is a no-op for IT.** The IT text in the mismatch index
   contains no `,`, so `CB=break` and `CB=join` give identical IT numbers. The
   reporting grid still has 8 cells but only 6 distinct word counts.
6. **Baseline counts, measured** (`phase0_manifest.json`): ZL 4,072 lines,
   33,728 words (`CB=break`), 170,988 `T0-char` units, 152,601 `T1-glyph` units;
   IT 4,061 lines (11 lines empty or absent after cleaning), 33,176 words,
   153,264 glyph units. Consensus subset 3,414 lines (83.9%), as predicted.
   Held-out split: 41 of 206 pages, 698 lines.
7. **Reference corpora: 9 text + 1 lexicon, all checksum-pinned** (§2.4 table
   updated below). Four of them (Clementine Vulgate, Douay-Rheims, Elberfelder
   1905, Finnish 1933/38) are the same text in four languages, which holds genre
   constant across the language contrast — a stronger control than the plan
   assumed. Not obtainable as checksummed public-domain plain text: Old Occitan,
   Middle High German, a medieval Latin herbal proper (*Circa Instans*,
   *Herbarium Apuleii*), Semitic text in Latin transliteration, Turkish, pinyin.
   Clusius (1605) is the herbal-register proxy that was obtainable.
8. **Corpora are fetched, not vendored** (Decision 9): `make corpora` verifies
   SHA256 into a git-ignored cache. Corpus tests skip cleanly when the cache is
   absent, so CI stays offline.
9. **`T2-slot` / `T3-merge` raise `NotImplementedError`** until Phase 1.4 and
   Phase 2 produce the inductions they depend on.
10. **Open normalisation decision deferred to Phase 1**: whether Latin baselines
    fold `u/v` and `i/j`. Current normalisation does not; this matters for Latin
    letter-frequency comparisons.
11. **Scaffold built to need.** `decipher/` and `lexicon/` exist as empty
    packages; `gloss.py`, `render.py`, `confidence.py` and `pipeline.py` are
    Phase 4 work and were not stubbed. `make analyse2`, `decipher`, `translate`
    and `audit` arrive with their phases; `make corpora`, `make phase0` and
    `make analyse1` exist now.

---

### Phase 1 as built (deltas from the plan below)

1. **Headline numbers.** h2 = **2.253 bits/glyph** [2.242, 2.262] on ZL / `T1-glyph`
   / `CB=break` (2.126 on `T0-char`), against **3.08–3.37** for nine
   sample-size-matched natural-language baselines — every CI disjoint. Hapax rate
   0.700 (highest baseline: Clusius 0.670). Adjacent near-repeat rate (edit
   distance ≤ 2) 0.148 versus 0.038 for Latin. Zipf α = 2.116, Heaps β = 0.707.
   Word-length CV 0.393 and a binomial fit — natural language sits at 0.50–0.55
   and prefers negative binomial.
2. **Landmark gate: GREEN, 6/6** (`reports/phase1/landmarks.md`). Nothing in the
   plan needed to be weakened to pass it.
3. **NSB entropy was not implemented** (Decision 11). Miller–Madow plus Chao–Shen
   agree to within the bootstrap CI at orders 1–3, which is where every claim
   lives; orders 4–5 are reported but never used as evidence. Bootstrap = 200
   line-resamples (50 for metrics that rebuild a view).
4. **`T2-slot` now exists.** The MDL induction yields prefixes
   `qo cho ol o y l q` and suffixes `ody s o`, saving 49,051 bits of description
   length (1.51 bits/word, versus 0.15 for Latin and 0.00 for both
   pseudo-Voynich generators). `translations.tokenize` gained an explicit
   `segmenter` argument so `T2-slot` is usable without the tokenizer owning a
   model; the inventory is written to `output/translation/phase1_slot_model.json`.
5. **FSA induction needed k-tails, not minimisation.** Exact Moore minimisation of
   a prefix tree just rebuilds the word list (0% held-out acceptance), so the
   acceptor is induced by k-tails merging. Read as a trade-off, not a score: at
   k=1 Voynich needs **103 states** for 92.6% held-out type acceptance while Latin
   needs **7** for 99.9%; over-generation is 95.7% versus 98.8%. The state count,
   not the acceptance rate, is what separates them.
6. **Word order carries little information**: 0.093 bits/word gained over a
   word-order-shuffled surrogate, versus 0.504 for Latin and 0.592 for English.
   Excess MI at distance 1 is 0.156 bits versus Latin's 0.724, and it does not
   decay — it is flat from d=2 to d=50, unlike Latin's decay curve.
7. **`section` and `illustration_type` are redundant** in `eva_lines` (a 1:1
   mapping), so §3.5's "do page topics align with illustrations" is the same
   question as "do they align with sections". NMF over the page × word matrix
   gives NMI 0.410 and purity 0.762 against both.
8. **Layout effects are real but small in aggregate.** Line-initial/mid/final
   first-glyph distributions differ with Cramér's V 0.307 (χ² p ≈ 0), while the
   Latin control at arbitrary line breaks gives p = 0.589. The running-prose rule
   (Decision 12) costs 170 lines (4.2%) and 587 tokens (1.7%) and moves h2 by
   0.006 bits.
9. **Currier B is not a transform of A** (Decision 14, falsified): the best of
   ~600 single-glyph substitutions and 48 affix operations lifts A→B type
   coverage from 0.243 to 0.266. Matched-size Jaccard 0.151, Δh2 0.270 bits. In a
   per-line factor model, quire (partial R² 0.058) and section (0.045) explain
   more of mean word length than language (0.026) or hand (0.016) — the A/B split
   is not cleanly separable from where and by whom the page was written.
10. **Transcription robustness is metric-specific** (Decision 13). Robust within
    EVA (|Δ| below the metric's own CI): h2, hapax rate, near-repeat rate. Not
    robust: TTR (1.5× CI) and mean word length (2.3× CI). CD/FG/GC are included
    for context only, since their alphabets differ; GC shifts mean word length by
    1.18 glyphs.
11. **The uncertainty flags do not matter much.** Dropping any flag class, or all
    of them (27,434 tokens remain), moves every headline metric by **< 1.9%**.
    Re-reading with the *second* `[a:b]` option changes 627 tokens on 584 lines and
    moves nothing by more than 0.3% — so the first-option convention is not
    load-bearing (Decision 15, which added the `alternative` parameter to
    `vcat/text_processing.py` rather than duplicating its regex).
12. **The tuned pseudo-Voynich is a strong control on two axes and weak on a
    third.** Tuned grille matches h2 to 0.02 bits and word length to 0.06 glyphs
    but produces only **96 word types** (hapax 0.000): a Cardan-grille table
    cannot reach the manuscript's hapax rate, which is a genuine limit of the Rugg
    model rather than a tuning failure. Tuned selfcite (window 40, mutation 0.05)
    matches word length but overshoots repetition badly (90.5% of tokens identical
    to a word in the preceding 20). Both generators were revised during tuning:
    the grille got multiple grilles per table, and selfcite's mutation operators
    were rebalanced so word length does not drift.
13. **Runtime and dependencies.** `make analyse1` takes ~100 s wall clock
    (entropy 36 s, robustness 25 s, morphology 14 s, syntax 10 s) — far inside the
    24 h ceiling, which is reserved for Phase 2/3 search. numpy and scipy were
    added as dependencies; `mypy` needed a `numpy.*` `follow_imports = "skip"`
    override because numpy 2.x stubs use 3.12+ syntax while the project targets
    3.11. No torch yet.
14. **Deliverable count.** §3.11 asked for 9 topic reports plus a summary; there
    are 9 (`entropy`, `lexis`, `morphology`, `syntax`, `position`, `currier`,
    `robustness`, `uncertainty`, `landmarks`) plus `summary.md`. §3.1's
    stratification harness landed in Phase 0 as `translations/strata.py`, so no
    separate `analysis/strata.py` exists.

---

### Phase 2 as built (deltas from the plan below)

*Numbers below come from the scored run of 2026-08-20. The clarifying answers for
this session set the search budget at 1–2 h (against the plan's 24 h ceiling, which
stays in `config.py`), kept the engine on CPU with no torch, funded H1/H2/H3/H4/
H6a/H6b/H7 plus the descriptive H8/H9, left H5 registered but unfunded, and built
the synthetic-ciphertext harness now while deferring the calibration maps to
Phase 4.*

1. **One scale for all ten records** (Decision 16). Every hypothesis is scored as a
   *code*: total bits to reconstruct the observed glyph stream, model plus data,
   measured as **gain per token against an order-2 Markov model of the glyph stream
   itself**. This is what puts "enciphered Latin" and "meaningless table-generated
   text" on one axis, and it is the plan's MDL penalty made concrete. Two costs are
   charged that are easy to omit: the key description, and **ambiguity bits** —
   without the latter every search collapses the key onto `e`, because the decoded
   plaintext alone would not reconstruct the manuscript.
2. **The headline result is negative and uniform.** No hypothesis — cipher or
   generative — describes the manuscript better than its own local statistics. The
   ranking is a ranking of *losers*, and the plan's §4.2 rule that H6a/H6b are scored
   on the same scale means the "no plaintext" rivals lose too, and by more than the
   cipher hypotheses do.
3. **The engine works, and that is checkable.** On ciphers this project built and
   then attacked blind, key recovery is 100% for monoalphabetic substitution,
   fixed-width verbose, and abjad. Two real bugs surfaced only because of this test:
   scoring vowel-suppressed plaintext against a vowel-ful LM rewards the wrong key
   (H3 needs a matched stripped model), and a verbose cipher must be attacked
   through the same fixed-width channel H2 uses or it cannot be recovered at all.
4. **A search-correctness fix mid-phase.** Injective key moves are meaningless once
   the cipher alphabet exceeds 26 units, which silently disabled most of the
   annealer's moves on the wide fixed-width channels (142 and 263 units). The first
   full run reported those variants as unconverged; `can_be_injective` now switches
   to unrestricted moves and the run was repeated.
5. **Null resolution is a design limit, and it is stated in the report.** With one
   surrogate per family the empirical p-value cannot fall below 0.2, which is not a
   test. Each family now gets `CONFIG.null_replicates = 3` independently seeded
   surrogates (12 nulls), flooring p at 0.077 — still short of 0.05, and the report
   says so rather than dressing the number up.
6. **Gibbs decipherment was not implemented** (Decision 17). Frequency-matched
   initialisation, annealing with restarts, and exact linear assignment for the
   order-1 case cover every funded hypothesis; Gibbs earns its keep on H5-sized key
   spaces, and H5 is unfunded.
7. **H4 was funded** at a 6% share beyond the hypotheses named in the session scope,
   because it reuses the H3 machinery with an abbreviation-transformed Latin model.
   The transform is a crude rule-based proxy for scribal abbreviation (Decision 18),
   so a negative H4 falsifies *this model*, not abbreviated Latin.
8. **H5 is registered unfunded, never falsified** (Decision 19), with its grid and
   iteration counts committed so it can be run unchanged when the budget exists.
9. **Anchors are implemented as a protocol with an empty catalogue.** The zodiac
   month names and marginalia cannot enter it until Phase 3 can source them with
   checksums, and the code enforces the plan's rule that anchors may only rank
   finished candidates — never train, constrain or seed a search.
10. **Language models are dense n-gram tables capped at order 4.** A 27-symbol
    alphabet at order 5 needs a 115 MB table per corpus; orders 3–4 are what the
    budget and the memory allow, against the plan's "order-3 to order-6". Scoring is
    vectorised over *distinct* cipher n-grams rather than positions, which is what
    makes ~1M key evaluations per hypothesis affordable on CPU.
11. **Held-out discipline held.** Searches see training pages only; the frozen 41
    held-out pages are scored exactly once per hypothesis, with the key the search
    had already committed to. Every candidate — losers, null runs, held-out rows —
    is written to `output/decipher/candidates.parquet` with its budget, convergence
    and truncation flags.
12. **Budget.** The ceiling is `CONFIG.search_budget_seconds` (7,200 s) allocated by
    each record's declared share, H2 taking 45%. The scored run spent 3,356 s of it
    (H2: 1,750 s of its 3,240 s allocation); nothing was truncated. `make decipher`
    is ≈56 min end to end.
13. **H2's advantage is in the wrong place.** Its best variants are the *wide*
    fixed-width channels — 142 units at width 2, 263 at width 3 — which are large
    codebooks, not verbose ciphers, and neither converged across restarts. The
    linguistically motivated searched-merge variant (22 merges, 48 units, seeded
    with the Phase 1 morphs) converged and scored −6.50 bits/token. H2 is therefore
    falsified on its converged variants and *inconclusive* on the wide-alphabet
    corner of its space.
14. **The rivals lose too, and by more.** H6a costs 24 bits/token more than a plain
    bigram model of the glyphs and H6b costs 13 more, so this run supports neither
    Rugg nor Timm & Schinner. The honest summary of Phase 2 is that no registered
    model of any family beats the manuscript's own local statistics — which is a
    statement about the models tested at this budget, not about the manuscript.

---

### Phase 3 as built (deltas from the plan below)

*Numbers from the run of 2026-08-20. The clarifying answers for this session set the
round-2 ceiling at ~4 h (7,440 s were spent), told Phase 3 to attempt the new sources
and fall back to an open gap where none exists, dropped §5.2 item 7 (numerals), and
scoped the token alignment to the EVA pair.*

1. **Paragraph segmentation needed no heuristics** (Decision 21). §5.1 expected it to be
   derived from the `position` locator; the locator cannot carry it (`+` alone covers 3,729
   of 4,072 lines). IVTFF already marks paragraph starts (`<%>`, 707) and ends (`<$>`, 670)
   inline, and the builders strip them on the way to `text_clean`. `vcat/text_processing.py`
   gained an `inline_tags()` accessor — the tag regex stays in the one module allowed to own
   it — and the result is 717 blocks, 93.4% opened *and* closed by a marker.
2. **Line-level transcription noise was overstated.** Phase 1 could only say 29.3% of lines
   are identical between ZL and IT. At token level **86.2%** of ZL tokens are read
   identically and mean agreement where a counterpart exists is 0.965. A line-level mismatch
   is usually one word, not a different reading of the line — which changes how much of
   Phase 1's "transcription-limited" hedging was warranted.
3. **The reliability weight is a declared policy, not a fitted model** (Decision 22). There
   is no labelled data to fit it on, so the six penalties are constants in
   `translations/alignment.py`. Only **2.3%** of tokens (780) fall below the 0.5 floor, so
   the `reliable` representation is close to the raw one and its analyses move very little.
   A stricter floor is a different experiment, not a tuning knob to reach for.
4. **`T3-merge` is implemented.** §2.3 deferred it to "the Phase 2 glyph-merge search"; that
   search has now produced a partition, so `tokenize.apply_merges` exists and
   `decipher/channel.merge_units` delegates to it rather than keeping a second copy of the
   longest-match loop.
5. **Three gaps stay open, and they are the ones that matter most** (Decision 24). No
   checksummable illustration↔label concordance and no marginalia transcription could be
   found — the candidates are narrative HTML pages and one application database covering
   three folios. §5.1's pre-committed fallback therefore fires: label-level anchor seeding is
   dropped and the anchor catalogue stays empty, so **Phase 4 will render with no external
   tie-point at all**. The v101 mapping was deliberately deferred.
6. **Two new checksummed corpora** (Decision 23). `herbal_latin` (Isidore, *Etymologiae* IV
   and XVII; Columella, *De re rustica*) is 128,497 words against Clusius's 11,638 — 11× the
   herbal-register Latin Phase 2 leaned on. It is *not* a medieval herbal, and the report
   says so. `iau_star_names` pins 451 star names for Phase 4. The registry gained multi-part
   entries (`urls:`, checksum over the concatenation). Adding a corpus changed the Phase 1
   baseline set from 9 to 10, so `make analyse1` was re-run: the h2 gap moves from −0.965 to
   −0.976 bits and the landmark gate stays **GREEN**.
7. **Merging trades entropy for word length and repetition.** This is §5.2.1's make-or-break
   diagnostic and the answer is a qualified no. H2's converged merge does pull h2 (2.253 →
   3.111), h3 and word-length CV *inside* the natural-language range — 4 of 11 metrics
   against 3 for raw — but it drives mean word length to 2.81 units, below every baseline
   (min 3.97), and doubles the adjacent near-repeat rate (0.148 → 0.331). Entropy bought,
   paid for elsewhere: the signature of a compression, not of a plaintext.
8. **Reliability filtering does not move the landmarks**, which is the useful negative: they
   are properties of the text, not artifacts of the tokens the two transcribers disagree
   about.
9. **The paradigm probe weakens the morphology reading** (§5.2.2). Voynich roots take 3.76
   distinct suffixes each against 1.90 in Latin and 1.63 in Finnish, only 9% of roots are
   single-suffix against ~50% in both languages, and root↔suffix NMI is 0.35 against 0.51.
   Suffix choice is *freer* than inflection allows and is barely conditioned by the previous
   word (1.7% of suffix entropy). The plan named Turkish as the agglutinative comparator;
   Finnish is what `sources.yaml` pins, and it fills the same role at matched genre.
   The comparison also needed a **frequency inventory** (12 commonest word-final sequences
   per view) rather than the MDL induction, because at matched sample size Latin induces
   exactly **one** affix that pays for itself — the Phase 1 asymmetry, restated so starkly it
   makes a cross-language table impossible.
10. **Section-specific vocabulary is real** (§5.2.4): mean section divergence 0.461 bits
    against a page-permutation null whose *maximum* over 200 permutations is 0.199, p = 0.005.
    The null reassigns whole pages, so page-level repetitiveness is preserved and only the
    section↔vocabulary link is destroyed. This is the strongest positive result in the
    programme so far and it is what makes herbal-only and pharma-only subsets the most
    translatable parts of the manuscript, if any part is.
11. **Labels behave like a nomenclature** (§5.2.5): 124 tokens over 115 lines, mean 2.37 units
    against 4.92 in a size-matched prose sample, suffix rate 0.24 against 0.90, and a page's
    labels are tighter to each other than the label vocabulary at large. Half of label types
    also occur in running text. What they name is still unknown — that needs the concordance
    gap 2 leaves open.
12. **Round-2 re-scoring narrows every gap and changes no verdict** (§5.2.8, Decision 25).
    All eight funded hypotheses were re-searched on `merged` and `reliable`; 286 candidates,
    18 summary rows. Best is H2 on merged at −0.105 bits/token — within a tenth of a bit of
    parity, with a *positive* held-out gain of +3.05 — and it is not evidence. On the same
    channel the shuffled-text surrogate gains **+9.97 to +10.02**, the held-out Markov
    baseline costs 13.58 bits/token against 12.55 on training (fewer tokens, same parameter
    cost), and the variant did not converge. `raw` was not re-searched: Phase 2 ran it with
    this code and these seeds, and its numbers are carried from the Phase 2 manifest.
13. **The translator configuration separates "best" from "usable".**
    `output/translation/phase3_translator_config.json` records `best_scoring` (the
    unconverged H2 row, so the number is not hidden) and `chosen` — the best *converged*
    candidate that committed to a key, which is H1 on the merged representation at −5.771.
    Phase 4 runs `chosen`, and still renders under a losing model.
14. **`--analysis-only` and `--reports-only`.** The searches are ~2 h of the ~2 h 6 min run;
    the write-up must be fixable without spending them again. Both flags exist on
    `translations.phase3` and the reports regenerate from
    `output/translation/phase3_manifest.json`.

---

### Phase 4 as built (deltas from the plan below)

*Numbers from the run of 2026-08-20. The clarifying answers for this session rendered all
five keyed hypotheses, skipped the distributional gloss, ran the full blind-search
calibration, and set a ~4 h ceiling for it (107 s were spent).*

1. **The control is the result** (Decision 29). §7.2.1 called the pseudo-Voynich control
   decisive and §6.6 gated Phase 4 on running it. It was run, and the `grille` corpus —
   Rugg-style table generation from a syllable table induced from the manuscript, encoding
   nothing — renders **75.1%** of tokens in the gated view against the manuscript's
   **61.1%**, at a slightly *higher* mean confidence (0.524 vs 0.494). A corpus with no
   content translates better than the manuscript. `reports/translation/coverage.md` prints
   this before anything else. `selfcite` fails the pipeline from the other side, collapsing
   to 4.5%: its vocabulary is so repetitive that permuted keys gloss it as well as the real
   one does.

2. **All five keyed hypotheses are rendered** — H1 (primary, the Phase 3 `chosen`), H2, H3,
   H4, H7. H6a, H6b, H8 and H9 are generative: they claim a production process rather than
   an encipherment, so there is no plaintext to gloss and no rendering to make. The
   variant, channel and significance for each come from
   `reports/phase3/rescoring.json` — Phase 4 re-derives no score.

3. **The calibration is real and mostly flat** (Decision 26). §4.6's design was implemented
   in full: encipher a reference corpus in the language each hypothesis' own model assumes,
   at its own channel width, attack it blind with its own search settings, gloss the
   result. Four of the five recover the hidden key at **100%** token-weighted accuracy, so
   their isotonic maps are flat at 1.0 above zero. Only H7 (order-1 assignment, 49.1% key
   accuracy) yields an informative curve. The map is fitted on half the synthetic tokens
   and the reliability diagram computed on the other half; predicted and observed agree
   within 0.01 in every bin.

4. **So confidence is not the calibrated value alone.** A flat map would print a confident
   translation under a key that lost to a Markov model. The confidence is
   `calibrated(raw) × (1 − null p) × reliability`, where `raw = gloss score × length
   specificity × key coverage`, and the **null p** is an empirical per-token p-value against
   20 permutations of the key's own letter assignments. The **length specificity** is
   *measured*, not assumed: a one-letter hit against a 48,000-stem Latin dictionary is worth
   0.087 and a two-letter hit 0.60. Without these two terms the pipeline would report most of
   the manuscript as high confidence purely because short strings hit dictionaries.

5. **The distributional gloss is not implemented** (Decision 27). The chain is exact stem →
   stem after one stripped ending → verified edit-distance-1 neighbour → transliteration, and
   it is *strict*: the first rung that fires supplies all the candidates. 18.1% of types
   resolve on an exact stem, 30.4% stripped, 31.5% by neighbour, 20.1% not at all.

6. **No reordering and no inserted function words** (Decision 28). §6.3 assumed an induced
   syntactic ordering from §5.2. There is none: Phase 1 §3.5 found no word-order model worth
   applying and Phase 3 did not produce one. Applying a grammar that was never induced would
   make the output read more like English exactly where the evidence is weakest.

7. **No per-stratum gloss overrides.** §6.2 allows them "when Phase 3 evidence supports
   them". Phase 3 showed section-specific *vocabulary* (0.461 bits, p = 0.005) — that
   different sections use different words, not that one word means different things in
   different sections. The second is what an override needs, so the consistency constraint
   holds corpus-wide.

8. **`make calibrate` is split from `make translate`.** §6.5 asks for the full corpus in
   minutes; the blind searches are the expensive half. Calibration writes
   `output/translation/calibration.json` (107 s of a 4 h ceiling) and `make translate`
   reads it, running the whole corpus × 5 hypotheses × 3 corpora in **33 s**. `phase4`
   refuses to run without the maps rather than silently falling back to raw scores.

9. **Artifact shape (§6.4) is normalised.** Ranked gloss candidates are a property of the
   *type*, so they live once per type in `lexicon.jsonl` and are joined on `surface` rather
   than repeated on all 33,728 tokens — that alone halved the JSONL. `translation_lines.jsonl`
   is the primary hypothesis with the full per-token trace (10 MB);
   `translation_lines.parquet` is all five hypotheses at line level (20,360 rows, 1.5 MB).
   `token_alignment.parquet` is not re-emitted: Phase 3 already writes it to the same
   directory.

10. **`nulls.encipher` gained a `width` parameter.** H2's committed channel is
    `fixed-width-3`, but the verbose scheme was hard-coded to glyph *pairs*, so calibrating
    it would have simulated a channel narrower than the one its key was searched on. The
    default is unchanged, so Phase 2's synthetic validation numbers are untouched.

11. **The synthetic plaintext alphabet is fitted to the cipher alphabet.** A
    one-glyph-per-letter channel has 23 symbols (17 basic EVA glyphs + 6 compounds) and the
    normalised Latin corpora carry 26 letters. Words using the rarest letters are dropped
    rather than the cipher alphabet padded — padding would simulate a wider channel than the
    real one.

12. **Held-out pages were rendered and scored once**: 0.600 gated coverage against 0.613 on
    the training pages. A pipeline that had learned something about the manuscript would
    show a gap; one matching a dictionary against short strings does not, and this is the
    expected result rather than a reassuring one.

13. **`iau_star_names` is pinned but unconsumed.** It was fetched for label glossing in
    Phase 3, and with no illustration↔label concordance (Decision 24) there is nothing to
    match star names against. Recorded in `docs/sources.md` rather than quietly used.

14. **Schema and validator** were added per repo convention:
    `schemas/translation_lines.schema.json` and
    `validators/validate_translation_outputs.py`, which checks the schema, the banner on
    every row and report, one row per manuscript line, that the gated view exactly matches
    the confidence bands, and that `SHA256SUMS` matches disk. `make translate` runs it.

15. **Determinism holds**: two runs produce byte-identical `translation_lines.jsonl`,
    manifest and reports. The manifest carries no wall-clock field.

---

## 0. Framing, constraints and honesty policy

### 0.1 What this plan is

A phased, falsifiable programme that (a) characterises the manuscript
statistically, (b) formalises a hypothesis space for how Voynichese might encode
a plaintext, (c) searches that space with deterministic algorithms, and
(d) emits a **repeatable, fully automated, full-coverage English rendering** of
every line, with per-token confidence and prominent speculative labelling.

### 0.2 What this plan is NOT

It is not a claim of decipherment. **No accepted decipherment of the Voynich
Manuscript exists.** The most likely outcome of Phase 4 is a fluent-looking
English rendering that is largely or entirely wrong. The plan is engineered so
that this outcome is *detectable and reported* rather than hidden — see
Phase 5, especially the pseudo-Voynich control (§5.2.2), which is the single
most important test in this document.

### 0.3 Decisions taken (from clarifying questions)

| Decision | Choice | Consequence |
| --- | --- | --- |
| LLM in pipeline | **No.** Deterministic code only. | No network at run time; byte-reproducible outputs; weaker fluency, stronger auditability. |
| New deps / corpora | **Allowed**, pinned with SHA256 in `sources.yaml`. | numpy/scipy/scikit-learn plus **torch (Apple Metal / MPS)**, plus public-domain reference corpora. |
| Output posture | **Full coverage, flagged.** | Every line gets a best-guess English string; every artifact carries a confidence column and a speculative banner. A gated (UNKNOWN-masked) view is retained internally as a diagnostic. |
| This session | **Plan only.** (Superseded 2026-08-19: Phase 0 implemented.) | No code written until this plan is approved. |
| Publication | **None.** Nothing published to HuggingFace or elsewhere. | All artifacts stay local in `output/` and `reports/`; no dataset cards authored for the translation outputs. |
| Plaintext language priority | **No preference expressed** ⇒ plan's default stands. | Latin (herbal register) front-loaded; Romance/Germanic/Semitic secondary. |
| Annotation | **Fully automated.** No hand annotation. | Any data gap that cannot be closed by a checksummed source stays open, and the tests depending on it are downgraded or dropped (§5.1). |
| Compute ceiling | **24 h wall clock** for the Phase 2/3 search runs. | Search is budgeted, checkpointed and anytime-terminable; budget is a config value, not an emergent property (§4.3.6). |

### 0.4 Non-negotiable honesty rules (apply to every artifact produced)

1. Every output file, report and notebook carries the banner:
   `SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript
   exists. This is model output under a stated hypothesis, not a reading of the
   manuscript.`
2. Every English token is traceable to (hypothesis id, key id, evidence, score).
   Untraceable glosses are a bug.
3. Confidence numbers must be **calibrated against synthetic ground truth**
   (§4.6). An uncalibrated confidence column is prohibited.
4. Falsified hypotheses are deliverables. Each gets an entry in
   `docs/decisions.md` with the test that killed it.
5. Every headline metric in a report must be accompanied by the same metric
   computed on the pseudo-Voynich control corpus.
6. Nothing produced by this plan is published externally (see §0.3). If that
   decision is ever revised, publication requires a fresh decision-log entry and
   a limitations-first dataset card.

### 0.5 Repo constraints inherited from `AGENTS.md`

- All text stripping/cleaning imports `vcat/text_processing.py`. Never
  re-implement regexes.
- EVA charset locked per version (`docs/charset_decisions.md`).
- Data changes need provenance: `sources.yaml` entry with checksum, or a
  documented decision.
- Source-faithful numbering; disagreement is recorded, never smoothed.
- Methodology change ⇒ doc + dataset card updated in the same PR.
- Style: line length 100, `black` + `ruff`, `mypy --disallow-untyped-defs`,
  `from __future__ import annotations`, `pathlib`, dataclasses,
  `get_logger(__name__)`, custom exceptions from `vcat.exceptions`.
- Simplicity first. If a module is 200 lines and could be 50, rewrite it.
- Coding tasks delegated to lower-power subagents where appropriate.

### 0.6 New code location

**All new analysis, decipherment and translation code lives in `./translations/`.**
Existing `vcat/`, `parsers/`, `builders/`, `validators/` are read-only for this
plan, except: (a) an optional `vcat.text_processing` addition if a genuinely
shared primitive emerges (needs a decision-log entry), and (b) new
`sources.yaml` entries for reference corpora.

---

## 1. Baseline: what the repo already gives us

From `output/` and `reports/` at time of writing:

**Corpus** — `eva_lines` (ZL transcription): 4,072 lines, 206 pages,
170,564 chars, 33,711 words, 8,331 unique words, TTR 0.247, hapax 6,139
(69.8% of vocabulary), mean word length 5.42 chars (5.06 on the
alpha-filtered deep-analysis view).

**Strata available today** — `section` (7 values: herbal 1,612 lines /
stars 1,159 / biological 722 / text_only 277 / pharmaceutical 223 /
cosmological 48 / astronomical 31), `currier_language` (A 1,562 lines /
B 2,437 / unknown 73), `hand`, `quire`, `line_type` (paragraph 3,957 /
label 115), `position`, `illustration_type`, plus uncertainty flags
`has_uncertain | has_illegible | has_alternatives | has_high_ascii`.

**Cross-transcription** — `mismatch_index`, 4,072 rows, sources ZL/IT/CD/FG/GC.
Exact matches 901 (22.1%), normalized matches 293 (7.2%) ⇒ **29.3% identical**;
high-similarity 2,220 (54.5%); **content mismatches 655 (16.1%)**;
overall agreement rate 0.839. CD covers only 2,154 lines (52.9%).

**Existing findings to reproduce, not re-derive** (`reports/deep_analysis.md`):
h2 ≈ 2.314 bits/char (H1 3.865, h3 2.071, h4 1.982); gzip ratio 0.327 real vs
0.578 shuffled; strong per-position glyph constraints (pos-1 top o/c/q =54%,
pos-6+ dominated by `y`); word-length CV 0.38 (below natural-language 0.4–0.6);
zero-count bigrams that should exist (`oh`, `eh`, `co`, `ce`, `ah`, `dh` …);
A/B entropy split (h2 A 2.357 vs B 2.184); A-only 2,336 word types, B-only
3,776.

**Known gaps in the current data** (drive Phase 3 scope):
- No token-level alignment across transcriptions — only line-level similarity.
- No illustration↔label linkage (which label sits on which plant/star/nymph).
- No glyph coordinates or image references; no access to page images in-repo.
- No inventory of non-Voynichese marginalia (zodiac month names, f116v,
  f17r, f66r), which are the best available cribs.
- No paragraph/block structure above the line (`position` is partial).
- No canonical mapping between EVA and alternative alphabets (Currier, v101)
  beyond raw parallel text in the mismatch index.

---

## 2. Phase 0 — Foundations (deterministic infrastructure + reference corpora)

**Goal**: make everything downstream reproducible, stratifiable, and comparable
to non-Voynich baselines. Nothing in Phases 1–5 is trustworthy without this.

### 2.1 Package scaffold

```
translations/
  __init__.py
  config.py             # frozen dataclasses: paths, seeds, tokenizer choice, strata
  determinism.py        # seed control, sorted-iteration helpers, run manifest hashing
  io.py                 # loaders for output/*.jsonl|parquet (local only, no network)
  tokenize.py           # tokenization variants (§2.3) — the only tokenizer in the repo
  strata.py             # stratum definitions and split logic
  corpora/              # reference-corpus loaders + normalisation to a common form
  analysis/             # Phase 1 + Phase 3 analysis modules, one concern per file
  nulls/                # surrogate/pseudo-Voynich generators (§2.5)
  decipher/             # channel models, search algorithms, hypothesis runners
  lexicon/              # induced lexeme inventory, gloss tables, provenance
  gloss.py              # token -> ranked English candidates
  render.py             # line-level English rendering + flagging
  confidence.py         # scoring and calibration
  pipeline.py           # end-to-end CLI entrypoint
  report.py             # md/json/parquet emitters with mandatory banner
tests/translations/     # mirrors the above; every module has tests
```

New Makefile targets: `make corpora`, `make analyse1`, `make analyse2`,
`make decipher`, `make translate`, `make audit`. Each is a thin wrapper over
`uv run python -m translations.<entrypoint>`.

**As built:** `config.py`, `determinism.py`, `io.py`, `tokenize.py`, `strata.py`,
`corpora/` (`registry.py`, `normalise.py`), `nulls/` (`surrogates.py`,
`markov.py`, `pseudo.py`, `encipher.py`) and `phase0.py` exist and are tested;
`analysis/`, `decipher/`, `lexicon/` are empty packages; `gloss.py`, `render.py`,
`confidence.py`, `pipeline.py`, `report.py` arrive with Phases 3–4. Targets
`make corpora` and `make phase0` exist; the rest arrive with their phases.
`scripts/fetch_corpora.py` (not `fetch_sources.py`) fetches reference corpora, so
transcription and corpus provenance stay separable.

### 2.2 Determinism contract

- Single global seed in `config.py`; every stochastic algorithm takes an
  explicit `rng` — no implicit global RNG use.
- No `set`/`dict` iteration order dependence: sort before iterating anywhere a
  result depends on order. Lint rule or review checklist item.
- No network access inside `translations/` at run time. Corpora are fetched by
  `scripts/fetch_sources.py` into `data_sources/cache/` and verified by checksum.
- Every run writes `output/translation/manifest.json`: input file SHA256s,
  config hash, git commit, package versions, seeds, wall-clock excluded.
- **Acceptance test**: `make translate` twice produces byte-identical outputs;
  a test asserts the SHA256 of each emitted artifact against a recorded value.

**As built:** manifests are written by `translations.determinism.write_manifest`
and contain the banner, config hash, seed, git commit, recorded package versions
and input SHA256s — and no wall-clock field, which is what makes byte-identity
achievable. The Phase 0 instance is `output/translation/phase0_manifest.json`
(also carrying the tokenization grid, strata summary and corpus checksum status).

### 2.3 Tokenization contract (decide once, report everywhere)

`AGENTS.md` warns results swing on tokenization. Define four variants and treat
the choice as a first-class experimental factor:

| Id | Unit | Definition |
| --- | --- | --- |
| `T0-char` | ASCII char | `text_clean` characters as-is. Baseline for comparability with prior work. |
| `T1-glyph` | EVA glyph | Compound-aware: `ch`, `sh`, `cth`, `ckh`, `cph`, `cfh` merged to single units. Reflects visual glyph reality. |
| `T2-slot` | morph | `T1` plus induced prefix/root/suffix segmentation from Phase 1.4. |
| `T3-merge` | cipher unit | `T1` plus the empirically-searched glyph-merge partition from Phase 2 H2 (e.g. `qo`, `ee`, `ain`). |

In `T1-glyph` a high-ASCII token `@NNN;` is one opaque unit and the ligature
connector `'` is dropped (Decision 8). `T2-slot` was implemented in Phase 1.4:
`tokenize_word(word, T2_SLOT, segmenter)` takes an induced segmenter (the MDL
inventory in `output/translation/phase1_slot_model.json`) and raises without one,
so a slot tokenization always names the model behind it. `T3-merge` was implemented
in Phase 3 on the same pattern: `tokenize_word(word, T3_MERGE, merges=...)` takes the
merge partition Phase 2's H2 search committed to (22 merges: `qo`, `ol`, `aiin`, `chedy`,
…) and raises without one. `decipher/channel.merge_units` delegates to it rather than
keeping a second copy of the longest-match loop.

Orthogonal binary factor: **comma policy** — `,` (uncertain word break) treated
as a break (`CB=break`) or as within-word (`CB=join`). Both computed; the
default for headline numbers is `CB=break`, stated explicitly in every report.

Rule: no analysis reports a single number. Every headline metric is reported as
a grid over `{T0,T1} × {CB=break,CB=join} × {ZL, IT, consensus}` at minimum.

### 2.4 Reference corpora (new `sources.yaml` entries, SHA256-pinned)

Purpose: null models and channel-model language models. Selection criteria —
public domain or permissive licence, plain text obtainable, plausible as a
15th-century European plaintext, or useful as a contrast.

| Group | Candidates | Role |
| --- | --- | --- |
| Latin | Vulgate; Perseus/Latin Library classical + medieval prose; a medieval herbal (e.g. *Herbarium Apuleii*, Circa Instans if obtainable) | Primary plaintext hypothesis; herbal register match |
| Romance/Germanic | Old Occitan, Middle High German, Old Italian, Middle English | Secondary plaintext hypotheses; zodiac month-name script is Romance-like |
| Semitic | Hebrew and Arabic in Latin transliteration, plus vowel-stripped variants | Abjad hypothesis |
| Contrast | Modern English, Finnish/Turkish (agglutinative), Chinese pinyin | Distributional contrast set |
| English target | Modern English (for target-side LM) + Latin↔English and Latin↔modern-language lexicons (e.g. Whitaker's Words data, Wiktionary extracts) | Gloss generation |

**As built** (`reference_corpora:` in `data_sources/sources.yaml`; word counts
after normalisation, from `phase0_manifest.json`):

| Id | Text | Lang | Group | Words |
| --- | --- | --- | --- | --- |
| `vulgate_clementine` | Clementine Vulgate | la | latin | 611,765 |
| `caesar_bello_gallico` | Caesar, *De Bello Gallico* I–IV | la | latin | 20,545 |
| `clusius_rariorum` | Clusius, *De Rariorum Animalium atque Stirpium Historia* (1605) | la | latin | 11,638 |
| `dante_commedia` | Dante, *La Divina Commedia* | it | romance | 102,005 |
| `chaucer_canterbury` | Chaucer, *The Canterbury Tales* | enm | germanic | 281,126 |
| `german_bible_elberfelder` | Elberfelder Bibel 1905 | de | germanic | 722,778 |
| `finnish_bible` | Pyhä Raamattu 1933/38 | fi | contrast | 622,413 |
| `douay_rheims` | Douay-Rheims Bible | en | english | 891,382 |
| `austen_pride_prejudice` | Austen, *Pride and Prejudice* | en | english | 128,559 |
| `whitakers_words` | Whitaker's Words `DICTLINE.GEN` | la | lexicon | — (Phase 4) |

The four Bible texts are verse-parallel, so cross-language comparisons hold
genre constant. Voynich is ~33.7k words, so every one of these needs
subsampling before comparison (`translations.corpora.subsample_words`, contiguous
window). Not obtainable as checksummed public-domain plain text, and therefore
**open gaps**: Old Occitan, Middle High German, a medieval Latin herbal proper,
Semitic text in Latin transliteration, Turkish, pinyin. The Semitic/abjad
hypothesis is consequently tested only via `encipher(..., "abjad")` on Latin
until a transliterated corpus is found.

Tasks:
1. `docs/sources.md` + `data_sources/sources.yaml` entries with URL, licence,
   checksum, retrieval date.
2. `docs/SOURCES_LICENSE.md` updated; any corpus whose licence blocks
   redistribution is fetched-not-vendored and flagged in the manifest.
3. `translations/corpora/normalise.py`: lowercase, strip diacritics (configurable),
   strip punctuation, produce (a) a word stream and (b) a char stream, with the
   same tokenizer discipline as §2.3.
4. **Sample-size matching**: every baseline metric is computed on corpora
   subsampled to the Voynich token/char count (and per stratum), because entropy
   and TTR are strongly sample-size dependent. This is a common failure mode in
   published Voynich comparisons — do not repeat it.

### 2.5 Null and surrogate generators (`translations/nulls/`)

| Generator | Destroys | Purpose |
| --- | --- | --- |
| `shuffle_chars` | everything | absolute floor |
| `shuffle_within_word` | word-internal order, keeps word length + inventory | tests slot structure |
| `shuffle_word_order` | syntax, keeps vocabulary + line lengths | tests whether word order carries information |
| `markov_char(n=1..5)` | long-range structure | tests what n-gram statistics alone explain |
| `markov_word(n=1,2)` | long-range word structure | vocabulary-preserving prose surrogate |
| `grille` (Rugg-style) | — generates text from a syllable table + Cardan grille | rival hypothesis H6a: meaningless table-generated text |
| `selfcite` (Timm/Schinner-style) | — generates by copying and mutating earlier words | rival hypothesis H6b: autocopying |
| `encipher(corpus, scheme)` | — enciphers real Latin/English under each hypothesised scheme | **synthetic ground truth** for calibration (§4.6) and for the Phase 5 audit |

The `grille` and `selfcite` generators are tuned in Phase 1 to match Voynich
h2, word-length distribution and hapax rate as closely as possible. A
well-matched pseudo-Voynich is the control that makes Phase 5 meaningful.

**As built** (revised during Phase 1 tuning — see Phase 1 delta 12: the grille
gained multiple grilles per table, and selfcite's mutation operators were
rebalanced so word length does not drift): `markov_chars(words, order, rng)` / `markov_words(...)` (word
boundaries are a symbol in the char model, so word lengths are generated rather
than copied); `grille(table, n_words, rng)` with `induce_table()` deriving the
syllable table from a corpus — the Phase 1 tuning hook; `selfcite(seed_words,
n_words, rng, window, mutation_rate)`; `encipher(words, scheme, rng)` with
schemes `substitution`, `abjad`, `verbose`, returning ciphertext plus the `Key`
so recovery can be scored. All take an explicit `rng` from
`translations.determinism.derived_rng(salt)`.

### 2.6 Phase 0 exit gate — **met 2026-08-19**

- [x] `translations/` importable, typed, `ruff`/`black`/`mypy` clean, tests pass
      (391 passed, 7 skipped).
- [x] All corpora fetched and checksum-verified; `make corpora` idempotent
      (re-runs verify the cache and download nothing).
- [x] Determinism test green: `make phase0` twice gives a byte-identical
      `output/translation/phase0_manifest.json`; `tests/translations/test_determinism.py`
      asserts manifest stability and seeded-RNG reproducibility.
- [x] Tokenizer variants unit-tested against hand-checked lines — f1r:1, f1r:2
      (comma), f1r:19 (high-ASCII), f2r:10 (ligature), f68r1:1 (circular page),
      f66r:1 (label). Note: f100r has **no** label lines and no `line_type`
      distinguishes circular text, so the planned f68r/f100r pairing was
      replaced by f68r1 + f66r.

---

## 3. Phase 1 — Extensive analysis, round 1

**Goal**: a complete, stratified, cross-transcription statistical portrait of
the manuscript, with every number carrying a confidence interval and a baseline.
Outputs feed the hypothesis space in Phase 2.

Deliverables: `reports/phase1/<topic>.md` + machine-readable
`reports/phase1/<topic>.json`, one module per topic in `translations/analysis/`.

### 3.1 Stratification harness (`analysis/strata.py`)

Build a per-line stratum table joining `eva_lines` + `pages`/`folios`/`quires`
metadata + mismatch status. Strata dimensions: Currier A/B, hand, section,
line_type, quire, folio, in-line position bucket, first/last line of page,
uncertainty flags, transcription-agreement class.

Also define the **consensus subset**: lines with mismatch status `exact` or
`normalized` or `high_similarity` (3,414 lines, 83.9%). Every headline finding
is recomputed here; a finding that only survives on full-ZL is a transcription
artifact.

And the **held-out folio split**: a seeded 80/20 page-level split, recorded in
`translations/config.py` and never changed. Held-out pages are illegal inputs to
any key search in Phase 2/3 and are only touched at the Phase 4 validation gate.

**As built:** this landed in Phase 0 as `translations/strata.py` (there is no
`analysis/strata.py`). Consensus subset 3,414 lines as predicted; held-out split
41 of 206 pages / 698 lines. `translations/analysis/context.py` builds the shared
`Context` of views (grid, strata, 9 matched baselines, 8 nulls, 2 tuned
pseudo-Voynich) that every topic module consumes.

### 3.2 Information-theoretic suite (`analysis/entropy.py`)

- H0–H5 and conditional entropies h1–h5 per tokenization × stratum ×
  transcription, with **Miller–Madow (and NSB where feasible) bias correction**
  and bootstrap 95% CIs. Raw plug-in entropy on 170k chars badly overestimates
  order-3+ structure; correction is mandatory.
- Same metrics on all baselines at matched sample sizes, and on all nulls.
- Compression bounds (gzip/bz2/lzma/PPM if available) real vs shuffled vs
  baselines vs pseudo-Voynich.
- Word-level entropy and conditional word entropy; entropy rate estimates.
- **Deliverable claim to test**: "Voynich h2 is anomalously low versus natural
  language at matched sample size." Report effect size and whether it survives
  on IT and on the consensus subset.

**As built** (`reports/phase1/entropy.md`): claim **upheld** — h2 = 2.253
[2.242, 2.262] versus 3.077–3.365 across nine matched baselines, all CIs
disjoint; it survives on IT (2.263) and on the consensus subset (2.219). NSB was
not implemented (Decision 11); Chao–Shen is the second estimator. Note the
order-1 Markov surrogate reproduces h2 exactly, as it must — h2 alone does not
distinguish the manuscript from its own bigram statistics, so the claim is about
comparison with *language*, not about depth of structure.

### 3.3 Distributional and lexical structure (`analysis/lexis.py`)

- Zipf fit (with proper MLE fitting, not log-log regression) and the
  low-frequency tail anomaly; Heaps' law exponent vs baselines.
- Hapax/dis-legomena curves vs sample size (vs baselines at matched size).
- Word-length distribution, CV, and comparison to binomial/negative-binomial —
  quantify the "unusually symmetric" observation.
- Type/token growth by page order (is vocabulary drifting through the codex?).
- Vocabulary overlap matrices between sections, hands, quires, A/B.

**As built** (`reports/phase1/lexis.md`): Zipf α = 2.116 by discrete power-law MLE
(KS 0.054); Heaps β = 0.707. Word-length CV 0.393 with a binomial fit, against
0.495–0.553 and negative-binomial fits for the baselines — the "unusually
symmetric" observation is confirmed and quantified. Vocabulary drift through the
codex is present but weak (Spearman ρ on new-type rate by page order, reported in
the topic JSON). Section vocabularies overlap little at matched size (Jaccard
matrix in the report).

### 3.4 Word-internal structure and slot grammar (`analysis/morphology.py`)

The strongest known regularity; must be quantified precisely.

- Per-position glyph distributions (already partially in `deep_analysis`), now
  per stratum, per tokenization, with CIs.
- **Successor/predecessor entropy (Harris) segmentation** → candidate morph
  boundaries.
- **MDL/unsupervised morphology** (Morfessor-style, own minimal implementation
  or dependency) → prefix/root/suffix inventory. This yields `T2-slot`.
- **Finite-state acceptor induction**: build a minimal FSA/slot template
  (Stolfi's crust–mantle–core and Tiltman-style paradigms are the reference
  points). Metric: % of word *types* and *tokens* accepted; % of accepted
  strings that never occur (over-generation). Compare against the same procedure
  applied to Latin, English, Turkish, and pseudo-Voynich.
- Gallows glyph behaviour (`k t p f` and compounds): distribution by word
  position, line position, paragraph position (LAAFU — line-as-a-functional-unit
  effects), and by stratum.
- **Key discriminative question for Phase 2**: is word structure better
  described as (a) natural morphology, (b) a positional cipher/slot code, or
  (c) a generative template with no lexical content? Report likelihoods under
  each, not a verdict.

**As built** (`reports/phase1/morphology.md`): held-out bits per word — Voynich
morphology 13.04, positional slot code 18.54, order-2 chain **12.10**; Latin
morphology **10.36** versus chain 16.77. So on the manuscript the chain narrowly
wins and morphology is close behind, while on natural language morphology wins
decisively. That is the honest state of the question, reported without a verdict.
Harris segmentation gives 1.40 morphs/word and an inventory of 4,365, topped by
`qo`, `y`, `ol`, `che`, `she`, `qot` — the known affixes fall out unsupervised.
The MDL inventory defines `T2-slot` (see delta 4 above). Gallows glyphs are
word-initial-enriched in A (0.150 vs 0.101) and word-initial-*depleted* in B
(0.084 vs 0.125) — an A/B difference not previously in the plan's list.

### 3.5 Syntax, order and long-range structure (`analysis/syntax.py`)

- Mutual information between words at distance d = 1..50 (within and across
  line/paragraph/page boundaries); decay curve vs natural language vs surrogates.
  Natural languages show long-range MI decay; table-generated text does not.
- Does word order carry information? Compare model likelihood of real text under
  a word-bigram model vs `shuffle_word_order` surrogate.
- Adjacent near-repeat rate: exact repeats, Levenshtein-1, Levenshtein-2
  neighbours; run-length distribution (`daiin daiin daiin`). Compare to all
  baselines — this is a signature anomaly.
- Self-citation / autocopy: for each word, distance to the most similar earlier
  word; distribution vs `selfcite` surrogate.
- Topic structure: per-page word distributions, LDA or NMF over pages, and
  whether induced topics align with `section` / `illustration_type`. If page
  topics correlate with illustrations, that is evidence of semantic content.

**As built** (`reports/phase1/syntax.md`): NMF (own multiplicative-update
implementation, no scikit-learn) over 206 pages × 1,000 words gives NMI 0.410 and
purity 0.762 against section — but `section` and `illustration_type` are the same
labelling in this data, so this is one result, not two. Word order carries 0.093
bits/word versus Latin's 0.504. Excess MI is 0.156 bits at d=1 and then flat to
d=50, where Latin decays from 0.724 — the manuscript has local structure and
almost no long-range structure. The tuned selfcite surrogate sits at a constant
3.19 bits of excess MI at every distance, which is what pathological autocopying
looks like and is nothing like the manuscript.

### 3.6 Positional and layout effects (`analysis/position.py`)

- Line-initial vs mid vs line-final glyph and word distributions, per stratum,
  with significance tests.
- First line of paragraph / first word of page effects.
- Label vocabulary vs paragraph vocabulary (115 labels — small, treat carefully).
- Circular/radial text handling — flag and exclude from prose statistics by
  default; report separately.
- Quantify how much of the corpus must be excluded to have a clean "running
  prose" subset, and report all headline metrics on that subset too.

**As built** (`reports/phase1/position.md`): there is no line-level marker for
circular or radial text, so the running-prose rule is page-level (Decision 12):
paragraph lines on pages whose illustration type is not A or C. Cost: 170 lines
(4.2%), 587 tokens (1.7%); h2 moves 0.006 bits. First-glyph distributions differ
strongly by line position (Cramér's V 0.307, p ≈ 0) while the Latin control gives
p = 0.589. Line-initial words are longer (4.83 vs 4.49 mid-line). Labels are a
different register: 124 tokens, mean length 2.37 versus 4.53 in prose, and only a
minority of label types occur in paragraph text.

### 3.7 Currier A vs B (`analysis/currier.py`)

- Full metric battery per language; effect sizes and CIs.
- Shared vs exclusive vocabulary, controlling for sample size (B has ~2× the
  tokens — subsample A/B to equal size before comparing).
- Is B derivable from A by a systematic transformation? Search simple
  glyph-level and affix-level mappings that maximise vocabulary overlap.
  A positive result would be a major structural finding.
- Is A/B a scribal-hand effect, a section effect, or independent? Fit a model
  with hand, section, quire and language as factors; report partial effects.

**As built** (`reports/phase1/currier.md`): at matched size (10,774 tokens each)
Δh2 = 0.270 bits, Jaccard 0.151, and B has the longer words (4.64 vs 4.30) with
the lower hapax rate. The transformation search is a **falsified hypothesis**
(Decision 14): the best single transformation gains 2.3 points of A→B type
coverage over a 24.3% baseline. The factor model gives quire (0.058) and section
(0.045) larger partial R² than language (0.026) on mean word length, so the A/B
label is not separable from where the page sits in the codex; compound
transformations were not searched.

### 3.8 Transcription robustness (`analysis/robustness.py`)

- Re-run §3.2–§3.7 headline metrics on IT, and on GC/FG where the alphabet maps
  cleanly (build the mapping; where lossy, say so and restrict).
- Per-metric stability score: |Δ metric| across transcriptions vs the metric's
  own bootstrap CI. Any metric whose cross-source variation exceeds its CI is
  labelled **transcription-limited** and cannot support a decipherment claim.
- Publish a ranked table: metrics robust enough to build on, metrics that are not.

**As built** (`reports/phase1/robustness.md`): each non-ZL source is compared to
ZL **on exactly the lines that source covers**, so coverage differences cannot
masquerade as instability. Robust within EVA: h2 (Δ/CI 0.35), hapax rate (0.04),
near-repeat rate (0.32). Transcription-limited: TTR (1.53) and mean word length
(2.31). CD/FG/GC use other alphabets, so their deltas (GC shifts mean word length
by 1.18) are context, not instability (Decision 13); only `T0-char`
tokenization is meaningful for them.

### 3.9 Uncertainty-flag sensitivity (`analysis/uncertainty.py`)

Re-run headline metrics with (a) all lines, (b) dropping `has_uncertain`,
(c) dropping `has_illegible`, (d) dropping `has_alternatives`, (e) dropping
`has_high_ascii`, (f) dropping all. Report metric drift. `text_clean` keeps only
the first option of `[a:b]` — quantify how many tokens that affects and whether
choosing the second option changes conclusions.

**As built** (`reports/phase1/uncertainty.md`): maximum drift across all six
variants is **1.8%** (TTR under "drop all flagged", which removes 6,294 tokens).
`has_illegible` is a no-op at line level. The second `[a:b]` reading changes 627
tokens on 584 lines and moves nothing by more than 0.3%. Implemented by adding an
`alternative` parameter to `vcat/text_processing.py` (Decision 15) rather than
duplicating its regex.

### 3.10 Landmark reproduction gate (blocking) — **GREEN 2026-08-19**

Phase 1 is not complete until the pipeline independently reproduces, from
`output/`, all of:

- [x] Conditional entropy h2 well below natural language at matched sample size —
      2.253 vs lowest baseline 3.077, CIs disjoint.
- [x] Rigid word-internal glyph ordering / slot structure — within-word shuffling
      raises h2 by 1.344 bits; the k=1 acceptor takes 92.6% of held-out word types.
- [x] Zipf-like word frequency with an anomalous low-frequency tail — α = 2.116,
      hapax 70.0% vs the highest baseline's 67.0%.
- [x] High rate of near-repeat adjacent words vs all baselines — 14.8% within edit
      distance 2 vs 8.2% (English) and 3.8% (Latin).
- [x] Currier A/B divergence surviving sample-size control — Δh2 0.270 bits,
      Jaccard 0.151 at 10,774 tokens each.
- [x] Line-position effects — Cramér's V 0.307, p ≈ 0, Latin control p = 0.589.

`make analyse1` exits non-zero if any check fails, so the gate cannot be passed by
forgetting to look at it.

### 3.11 Phase 1 exit deliverables — **met 2026-08-19**

- [x] `reports/phase1/` — 9 topic reports + `summary.md` with a single findings
      table: finding, effect size, CI, robust-across-transcriptions?, survives on
      consensus subset?, distinguishes Voynich from pseudo-Voynich? (10 findings,
      including one falsified hypothesis.)
- [x] `docs/decisions.md` entries for every methodological choice made —
      Decisions 11–15 (entropy protocol, running-prose rule, EVA-only stability
      verdict, the falsified A→B transformation, the `alternative` parameter).
- [x] An explicit **"what we still cannot tell" list** → seven open questions in
      `reports/phase1/summary.md`, carried into Phase 3's gap analysis: the
      language-versus-cipher ambiguity behind low h2, what A/B actually is,
      whether the hapax tail is textual or transcriptional, morphology versus
      positional generation, what labels refer to, meaningful repetition versus
      autocopying, and the still-missing token-level alignment across
      transcriptions.

---

## 4. Phase 2 — Approach to cracking, with a view to English translation

**Goal**: convert Phase 1 findings into a pre-registered, scored hypothesis
space and a deterministic decipherment engine that can search it.

### 4.1 Formalisation

Model the manuscript as a noisy channel:

```
plaintext P (in language L)  --encode/cipher C-->  Voynichese V (as transcribed) --transcription noise--> observed text
```

Decipherment = find `(L, C, key k)` maximising

```
score = log P_LM_L(decode_k(V))  +  log P(k | structural priors)  -  complexity_penalty(C, k)
```

subject to: the same `(L, C, k)` must work across held-out folios, across
Currier A and B, and must beat the score achieved by the same search run on
pseudo-Voynich. The complexity penalty (MDL) is essential — an unconstrained
key space will always fit something.

**As built:** the objective is expressed as a two-part code — `model_bits +
data_bits` — so the MDL penalty is not a term bolted onto a likelihood but the
score itself (Decision 16). `model_bits` pays for the key, the merge partition,
the syllable table or the automaton; `data_bits` pays for the manuscript under
that model, including **ambiguity bits** (`log2` of the number of glyphs sharing
a plaintext letter, charged per occurrence) so that a decode which cannot be
inverted is priced accordingly. Scores are reported as *gain per token* against
an order-2 Markov model of the glyph stream itself: the model that knows the
manuscript's local statistics and nothing about language.

### 4.2 Pre-registered hypothesis space (`translations/hypotheses/*.yaml`)

Each hypothesis is a YAML record: id, description, prior rationale, the Phase 1
evidence for/against, the **prediction it makes**, the test that would falsify
it, the search algorithm, and the parameter grid. Registered *before* running.

| Id | Hypothesis | Prediction if true | Prior from Phase 1 |
| --- | --- | --- | --- |
| H1 | Monoalphabetic substitution of a natural language | Decoded text's h2 ≈ source language h2; letter frequencies map cleanly | Very low. h2 too low, word-length CV too tight |
| H2 | **Verbose cipher** — one plaintext letter written as multiple EVA glyphs (`ch`, `qo`, `ee`, `ain` as units) | After the correct merge, entropy rises to natural-language range and word lengths shorten to plausible values | High priority. Directly explains low h2 and rigid bigram structure |
| H3 | Abjad / vowel-suppressed script (Semitic or abbreviated Romance) | Matches vowel-stripped Latin/Hebrew/Arabic baselines on entropy, word length, and type counts | Medium. Testable directly against stripped baselines |
| H4 | Medieval Latin scribal abbreviation / shorthand | Matches an abbreviation-transformed Latin corpus; suffix inventory maps to case/number endings | Medium-high. Herbal register fits |
| H5 | Homophonic or slot-conditioned polyalphabetic cipher | Slot position predicts which sub-alphabet applies; per-slot decipherment succeeds where global fails | Medium. Slot structure is the strongest Phase 1 signal |
| H6a | Table/grille-generated meaningless text (Rugg) | Real text is statistically indistinguishable from `grille` surrogate | Live rival. Must be scored, not dismissed |
| H6b | Autocopying / self-citation generation (Timm & Schinner) | Real text matches `selfcite` surrogate on near-repeat and self-similarity curves | Live rival |
| H7 | Transposition / anagrammed plaintext | Letter-multiset statistics match a natural language even though order does not | Low, but cheap to test |
| H8 | Natural language with agglutinative/affixal morphology, lightly encoded | Induced morphs behave like real morphemes (productivity, paradigm completeness, semantic clustering by section) | Medium. Follows from §3.4 |
| H9 | Constructed/artificial language or ars combinatoria | Slot grammar is near-exhaustively productive; vocabulary is systematically generated | Medium |

Rule: **H6a/H6b are scored on the same scale as H1–H9 in every comparison.** If
a "no plaintext" hypothesis wins, that is the finding, and the translation in
Phase 4 is delivered explicitly labelled as a rendering under a losing model.

**As built** (`reports/phase2/hypothesis_scores.md`, run of 2026-08-20). All ten
records exist as YAML with prediction, falsifier, prior, Phase 1 evidence, search
grid and budget share, committed before any search ran. Eight were funded and
executed; H5 was registered unfunded. Scored gain is bits per token against an
order-2 Markov model of the glyph stream, each hypothesis positioned against 12
seeded surrogates:

| id | best variant | gain | held-out | nulls beating it | outcome |
| --- | --- | --- | --- | --- | --- |
| H2 | fixed-width-3, herbal Latin | −4.23 | −2.37 | 6 / 12 | falsified (widest variant unconverged) |
| H8 | MDL slot inventory | −5.39 | −5.38 | 6 / 12 | falsified |
| H7 | Latin unigram, exact assignment | −9.66 | −8.70 | 3 / 12 | falsified |
| H1 | herbal Latin (Clusius) | −10.28 | −9.07 | **0 / 12** | falsified vs baseline; only null-beating result |
| H4 | abbreviation proxy | −10.38 | −9.34 | 1 / 12 | falsified (this model) |
| H3 | vowel-stripped Latin | −11.01 | −10.03 | 4 / 12 | falsified |
| H6b | copy-plus-edit code | −13.02 | −10.36 | 9 / 12 | falsified |
| H9 | k=2 slot grammar | −15.20 | −13.94 | 7 / 12 | falsified |
| H6a | fitted table + grilles | −23.92 | −18.22 | 11 / 12 | falsified |

The rule above was honoured and its consequence is unusual: **the "no plaintext"
rivals lose too, and by more than the cipher hypotheses.** H6a costs 24 bits per
token more than a bigram model of the glyphs; H6b costs 13 more. So this run gives
no support to Rugg or to Timm & Schinner either — the finding is that *no
registered model of any family* beats the manuscript's own local statistics.
Decision 20 records the falsifications; the one residual asymmetry is H1 on the
herbal-Latin model, which beat all twelve surrogates by 0.16 bits/token (p at the
0.077 floor, q = 0.69 — not significant, but the only asymmetry in the table).

Two priors from the table above were wrong in an informative direction. H2's prior
was "high" and it is still the best-scoring channel, but its advantage is entirely
in the *wide* fixed-width channels (142 and 263 units), which are large codebooks
rather than verbose ciphers — the linguistically motivated searched-merge variant
(22 merges, 48 units) scores −6.50. And H6a's live-rival status is downgraded by
its own score, not by argument.

### 4.3 The decipherment engine (`translations/decipher/`)

Deterministic algorithms only, all seeded:

1. **Channel models** (`channel.py`): monoalphabetic, many-to-one (verbose),
   one-to-many (homophonic), slot-conditioned, and segmentation-aware variants.
   Each declares its key space size — used by the MDL penalty.
2. **Language models** (`lm.py`): order-3 to order-6 character LMs with
   Kneser–Ney or Witten–Bell smoothing over each reference corpus and each
   register subset (e.g. herbal Latin separately). Word-level LM for rescoring.
3. **Search** (`search.py`):
   - EM over mapping probabilities against a fixed LM (Knight et al. style
     statistical decipherment) — the workhorse for H1/H3/H5.
   - Bayesian/Gibbs decipherment with sparse priors for larger key spaces
     (Ravi & Knight style), seeded and iteration-capped.
   - Simulated annealing + beam search with multi-restart grids for
     non-differentiable objectives; restarts enumerated deterministically.
   - Integer programming / exhaustive enumeration where the key space is small.
   - **Glyph-merge partition search** for H2: search over partitions of the EVA
     glyph inventory into cipher units (constrained by observed bigram
     structure and the zero-count bigrams from Phase 1), scoring each partition
     by post-merge entropy fit to candidate languages. This is the highest-value
     single experiment in the plan.
4. **Structural priors** (`priors.py`): initialise and constrain searches using
   Phase 1 slot statistics, positional distributions, and A/B structure, so the
   search is not starting from uniform noise.
5. **Runner** (`run_hypothesis.py`): takes a hypothesis YAML, executes the grid,
   writes every candidate key with its scores to
   `output/decipher/candidates.parquet` — including losers.

   **As built:** implemented as described. Rows carry hypothesis, variant, corpus
   (real or which null), split (train or holdout), model/data/total bits, gain,
   the key as a readable mapping, the merge list, iterations, restarts,
   evaluations, `budget_spent_s`, `converged` and `truncated`.
6. **Compute budget** (`budget.py`): a hard **24 h wall-clock ceiling** across
   all Phase 2/3 search runs, declared in `config.py` and enforced by the runner.
   Consequences for the design:
   - Budget is *allocated up front* per hypothesis (proportional to prior and
     key-space size), recorded in the hypothesis YAML, and spent — not
     discovered. H2 (glyph-merge search) gets the largest single allocation.
   - Every search is **anytime**: it checkpoints deterministically at fixed
     iteration counts and reports the best-so-far with its elapsed budget, so a
     truncated run is still a valid, reportable result.
   - **Truncation is recorded, never hidden**: each candidate row carries
     `budget_spent_s`, `converged: bool`, `truncated: bool`. A hypothesis that
     lost while truncated is reported as *inconclusive*, not falsified.
   - Determinism is defined by iteration count, not by time — resuming from a
     checkpoint must reproduce the same result as an uninterrupted run (tested).
   - The null-distribution runs (§4.5) are inside the same budget: a search that
     cannot afford its own null does not get to report a score.

   **As built:** `budget.py` allocates each record's declared share of
   `CONFIG.search_budget_seconds` and hands the search a `Deadline` that can only
   *stop* it (marking `truncated`), never change the result of a run that
   finishes — iteration counts, not seconds, define the output. Null runs are
   inside each hypothesis' allocation, and use the identical settings on the best
   variant only; running every language against every null would quadruple the
   cost for no extra discrimination.
7. **Torch / Apple Metal**: torch with the MPS backend is permitted for the
   larger LMs and for batched scoring. Constraint: **MPS and multi-threaded
   float reductions are not bit-reproducible.** Therefore anything whose value
   lands in a committed artifact (final keys, scores, glosses, confidences) is
   either computed on CPU in float64, or computed on MPS and then *verified* by
   a CPU recomputation of the final selected candidate, with the CPU value being
   the one recorded. MPS is an accelerator for search, never the authority for
   an emitted number. The determinism test (§2.2) runs CPU-only.

   **As built: no torch.** Scoring is vectorised over the *distinct* cipher
   n-grams of a text rather than its positions, which turns a key evaluation into
   one numpy fancy-index over a few thousand rows — about 26,000 evaluations per
   second on CPU in float64. At that rate the whole phase fits in ~25 minutes, so
   the accelerator (and its non-reproducible reductions) was never needed. The
   MPS protocol above stands unused, for Phase 4 to invoke if it ever is.

### 4.4 Anchors and cribs (`translations/decipher/anchors.py`)

Weak but real external constraints, to be catalogued in Phase 3 (§5) and used
as soft evidence, never as assumed truth:

- **Zodiac folio month names** (f70v–f73v) — written in a non-Voynichese,
  Romance/Occitan-like hand. The best available crib for language and date.
- **f116v marginalia** ("michiton oladabas…") and other marginal lines
  (f17r, f66r, f76v) — partially readable, disputed.
- **Herbal folios**: if the plant illustrations are identifiable, plant names in
  medieval herbal lexicons constrain label vocabulary.
- **Star/label folios**: candidate star and month nomenclature.
- **Structural anchor**: recipe/pharma pages (f99r–f102v) plausibly contain
  ingredient lists → predicts repeated nominal forms with list syntax.

Anchor use protocol: an anchor may *rank* candidate keys; it may never be
injected as ground truth into the LM or the training data. Anchor-derived
scores are reported separately from corpus-derived scores.

**As built:** `anchors.py` implements the protocol with an **empty catalogue**.
No anchor can be entered by hand under this plan's automation rule (§0.3), so the
catalogue stays empty until Phase 3 can source the zodiac month names and
marginalia with checksums. `anchor_score` returns 0.0 for every candidate today,
which is the honest value: nothing in the Phase 2 ranking is anchor-derived.

### 4.5 Statistical discipline (`translations/decipher/stats.py`)

The failure mode of Voynich research is multiple comparisons. Enforcement:

- Hypotheses and parameter grids are pre-registered (git-committed) before runs.
- Every reported score carries an **empirical null distribution**: identical
  search run on (a) pseudo-Voynich, (b) shuffled Voynich, (c) surrogate text.
  Significance = position in that null distribution, not a raw likelihood.
- FDR (Benjamini–Hochberg) correction across the full grid; the total number of
  comparisons is logged automatically by the runner.
- **Held-out folios** (§3.1) are scored only once per hypothesis, at the gate.
- A key that scores well in-sample but not on held-out pages is recorded as
  falsified and written to `docs/decisions.md`.

**As built:** all four rules hold, with one limitation stated in the report rather
than smoothed over. The empirical p-value is the real score's position among the
surrogate runs, so with *n* nulls it cannot fall below `1/(n+1)`. Each family
(grille, autocopy, glyph shuffle, order-2 Markov) therefore gets
`CONFIG.null_replicates` independently seeded surrogates; at 3 replicates the
floor is 0.077. Nothing in Phase 2 could have reached p < 0.05 by design, and the
report says exactly that instead of presenting the q-values as a passed test.

### 4.6 Confidence calibration design (used in Phase 4)

Because there is no ground truth, confidence is calibrated on **synthetic
ciphertexts**: take Latin/English of matched size, encipher under each
hypothesis's scheme, run the *entire* pipeline blind, and measure token-level
accuracy as a function of the pipeline's own confidence score. Produce
reliability diagrams and an isotonic/Platt calibration map per hypothesis. The
resulting map is what converts raw scores into the confidence column in Phase 4.

Stated limitation, to be printed in the output: calibration is valid **only if
the true system resembles the hypothesised one**. It bounds optimism; it does
not certify correctness.

**As built (harness in Phase 2, maps built in Phase 4):** `synthetic.py` builds ciphertexts
from a reference corpus under each scheme and runs the *whole* search against
them blind, reporting token-weighted key accuracy and token accuracy. Recovery is
100% for monoalphabetic substitution, fixed-width verbose and abjad. The
reliability diagrams and the isotonic/Platt maps were built in Phase 4
(`translations/calibrate.py`, PAVA isotonic): four of the five keyed hypotheses recover
their hidden key at 100%, so their maps are flat at 1.0 above zero and the confidence
column had to be composed rather than read off the map — see Phase 4 delta 3–4 and
Decision 26. Two engine bugs were caught only by this harness — see Phase 2 delta 3.

### 4.7 Phase 2 exit deliverables — **met 2026-08-20**

- [x] `translations/hypotheses/` — ten registered records (H1–H9 plus H6a/H6b as
      separate files), each with prediction, falsifier and grid, committed before
      the run.
- [x] `reports/phase2/hypothesis_scores.md` — ranked table with null-relative
      significance, held-out results and MDL-penalised scores, plus the explicit
      statement that with 12 nulls the p-value floor is 0.077.
- [x] `reports/phase2/approach.md` — the method write-up.
- [x] `reports/phase2/synthetic_validation.md` — the known-answer tests (not in the
      original deliverable list; added because a search that cannot break its own
      cipher cannot be trusted with the manuscript).
- [x] `output/decipher/candidates.parquet` — 143 candidate rows: every variant,
      every null run, every held-out score, with budget, convergence and
      truncation flags.
- [x] Decision-log entries — Decisions 16–20 (scale, search choice, the H4 proxy,
      H5 unfunded, and the falsifications).
- [x] A ranked shortlist carried into Phase 4: **H2, H8, H1, and H6b as the rival
      control** — all four of which lost, so Phase 4 renders under a losing model
      and must label every artifact accordingly.

**Run cost**: 3,356 s of the 7,200 s ceiling (H2 took 1,750 s of its 3,240 s
allocation); nothing truncated. Wall clock for `make decipher` ≈ 56 min.

---

## 5. Phase 3 — Gap analysis and extensive analysis, round 2

**Goal**: close the specific gaps that Phases 1–2 expose, then run targeted
analysis that directly feeds the translator. Scope here is deliberately
*derived*, not fixed in advance; the items below are the expected set.

### 5.1 Formal gap analysis (`reports/phase3/gap_analysis.md`) — **done 2026-08-20**

Structured as: gap → why it blocks translation → proposed remedy → cost → data
provenance required. Expected gaps (outcome column added after the run;
`reports/phase3/gap_analysis.md` carries the full register):

| Gap | Blocks | Remedy | Outcome |
| --- | --- | --- | --- |
| No token-level cross-transcription alignment | Per-token confidence weighting | Needleman–Wunsch alignment of ZL/IT/GC per line → new `output/translation/token_alignment.parquet` | **Closed**, ZL/IT only (Decision 22). 33,728 tokens; 86.2% read identically |
| No illustration↔label linkage | Anchor-based gloss seeding on labels | Automated only: ingest a published concordance (Voynich Nu / plant-ID lists) as a checksummed source. **No hand annotation** — if no usable source exists, the gap stays open, label-level anchor seeding is dropped, and §7.1.5 falls back to page-level `section` / `illustration_type` | **Open**. No checksummable concordance found; the pre-committed fallback applies |
| Marginalia not in dataset | Best cribs unavailable | Add a `marginalia.jsonl` source with transcription variants and explicit dispute flags | **Open**. Readings are disputed and exist only as prose discussion |
| No paragraph/block segmentation | Line-as-unit vs paragraph-as-unit modelling | Derive from `position` + layout heuristics; validate on a sample | **Closed** without heuristics: IVTFF marks `<%>`/`<$>` inline (Decision 21). 717 blocks |
| Currier/v101 alphabet not mapped | Robustness checks on GC/FG limited | Build and test an explicit mapping table with lossiness documented | **Open**, deliberately deferred; nothing in Phase 3 depends on it |
| No plant/star reference lexicons | Anchor scoring for herbal/astro labels | Add medieval herbal + star-name lexicons to `sources.yaml` | **Partial**: `iau_star_names` pinned; no plant lexicon located |
| Register-matched Latin scarce | LM quality for H4 | Assemble a medieval-herbal Latin subcorpus; document its size limits | **Closed**: `herbal_latin`, 128,497 words, 11× Clusius (Decision 23) |

Each remedy that touches data gets a `sources.yaml` entry or a decision-log
entry — no undocumented data appears in the pipeline.

### 5.2 Targeted analysis round 2 (`translations/analysis/` additions) — **done 2026-08-20**

Driven by the shortlist from Phase 2. Expected work (item 7 was dropped by the
clarifying answers for this session; everything else was built):

1. **Post-merge re-characterisation** — if H2 (verbose cipher) produces a
   plausible merge, re-run the *entire* Phase 1 battery on the merged
   representation. Does merged Voynichese now sit inside the natural-language
   region on entropy, word length, Zipf, and MI decay? This is the make-or-break
   diagnostic.
2. **Slot-to-function mapping** — for the induced slot grammar, test whether
   slot fillers behave like inflectional paradigms: do the same roots appear
   with a consistent suffix set? Is suffix choice predicted by syntactic
   context? Compare paradigm completeness against Latin and Turkish.
3. **Function-word discovery** — identify candidate high-frequency grammatical
   items by distributional clustering (context-vector clustering of word types),
   and test whether their distribution matches function words in baselines.
4. **Semantic-field probe** — do word types cluster by section beyond what page
   topic frequency predicts? If herbal-only and pharma-only vocabularies are
   real, they are the most translatable subsets.
5. **Label-specific analysis** — labels (115) as a nomenclature: are they
   morphologically simpler? Do they resemble entries in a list?
6. **Token-level uncertainty model** — combine transcription alignment,
   uncertainty flags, hapax status and rare-glyph presence into a single
   per-token reliability weight used by the translator.
7. **Number/quantity hypothesis** — pharma/recipe pages: search for
   numeral-like paradigms (small closed sets in list-initial position).
   **Dropped for this session.** Nothing in Phase 1 flagged small closed sets in
   list-initial position, so the probe would have been a scan without a
   pre-registered hypothesis — exactly what §4.5 forbids.
8. **Re-scoring of hypotheses** with the improved representation, anchors, and
   held-out data. Anchors are still unavailable (§5.1), so the re-scoring is on
   representation and held-out data only.

### 5.3 Phase 3 exit deliverables — **met 2026-08-20**

- ✅ `reports/phase3/gap_analysis.md` (7 gaps: 3 closed, 1 partial, 3 open, each with
  cost and provenance), `reports/phase3/round2_findings.md` (7 findings), plus
  `rescoring.md` and the five round-2 topic reports.
- ✅ New `sources.yaml` entries with checksums: `herbal_latin` (multi-part, 15 pinned
  files) and `iau_star_names`.
- ✅ `output/translation/token_alignment.parquet` — 33,728 rows, one per ZL token, with
  its IT counterpart, agreement and reliability weight.
- ✅ Final ranked hypothesis list (`rescoring.md`, 18 rows over two representations) and
  the translator configuration at
  `output/translation/phase3_translator_config.json`.

**Run cost**: 2 h 6 min wall clock, of which 7,440 s of search against a 14,400 s
ceiling. 286 candidates in `output/decipher/round2_candidates.parquet`.

---

## 6. Phase 4 — Automated, repeatable English translation

**Goal**: a single deterministic command that turns `output/` into a
full-coverage English rendering of all 4,072 lines, with calibrated per-token
confidence and mandatory speculative labelling.

### 6.1 Pipeline architecture — **built 2026-08-20**

```
eva_lines (+ metadata, mismatch_index, token_alignment)
  → tokenize (T-variant from config)
  → segment (slot grammar / merge partition)
  → decipher (winning hypothesis key(s) from Phase 2/3)
  → intermediate plaintext hypothesis (e.g. Latin-like string per token)
  → lexicon lookup + morphological analysis against reference lexicons
  → English gloss candidates (ranked, with scores)
  → line-level rendering (word order + light English smoothing, rule-based)
  → confidence calibration
  → emit artifacts + reports
```

Every stage is a pure function with typed inputs/outputs and its own tests.
Intermediate stages are persisted so any English word can be traced back to a
glyph sequence.

### 6.2 Gloss generation (`translations/gloss.py`, `translations/lexicon/`) — **built 2026-08-20, fallback (b) declined**

- Intermediate plaintext token → lexicon lookup (Latin/Romance lemma lists with
  English glosses; morphological stripping for inflected forms).
- Ranked candidate list per token: `(english, lemma, score, evidence)`.
- Where no lexicon hit exists (expected to be common), fall back in order:
  (a) nearest-neighbour lemma by edit distance with a penalty;
  (b) distributional gloss — assign the English word whose corpus distribution
  best matches this Voynich type's distribution (a weak, clearly-flagged
  heuristic);
  (c) transliteration passthrough `⟨daiin⟩`.
- Consistency constraint: one Voynich type resolves to one primary gloss
  corpus-wide by default; per-stratum overrides only when Phase 3 evidence
  supports them, and always logged.

**As built:** fallback (b) is declined (Decision 27) and the chain is strict — the first
rung that fires supplies all the candidates. No per-stratum overrides were taken: Phase 3
showed section-specific *vocabulary*, not section-specific *meaning*. See Phase 4 deltas
5 and 7.

### 6.3 Line rendering (`translations/render.py`) — **built 2026-08-20, no reordering**

- Rule-based English assembly: apply the induced syntactic ordering (from §5.2)
  to reorder glosses; insert function words only where the induced grammar
  licenses them; no free-text generation.

  **As built:** neither reordering nor insertion happens — there is no induced ordering
  model to apply (Decision 28). Word order is the manuscript's own. The band thresholds
  below are applied to the *composed* confidence of Phase 4 delta 4, not to a raw score.
- **Full coverage (per the chosen output posture)**: every line always produces
  a non-empty `english_speculative` string. Low-confidence material is rendered
  but visually marked, never silently invented:

  | Confidence band | Rendering |
  | --- | --- |
  | high (≥ calibrated 0.7) | `plain word` |
  | medium (0.4–0.7) | `*word*` |
  | low (0.15–0.4) | `?word?` |
  | none (< 0.15) | `⟨daiin⟩(≈guess)` — transliteration first, best guess in parens |

- A parallel `english_gated` field masks everything below the medium band with
  `UNKNOWN`. It is retained as the honest diagnostic view and is what §7 uses
  for coverage statistics.

### 6.4 Output artifacts (`output/translation/`) — **written 2026-08-20**

| File | Contents |
| --- | --- |
| `translation_lines.jsonl` / `.parquet` | one row per line: `line_id`, `page_id`, `section`, `currier_language`, `hand`, `text_clean`, `tokens[]` (surface, segmentation, intermediate, gloss candidates top-k, chosen, token_confidence, evidence flags), `english_speculative`, `english_gated`, `line_confidence`, `hypothesis_id`, `key_id`, `banner` |
| `lexicon.jsonl` | Voynich type → ranked English glosses + provenance + support counts |
| `token_alignment.parquet` | cross-transcription per-token agreement (from Phase 3) |
| `manifest.json` | input hashes, config hash, git commit, seeds, package versions |
| `SHA256SUMS` | matching repo convention |
| `reports/translation/folio_readings.md` | human-readable page-by-page rendering, banner at top of every page section |
| `reports/translation/coverage.md` | coverage and confidence distribution by stratum |

**As built:** ranked gloss candidates live once per type in `lexicon.jsonl` and are joined
on `surface` rather than repeated on every token; `translation_lines.jsonl` carries the
primary hypothesis with the full per-token trace and `.parquet` carries all five at line
level; `token_alignment.parquet` is not re-emitted because Phase 3 already writes it here.
`calibration.json` is added. See Phase 4 delta 9.

Schemas added to `schemas/`; validators added to `validators/` mirroring existing
practice. **Nothing is published** — no HuggingFace dataset, no dataset card, no
release. Artifacts remain local to `output/translation/` and
`reports/translation/`, and the existing published VCAT datasets are untouched
by this plan.

### 6.5 Repeatability requirements — **met 2026-08-20**

- `make translate` runs end-to-end offline from `output/` + cached corpora. **As built** the
  expensive blind-search calibration is split into `make calibrate`, so `make translate`
  itself is 33 s (Phase 4 delta 8).
- Two runs produce byte-identical artifacts (asserted in tests).
- Runtime target: full corpus in minutes, not hours, on a laptop, CPU-only; the
  expensive search lives in Phases 2–3 under the 24 h ceiling (§4.3.6) and its
  results are committed as key files. The translation run itself must never need
  torch or MPS.
- Config, seeds and hypothesis id are recorded in every row, so a row can be
  regenerated from the manifest alone.

### 6.6 Phase 4 validation gate — **met 2026-08-20**

- [x] Held-out folios scored once; results reported whatever they are — 0.600 gated
      coverage against 0.613 on the training pages (`coverage.md`).
- [x] Confidence calibration curves produced and included — `calibration.md`, with the
      reliability diagrams computed on synthetic tokens the maps were not fitted on.
- [x] Pseudo-Voynich control run completed (§7.2) and its results included in the same
      report — and it is the first table in `coverage.md`, because the `grille` control
      renders *more* than the manuscript does (Decision 29).
- [x] Banner present in every artifact and every report — asserted by
      `validators/validate_translation_outputs.py` and by `tests/translations/test_phase4.py`.
- [x] Determinism test green — two runs byte-identical.

**Run cost**: 107 s of the 14,400 s calibration ceiling, plus 33 s for the pipeline itself.

**Verdict carried into Phase 5**: the pipeline meets every engineering requirement in this
section and produces a full-coverage, traceable, calibrated rendering — of nothing. Under
the criterion §7.2.1 fixed in advance, the control result already retires it as evidence.
Phase 5's job is to quantify the remaining weaknesses, not to decide the question.

---

## 7. Phase 5 — Strengths and weaknesses of the automated translation

**Goal**: an adversarial, automated self-audit that tells the reader exactly how
much to believe. This phase is a deliverable in its own right and is the
protection against the plan's main risk.

### 7.1 Strength evidence (what would make the translation credible)

Automated tests, each producing a number and a null comparison:

1. **Synthetic recovery** — encipher known Latin/English under the winning
   scheme; run the full pipeline blind; report token accuracy, lemma accuracy,
   and key recovery rate. Upper bound on achievable quality.
2. **Held-out generalisation** — key learned on train folios, scored on held-out
   folios; degradation measured.
3. **Cross-transcription stability** — full pipeline re-run on IT; per-token
   gloss agreement rate. Target to beat: the 29.3% baseline identity of the
   transcriptions themselves — gloss agreement below that is meaningless.
4. **Internal consistency** — same Voynich type glossed the same way across
   sections; paradigm coherence; repeated-phrase consistency.
5. **Illustration congruence** — herbal pages should yield plant/botanical
   vocabulary; balneological pages should yield body/water vocabulary; pharma
   pages should yield ingredient/measure vocabulary. Measured as topic
   concentration versus a permutation null on page labels. **A genuine positive
   here would be the strongest evidence in the whole programme.** Runs at
   page level using existing `section` / `illustration_type` metadata (always
   available); the sharper label-level variant runs only if §5.1 lands an
   automated concordance source.
6. **Syntactic plausibility** — perplexity of the rendered English under an
   independent English LM, versus (a) shuffled-gloss rendering and (b) rendering
   produced from pseudo-Voynich.
7. **Anchor agreement** — do zodiac/marginalia anchors come out consistent with
   the key rather than contradicting it?

### 7.2 Weakness evidence (the tests designed to break it)

1. **Pseudo-Voynich control (the decisive test)** — run the *entire* pipeline,
   unchanged, on `grille` and `selfcite` corpora that were tuned to match
   Voynich statistics. If the output is comparably fluent and comparably
   confident, the pipeline is a fluency generator and its Voynich output carries
   no evidential weight. **This comparison is printed at the top of the report,
   before any sample translation.**
2. **Shuffled-input control** — same, on shuffled Voynichese.
3. **Rival-language ambiguity** — run the winning scheme against several
   candidate plaintext languages. If Latin, Hebrew-transliterated and Turkish
   all yield similar scores, the method cannot identify the language and the
   glosses are arbitrary.
4. **Key instability** — how much do glosses change under (a) different seeds,
   (b) different restarts with near-equal scores, (c) small perturbations of the
   training subset? High volatility ⇒ the key is not identified.
5. **Ablations** — tokenization variant, comma policy, transcription source,
   uncertainty filtering, stratum. Report the swing in headline output.
6. **Known-weak zones**, quantified and listed explicitly: labels, circular and
   radial text, high-hapax lines, `has_uncertain`/`has_illegible`/`has_alternatives`
   rows, rare and "weirdo" glyphs, high-ASCII tokens, Currier-unknown pages, and
   the 655 content-mismatch lines (16.1%) where transcribers disagree materially.
7. **Coverage honesty** — the `english_gated` view's true coverage at each
   confidence band, per stratum. If gated coverage is, say, 3%, the report says
   so in the first paragraph, regardless of how complete `english_speculative`
   looks.

### 7.3 Deliverable

`reports/translation/strengths_weaknesses.md`, generated by `make audit`,
structured as:

1. Banner and one-paragraph bottom line ("what this is / what it is not").
2. The pseudo-Voynich control comparison table.
3. Gated coverage by stratum.
4. Strength evidence table (metric, value, null, verdict).
5. Weakness evidence table (test, result, implication).
6. Known-weak zones list with row counts.
7. **Falsification conditions**: exactly what result would retire the current
   hypothesis, and what evidence would raise confidence.
8. Links to every decision-log entry generated by the programme.

Plus `docs/decisions.md` entries for all negative results — per `AGENTS.md`, a
cleanly falsified hypothesis is a deliverable.

### 7.4 Kill criteria (agreed in advance)

Declare the decipherment attempt unsuccessful — and publish that as the finding,
with the translation clearly labelled as an unvalidated rendering — if:

- The pipeline produces comparable fluency and confidence on pseudo-Voynich; **or**
- Held-out folio performance is indistinguishable from the null distribution; **or**
- Cross-transcription gloss agreement is no better than baseline transcription
  identity; **or**
- Multiple unrelated plaintext languages score equivalently; **or**
- Illustration congruence shows no signal above the permutation null.

Meeting any kill criterion does not stop delivery of the Phase 4 artifacts (the
user asked for full-coverage output); it changes their framing to
"speculative rendering under a hypothesis that failed validation", stated in the
banner, the report's first paragraph, and `reports/translation/coverage.md`.

---

## 8. Cross-cutting engineering requirements

- **Tests**: every module in `translations/` has unit tests; golden-file tests
  for the pipeline on a 20-line fixture; determinism tests on hashes; property
  tests for tokenizers (round-trip, idempotence).
- **CI**: `ruff check . && black --check . && mypy vcat parsers builders
  validators hf translations && pytest tests/` — mypy scope extended to
  `translations`.
- **Performance**: search phases may be slow but must be resumable and must
  checkpoint deterministically; the translation run must be fast.
- **Docs**: `docs/translation_method.md` (method), `docs/decisions.md` (every
  choice), `docs/sources.md` (every corpus). No dataset cards — nothing from this
  plan is published (§0.3). The repo's "methodology change ⇒ card update" rule
  still binds the *existing* published datasets, which this plan does not touch.
- **No scope creep into existing packages**: `translations/` depends on
  `vcat`/`output`, never the reverse.
- **Delegation**: implementation tasks are farmed to lower-power subagents with
  a precise spec per module; review and statistical design stay with the lead.

---

## 9. Sequencing, sizing and gates

| Phase | Output | Rough size | Blocking gate |
| --- | --- | --- | --- |
| 0 Foundations | scaffold, corpora, nulls, determinism | ~1 unit | determinism test green; corpora checksummed |
| 1 Analysis R1 | 9 topic reports + summary | ~3 units | **landmark reproduction gate (§3.10)** |
| 2 Approach | hypothesis registry, engine, scores | ~3 units | hypotheses pre-registered before runs; null distributions computed |
| 3 Gap + Analysis R2 | gap analysis, remediation, re-scoring | ~2 units | new data has provenance; held-out untouched |
| 4 Translation | `output/translation/*`, folio readings | ~2 units | validation gate (§6.6) |
| 5 Audit | strengths/weaknesses report | ~1 unit | pseudo-Voynich control run and reported |

("unit" = a coherent block of work, not a calendar promise. Phases 1→2 and
3→4 may partially overlap; Phase 5 tests must be written *before* Phase 4
output is read, to avoid tuning the pipeline against its own audit.)

**Compute budget (24 h total, Phases 2–3 search only)** — indicative allocation,
declared in config before any run and revised only by decision-log entry:

| Allocation | Share | Rationale |
| --- | --- | --- |
| H2 glyph-merge partition search + its nulls | ~40% (≈9.5 h) | Highest-value single experiment (§4.3.3) |
| H3/H4/H5 EM + Bayesian decipherment + nulls | ~30% (≈7 h) | Three hypotheses, shared LM infrastructure |
| H1/H7/H8/H9 cheaper tests + nulls | ~10% (≈2.5 h) | Small key spaces or direct distributional tests |
| H6a/H6b surrogate fitting and control runs | ~10% (≈2.5 h) | Non-optional: the controls are the point |
| Reserve for Phase 3 re-scoring after remediation | ~10% (≈2.5 h) | Held back until gaps are closed |

Phase 1 analysis, Phase 4 translation and Phase 5 audit sit outside this ceiling
(all are minutes-to-low-hours, CPU-only).

Each phase ends with a PR containing: code + tests + report + decision-log
entries + doc updates, per repo convention.

---

## 10. Risk register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Pipeline produces fluent nonsense and it is believed | High | Severe (reputational; misinformation) | §7.2.1 pseudo-Voynich control printed first; mandatory banners; kill criteria agreed in advance |
| Multiple-comparison false positive | High | Severe | Pre-registration, FDR correction, empirical nulls, held-out folios scored once |
| Transcription noise mistaken for signal | High | High | Everything re-run on IT and on the consensus subset; transcription-limited metrics labelled |
| Tokenization artifact drives result | Medium-high | High | Every headline metric reported over the tokenization × comma-policy grid |
| Entropy comparisons invalidated by sample size | Medium-high | High | Bias correction + sample-size-matched baselines, mandatory |
| Reference corpus is anachronistic or wrong register | Medium | Medium | Register-matched subcorpora; report LM sensitivity as an ablation |
| Corpus licensing blocks redistribution | Medium | Low-medium | Fetch-not-vendor; licence recorded per source |
| Anchors (marginalia) are themselves disputed | High | Medium | Anchors only rank, never train; dispute flags carried through |
| Determinism lost via dict/set ordering or library nondeterminism | Medium | Medium | Sorted iteration discipline; hash-equality tests in CI |
| MPS/float nondeterminism leaks into emitted numbers | Medium | Medium | MPS for search only; final candidate recomputed on CPU float64 and that value recorded (§4.3.7); determinism test is CPU-only |
| 24 h ceiling truncates a search that would have succeeded | Medium | Medium | Anytime search with checkpoints; `truncated` flag; truncated losers reported as *inconclusive*, not falsified; reserve allocation held back |
| Budget consumed by an unpromising hypothesis | Medium | Low-medium | Up-front per-hypothesis allocation tied to prior and key-space size; no dynamic reallocation without a decision-log entry |
| Scope creep into a general decipherment framework | Medium | Medium | Simplicity-first rule; each module justified by a named phase gate |

---

## 11. Reviewer decisions (resolved)

All five open questions have been answered. Recorded here as binding
constraints; each is reflected in the relevant section above and each becomes a
`docs/decisions.md` entry at Phase 0.

| # | Question | Decision | Where it binds |
| --- | --- | --- | --- |
| 1 | Publication posture | **No publication.** Nothing goes to HuggingFace or any external host; no dataset cards for translation outputs. | §0.3, §0.4.6, §6.4, §7.4, §8 |
| 2 | Intermediate plaintext language priority | **No preference** — the plan's default ordering stands: Latin (herbal register) first, Romance/Germanic/Semitic secondary, contrast set for discrimination. | §2.4, §4.2 |
| 3 | Manual annotation | **All automated.** No hand-annotated subsets. Gaps that no checksummed source can close stay open and are reported as open. | §5.1, §7.1.5 |
| 4 | Torch | **Permitted, incl. Apple Metal (MPS).** Search-time accelerator only; every emitted number is CPU float64. | §0.3, §4.3.7, §6.5 |
| 5 | Compute ceiling | **24 h wall clock** across all Phase 2/3 search runs, allocated per hypothesis up front. | §4.3.6, §9 |

### 11.1 Consequences worth flagging

- **No publication simplifies the honesty problem but does not remove it.** The
  banner, calibration and pseudo-Voynich control requirements stand unchanged —
  a local artifact that reads as a translation is still capable of misleading
  its reader, including us. §0.4 applies in full.
- **All-automated annotation costs one test's sharpest form.** Label↔illustration
  linkage is the single most useful missing dataset for anchor seeding. Without
  hand annotation it depends entirely on finding a published, licensable
  concordance. If none lands, §7.1.5 runs only at page level — weaker, but still
  the strongest available evidence of semantic content. This is recorded as an
  accepted limitation, not a deferred task.
- **MPS buys search throughput, not credibility.** It changes how many restarts
  and how large an LM Phase 2 can afford inside 24 h; it must not change any
  recorded value. The CPU-recompute rule (§4.3.7) is what keeps the determinism
  contract (§2.2) intact.
- **24 h is a real constraint on ambition.** It forces the anytime/checkpoint
  design and the up-front allocation, and it makes the *inconclusive* verdict a
  first-class outcome alongside *supported* and *falsified*. Reporting a
  truncated search as a falsification would be the easiest way to poison the
  decision log, so the runner enforces the distinction rather than leaving it to
  the writer.
- **Nulls are not negotiable under budget pressure.** If a hypothesis cannot
  afford both its search and its empirical null within its allocation, its
  allocation is too small — the search is shortened, never the control.

---

## Appendix A — Reference points and prior art to check against

Not to be copied, but the programme must be aware of, and where possible
reproduce or contrast with: Currier's A/B distinction; Tiltman's and Stolfi's
word-structure paradigms (crust/mantle/core); Landini's and Zandbergen's
transcription work; Bowern & Lindemann's linguistic surveys; Montemurro &
Zanette's information-structure analysis; Reddy & Knight's computational
analysis; Rugg's grille hypothesis; Timm & Schinner's self-citation model;
Knight/Ravi's statistical decipherment methods; Schinner's random-walk
statistics; the LAAFU (line as a functional unit) observations. Each is a
target for the "can our pipeline reproduce this?" checklist in Phase 1.

## Appendix B — Artifact inventory produced by this plan

```
translations/                       new package (all new code)
tests/translations/                 tests
plans/001_initial_automated_english_translation.md   this file
reports/phase1/*.md|json            analysis round 1
reports/phase2/*.md|json            hypothesis scores + approach
reports/phase3/*.md|json            gap analysis + analysis round 2
reports/translation/                folio readings, coverage, strengths/weaknesses
output/translation/                 translation_lines, lexicon, token_alignment,
                                    manifest, SHA256SUMS
schemas/translation_*.json          output schemas
docs/translation_method.md          method write-up
docs/decisions.md                   appended: every decision + every negative result
docs/sources.md, data_sources/sources.yaml   reference corpora with checksums
Makefile                            + corpora, analyse1, analyse2, decipher,
                                    translate, audit
```
