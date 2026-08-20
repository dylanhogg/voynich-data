# Phase 2 — Synthetic validation of the search

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Blind recovery of hidden keys

| scheme | corpus | tokens | key accuracy | token accuracy | found ≤ true bits |
| --- | --- | --- | --- | --- | --- |
| substitution | caesar_bello_gallico | 8,000 | 1.000 | 1.000 | yes |
| verbose | caesar_bello_gallico | 8,000 | 1.000 | 1.000 | no |
| abjad | caesar_bello_gallico | 7,854 | 1.000 | 1.000 | yes |

Each line is a cipher this project built and then tried to break without the key. A search that cannot recover a key it invented itself cannot be trusted with the manuscript. Key accuracy is token-weighted; the verbose scheme has no single-unit key to compare against, so only token accuracy is meaningful there.
