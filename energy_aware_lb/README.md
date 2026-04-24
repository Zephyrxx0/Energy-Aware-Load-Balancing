# Energy-Aware Load Balancing (Professional Test Harness)

This package upgrades the old notebook-only experiment into a modular, production-style control loop inspired by the research in papers/ and implementations/.

## Design Goals

- Modular architecture for forecasting, routing policy, and orchestration.
- Real-world cloud adaptation points for AWS EC2 + CloudWatch and Kubernetes.
- Multi-objective decision function for energy, migration stability, and SLA risk.
- Scale-aware controls (elastic up/down within bounded limits per control step).

## Modules

- config.py: runtime, policy, and forecaster configuration dataclasses.
- models.py: typed domain entities (nodes, workload samples, decisions, metrics).
- providers.py: provider interfaces and adapters.
- forecasting.py: hybrid short-horizon predictor (EWMA + trend + uncertainty).
- policy.py: energy-aware tiering, placement scoring, and elasticity.
- orchestrator.py: closed-loop decision engine and aggregated KPIs.
- workload.py: workload trace loader (real CSV) + synthetic fallback.
- simulation.py: end-to-end runner for experiments.

The synthetic fallback now reuses `implementations/data.py` (`generate_synthetic_workload`) so the
`testing` and `implementations` tracks share the same synthetic workload profile.

## Run

From the testing folder:

python run_professional_benchmark.py --hours 24 --step-minutes 5 --seed 42

Run with a real dataset (NAB AWS CloudWatch sample included in `testing/datasets/`):

python run_professional_benchmark.py --dataset-csv testing/datasets/nab_realAWSCloudwatch/ec2_cpu_utilization_24ae8d.csv --dataset-max-points 288

Run all NAB EC2 CSV traces and export combined JSON/CSV reports:

python testing/run_dataset_comparison.py --dataset-dir testing/datasets/nab_realAWSCloudwatch --output-dir benchmark_results

## Production Integration Notes

- AWSCloudWatchProvider: implement list_nodes() from EC2 inventory and cloudwatch metrics.
- KubernetesMetricsProvider: map metrics-server node/pod usage into ClusterNode state.
- Replace HybridForecaster with trained LSTM/Transformer inference service for online operation.
