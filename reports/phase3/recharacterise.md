# Phase 3 — Post-merge re-characterisation

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Where each representation sits

| metric | natural range | raw | merged | reliable | moved toward natural |
| --- | --- | --- | --- | --- | --- |
| h1 | 3.871 … 4.091 | 3.855 | 4.501 | 3.850 | — |
| h2 | 3.077 … 3.365 | 2.253 | 3.111* | 2.234 | merged |
| h3 | 2.282 … 2.789 | 2.032 | 2.847 | 2.014 | merged |
| word_length_mean | 3.966 … 6.125 | 4.524* | 2.814 | 4.546* | — |
| word_length_cv | 0.458 … 0.565 | 0.393 | 0.471* | 0.385 | merged |
| zipf_alpha | 1.612 … 2.207 | 2.116* | 2.116* | 2.091* | — |
| hapax_rate | 0.395 … 0.672 | 0.700 | 0.700 | 0.690 | reliable |
| mi_excess_d1 | 0.185 … 1.335 | 0.173 | 0.167 | 0.170 | — |
| mi_excess_d5 | -0.017 … 0.127 | 0.015* | 0.020* | -0.006* | — |
| near_repeat_within_2 | 0.023 … 0.114 | 0.148 | 0.331 | 0.147 | reliable |
| morph_bits_saved_per_word | 0.000 … 0.683 | 1.513 | 0.968 | 1.217 | merged, reliable |

`*` marks a value inside the natural-language range (min–max over 10 sample-size-matched reference corpora). The range is a *region*, not a test: sitting inside it is necessary for a natural-language reading, never sufficient.

## Did the merge help?

| representation | metrics inside natural range | metrics moved toward it | origin |
| --- | --- | --- | --- |
| raw | 3 / 11 | — | Phase 1 tokenization contract (T1-glyph, CB=break, ZL) |
| merged | 4 / 11 | 4 / 11 | Phase 2 H2 converged merge search (clusius_rariorum-o3\|searched-merges, 22 merges) |
| reliable | 3 / 11 | 3 / 11 | Phase 3 token reliability model (translations/alignment.py) |

## Pseudo-Voynich controls on the same metrics

| view | h1 | h2 | h3 | word_length_mean | word_length_cv | zipf_alpha | hapax_rate | mi_excess_d1 | mi_excess_d5 | near_repeat_within_2 | morph_bits_saved_per_word |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grille | 4.092 | 2.749 | 1.932 | 4.581 | 0.281 | 1.156 | 0.000 | 0.001 | -0.004 | 0.060 | 0.000 |
| selfcite | 4.820 | 2.645 | 1.464 | 3.496 | 0.438 | 1.528 | 0.365 | 3.109 | 2.620 | 0.844 | 0.000 |

The controls are here because a representation that moves Voynichese toward natural language moves the pseudo-Voynich too if the movement is an artifact of the transform rather than a property of the text.
