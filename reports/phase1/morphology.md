# Phase 1 — Word-internal structure and slot grammar

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Per-position glyph distributions

| view | position | n | entropy | distinct | top 1 | top 2 |
| --- | --- | --- | --- | --- | --- | --- |
| voynich\|base | 1 | 33,728 | 3.470 | 64.000 | o 0.204 | ch 0.161 |
| voynich\|base | 2 | 32,543 | 3.328 | 37.000 | o 0.277 | e 0.166 |
| voynich\|base | 3 | 29,760 | 3.650 | 33.000 | e 0.165 | k 0.135 |
| voynich\|base | 4 | 24,139 | 3.476 | 31.000 | e 0.185 | y 0.148 |
| voynich\|base | 5 | 16,646 | 3.371 | 30.000 | y 0.193 | i 0.144 |
| voynich\|base | 6+ | 15,785 | 3.236 | 34.000 | y 0.281 | n 0.178 |
| currier_a | 1 | 10,774 | 3.520 | 49.000 | ch 0.190 | o 0.166 |
| currier_a | 2 | 10,260 | 3.162 | 30.000 | o 0.337 | a 0.143 |
| currier_a | 3 | 9,185 | 3.714 | 28.000 | o 0.144 | i 0.119 |
| currier_a | 4 | 6,903 | 3.536 | 28.000 | i 0.160 | o 0.137 |
| currier_a | 5 | 4,620 | 3.477 | 26.000 | n 0.165 | y 0.159 |
| currier_a | 6+ | 4,561 | 3.571 | 29.000 | y 0.174 | n 0.159 |
| currier_b | 1 | 22,521 | 3.347 | 38.000 | o 0.223 | q 0.181 |
| currier_b | 2 | 21,874 | 3.356 | 31.000 | o 0.250 | e 0.185 |
| currier_b | 3 | 20,203 | 3.555 | 28.000 | e 0.188 | k 0.159 |
| currier_b | 4 | 16,949 | 3.389 | 27.000 | e 0.215 | y 0.153 |
| currier_b | 5 | 11,826 | 3.259 | 29.000 | y 0.206 | i 0.153 |
| currier_b | 6+ | 11,017 | 3.016 | 27.000 | y 0.325 | n 0.188 |
| vulgate_clementine | 1 | 33,728 | 4.035 | 22.000 | e 0.166 | a 0.093 |
| vulgate_clementine | 2 | 33,613 | 3.623 | 24.000 | e 0.166 | u 0.160 |
| vulgate_clementine | 3 | 27,682 | 4.170 | 24.000 | r 0.105 | n 0.087 |
| vulgate_clementine | 4 | 23,587 | 3.730 | 24.000 | i 0.200 | e 0.165 |
| vulgate_clementine | 5 | 19,042 | 3.870 | 22.000 | e 0.118 | t 0.095 |
| vulgate_clementine | 6+ | 38,565 | 3.752 | 24.000 | t 0.124 | s 0.118 |
| austen_pride_prejudice | 1 | 33,728 | 4.132 | 25.000 | t 0.131 | a 0.105 |
| austen_pride_prejudice | 2 | 32,396 | 3.596 | 23.000 | o 0.188 | e 0.153 |
| austen_pride_prejudice | 3 | 25,734 | 4.070 | 26.000 | e 0.138 | r 0.104 |
| austen_pride_prejudice | 4 | 17,943 | 4.081 | 26.000 | e 0.168 | t 0.117 |
| austen_pride_prejudice | 5 | 11,608 | 3.909 | 24.000 | e 0.200 | r 0.092 |
| austen_pride_prejudice | 6+ | 22,906 | 3.954 | 25.000 | e 0.165 | n 0.107 |
| finnish_bible | 1 | 33,728 | 3.784 | 21.000 | s 0.128 | k 0.123 |
| finnish_bible | 2 | 33,728 | 2.977 | 21.000 | a 0.319 | i 0.173 |
| finnish_bible | 3 | 29,741 | 3.735 | 21.000 | n 0.196 | i 0.154 |
| finnish_bible | 4 | 28,103 | 3.908 | 21.000 | a 0.165 | t 0.109 |
| finnish_bible | 5 | 23,395 | 3.395 | 21.000 | a 0.281 | e 0.104 |
| finnish_bible | 6+ | 57,895 | 3.445 | 21.000 | a 0.206 | n 0.154 |
| grille | 1 | 33,728 | 4.584 | 24.000 | f 0.044 | r 0.044 |
| grille | 2 | 33,728 | 2.822 | 12.000 | o 0.289 | e 0.213 |
| grille | 3 | 32,372 | 3.087 | 15.000 | k 0.259 | e 0.174 |
| grille | 4 | 26,681 | 3.319 | 19.000 | e 0.238 | a 0.182 |
| grille | 5 | 16,754 | 3.463 | 17.000 | i 0.275 | e 0.184 |
| grille | 6+ | 11,260 | 4.021 | 20.000 | i 0.159 | d 0.153 |
| selfcite | 1 | 33,728 | 4.813 | 85.000 | @199; 0.125 | ckh 0.113 |
| selfcite | 2 | 30,341 | 5.146 | 85.000 | v 0.075 | ckh 0.070 |
| selfcite | 3 | 23,540 | 4.312 | 83.000 | v 0.225 | @197; 0.134 |
| selfcite | 4 | 16,696 | 3.661 | 78.000 | @197; 0.244 | @187; 0.187 |
| selfcite | 5 | 9,815 | 3.101 | 59.000 | @187; 0.367 | @197; 0.136 |
| selfcite | 6+ | 3,801 | 2.631 | 33.000 | @187; 0.361 | @169; 0.301 |

