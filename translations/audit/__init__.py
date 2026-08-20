"""Phase 5 — the adversarial self-audit of the Phase 4 translation (plan §7).

Two batteries, both automated and both reported whatever they say:
:mod:`strength` collects the evidence that would make the rendering credible,
:mod:`weakness` collects the tests designed to break it. :mod:`common` holds the
harness they share — one loaded pipeline, re-run over whatever view a test
hands it.
"""

from __future__ import annotations

from translations.audit.common import Check, Finding, Harness, build_harness

__all__ = ["Check", "Finding", "Harness", "build_harness"]
