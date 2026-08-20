# Phase 3 — Slot-to-function mapping

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Paradigm density

| view | roots (≥5 tokens) | suffixes | cells filled | expected by chance | excess | single-suffix roots |
| --- | --- | --- | --- | --- | --- | --- |
| raw | 604.000 | 13.000 | 0.289 | 0.598 | -0.308 | 0.091 |
| merged | 628.000 | 13.000 | 0.283 | 0.558 | -0.274 | 0.239 |
| reliable | 595.000 | 13.000 | 0.285 | 0.599 | -0.314 | 0.094 |
| vulgate_clementine | 854.000 | 13.000 | 0.146 | 0.590 | -0.444 | 0.498 |
| herbal_latin | 1,029 | 13.000 | 0.182 | 0.547 | -0.365 | 0.405 |
| finnish_bible | 911.000 | 13.000 | 0.125 | 0.532 | -0.407 | 0.543 |

Chance is the fill a root would reach by drawing its tokens independently from the pooled suffix distribution. An inflectional paradigm fills *fewer* cells than chance in a fusional language (roots select a declension) and more in an agglutinative one.

## Paradigm classes

| view | pooled suffix entropy | within-class entropy | explained by class |
| --- | --- | --- | --- |
| raw | 3.527 | 2.250 | 0.362 |
| merged | 3.231 | 2.264 | 0.299 |
| reliable | 3.530 | 2.254 | 0.361 |
| vulgate_clementine | 3.560 | 2.170 | 0.391 |
| herbal_latin | 3.523 | 2.104 | 0.403 |
| finnish_bible | 3.487 | 1.737 | 0.502 |

Six classes, k-means on each root's suffix distribution. A language with declensions concentrates suffix choice inside a class.

## Is suffix choice conditioned by context?

| view | suffix entropy | MI with next suffix | NMI with own root | share explained |
| --- | --- | --- | --- | --- |
| raw | 3.510 | 0.059 | 0.350 | 0.017 |
| merged | 3.178 | 0.037 | 0.319 | 0.012 |
| reliable | 3.516 | 0.059 | 0.352 | 0.017 |
| vulgate_clementine | 3.576 | 0.075 | 0.515 | 0.021 |
| herbal_latin | 3.580 | 0.043 | 0.483 | 0.012 |
| finnish_bible | 3.538 | 0.090 | 0.530 | 0.025 |

Agreement and government make a suffix predictable from its neighbours. Positional generation does not: the suffix is decided inside the word and owes nothing to the word before it.

## Induced inventories, for reference

| view | MDL affixes | MDL suffixes |
| --- | --- | --- |
| raw | 30.000 | kar, chey, ody, ain, eey, ky, or, ol, am, chy, al, ar, s, d |
| merged | 30.000 | am, chy, chey, s, d, daiin, or, ol, ar, al, aiin, ain, o, chedy, ody |
| reliable | 30.000 | kar, chey, kal, ody, ain, ky, am, or, ol, chy, ar, al, s, d |
| vulgate_clementine | 1.000 | que |
| herbal_latin | 9.000 | que, tur, bus, rum, nt, s, m |
| finnish_bible | 4.000 | nsa, vat, sta, si |

The tables above use the frequency inventory (12 commonest word-final sequences per view) so the columns are comparable. This table is the MDL induction the plan names, and its point is the asymmetry: affixes pay for themselves on the manuscript and largely do not on size-matched natural language.
