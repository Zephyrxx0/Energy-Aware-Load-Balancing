from __future__ import annotations

from typing import List

import numpy as np

from .models import WorkloadSample


def generate_workload_trace(
    hours: int = 24,
    step_minutes: int = 5,
    seed: int = 42,
) -> List[WorkloadSample]:
    points = int(hours * 60 / step_minutes)
    t = np.arange(points, dtype=float)
    rng = np.random.default_rng(seed)

    base = 0.36 + 0.28 * np.sin(2 * np.pi * (t / points) - 0.9)
    sub_cycle = 0.09 * np.sin(4 * np.pi * (t / points) + 1.1)
    noise = rng.normal(0.0, 0.04, points)

    cpu = np.clip(base + sub_cycle + noise, 0.05, 0.98)
    mem = np.clip(0.45 + 0.35 * cpu + rng.normal(0.0, 0.03, points), 0.1, 0.95)

    for start_ratio, end_ratio, burst in [(0.18, 0.22, 0.18), (0.52, 0.57, 0.14), (0.77, 0.81, 0.21)]:
        start = int(points * start_ratio)
        end = int(points * end_ratio)
        cpu[start:end] = np.clip(cpu[start:end] + burst, 0.0, 1.0)

    latency_budget = 200.0
    step_seconds = step_minutes * 60

    return [
        WorkloadSample(
            timestamp_s=i * step_seconds,
            cpu_demand=float(cpu[i]),
            mem_demand=float(mem[i]),
            latency_budget_ms=latency_budget,
        )
        for i in range(points)
    ]
