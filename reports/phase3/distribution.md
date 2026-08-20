# Phase 3 — Function words and semantic fields

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Function-word axes, by corpus

| view | top-20 token share | mean context entropy | mean dispersion | mean length |
| --- | --- | --- | --- | --- |
| raw | 0.203 | 6.829 | 0.785 | 3.850 |
| merged | 0.203 | 6.829 | 0.785 | 1.950 |
| reliable | 0.203 | 6.790 | 0.783 | 3.850 |
| vulgate_clementine | 0.264 | 6.147 | 0.890 | 3.650 |
| austen_pride_prejudice | 0.331 | 6.298 | 0.933 | 2.500 |
| grille | 0.225 | 6.115 | 0.935 | 4.700 |
| selfcite | 0.330 | 3.136 | 0.367 | 3.500 |

A function-word class shows up as a top of the frequency list that is short, maximally promiscuous in its contexts and evenly dispersed. Dispersion is the page distribution's entropy over log2(pages), so 1.0 means present everywhere; reference corpora have no pages, so blocks of 20 pseudo-lines stand in for them.

## Candidate function words in raw

| form | count | share | context entropy | dispersion | units |
| --- | --- | --- | --- | --- | --- |
| daiin | 755.000 | 0.022 | 7.264 | 0.937 | 5.000 |
| ol | 515.000 | 0.015 | 7.301 | 0.814 | 2.000 |
| chedy | 480.000 | 0.014 | 7.211 | 0.761 | 4.000 |
| aiin | 436.000 | 0.013 | 6.873 | 0.817 | 4.000 |
| shedy | 414.000 | 0.012 | 7.044 | 0.715 | 4.000 |
| chol | 360.000 | 0.011 | 7.198 | 0.882 | 3.000 |
| or | 341.000 | 0.010 | 6.829 | 0.849 | 2.000 |
| chey | 332.000 | 0.010 | 7.217 | 0.818 | 3.000 |
| ar | 314.000 | 0.009 | 6.972 | 0.780 | 2.000 |
| qokeey | 301.000 | 0.009 | 6.794 | 0.717 | 6.000 |
| qokeedy | 299.000 | 0.009 | 6.598 | 0.670 | 7.000 |
| s | 280.000 | 0.008 | 6.176 | 0.892 | 1.000 |
| y | 278.000 | 0.008 | 6.288 | 0.867 | 1.000 |
| qokain | 277.000 | 0.008 | 6.550 | 0.634 | 6.000 |
| qokedy | 265.000 | 0.008 | 6.507 | 0.694 | 6.000 |
| shey | 263.000 | 0.008 | 7.083 | 0.767 | 3.000 |
| qokaiin | 262.000 | 0.008 | 6.783 | 0.732 | 7.000 |
| dar | 260.000 | 0.008 | 6.622 | 0.855 | 3.000 |
| al | 213.000 | 0.006 | 6.594 | 0.724 | 2.000 |
| okaiin | 201.000 | 0.006 | 6.678 | 0.779 | 6.000 |

These are candidates by distribution alone. Nothing here says what they mean, and a generated text with a frequency skew produces the same table.

## Semantic-field probe

| quantity | value |
| --- | --- |
| types tested (≥20 tokens) | 257 |
| mean section divergence (bits) | 0.461 |
| null mean | 0.165 |
| null max | 0.199 |
| permutations | 200 |
| p | 0.005 |

The null reassigns whole pages to sections, so it keeps every page's own repetitiveness and destroys only the link between a section and its vocabulary. A low p means section-specific vocabulary exists beyond page topic frequency — which is what would make herbal-only and pharma-only subsets the most translatable parts of the manuscript.

## Most section-specific types

| section | types |
| --- | --- |
| astronomical | — |
| biological | olkain, qol, sol, sheckhy, olchedy, qokedy, qokain, qokal, qoteedy, tedy |
| cosmological | — |
| herbal | kchy, cthor, dchy, dchor, tchy, cthy, cthol, kchol, otchol, ckhy |
| pharmaceutical | okeol, qokeol, cheor, qokol, cheol, okeey, s, daiin, dal, chor |
| stars | lkeey, lkain, lkaiin, lkeedy, chedar, qokchedy, lkar, al, qopchedy, oteedy |
| text_only | qokar, or, dar, ar, shedy, dal, shey, aiin, y, ol |
