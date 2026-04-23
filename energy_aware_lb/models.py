from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClusterNode:
    node_id: str
    provider: str
    tier: str
    cpu_capacity: float
    mem_capacity_gb: float
    idle_power_w: float
    max_power_w: float
    cpu_utilization: float = 0.0
    mem_utilization: float = 0.0
    active: bool = True

    @property
    def available_cpu(self) -> float:
        return max(0.0, 1.0 - self.cpu_utilization)

    @property
    def estimated_power_w(self) -> float:
        util = min(1.0, max(0.0, self.cpu_utilization))
        return self.idle_power_w + (self.max_power_w - self.idle_power_w) * util


@dataclass(frozen=True)
class WorkloadSample:
    timestamp_s: int
    cpu_demand: float
    mem_demand: float
    latency_budget_ms: float


@dataclass
class ForecastSnapshot:
    predicted_load: float
    confidence: float
    uncertainty: float


@dataclass
class RoutingDecision:
    timestamp_s: int
    workload_cpu: float
    chosen_tier: str
    node_id: str
    predicted_load: float
    confidence: float
    expected_latency_ms: float
    sla_met: bool
    migration_triggered: bool


@dataclass
class StepMetrics:
    timestamp_s: int
    avg_power_w: float
    p95_latency_ms: float
    sla_violation_rate: float
    active_nodes: int
    efficient_ratio: float
    migrations: int
