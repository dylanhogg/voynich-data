# Phase 4 — Confidence calibration

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Method

Each keyed hypothesis is given a problem whose answer we hid: a reference corpus in the language its own model assumes, enciphered under its own scheme at its own channel width, attacked blind with its own search settings, then pushed through the same decode-and-gloss stages. The isotonic map is fitted on half those tokens; the reliability diagram below is computed on the other half, so it checks the map rather than redrawing it.

## Recovery on ciphertext we built

| id | corpus | scheme | synthetic tokens | key accuracy | token accuracy |
| --- | --- | --- | --- | --- | --- |
| H1 | clusius_rariorum | substitution | 11,600 | 1.000 | 0.909 |
| H2 | austen_pride_prejudice | verbose | 20,000 | 1.000 | 0.716 |
| H3 | vulgate_clementine | abjad | 19,787 | 1.000 | 0.733 |
| H4 | clusius_rariorum | substitution | 11,600 | 1.000 | 0.887 |
| H7 | austen_pride_prejudice | substitution | 19,673 | 0.491 | 0.122 |

## Reliability diagrams (held-out synthetic tokens)

### H1

| predicted confidence | observed accuracy | tokens |
| --- | --- | --- |
| 0.000 | 0.000 | 542 |
| 1.000 | 1.000 | 5,258 |

### H2

| predicted confidence | observed accuracy | tokens |
| --- | --- | --- |
| 0.000 | 0.000 | 2,901 |
| 1.000 | 1.000 | 7,099 |

### H3

| predicted confidence | observed accuracy | tokens |
| --- | --- | --- |
| 0.000 | 0.000 | 2,731 |
| 1.000 | 1.000 | 7,162 |

### H4

| predicted confidence | observed accuracy | tokens |
| --- | --- | --- |
| 0.000 | 0.000 | 674 |
| 1.000 | 1.000 | 5,126 |

### H7

| predicted confidence | observed accuracy | tokens |
| --- | --- | --- |
| 0.047 | 0.046 | 6,911 |
| 0.307 | 0.300 | 2,925 |

## The fitted maps

### H1

| raw score | calibrated confidence |
| --- | --- |
| 0.000 | 0.000 |
| 0.049 | 1.000 |
| 0.110 | 1.000 |
| 0.268 | 1.000 |
| 0.381 | 1.000 |
| 0.437 | 1.000 |
| 0.447 | 1.000 |
| 0.448 | 1.000 |
| 0.450 | 1.000 |
| 0.597 | 1.000 |
| 0.635 | 1.000 |
| 0.729 | 1.000 |
| 0.747 | 1.000 |
| 0.750 | 1.000 |
| 0.847 | 1.000 |
| 0.972 | 1.000 |
| 0.996 | 1.000 |
| 1.000 | 1.000 |

### H2

| raw score | calibrated confidence |
| --- | --- |
| 0.000 | 0.000 |
| 0.045 | 1.000 |
| 0.101 | 1.000 |
| 0.300 | 1.000 |
| 0.407 | 1.000 |
| 0.443 | 1.000 |
| 0.448 | 1.000 |
| 0.450 | 1.000 |
| 0.499 | 1.000 |
| 0.666 | 1.000 |
| 0.679 | 1.000 |
| 0.739 | 1.000 |
| 0.747 | 1.000 |
| 0.750 | 1.000 |
| 0.905 | 1.000 |
| 0.985 | 1.000 |
| 0.997 | 1.000 |
| 1.000 | 1.000 |

### H3

| raw score | calibrated confidence |
| --- | --- |
| 0.000 | 0.000 |
| 0.016 | 1.000 |
| 0.035 | 1.000 |
| 0.403 | 1.000 |
| 0.450 | 1.000 |
| 0.671 | 1.000 |
| 0.750 | 1.000 |
| 0.894 | 1.000 |
| 1.000 | 1.000 |

### H4

| raw score | calibrated confidence |
| --- | --- |
| 0.000 | 0.000 |
| 0.043 | 1.000 |
| 0.096 | 1.000 |
| 0.275 | 1.000 |
| 0.392 | 1.000 |
| 0.436 | 1.000 |
| 0.449 | 1.000 |
| 0.450 | 1.000 |
| 0.459 | 1.000 |
| 0.611 | 1.000 |
| 0.654 | 1.000 |
| 0.727 | 1.000 |
| 0.748 | 1.000 |
| 0.750 | 1.000 |
| 0.872 | 1.000 |
| 0.970 | 1.000 |
| 0.997 | 1.000 |
| 1.000 | 1.000 |

### H7

| raw score | calibrated confidence |
| --- | --- |
| 0.000 | 0.000 |
| 0.097 | 0.088 |
| 0.298 | 0.088 |
| 0.402 | 0.088 |
| 0.442 | 0.088 |
| 0.448 | 0.088 |
| 0.450 | 0.161 |
| 0.497 | 0.307 |
| 0.663 | 0.307 |
| 0.670 | 0.307 |
| 0.736 | 0.307 |
| 0.747 | 0.307 |
| 0.750 | 0.307 |
| 0.893 | 0.307 |
| 0.982 | 0.307 |
| 0.997 | 0.307 |

## What this does not certify

The map is flat at 1.0 above zero for H1, H2, H3, H4: whenever the hypothesised system is genuinely present, this search recovers the key exactly and the gloss is then right whenever the lexicon has the word. That is a statement about the pipeline, not about the manuscript. Calibration is valid only if the true system resembles the hypothesised one. The manuscript sits at a score no synthetic ciphertext in this harness reaches — every hypothesis loses to a Markov model of the manuscript's own statistics — so the map is being read far outside the range it was fitted on. It bounds optimism about a system we can simulate; it certifies nothing about one we cannot.

This is why the confidence column is the calibrated value multiplied by the random-key null term and the transcription reliability weight. The calibration says how often a gloss is right *given* the hypothesis; the null term says how much of the gloss a key with no information would have produced anyway.
