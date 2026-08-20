# Phase 1 — Summary

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Findings

| finding | effect size | 95% CI | robust across EVA transcriptions | survives on consensus subset | distinguishes Voynich from pseudo-Voynich |
| --- | --- | --- | --- | --- | --- |
| h2 far below natural language at matched size | -0.965 bits vs mean baseline | [2.242, 2.262] | yes | yes | yes |
| Hapax rate above every natural baseline | 0.700 | — | yes | yes | yes |
| Adjacent near-repeat rate several times natural language | 0.148 vs 0.038 (Latin) | — | yes | yes | yes |
| Rigid word-internal ordering (slot structure) | k=1 acceptor accepts 0.926 of held-out types | — | — | — | yes |
| Affixal structure pays for itself far more than in Latin | 1.513 vs 0.153 bits/word | — | — | — | yes |
| Line position changes the glyph distribution (LAAFU) | Cramér's V 0.307 (Latin control 0.024) | — | — | — | — |
| Currier A/B differ after equalising sample size | Δh2 0.270 bits, Jaccard 0.151 | — | yes | — | — |
| Word order carries little information | 0.093 bits/word gained from order vs 0.504 in Latin | — | — | — | — |
| Page word distributions track the illustration sections | NMI 0.410, purity 0.762 | — | — | — | — |
| No single transformation maps Currier A onto B (negative result) | best gain 0.023 over a 0.24 baseline | — | — | — | — |

Blank cells are questions this table cannot answer for that finding, not silent passes.

## Landmark gate

| landmark | result | evidence |
| --- | --- | --- |
| Conditional entropy h2 well below natural language | PASS | Voynich h2 2.253 vs lowest baseline douay_rheims 3.077 |
| Rigid word-internal glyph ordering / slot structure | PASS | within-word shuffle raises h2 by 1.344 bits; k=1 acceptor accepts 92.6% of held-out word types |
| Zipf-like frequencies with an anomalous low-frequency tail | PASS | α = 2.116, hapax 70.0% vs highest baseline clusius_rariorum 67.0% |
| High rate of near-repeat adjacent words | PASS | within-2 rate 14.8% vs austen_pride_prejudice 8.2% |
| Currier A/B divergence surviving sample-size control | PASS | matched h2 differs by 0.270 bits; vocabulary Jaccard 0.151 |
| Line-position effects (initial/final differ from mid) | PASS | Voynich χ² p = 0.00e+00, V = 0.307; Latin control p = 0.589 |

**Gate: GREEN.** All six known properties reproduce from `output/`, so the pipeline is trustworthy enough to build Phase 2 on.

## What we still cannot tell (input to Phase 3)

1. Whether the low h2 comes from the writing system (verbose cipher, abjad) or from the language: entropy alone cannot separate those, and both fit.
2. Whether Currier A and B are two languages, two cipher settings, or two scribal habits: hand, section and quire each explain part of the per-line variance and none dominates.
3. Whether the hapax tail is a property of the text or of transcription disagreement: hapax rate is stable across the EVA pair but the non-EVA transcriptions disagree enough that this cannot be settled at line level.
4. Whether words are morphologically composed or positionally generated: the order-2 chain and the MDL morphology are within ~1 bit/word of each other on the manuscript, unlike on natural language where morphology wins clearly.
5. What labels refer to: there is no illustration↔label linkage in the data, so the 115 label lines cannot be tied to the plants, stars or nymphs beside them.
6. Whether the near-repeat rate reflects meaningful repetition or autocopying: the tuned selfcite surrogate reproduces it, and nothing in the text distinguishes the two at this level of analysis.
7. Token-level alignment across transcriptions is still missing: the mismatch index aligns lines, so per-glyph disagreement cannot be quantified.

## Run

Topics: currier, entropy, landmarks, lexis, morphology, position, robustness, syntax, uncertainty. Bootstrap resamples: 200. Wall clock: 97s (excluded from the manifest, which is byte-stable).
