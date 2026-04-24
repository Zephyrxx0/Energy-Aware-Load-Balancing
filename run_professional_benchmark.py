from __future__ import annotations

import argparse
import json

from energy_aware_lb import run_simulation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run modular energy-aware load-balancing simulation for cloud-scale policies."
    )
    parser.add_argument("--hours", type=int, default=24, help="Simulation duration in hours")
    parser.add_argument("--step-minutes", type=int, default=5, help="Sampling interval in minutes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--efficient-nodes", type=int, default=12, help="Initial efficient-tier node count")
    parser.add_argument("--fallback-nodes", type=int, default=3, help="Initial fallback-tier node count")
    parser.add_argument(
        "--dataset-csv",
        type=str,
        default=None,
        help="Optional path to a real workload CSV file with a 'value' CPU-utilization column",
    )
    parser.add_argument(
        "--dataset-max-points",
        type=int,
        default=None,
        help="Optional maximum number of rows to read from dataset-csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_simulation(
        hours=args.hours,
        step_minutes=args.step_minutes,
        seed=args.seed,
        efficient_nodes=args.efficient_nodes,
        fallback_nodes=args.fallback_nodes,
        dataset_csv=args.dataset_csv,
        dataset_max_points=args.dataset_max_points,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
