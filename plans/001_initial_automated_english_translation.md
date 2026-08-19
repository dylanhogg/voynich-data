# Plan 001 — Initial Automated English Translation

**Status**: Phases 0–1 complete (landmark gate green); Phases 2–5 not started
**Author**: VCAT / agent-assisted
**Date**: 2026-08-19 (Phases 0 and 1 implemented 2026-08-19)
**Scope**: Extend voynich-data (VCAT) from dataset building into analysis, code
breaking, and a best-efforts automated English translation.

---

## Phase status

| Phase | State | Evidence |
| --- | --- | --- |
| 0 — Foundations | **Complete** | `translations/` package (config, determinism, io, tokenize, strata, corpora, nulls, phase0), 10 checksum-pinned reference corpora, 48 new tests (391 passed / 7 skipped total), `output/translation/phase0_manifest.json` byte-identical across runs |
| 1 — Analysis round 1 | **Complete** | `translations/analysis/` (12 modules), `reports/phase1/` (9 topic reports + `summary.md`), landmark gate **GREEN** (6/6), 64 new tests (455 passed / 7 skipped total), `make analyse1` ≈100 s and byte-stable across runs |
| 2 — Hypothesis space + search | Not started | — |
| 3 — Analysis round 2 | Not started | — |
| 4 — Translation pipeline | Not started | — |
| 5 — Audit + honesty gate | Not started | — |

**Run Phases 0–1:**

```bash
make corpora   # fetch + SHA256-verify reference corpora into data_sources/cache/corpora/
make phase0    # verify inputs, summarise strata, write output/translation/phase0_manifest.json
make analyse1  # Phase 1 suite -> reports/phase1/ (~100 s; non-zero exit if the gate is red)
make test      # 455 passed, 7 skipped
```

Start reading at `reports/phase1/summary.md`: findings table, landmark gate, and
the "what we still cannot tell" list that feeds Phase 3.

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
so a slot tokenization always names the model behind it. `T3-merge` still raises
`NotImplementedError` pending the Phase 2 merge search.

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
7. **Torch / Apple Metal**: torch with the MPS backend is permitted for the
   larger LMs and for batched scoring. Constraint: **MPS and multi-threaded
   float reductions are not bit-reproducible.** Therefore anything whose value
   lands in a committed artifact (final keys, scores, glosses, confidences) is
   either computed on CPU in float64, or computed on MPS and then *verified* by
   a CPU recomputation of the final selected candidate, with the CPU value being
   the one recorded. MPS is an accelerator for search, never the authority for
   an emitted number. The determinism test (§2.2) runs CPU-only.

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

### 4.7 Phase 2 exit deliverables

- `translations/hypotheses/` with all registered hypotheses.
- `reports/phase2/hypothesis_scores.md` — ranked table with null-relative
  significance, held-out results, and MDL-penalised scores.
- `reports/phase2/approach.md` — the full method write-up.
- Decision-log entries for hypotheses falsified at this stage.
- A ranked shortlist (expected: 2–4 hypotheses) carried into Phase 4.

---

## 5. Phase 3 — Gap analysis and extensive analysis, round 2

**Goal**: close the specific gaps that Phases 1–2 expose, then run targeted
analysis that directly feeds the translator. Scope here is deliberately
*derived*, not fixed in advance; the items below are the expected set.

### 5.1 Formal gap analysis (`reports/phase3/gap_analysis.md`)

Structured as: gap → why it blocks translation → proposed remedy → cost → data
provenance required. Expected gaps:

