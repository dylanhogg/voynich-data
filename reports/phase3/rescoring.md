# Phase 3 — Re-scored hypotheses

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Final ranked hypotheses, after remediation

| id | Phase 2 gain (raw) | best round-2 representation | round-2 gain | Δ | held-out gain | p | beat every null | converged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H2 | -4.233 | merged | -0.105 | 4.128 | 3.050 | 0.308 | no | no |
| H8 | -5.390 | merged | -2.960 | 2.430 | -2.908 | 0.692 | no | yes |
| H3 | -11.010 | merged | -3.677 | 7.333 | -2.529 | 0.308 | no | no |
| H4 | -10.384 | merged | -5.676 | 4.708 | -4.630 | 0.308 | no | no |
| H1 | -10.283 | merged | -5.771 | 4.511 | -4.848 | 0.308 | no | yes |
| H7 | -9.659 | merged | -7.730 | 1.928 | -6.542 | 0.308 | no | yes |
| H6b | -13.023 | merged | -9.136 | 3.887 | -6.643 | 0.538 | no | yes |
| H9 | -15.198 | merged | -10.914 | 4.284 | -10.516 | 0.615 | no | yes |
| H6a | -23.915 | merged | -13.780 | 10.135 | -10.428 | 0.462 | no | yes |

Gain is bits per token against an order-2 Markov model **of the same representation**. The baseline is re-based for every representation, so Δ is not a like-for-like improvement over Phase 2 — it is the gap to a different reference. Read the `p` and `beat every null` columns first.

## Why the round-2 numbers look better, and why they are not evidence

Every gain in the table above is larger than its Phase 2 counterpart, and the top row is within a tenth of a bit of parity. Neither fact is evidence, for two measurable reasons.

**The baseline moved.** On the merged representation the same search scores +9.97 to +10.02 bits/token on *shuffled* manuscript text, against -0.105 on the real thing. Shuffled text has no local structure for an order-2 Markov model to exploit, so the reference collapses and a substitution code beats it easily. A channel where random text outscores the manuscript by ten bits is measuring the channel, not the text.

**The held-out baseline moved further.** The order-2 reference costs 13.58 bits/token on the 41 held-out pages against 12.55 on the training pages, because its parameter cost is amortised over a fifth as many tokens. That, not a better key, is why H2's held-out gain is positive while its training gain is not.

**And the variant did not converge.** H2's best merged variant is fixed-width-3 over already-merged units — a codebook of hundreds of symbols against 26 letters, the same wide-alphabet corner Phase 2 recorded as inconclusive rather than falsified. Nothing here changes that verdict; it re-states it on a second representation.

On the training pages, no hypothesis on any representation beats a Markov model of its own representation, and not one of the eighteen rows beat every surrogate.

## Every representation, every hypothesis

| id | representation | variant | gain | held-out | p | converged |
| --- | --- | --- | --- | --- | --- | --- |
| H2 | merged | austen_pride_prejudice-o3\|fixed-width-3 | -0.105 | 3.050 | 0.308 | no |
| H8 | merged | morphology | -2.960 | -2.908 | 0.692 | yes |
| H3 | merged | vulgate_clementine-abjad-o3\|plain | -3.677 | -2.529 | 0.308 | no |
| H2 | reliable | clusius_rariorum-o3\|fixed-width-3 | -4.379 | -1.964 | 0.538 | no |
| H8 | reliable | morphology | -4.755 | -5.206 | 0.538 | yes |
| H4 | merged | clusius_rariorum-abbrev-o3\|plain | -5.676 | -4.630 | 0.308 | no |
| H1 | merged | clusius_rariorum-o3\|plain | -5.771 | -4.848 | 0.308 | yes |
| H7 | merged | austen_pride_prejudice-o1\|plain | -7.730 | -6.542 | 0.308 | yes |
| H6b | merged | selfcite | -9.136 | -6.643 | 0.538 | yes |
| H7 | reliable | vulgate_clementine-o1\|plain | -9.803 | -8.907 | 0.308 | yes |
| H1 | reliable | clusius_rariorum-o3\|plain | -10.343 | -9.160 | 0.077 | yes |
| H4 | reliable | clusius_rariorum-abbrev-o3\|plain | -10.457 | -9.445 | 0.077 | no |
| H9 | merged | slot_grammar | -10.914 | -10.516 | 0.615 | yes |
| H3 | reliable | vulgate_clementine-abjad-o3\|plain | -11.055 | -10.120 | 0.308 | yes |
| H6b | reliable | selfcite | -11.442 | -9.877 | 0.615 | yes |
| H6a | merged | grille | -13.780 | -10.428 | 0.462 | yes |
| H9 | reliable | slot_grammar | -14.174 | -13.465 | 0.308 | yes |
| H6a | reliable | grille | -20.261 | -17.249 | 0.769 | yes |

## Representations searched

| representation | re-searched | origin |
| --- | --- | --- |
| merged | yes | Phase 2 H2 converged merge search (clusius_rariorum-o3\|searched-merges, 22 merges) |
| raw | no | Phase 1 tokenization contract (T1-glyph, CB=break, ZL) |
| reliable | yes | Phase 3 token reliability model (translations/alignment.py) |

`raw` is not re-searched: Phase 2 ran it with this code, these seeds and this budget, and its numbers are carried from `output/translation/phase2_manifest.json` rather than spent again.

Ceiling 14400 s; spent 7440 s.