## Harris successor/predecessor segmentation

Mean morphs per word: 1.402; morph inventory 4,365.

| morph | count |
| --- | --- |
| qo | 3,449 |
| y | 2,133 |
| ol | 2,003 |
| che | 1,730 |
| she | 1,097 |
| qot | 987 |
| daiin | 877 |
| or | 666 |
| al | 645 |
| aiin | 626 |
| chedy | 603 |
| s | 570 |
| ar | 569 |
| chol | 498 |
| cho | 469 |

## MDL slot inventory (defines `T2-slot`)

Prefixes: `qo`, `cho`, `ol`, `o`, `y`, `l`, `q`

Suffixes: `ody`, `s`, `o`

| initial DL (bits) | final DL (bits) | saved | affixes |
| --- | --- | --- | --- |
| 625,660 | 576,609 | 49,051 | 10 |

## Three models of word structure (held-out bits per word)

| view | morphology | positional slot code | order-2 chain | best | MDL bits saved / word | affixes |
| --- | --- | --- | --- | --- | --- | --- |
| voynich\|base | 13.043 | 18.539 | 12.102 | chain | 1.513 | 10 |
| currier_a | 13.088 | 17.977 | 12.804 | chain | 2.697 | 10 |
| currier_b | 12.500 | 18.217 | 11.288 | chain | 1.328 | 10 |
| vulgate_clementine | 10.363 | 23.391 | 16.766 | morphology | 0.153 | 1 |
| austen_pride_prejudice | 9.693 | 19.937 | 13.919 | morphology | 0.151 | 2 |
| finnish_bible | 11.714 | 24.960 | 18.566 | morphology | 0.111 | 3 |
| grille | 6.588 | 18.413 | 11.053 | morphology | 0.000 | 0 |
| selfcite | 8.055 | 17.998 | 10.254 | morphology | 0.000 | 0 |

Reported as likelihoods, not as a verdict: the three models are not nested and their priors differ.

## Induced finite-state acceptors

| view\|k | states | transitions | held-out type acceptance | token acceptance | over-generation |
| --- | --- | --- | --- | --- | --- |
| voynich\|base\|k=1 | 103 | 1,076 | 0.926 | 0.979 | 0.957 |
| voynich\|base\|k=2 | 814 | 4,177 | 0.624 | 0.901 | 0.941 |
| voynich\|base\|k=3 | 1,324 | 5,348 | 0.454 | 0.860 | 0.923 |
| currier_a\|k=1 | 62 | 619 | 0.910 | 0.983 | 0.967 |
| currier_a\|k=2 | 441 | 2,125 | 0.569 | 0.902 | 0.945 |
| currier_a\|k=3 | 737 | 2,725 | 0.427 | 0.874 | 0.929 |
| currier_b\|k=1 | 55 | 578 | 0.947 | 0.987 | 0.962 |
| currier_b\|k=2 | 546 | 2,696 | 0.619 | 0.897 | 0.933 |
| currier_b\|k=3 | 957 | 3,671 | 0.445 | 0.857 | 0.923 |
| vulgate_clementine\|k=1 | 7 | 121 | 0.999 | 1.000 | 0.988 |
| vulgate_clementine\|k=2 | 276 | 1,384 | 0.921 | 0.966 | 0.962 |
| vulgate_clementine\|k=3 | 916 | 3,040 | 0.798 | 0.934 | 0.960 |
| austen_pride_prejudice\|k=1 | 21 | 219 | 0.979 | 0.981 | 0.969 |
| austen_pride_prejudice\|k=2 | 180 | 945 | 0.881 | 0.911 | 0.940 |
| austen_pride_prejudice\|k=3 | 597 | 1,919 | 0.733 | 0.844 | 0.912 |
| finnish_bible\|k=1 | 1 | 21 | 1.000 | 1.000 | 0.999 |
| finnish_bible\|k=2 | 214 | 1,191 | 0.958 | 0.988 | 0.989 |
| finnish_bible\|k=3 | 883 | 3,280 | 0.839 | 0.902 | 0.974 |
| grille\|k=1 | 1 | 31 | 1.000 | 1.000 | 1.000 |
| grille\|k=2 | 15 | 77 | 0.500 | 0.897 | 0.997 |
| grille\|k=3 | 92 | 178 | 0.050 | 0.800 | 0.526 |
| selfcite\|k=1 | 104 | 885 | 0.522 | 0.941 | 0.924 |
| selfcite\|k=2 | 273 | 1,291 | 0.199 | 0.881 | 0.861 |
| selfcite\|k=3 | 407 | 1,487 | 0.052 | 0.782 | 0.792 |

## Gallows glyphs

| view | word-initial | word-other | line-first word | line-other | page-first line | page-other | h (word) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| voynich\|base | 0.105 | 0.117 | 0.110 | 0.115 | 0.132 | 0.114 | -0.038 |
| currier_a | 0.150 | 0.101 | 0.119 | 0.111 | 0.132 | 0.111 | 0.150 |
| currier_b | 0.084 | 0.125 | 0.105 | 0.117 | 0.133 | 0.115 | -0.132 |
| prose | 0.106 | 0.118 | 0.110 | 0.116 | 0.133 | 0.114 | -0.038 |
| labels | 0.113 | 0.129 | 0.125 | 0.100 | 0.077 | 0.127 | -0.051 |
