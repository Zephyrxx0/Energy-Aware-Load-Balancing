from __future__ import annotations

from pathlib import Path

import nbformat as nbf


def build_notebook() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()

    nb.cells.append(
        nbf.v4.new_markdown_cell(
            """
# Enhanced Energy-Aware Load Balancing

## Objective
This notebook uses a modular, production-style simulation harness for hybrid predictive routing.
The architecture follows the paper constraints:

- Multi-objective control over energy, migration, and SLA safety.
- Tiered routing with deterministic fallback.
- Hooks for AWS EC2/CloudWatch and Kubernetes metrics integration.
"""
        )
    )

    nb.cells.append(
        nbf.v4.new_code_cell(
            """
import json
import matplotlib.pyplot as plt
import numpy as np

from energy_aware_lb.simulation import run_simulation
from energy_aware_lb.workload import generate_workload_trace
"""
        )
    )

    nb.cells.append(
        nbf.v4.new_markdown_cell(
            """
## 1. Run Professional Simulation
"""
        )
    )

    nb.cells.append(
        nbf.v4.new_code_cell(
            """
report = run_simulation(hours=24, step_minutes=5, seed=42, efficient_nodes=12, fallback_nodes=3)
print(json.dumps(report["summary"], indent=2))
"""
        )
    )

    nb.cells.append(
        nbf.v4.new_markdown_cell(
            """
## 2. Workload Pattern and Forecasting Context
"""
        )
    )

    nb.cells.append(
        nbf.v4.new_code_cell(
            """
trace = generate_workload_trace(hours=24, step_minutes=5, seed=42)
cpu = np.array([x.cpu_demand for x in trace])
mem = np.array([x.mem_demand for x in trace])
t = np.arange(len(cpu)) * 5 / 60.0

plt.figure(figsize=(12, 4))
plt.plot(t, cpu * 100, label="CPU demand (%)", color="#0b7285", linewidth=2)
plt.plot(t, mem * 100, label="Memory demand (%)", color="#d9480f", linewidth=2, alpha=0.8)
plt.title("Synthetic Cloud Workload with Diurnal + Burst Dynamics")
plt.xlabel("Hour")
plt.ylabel("Demand (%)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
"""
        )
    )

    nb.cells.append(
        nbf.v4.new_markdown_cell(
            """
## 3. Control Outcomes
"""
        )
    )

    nb.cells.append(
        nbf.v4.new_code_cell(
            """
summary = report["summary"]
labels = ["Avg Power (W)", "P95 Latency (ms)", "SLA Viol. (%)", "Active Nodes", "Efficient Ratio"]
values = [
    summary["avg_power_w"],
    summary["p95_latency_ms"],
    summary["sla_violation_rate"],
    summary["active_nodes"],
    summary["efficient_ratio"] * 100,
]

plt.figure(figsize=(11, 4))
bars = plt.bar(labels, values, color=["#0b7285", "#d9480f", "#9c36b5", "#2b8a3e", "#e67700"])
for bar, value in zip(bars, values):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.2f}", ha="center", va="bottom")
plt.title("Hybrid Controller Outcome Metrics")
plt.grid(axis="y", alpha=0.25)
plt.tight_layout()
plt.show()
"""
        )
    )

    return nb


def main() -> None:
    target = Path(__file__).with_name("Enhanced_Load_Balancing.ipynb")
    notebook = build_notebook()
    with target.open("w", encoding="utf-8") as f:
        nbf.write(notebook, f)
    print(f"Notebook generated: {target}")


if __name__ == "__main__":
    main()
