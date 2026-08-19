# Phase 1 — Uncertainty-flag sensitivity

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Metrics under each filtering variant

| variant | lines | tokens | h2 | mean_word_length | ttr | hapax_rate | near_repeat_within_2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all lines | 4,072 | 33,728 | 2.253 | 4.524 | 0.215 | 0.700 | 0.148 |
| drop has_uncertain | 3,988 | 32,795 | 2.251 | 4.532 | 0.216 | 0.699 | 0.148 |
| drop has_illegible | 4,072 | 33,728 | 2.253 | 4.524 | 0.215 | 0.700 | 0.148 |
| drop has_alternatives | 3,488 | 28,546 | 2.235 | 4.530 | 0.218 | 0.690 | 0.150 |
| drop has_high_ascii | 3,957 | 32,772 | 2.243 | 4.530 | 0.213 | 0.697 | 0.147 |
| drop all flagged | 3,367 | 27,434 | 2.224 | 4.540 | 0.218 | 0.688 | 0.149 |
| second [a:b] option | 4,072 | 33,730 | 2.254 | 4.524 | 0.215 | 0.699 | 0.147 |

## Relative drift versus all lines

| variant | h2 | mean_word_length | ttr | hapax_rate | near_repeat_within_2 |
| --- | --- | --- | --- | --- | --- |
| drop has_uncertain | -0.001 | 0.002 | 0.006 | -0.001 | 0.001 |
| drop has_illegible | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| drop has_alternatives | -0.008 | 0.001 | 0.018 | -0.015 | 0.014 |
| drop has_high_ascii | -0.004 | 0.001 | -0.006 | -0.005 | -0.002 |
| drop all flagged | -0.013 | 0.004 | 0.018 | -0.017 | 0.013 |
| second [a:b] option | 0.001 | -0.000 | 0.000 | -0.002 | -0.003 |

Largest drift: ttr under "drop all flagged" at 1.8%.

## Footprint of the first-option convention

| lines with [a:b] | lines changed by second option | tokens changed |
| --- | --- | --- |
| 584 | 582 | 627 |
