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
- workload.py: diurnal + burst synthetic workload generator.
- simulation.py: end-to-end runner for experiments.

## Run

From the testing folder:

python run_professional_benchmark.py --hours 24 --step-minutes 5 --seed 42

## Production Integration Notes

- AWSCloudWatchProvider: implement list_nodes() from EC2 inventory and cloudwatch metrics.
- KubernetesMetricsProvider: map metrics-server node/pod usage into ClusterNode state.
- Replace HybridForecaster with trained LSTM/Transformer inference service for online operation.
