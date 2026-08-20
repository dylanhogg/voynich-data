"""The compute budget (plan §4.3.6).

The ceiling is declared in `config.py` and allocated up front per hypothesis;
searches spend their allocation rather than discovering it. A deadline can only
*stop* a search and mark it truncated — it can never change the result of a run
that finishes, because iteration counts, not seconds, define the output.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from vcat.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Deadline:
    """A wall-clock stop for one search."""

    seconds: float
    started: float = field(default_factory=time.monotonic)

    @property
    def elapsed(self) -> float:
        """Seconds since the deadline was created."""
        return time.monotonic() - self.started

    @property
    def expired(self) -> bool:
        """Whether the allocation is spent."""
        return self.elapsed >= self.seconds


@dataclass
class Budget:
    """Wall-clock allocation across hypotheses."""

    total_seconds: float
    spent: dict[str, float] = field(default_factory=dict)

    def allocate(self, hypothesis: str, share: float) -> Deadline:
        """Take a share (0–1) of the total budget for one hypothesis."""
        seconds = self.total_seconds * share
        logger.info("Allocated budget", hypothesis=hypothesis, seconds=round(seconds))
        return Deadline(seconds=seconds)

    def record(self, hypothesis: str, seconds: float) -> None:
        """Record what a hypothesis actually spent."""
        self.spent[hypothesis] = self.spent.get(hypothesis, 0.0) + seconds

    @property
    def total_spent(self) -> float:
        """Seconds spent across all hypotheses."""
        return sum(self.spent.values())

    @property
    def remaining(self) -> float:
        """Seconds left in the ceiling."""
        return self.total_seconds - self.total_spent
