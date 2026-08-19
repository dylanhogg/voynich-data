"""Phase 1 analysis modules, one topic per file.

``common`` and ``context`` build the shared corpus views; ``stats``,
``segmentation`` and ``fsa`` are the estimators and inductions the topics use;
``entropy``, ``lexis``, ``morphology``, ``syntax``, ``position``, ``currier``,
``robustness`` and ``uncertainty`` are the topic reports, and ``landmarks`` is
the blocking reproduction gate. Run them all with ``make analyse1``.
"""

from __future__ import annotations
