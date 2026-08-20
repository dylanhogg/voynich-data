# Translation method (plan 001, Phases 4–5)

> **SPECULATIVE OUTPUT — unvalidated rendering under a hypothesis that FAILED VALIDATION.
> Everything this document describes is model output, not a reading of the manuscript.
> Nothing produced by this pipeline is published.**

This is the method behind `output/translation/translation_lines.jsonl` and
`reports/translation/`. Read `reports/translation/strengths_weaknesses.md` first: it is the
Phase 5 audit, and it declares the decipherment attempt **unsuccessful** on 4 of the 5 kill
criteria plan 001 §7.4 agreed in advance (Decision 30). `coverage.md` is next, for the
control comparison that drives the verdict.

## The short version

The pipeline takes each manuscript line, re-tokenises it under the merge partition Phase 2
found, applies a substitution key Phase 2/3 committed to, treats the resulting letter
string as Latin, looks it up in Whitaker's Words, and prints the English gloss with a
confidence marker. Every stage is a pure function and every English word traces back to a
glyph sequence.

The keys it uses all **lost** to an order-2 Markov model of the manuscript's own
statistics. The pipeline is therefore a demonstration of what a losing model produces, run
end to end and measured, rather than a translation.

## Stages

```
eva_lines (ZL)
  -> tokenize          T1-glyph, comma = word break            translations.tokenize
  -> represent         T3-merge, 22 merges from Phase 2 H2     translations.represent
  -> decode            channel units -> plaintext letters      translations.decode
  -> gloss             Latin stem -> ranked English senses     translations.gloss
  -> score             raw score per token                     translations.pipeline
  -> null              20 permuted keys, per-token p-value     translations.pipeline
  -> calibrate         isotonic map from synthetic ciphertext  translations.calibrate
  -> render            confidence bands, two English views     translations.render
  -> emit              artifacts + reports                     translations.phase4
```

### Decode

A key maps *channel units* to plaintext letters, so a key means nothing without the
channel it was searched on. The channel is recovered from the candidate's variant string:
`plain` uses the representation's own units, `fixed-width-N` groups them in Ns. Units the
search never saw are folded to the rare symbol `?`, exactly as the search folded them, and
counted — a token decoded mostly from rare units says so in `key_coverage`.

Five hypotheses committed to a key and are rendered in full: H1, H2, H3, H4, H7. The other
four (H6a, H6b, H8, H9) are generative — they claim a production process rather than an
encipherment — so there is no plaintext to gloss.

### Gloss

`data_sources/cache/corpora/whitakers_words_dictline.gen`, SHA256-pinned in
`sources.yaml`, parsed to 48,000 Latin stems with English senses. A strict fallback chain,
first rung wins:

1. exact stem match (score 1.00);
2. stem match after one inflectional ending is stripped (0.75);
3. best stem at edit distance 1, verified (0.45);
4. nothing — the renderer prints `⟨surface⟩` and claims no English.

The distributional gloss the plan lists as fallback (b) is **not implemented**; see
Decision 27. Glossing is per type, so one Voynich type resolves to one primary gloss
corpus-wide.

### Score, null and confidence

    raw       = gloss score x length specificity x key coverage
    confidence = calibrated(raw) x (1 - null p) x transcription reliability

**Length specificity** is measured, not assumed: random strings are drawn from the decoded
text's own letter distribution and looked up, and the specificity of a length is `1 - hit
rate`. On the H1 rendering a one-letter hit is worth 0.087 and a two-letter hit 0.60,
because a short string hits a 48,000-stem dictionary almost whatever it is.

**The null p-value** is the pipeline's main defence. The key's letter assignments are
permuted 20 times — destroying its information while keeping its letter inventory — and
every token is scored again. `null_p` is the share of permutations that glossed the token
at least as well, floored at 1/21.

**Calibration** is fitted on ciphertext whose answer we hid: a reference corpus in the
language the hypothesis' own model assumes, enciphered under its own scheme at its own
channel width, attacked blind with its own search settings, then pushed through the same
gloss stage. Isotonic (PAVA), fitted on half the synthetic tokens and diagrammed on the
other half. See Decision 26 for why the map is flat for four of the five hypotheses.

**Reliability** is the Phase 3 per-token cross-transcription weight
(`output/translation/token_alignment.parquet`).

### Render

Word order is the manuscript's own and no function words are inserted. The plan called for
reordering under an induced syntactic grammar; Phase 1 found no word-order grammar to
induce and Phase 3 did not change that, so reordering would be invention (Decision 28).

| Confidence | `english_speculative` |
| --- | --- |
| >= 0.7 | `word` |
| 0.4-0.7 | `*word*` |
| 0.15-0.4 | `?word?` |
| < 0.15 | `⟨surface⟩(≈guess)` |

`english_gated` masks everything below the medium band with `UNKNOWN`. It is the view the
coverage statistics use.

## Controls

The §6.6 gate requires the pseudo-Voynich control, and it is the first thing
`coverage.md` prints. `grille` (Rugg-style table generation) and `selfcite` (Timm-style
autocopying) are built from the manuscript's own statistics, matched in token count, and
encode nothing. The identical pipeline, key and lexicon run over them.

`grille` renders 75.1% of tokens against the manuscript's 61.1%, so the pipeline fails its
own decisive test. Phase 4 acts on that itself: `translations.config.active_banner()` returns
one of two banner strings, and Phase 4 picks the failed-validation one whenever the control
ratio reaches 1.0. Both strings begin with `SPECULATIVE OUTPUT`, so the JSON schema is
unchanged; the validator checks that the banner on disk matches the verdict recorded in
`coverage.json` (Decision 31).

## The audit

Phase 5 (`make audit`, `translations/audit/`) re-runs this pipeline over everything that
should change the answer and everything that should not: fresh key searches under six seeds
and three perturbed training subsets, four rival plaintext languages, eight ablations, ZL
against IT, shuffled surrogates, and page-level illustration congruence measured against the
*untranslated* types. `reports/translation/strengths_weaknesses.md` holds the results and the
kill-criteria table. Two of its findings bear directly on how this method may be quoted: the
key is not identified — re-searching changes seven tokens in ten (Decision 33) — and where the
two transcriptions disagree, so do the glosses, four times in five (Decision 34).

## Reproducing

```bash
make calibrate   # blind search on synthetic ciphertext -> output/translation/calibration.json
make translate   # the pipeline + validators -> output/translation/, reports/translation/
make audit       # the Phase 5 self-audit -> reports/translation/strengths_weaknesses.md
```

All three are offline, CPU-only and deterministic: two runs produce byte-identical artifacts,
asserted in `tests/translations/test_phase4.py`. Seeds, config hash, git commit, package
versions and input checksums are in `output/translation/phase4_manifest.json` and
`phase5_manifest.json`, neither of which carries a wall-clock field, by design.

Reproducing a committed rendering from your own code needs its seed: pass
`translations.phase4.render_salt(hypothesis_id, view)` to the pipeline, or the random-key
null draws differently and you will report numbers the artifacts do not have.

## What would change the verdict

Not a better lexicon and not a smoother renderer. The pipeline is downstream of a key that
loses to a Markov model, and the control shows it renders gibberish at least as fluently
as it renders the manuscript. What would change the verdict is a hypothesis that beats its
surrogates in Phase 2/3 terms, or an anchor catalogue — an illustration↔label concordance
or a defensible marginalia reading — that ties a rendering to something outside the text.
Both remain open; see `reports/phase3/gap_analysis.md`, and
`reports/translation/strengths_weaknesses.md` for the falsification conditions in full.
