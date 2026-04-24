from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

from .models import WorkloadSample


def generate_workload_trace(
    hours: int = 24,
    step_minutes: int = 5,
    seed: int = 42,
    dataset_csv: Optional[str] = None,
    dataset_max_points: Optional[int] = None,
) -> List[WorkloadSample]:
    rng = np.random.default_rng(seed)

    if dataset_csv:
        cpu = _load_cpu_series_from_csv(Path(dataset_csv), max_points=dataset_max_points)
    else:
        cpu = _generate_synthetic_cpu(hours=hours, step_minutes=step_minutes, seed=seed)

    mem = np.clip(0.45 + 0.35 * cpu + rng.normal(0.0, 0.03, len(cpu)), 0.1, 0.95)
    latency_budget = 200.0
    step_seconds = step_minutes * 60

    return [
        WorkloadSample(
            timestamp_s=i * step_seconds,
            cpu_demand=float(cpu[i]),
            mem_demand=float(mem[i]),
            latency_budget_ms=latency_budget,
        )
        for i in range(len(cpu))
    ]


def _load_cpu_series_from_csv(csv_path: Path, max_points: Optional[int] = None) -> np.ndarray:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset CSV not found: {csv_path}")

    values: List[float] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Dataset CSV has no header: {csv_path}")

        field_map = {name.lower(): name for name in reader.fieldnames}
        value_col = field_map.get("value") or field_map.get("cpu") or field_map.get("cpu_utilization")
        if not value_col:
            raise ValueError(
                f"Dataset CSV must include one of: value, cpu, cpu_utilization. Found: {reader.fieldnames}"
            )

        for row in reader:
            raw = row.get(value_col)
            if raw is None or raw == "":
                continue
            try:
                values.append(float(raw))
            except ValueError:
                continue

            if max_points is not None and len(values) >= max_points:
                break

    if not values:
        raise ValueError(f"No numeric values found in dataset CSV column '{value_col}': {csv_path}")

    return np.clip(np.asarray(values, dtype=float), 0.0, 1.0)


def _generate_synthetic_cpu(hours: int, step_minutes: int, seed: int) -> np.ndarray:
    # Prefer the shared generator from implementations/ so both tracks use the same synthetic profile.
    try:
        from implementations.data import WorkloadConfig, generate_synthetic_workload

        cfg = WorkloadConfig(hours=hours, step_minutes=step_minutes, seed=seed)
        return generate_synthetic_workload(cfg)
    except ModuleNotFoundError:
        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from implementations.data import WorkloadConfig, generate_synthetic_workload

        cfg = WorkloadConfig(hours=hours, step_minutes=step_minutes, seed=seed)
        return generate_synthetic_workload(cfg)
