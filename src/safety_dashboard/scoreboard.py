"""In-memory scoreboard — counts attacks by outcome, category, and layer.

Resets on process restart by design. The educational use case is a
single dashboard session; persisting across restarts would mix data
across audiences (and risk the dashboard showing yesterday's bad
score in a live demo).
"""

from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Optional


class ScoreState:
    def __init__(self) -> None:
        self._lock = Lock()
        self.total = 0
        self.outcomes = {"blocked": 0, "sanitized": 0, "passed": 0, "override": 0}
        self.per_category: dict[str, dict[str, int]] = defaultdict(
            lambda: {"blocked": 0, "sanitized": 0, "passed": 0, "override": 0,
                     "total": 0}
        )
        self.passes_per_layer: dict[int, int] = defaultdict(int)

    def record(self, *, result: str, category: str = "",
               caught_at_layer: Optional[int] = None) -> None:
        with self._lock:
            self.total += 1
            if result not in self.outcomes:
                result = "passed"
            self.outcomes[result] += 1
            cat = category or "uncategorized"
            self.per_category[cat]["total"] += 1
            self.per_category[cat][result] += 1
            # "Weakest layer" = layer with most passes-through.
            # If nothing caught it, count it under expected-layer (the
            # one we wanted to catch it). When something DID catch it,
            # the upstream layers all "passed" — we don't penalise them.
            if result == "passed" and caught_at_layer is not None:
                self.passes_per_layer[caught_at_layer] += 1

    def to_dict(self) -> dict:
        with self._lock:
            defenses = self.outcomes["blocked"] + self.outcomes["sanitized"] + \
                       self.outcomes["override"]
            rate = (defenses / self.total) if self.total else 0.0
            weakest: Optional[int] = None
            if self.passes_per_layer:
                weakest = max(self.passes_per_layer.items(), key=lambda x: x[1])[0]
            return {
                "total": self.total,
                "blocked": self.outcomes["blocked"],
                "sanitized": self.outcomes["sanitized"],
                "passed": self.outcomes["passed"],
                "override": self.outcomes["override"],
                "defense_rate": rate,
                "per_category": {k: dict(v) for k, v in self.per_category.items()},
                "per_layer": {str(k): v for k, v in self.passes_per_layer.items()},
                "weakest_layer": weakest,
            }

    def reset(self) -> None:
        with self._lock:
            self.total = 0
            self.outcomes = {"blocked": 0, "sanitized": 0, "passed": 0, "override": 0}
            self.per_category.clear()
            self.passes_per_layer.clear()


_SCORE = ScoreState()


def get_scoreboard() -> ScoreState:
    return _SCORE