| Gap | Blocks | Remedy |
| --- | --- | --- |
| No token-level cross-transcription alignment | Per-token confidence weighting | Needleman–Wunsch alignment of ZL/IT/GC per line → new `output/translation/token_alignment.parquet` |
| No illustration↔label linkage | Anchor-based gloss seeding on labels | Automated only: ingest a published concordance (Voynich Nu / plant-ID lists) as a checksummed source. **No hand annotation** — if no usable source exists, the gap stays open, label-level anchor seeding is dropped, and §7.1.5 falls back to page-level `section` / `illustration_type` |
| Marginalia not in dataset | Best cribs unavailable | Add a `marginalia.jsonl` source with transcription variants and explicit dispute flags |
| No paragraph/block segmentation | Line-as-unit vs paragraph-as-unit modelling | Derive from `position` + layout heuristics; validate on a sample |
| Currier/v101 alphabet not mapped | Robustness checks on GC/FG limited | Build and test an explicit mapping table with lossiness documented |
| No plant/star reference lexicons | Anchor scoring for herbal/astro labels | Add medieval herbal + star-name lexicons to `sources.yaml` |
| Register-matched Latin scarce | LM quality for H4 | Assemble a medieval-herbal Latin subcorpus; document its size limits |

Each remedy that touches data gets a `sources.yaml` entry or a decision-log
entry — no undocumented data appears in the pipeline.

### 5.2 Targeted analysis round 2 (`translations/analysis/` additions)

Driven by the shortlist from Phase 2. Expected work:

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
8. **Re-scoring of hypotheses** with the improved representation, anchors, and
   held-out data.

### 5.3 Phase 3 exit deliverables

- `reports/phase3/gap_analysis.md`, `reports/phase3/round2_findings.md`.
- New/updated `sources.yaml` entries with checksums.
- `output/translation/token_alignment.parquet` and the token reliability model.
- Final ranked hypothesis list with post-remediation scores → the translator's
  configuration.

---

## 6. Phase 4 — Automated, repeatable English translation

**Goal**: a single deterministic command that turns `output/` into a
full-coverage English rendering of all 4,072 lines, with calibrated per-token
confidence and mandatory speculative labelling.

### 6.1 Pipeline architecture

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

### 6.2 Gloss generation (`translations/gloss.py`, `translations/lexicon/`)

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

### 6.3 Line rendering (`translations/render.py`)

- Rule-based English assembly: apply the induced syntactic ordering (from §5.2)
  to reorder glosses; insert function words only where the induced grammar
  licenses them; no free-text generation.
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

### 6.4 Output artifacts (`output/translation/`)

| File | Contents |
| --- | --- |
| `translation_lines.jsonl` / `.parquet` | one row per line: `line_id`, `page_id`, `section`, `currier_language`, `hand`, `text_clean`, `tokens[]` (surface, segmentation, intermediate, gloss candidates top-k, chosen, token_confidence, evidence flags), `english_speculative`, `english_gated`, `line_confidence`, `hypothesis_id`, `key_id`, `banner` |
| `lexicon.jsonl` | Voynich type → ranked English glosses + provenance + support counts |
| `token_alignment.parquet` | cross-transcription per-token agreement (from Phase 3) |
| `manifest.json` | input hashes, config hash, git commit, seeds, package versions |
| `SHA256SUMS` | matching repo convention |
| `reports/translation/folio_readings.md` | human-readable page-by-page rendering, banner at top of every page section |
| `reports/translation/coverage.md` | coverage and confidence distribution by stratum |

Schemas added to `schemas/`; validators added to `validators/` mirroring existing
practice. **Nothing is published** — no HuggingFace dataset, no dataset card, no
release. Artifacts remain local to `output/translation/` and
`reports/translation/`, and the existing published VCAT datasets are untouched
by this plan.

### 6.5 Repeatability requirements

- `make translate` runs end-to-end offline from `output/` + cached corpora.
- Two runs produce byte-identical artifacts (asserted in tests).
- Runtime target: full corpus in minutes, not hours, on a laptop, CPU-only; the
  expensive search lives in Phases 2–3 under the 24 h ceiling (§4.3.6) and its
  results are committed as key files. The translation run itself must never need
  torch or MPS.
- Config, seeds and hypothesis id are recorded in every row, so a row can be
  regenerated from the manifest alone.

### 6.6 Phase 4 validation gate (before any artifact is shared)

- [ ] Held-out folios scored once; results reported whatever they are.
- [ ] Confidence calibration curves produced and included.
- [ ] Pseudo-Voynich control run completed (§7.2) and its results included in
      the same report.
- [ ] Banner present in every artifact and every report.
- [ ] Determinism test green.

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
