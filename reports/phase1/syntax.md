# Phase 1 — Word order, repetition and topic structure

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Adjacent near-repeats

| view | exact | distance 1 | distance 2 | within 2 | longest identical run |
| --- | --- | --- | --- | --- | --- |
| voynich\|base | 0.008 | 0.041 | 0.099 | 0.148 | 3 |
| vulgate_clementine | 0.000 | 0.003 | 0.034 | 0.038 | 3 |
| austen_pride_prejudice | 0.001 | 0.007 | 0.074 | 0.082 | 2 |
| grille | 0.010 | 0.000 | 0.049 | 0.060 | 3 |
| selfcite | 0.324 | 0.295 | 0.224 | 0.844 | 31 |
| shuffle_word_order | 0.004 | 0.022 | 0.076 | 0.101 | 2 |
| markov_words\|n=1 | 0.007 | 0.041 | 0.100 | 0.147 | 3 |

## Self-citation within 20 preceding words

| view | identical | distance 1 | distance 2 | novel |
| --- | --- | --- | --- | --- |
| voynich\|base | 0.124 | 0.329 | 0.342 | 0.205 |
| vulgate_clementine | 0.175 | 0.077 | 0.184 | 0.565 |
| austen_pride_prejudice | 0.161 | 0.141 | 0.286 | 0.413 |
| grille | 0.187 | 0.000 | 0.492 | 0.321 |
| selfcite | 0.905 | 0.087 | 0.006 | 0.002 |
| shuffle_word_order | 0.063 | 0.280 | 0.397 | 0.260 |
| markov_words\|n=1 | 0.067 | 0.292 | 0.386 | 0.255 |

## Does word order carry information? (bits/word under a word bigram model)

| view | real | word order shuffled | gain from order |
| --- | --- | --- | --- |
| voynich\|base | 12.312 | 12.405 | 0.093 |
| vulgate_clementine | 11.488 | 11.992 | 0.504 |
| austen_pride_prejudice | 10.309 | 10.901 | 0.592 |
| grille | 6.742 | 6.743 | 0.001 |
| selfcite | 9.974 | 9.660 | -0.314 |
| shuffle_word_order | 12.404 | 12.401 | -0.004 |
| markov_words\|n=1 | 11.311 | 12.047 | 0.737 |

## Mutual information decay

| view | d=1 | d=2 | d=3 | d=5 | d=8 | d=12 | d=20 | d=30 | d=50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| voynich\|within_lines | 0.173 | 0.041 | 0.031 | 0.015 | -0.072 | -0.245 | — | — | — |
| voynich\|across_lines | 0.156 | 0.041 | 0.038 | 0.033 | 0.036 | 0.030 | 0.028 | 0.027 | 0.023 |
| vulgate_clementine | 0.724 | 0.264 | 0.125 | 0.068 | 0.040 | 0.034 | 0.026 | 0.020 | 0.013 |
| grille | 0.002 | 0.004 | -0.003 | 0.001 | -0.003 | 0.003 | 0.005 | -0.001 | -0.004 |
| selfcite | 3.189 | 3.184 | 3.181 | 3.197 | 3.179 | 3.194 | 3.186 | 3.174 | 3.156 |

Values are excess MI over a permuted control at the same sample size; plug-in MI at this vocabulary size is badly biased and only the excess is readable.

## Page topic structure (NMF)

| components | pages | NMI vs section | NMI vs illustration | purity vs section |
| --- | --- | --- | --- | --- |
| 7 | 206 | 0.410 | 0.410 | 0.762 |
