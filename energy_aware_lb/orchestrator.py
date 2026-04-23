from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from .config import RuntimeConfig
from .forecasting import HybridForecaster
from .models import RoutingDecision, StepMetrics, WorkloadSample
from .policy import EnergyAwarePolicy
from .providers import TelemetryProvider


@dataclass
class EnergyAwareOrchestrator:
    provider: TelemetryProvider
    config: RuntimeConfig
    forecaster: HybridForecaster = field(init=False)
    policy: EnergyAwarePolicy = field(init=False)
    routing_log: List[RoutingDecision] = field(default_factory=list, init=False)
    scale_events: int = 0

    def __post_init__(self) -> None:
        self.forecaster = HybridForecaster(self.config.forecast)
        self.policy = EnergyAwarePolicy(self.config.policy)

    def process_step(self, sample: WorkloadSample) -> RoutingDecision:
        nodes = self.provider.list_nodes()
        observed = float(np.mean([n.cpu_utilization for n in nodes if n.active]) if nodes else 0.0)
        self.forecaster.observe(observed)
        forecast = self.forecaster.snapshot()

        micro_batches = max(1, int(round(sample.cpu_demand * 20.0)))
        cpu_chunk = sample.cpu_demand / micro_batches
        mem_chunk = sample.mem_demand / micro_batches
        preferred_tier = self.policy.choose_tier(forecast, observed_load=observed)

        latencies: List[float] = []
        allocations: List[tuple[str, str]] = []
        rejects = 0

        for _ in range(micro_batches):
            node = self.policy.pick_node(nodes, tier=preferred_tier, demand=cpu_chunk)
            if node is None:
                rejects += 1
                continue
            self.policy.apply_workload(node, cpu_chunk, mem_chunk)
            latencies.append(self.policy.estimate_latency_ms(node, cpu_chunk))
            allocations.append((node.node_id, node.tier))

        if not allocations:
            decision = RoutingDecision(
                timestamp_s=sample.timestamp_s,
                workload_cpu=sample.cpu_demand,
                chosen_tier="rejected",
                node_id="none",
                predicted_load=forecast.predicted_load,
                confidence=forecast.confidence,
                expected_latency_ms=sample.latency_budget_ms * 1.8,
                sla_met=False,
                migration_triggered=False,
            )
            self.routing_log.append(decision)
            return decision

        tier_votes = [tier for _, tier in allocations]
        chosen_tier = "efficient" if tier_votes.count("efficient") >= tier_votes.count("fallback") else "fallback"
        node_id = allocations[0][0]
        latency = float(np.percentile(latencies, 95)) if latencies else sample.latency_budget_ms * 1.8
        reject_penalty = rejects * 10.0
        latency += reject_penalty
        sla_met = latency <= sample.latency_budget_ms
        migration = any(tier != preferred_tier for tier in tier_votes)

        up, down = self.policy.elastic_scale(
            nodes,
            predicted_load=forecast.predicted_load,
            max_up=self.config.orchestrator.max_step_scale_up,
            max_down=self.config.orchestrator.max_step_scale_down,
        )
        self.scale_events += up + down

        self.policy.decay_nodes(nodes, factor=self.config.orchestrator.placement_decay)
        self.provider.publish_allocations(nodes)

        decision = RoutingDecision(
            timestamp_s=sample.timestamp_s,
            workload_cpu=sample.cpu_demand,
            chosen_tier=chosen_tier,
            node_id=node_id,
            predicted_load=forecast.predicted_load,
            confidence=forecast.confidence,
            expected_latency_ms=latency,
            sla_met=sla_met,
            migration_triggered=migration,
        )
        self.routing_log.append(decision)
        return decision

    def aggregate_metrics(self) -> StepMetrics:
        nodes = self.provider.list_nodes()
        active = [n for n in nodes if n.active]
        avg_power = float(np.mean([n.estimated_power_w for n in active]) if active else 0.0)

        latencies = [d.expected_latency_ms for d in self.routing_log]
        violations = [d for d in self.routing_log if not d.sla_met]
        efficient = [d for d in self.routing_log if d.chosen_tier == "efficient"]
        migrations = [d for d in self.routing_log if d.migration_triggered]

        ts = self.routing_log[-1].timestamp_s if self.routing_log else 0
        return StepMetrics(
            timestamp_s=ts,
            avg_power_w=avg_power,
            p95_latency_ms=float(np.percentile(latencies, 95)) if latencies else 0.0,
            sla_violation_rate=float(100.0 * len(violations) / max(1, len(self.routing_log))),
            active_nodes=len(active),
            efficient_ratio=float(len(efficient) / max(1, len(self.routing_log))),
            migrations=len(migrations),
        )
