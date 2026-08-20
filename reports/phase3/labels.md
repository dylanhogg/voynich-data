# Phase 3 — Labels as a nomenclature

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Are labels morphologically simpler?

| view | tokens | types | ttr | hapax_rate | mean_length | cv_length | suffix_rate | gallows_initial_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| labels | 124.000 | 64.000 | 0.516 | 0.750 | 2.371 | 0.917 | 0.242 | 0.113 |
| prose (matched sample) | 124.000 | 105.000 | 0.847 | 0.867 | 4.919 | 0.356 | 0.895 | 0.105 |
| prose (all) | 33,141 | 7,128 | 0.215 | 0.701 | 4.534 | 0.391 | 0.860 | 0.106 |

The matched sample is the row to read against: labels are ~2% of the corpus and every one of these numbers moves with sample size. Suffix rate uses the frequency inventory induced on prose, so it asks whether labels carry the endings running text uses.

## Do labels on a page resemble each other?

| view | pairs | within-page distance | across-page distance | tightening |
| --- | --- | --- | --- | --- |
| labels | 1,800 | 2.899 | 3.093 | 0.193 |
| prose | 1,940 | 4.314 | 4.438 | 0.124 |

Glyph edit distance between random pairs of tokens on the same page versus random pairs from anywhere. Positive tightening means a page's labels are more like each other than like the label vocabulary at large — which is what a list of one kind of thing looks like.

## Label vocabulary against running text

| quantity | value |
| --- | --- |
| label types | 64.000 |
| share also seen in prose | 0.500 |
| label-only types | 32.000 |
| label types used more than once | 0.250 |

A nomenclature drawn from the same language as the text shares vocabulary with it; a separate naming system does not. Nothing here identifies what is being named — that needs the illustration↔label concordance the gap analysis leaves open.
