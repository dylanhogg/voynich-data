# Phase 1 — Positional and layout effects

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Line-initial / mid / final first-glyph distributions

| view | χ² | dof | p | Cramér's V | initial top | mid top | final top |
| --- | --- | --- | --- | --- | --- | --- | --- |
| voynich\|base | 6,328 | 36 | 0.000 | 0.307 | d, y, o | o, ch, q | o, d, ch |
| currier_a | 1,482 | 36 | 0.000 | 0.263 | o, y, d | ch, o, d | d, o, ch |
| currier_b | 5,524 | 34 | 0.000 | 0.351 | d, y, q | o, q, ch | o, ch, q |
| vulgate_clementine | 37.378 | 40 | 0.589 | 0.024 | e, a, s | e, a, s | e, a, s |

The Latin baseline is included to show what a *language* does at line boundaries when the lines are arbitrary blocks: nothing.

## Mean word length by position in line

| view | initial | mid | final |
| --- | --- | --- | --- |
| voynich\|base | 4.828 | 4.489 | 4.444 |
| currier_a | 4.592 | 4.196 | 4.506 |
| currier_b | 4.979 | 4.618 | 4.407 |
| vulgate_clementine | 5.227 | 5.221 | 5.246 |

## First line of page

| first-line mean length | other-line mean length | Mann–Whitney p | first-line words |
| --- | --- | --- | --- |
| 4.755 | 4.514 | 0.000 | 1,524 |

## Labels versus paragraph text

| label tokens | label types | types shared with prose | share shared | label mean length | prose mean length |
| --- | --- | --- | --- | --- | --- |
| 124 | 64 | 32 | 0.500 | 2.371 | 4.534 |

## Cost of the running-prose subset

Rule: paragraph lines only, excluding pages with illustration type A, C (astronomical and cosmological), because no line-level marker for circular or radial writing exists in the data.

| excluded lines | share of lines | excluded tokens | share of tokens |
| --- | --- | --- | --- |
| 170 | 0.042 | 587 | 0.017 |

| metric | full corpus | running prose |
| --- | --- | --- |
| h2 | 2.253 | 2.247 |
| hapax rate | 0.700 | 0.701 |
| near-repeat (within 2) | 0.148 | 0.146 |

Excluding circular pages moves h2 by -0.006 bits: the layout effects are real but they are not what drives the headline numbers.
