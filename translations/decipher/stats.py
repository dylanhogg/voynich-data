"""Statistical discipline for the search (plan §4.5).

Every reported score is positioned in an empirical null built by running the
*identical* search on pseudo-Voynich and on surrogates. A likelihood on its own
is not evidence; its position in that null is.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NullComparison:
    """Where a real score sits in its own null distribution."""

    real: float
    nulls: dict[str, float]

    @property
    def p_value(self) -> float:
        """One-sided empirical p: how often a null matched or beat the real score."""
        values = list(self.nulls.values())
        if not values:
            return 1.0
        beaten = sum(1 for value in values if value >= self.real)
        return (1 + beaten) / (1 + len(values))

    @property
    def z_score(self) -> float:
        """Standardised distance from the null mean (0 if the null has no spread)."""
        values = np.array(list(self.nulls.values()), dtype=float)
        if values.size < 2:
            return 0.0
        spread = float(values.std(ddof=1))
        return float((self.real - values.mean()) / spread) if spread else 0.0

    @property
    def best_null(self) -> tuple[str, float] | None:
        """The strongest null, which is what the real score has to beat."""
        if not self.nulls:
            return None
        name = max(self.nulls, key=lambda key: self.nulls[key])
        return name, self.nulls[name]

    def as_dict(self) -> dict[str, object]:
        """JSON-friendly form."""
        return {
            "real": self.real,
            "nulls": self.nulls,
            "p_value": self.p_value,
            "z_score": self.z_score,
            "best_null": self.best_null,
        }


def benjamini_hochberg(p_values: dict[str, float]) -> dict[str, float]:
    """Benjamini–Hochberg q-values over the whole comparison grid."""
    if not p_values:
        return {}
    names = sorted(p_values, key=lambda key: (p_values[key], key))
    total = len(names)
    q_values: dict[str, float] = {}
    running = 1.0
    for rank in range(total, 0, -1):
        name = names[rank - 1]
        running = min(running, p_values[name] * total / rank)
        q_values[name] = running
    return q_values
