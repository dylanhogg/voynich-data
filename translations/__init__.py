"""Analysis, decipherment and translation code for the Voynich manuscript.

Everything in this package is *speculative research code*. See
``translations.config.SPECULATIVE_BANNER`` and ``plans/001_initial_automated_english_translation.md``.

Nothing here touches the network at run time: reference corpora are fetched by
``scripts/fetch_corpora.py`` into ``data_sources/cache/corpora/`` and verified by
checksum before use.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
