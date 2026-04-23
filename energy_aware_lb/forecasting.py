from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque

import numpy as np

from .config import ForecastConfig
from .models import ForecastSnapshot


@dataclass
class HybridForecaster:
    config: ForecastConfig

    def __post_init__(self) -> None:
        self._history: Deque[float] = deque(maxlen=max(24, self.config.window * 4))

    def observe(self, value: float) -> None:
        self._history.append(float(np.clip(value, 0.0, 1.0)))

    def snapshot(self) -> ForecastSnapshot:
        if len(self._history) < 5:
            return ForecastSnapshot(predicted_load=0.5, confidence=0.2, uncertainty=0.8)

        arr = np.array(self._history, dtype=float)
        window = arr[-self.config.window :]

        ewma = window[0]
        for v in window[1:]:
            ewma = self.config.ewma_alpha * v + (1.0 - self.config.ewma_alpha) * ewma

        trend = 0.0
        if len(window) >= 6:
            x = np.arange(len(window), dtype=float)
            slope = np.polyfit(x, window, 1)[0]
            trend = slope * self.config.horizon_steps * self.config.trend_strength

        prediction = float(np.clip(ewma + trend, 0.0, 1.0))
        uncertainty = float(min(1.0, np.std(window) / max(1e-6, np.mean(window) + 1e-3)))
        confidence = float(np.clip(1.0 - uncertainty, 0.05, 0.98))

        return ForecastSnapshot(
            predicted_load=prediction,
            confidence=confidence,
            uncertainty=uncertainty,
        )
