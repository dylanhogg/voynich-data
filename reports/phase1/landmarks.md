# Phase 1 — Landmark reproduction gate

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Landmark reproduction

| landmark | result | evidence |
| --- | --- | --- |
| Conditional entropy h2 well below natural language | PASS | Voynich h2 2.253 vs lowest baseline douay_rheims 3.077 |
| Rigid word-internal glyph ordering / slot structure | PASS | within-word shuffle raises h2 by 1.344 bits; k=1 acceptor accepts 92.6% of held-out word types |
| Zipf-like frequencies with an anomalous low-frequency tail | PASS | α = 2.116, hapax 70.0% vs highest baseline clusius_rariorum 67.0% |
| High rate of near-repeat adjacent words | PASS | within-2 rate 14.8% vs austen_pride_prejudice 8.2% |
| Currier A/B divergence surviving sample-size control | PASS | matched h2 differs by 0.270 bits; vocabulary Jaccard 0.151 |
| Line-position effects (initial/final differ from mid) | PASS | Voynich χ² p = 0.00e+00, V = 0.307; Latin control p = 0.589 |

**Gate: GREEN.** All six known properties reproduce from `output/`, so the pipeline is trustworthy enough to build Phase 2 on.
