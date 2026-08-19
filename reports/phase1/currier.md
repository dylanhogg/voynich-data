# Phase 1 — Currier A versus B

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Metric battery, full and sample-size matched

| view | tokens | types | ttr | hapax_rate | mean_word_length | h1 | h2 | h3 | near_repeat_within_2 | gallows_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| currier_a (full) | 10,774 | 3,381 | 0.314 | 0.722 | 4.298 | 3.858 | 2.365 | 2.146 | 0.173 | 0.112 |
| currier_b (full) | 22,521 | 4,821 | 0.214 | 0.689 | 4.635 | 3.834 | 2.100 | 1.878 | 0.135 | 0.116 |
| currier_a (matched) | 10,774 | 3,381 | 0.314 | 0.722 | 4.298 | 3.858 | 2.365 | 2.146 | 0.173 | 0.112 |
| currier_b (matched) | 10,784 | 2,888 | 0.268 | 0.686 | 4.638 | 3.836 | 2.094 | 1.865 | 0.134 | 0.116 |

## Vocabulary at matched size

| matched tokens | A types | B types | shared | A only | B only | Jaccard |
| --- | --- | --- | --- | --- | --- | --- |
| 10,774 | 3,381 | 2,888 | 821 | 2,560 | 2,067 | 0.151 |

## Is B reachable from A by one systematic transformation?

Baseline: 0.243 of A types already occur in B.

| transformation | detail | coverage | gain |
| --- | --- | --- | --- |
| drop prefix | d | 0.266 | 0.023 |
| drop prefix | y | 0.265 | 0.022 |
| drop prefix | ch | 0.262 | 0.020 |
| drop prefix | o | 0.255 | 0.012 |
| drop prefix | ol | 0.255 | 0.012 |
| substitute | m→r | 0.253 | 0.011 |
| drop prefix | qo | 0.253 | 0.010 |
| drop suffix | d | 0.253 | 0.010 |
| substitute | m→l | 0.252 | 0.009 |
| substitute | ckh→k | 0.252 | 0.009 |

A single-step transformation that mattered would show a large positive gain.

## Language versus hand, section and quire (partial R² on per-line responses)

| response | R² full | partial R² currier_language | partial R² hand | partial R² section | partial R² quire_id |
| --- | --- | --- | --- | --- | --- |
| mean_word_length | 0.152 | 0.026 | 0.016 | 0.045 | 0.058 |
| gallows_rate | 0.028 | 0.000 | 0.003 | 0.003 | 0.011 |
