"""The decipherment engine (plan §4.3).

``lm`` holds the plaintext language models, ``channel`` the ways a plaintext
could have become glyphs, ``score`` the single description-length scale every
hypothesis is judged on, ``search`` the seeded key searches, ``generative`` the
no-plaintext rivals, ``priors`` the Phase 1 structure that seeds the search,
``stats`` the null positioning and FDR, ``budget`` the compute ceiling,
``anchors`` the (still empty) crib protocol, ``synthetic`` the known-answer
tests, and ``run_hypothesis`` the runner that executes a registered record.

Nothing here decides anything on its own: hypotheses are registered as YAML in
``translations/hypotheses/`` before a run, and the runner executes what they declare.
"""

from __future__ import annotations
