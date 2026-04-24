from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from energy_aware_lb import run_simulation


def _assign_rank(rows: List[Dict[str, object]], metric: str, rank_field: str, ascending: bool = True) -> None:
    ordered = sorted(rows, key=lambda r: float(r[metric]), reverse=not ascending)
    for idx, row in enumerate(ordered, start=1):
        row[rank_field] = idx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run benchmark across all CSV datasets in a directory and export combined JSON/CSV reports."
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="testing/datasets/nab_realAWSCloudwatch",
        help="Directory containing workload CSV datasets",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmark_results",
        help="Directory to write combined reports",
    )
    parser.add_argument("--step-minutes", type=int, default=5, help="Sampling interval in minutes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--efficient-nodes", type=int, default=12, help="Initial efficient-tier node count")
    parser.add_argument("--fallback-nodes", type=int, default=3, help="Initial fallback-tier node count")
    parser.add_argument(
        "--dataset-max-points",
        type=int,
        default=None,
        help="Optional max rows to read per dataset",
    )
    return parser.parse_args()


def run_suite(args: argparse.Namespace) -> Dict[str, object]:
    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    csv_files = sorted(dataset_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in: {dataset_dir}")

    results: List[Dict[str, object]] = []
    for csv_file in csv_files:
        report = run_simulation(
            step_minutes=args.step_minutes,
            seed=args.seed,
            efficient_nodes=args.efficient_nodes,
            fallback_nodes=args.fallback_nodes,
            dataset_csv=str(csv_file),
            dataset_max_points=args.dataset_max_points,
        )
        summary = report["summary"]
        row = {
            "dataset": csv_file.name,
            "points_used": report["config"]["total_steps"],
            "avg_power_w": summary["avg_power_w"],
            "p95_latency_ms": summary["p95_latency_ms"],
            "sla_violation_rate": summary["sla_violation_rate"],
            "active_nodes": summary["active_nodes"],
            "efficient_ratio": summary["efficient_ratio"],
            "migrations": summary["migrations"],
            "scale_events": report["scale_events"],
        }
        results.append({"dataset": csv_file.name, "report": report, "summary_row": row})

    rows = [x["summary_row"] for x in results]

    _assign_rank(rows, metric="avg_power_w", rank_field="rank_power", ascending=True)
    _assign_rank(rows, metric="p95_latency_ms", rank_field="rank_latency", ascending=True)
    _assign_rank(rows, metric="sla_violation_rate", rank_field="rank_sla", ascending=True)

    avg_power = sum(x["avg_power_w"] for x in rows) / len(rows)
    avg_p95_latency = sum(x["p95_latency_ms"] for x in rows) / len(rows)
    avg_sla_violation = sum(x["sla_violation_rate"] for x in rows) / len(rows)

    best_power_row = min(rows, key=lambda r: float(r["avg_power_w"]))
    best_latency_row = min(rows, key=lambda r: float(r["p95_latency_ms"]))
    best_sla_row = min(rows, key=lambda r: float(r["sla_violation_rate"]))

    return {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset_dir": str(dataset_dir),
            "dataset_count": len(results),
            "step_minutes": args.step_minutes,
            "seed": args.seed,
            "efficient_nodes": args.efficient_nodes,
            "fallback_nodes": args.fallback_nodes,
            "dataset_max_points": args.dataset_max_points,
        },
        "aggregate": {
            "mean_avg_power_w": avg_power,
            "mean_p95_latency_ms": avg_p95_latency,
            "mean_sla_violation_rate": avg_sla_violation,
            "best_by_power": {
                "dataset": best_power_row["dataset"],
                "avg_power_w": best_power_row["avg_power_w"],
            },
            "best_by_latency": {
                "dataset": best_latency_row["dataset"],
                "p95_latency_ms": best_latency_row["p95_latency_ms"],
            },
            "best_by_sla": {
                "dataset": best_sla_row["dataset"],
                "sla_violation_rate": best_sla_row["sla_violation_rate"],
            },
        },
        "datasets": results,
    }


def write_reports(payload: Dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "dataset_comparison_report.json"
    csv_path = output_dir / "dataset_comparison_report.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    rows = [x["summary_row"] for x in payload["datasets"]]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote JSON: {json_path}")
    print(f"Wrote CSV: {csv_path}")


def main() -> None:
    args = parse_args()
    payload = run_suite(args)
    write_reports(payload, Path(args.output_dir))


if __name__ == "__main__":
    main()
