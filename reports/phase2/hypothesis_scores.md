# Phase 2 — Hypothesis scores

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Ranked hypotheses

| id | hypothesis | best variant | gain (bits/token) | best null gain | p | q (BH) | held-out gain | truncated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H2 | Verbose cipher - one plaintext letter written as several glyphs | clusius_rariorum-o3\|fixed-width-3 | -4.233 | 5.097 | 0.538 | 0.791 | -2.374 | no |
| H8 | Natural language with heavy affixal morphology, lightly encoded | morphology | -5.390 | 3.768 | 0.538 | 0.791 | -5.375 | no |
| H7 | Transposition or anagrammed plaintext | vulgate_clementine-o1\|plain | -9.659 | 1.168 | 0.308 | 0.791 | -8.702 | no |
| H1 | Monoalphabetic substitution of a natural language | clusius_rariorum-o3\|plain | -10.283 | -10.439 | 0.077 | 0.692 | -9.072 | no |
| H4 | Medieval Latin scribal abbreviation | clusius_rariorum-abbrev-o3\|plain | -10.384 | -10.325 | 0.154 | 0.692 | -9.340 | no |
| H3 | Abjad / vowel-suppressed script | vulgate_clementine-abjad-o3\|plain | -11.010 | -7.633 | 0.385 | 0.791 | -10.030 | no |
| H6b | Autocopying / self-citation generation (Timm and Schinner) | selfcite | -13.023 | 0.581 | 0.769 | 0.846 | -10.357 | no |
| H9 | Constructed language or ars combinatoria | slot_grammar | -15.198 | -11.794 | 0.615 | 0.791 | -13.934 | no |
| H6a | Table and grille generated meaningless text (Rugg) | grille | -23.915 | -13.078 | 0.846 | 0.846 | -18.221 | no |

**Gain** is bits per token saved against an order-2 Markov model of the glyph stream itself, with the key, merge partition or grammar charged as model bits. Positive means the hypothesis describes the manuscript better than its own local statistics do.

**Resolution of the p-values.** Each hypothesis is positioned against 12 surrogate runs, so the smallest empirical p obtainable is 1/(12 + 1) = 0.077. No result in this table could have reached p < 0.05 by design, and none comes close to the floor either: read the columns as "the search does no better on the manuscript than on surrogate text", not as a significance test that was passed or failed.

## What each hypothesis actually cost

| id | budget share | spent (s) | converged | detail |
| --- | --- | --- | --- | --- |
| H2 | 0.450 | 1,750 | no | lm=clusius_rariorum-o3, units=263, merges=0 |
| H8 | 0.050 | 41.811 | yes | 6 prefixes, 4 suffixes, 39574 bits saved vs no affixes |
| H7 | 0.020 | 0.542 | yes | lm=vulgate_clementine-o1, units=26, merges=0 |
| H1 | 0.060 | 544.716 | yes | lm=clusius_rariorum-o3, units=26, merges=0 |
| H4 | 0.060 | 467.460 | yes | lm=clusius_rariorum-abbrev-o3, units=26, merges=0 |
| H3 | 0.080 | 515.659 | yes | lm=vulgate_clementine-abjad-o3, units=26, merges=0 |
| H6b | 0.050 | 30.721 | yes | window=20, tokens coded as copies=21041 |
| H9 | 0.050 | 1.322 | yes | k=2, 845 states, 100.0% of tokens accepted |
| H6a | 0.050 | 1.357 | yes | table=24, grilles=4, generated types=24 |

Ceiling 7200 s; spent 3356 s.

## Shortlist carried into Phase 4

| rank | id | gain | beat every null | converged | why it is carried |
| --- | --- | --- | --- | --- | --- |
| 1 | H2 | -4.233 | no | no | best-scoring channel, and the only one that shortens words toward plausible plaintext lengths; its widest variant did not converge, so it is inconclusive rather than falsified |
| 2 | H8 | -5.390 | no | yes | best structural description of word formation, and the inventory Phase 4 needs for morph-level glossing |
| 4 | H1 | -10.283 | yes | yes | the only hypothesis whose real score beat every surrogate run, on the herbal Latin model — a weak signal, but the only one in the table |
| 7 | H6b | -13.023 | no | yes | carried as the rival control: Phase 5 has to keep scoring the autocopy model against whatever Phase 4 produces |

Every one of these lost to the baseline, so Phase 4 will be rendering English under a *losing* model and must say so on every artifact it emits (§0.4, §6.3). They are carried because they are the least-bad decodes available, not because any of them is supported.

## Unfunded

- **H5 — Homophonic or slot-conditioned polyalphabetic cipher**: The key space is (slots x alphabet) rather than alphabet, which needs Gibbs sampling with sparse priors and a budget an order of magnitude beyond the one allocated to this run. Registered with its grid so it can be run unchanged when that budget exists; reported as unfunded, never as falsified.

Unfunded is not falsified. These records are registered with their grids so they can be run unchanged when the budget exists.
