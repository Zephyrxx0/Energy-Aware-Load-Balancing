from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from .config import PolicyConfig
from .models import ClusterNode, ForecastSnapshot


@dataclass
class EnergyAwarePolicy:
    config: PolicyConfig

    def choose_tier(self, forecast: ForecastSnapshot, observed_load: float) -> str:
        if forecast.uncertainty > 0.22:
            return "fallback"
        if forecast.predicted_load > self.config.overload_threshold:
            return "fallback"
        if observed_load > self.config.fallback_headroom:
            return "fallback"
        if np.random.random() <= self.config.efficient_target_ratio * max(0.65, forecast.confidence):
            return "efficient"
        return "fallback"

    def pick_node(self, nodes: List[ClusterNode], tier: str, demand: float) -> Optional[ClusterNode]:
        tier_nodes = [n for n in nodes if n.active and n.tier == tier and n.available_cpu >= demand]
        if not tier_nodes:
            alt = "fallback" if tier == "efficient" else "efficient"
            tier_nodes = [n for n in nodes if n.active and n.tier == alt and n.available_cpu >= demand]
            tier = alt
        if not tier_nodes:
            return None

        def score(node: ClusterNode) -> float:
            projected = min(1.0, node.cpu_utilization + demand)
            power_penalty = node.idle_power_w + (node.max_power_w - node.idle_power_w) * projected
            migration_penalty = 1.0 if projected > self.config.overload_threshold else 0.0
            latency_penalty = max(0.0, projected - 0.75) * 100.0
            return (
                self.config.energy_weight * power_penalty
                + self.config.migration_weight * migration_penalty
                + self.config.sla_weight * latency_penalty
            )

        tier_nodes.sort(key=score)
        return tier_nodes[0]

    def estimate_latency_ms(self, node: ClusterNode, demand: float) -> float:
        projected = min(1.0, node.cpu_utilization + demand)
        base = 30.0 if node.tier == "efficient" else 25.0
        return base + 105.0 * projected ** 2

    def apply_workload(self, node: ClusterNode, cpu_demand: float, mem_demand: float) -> None:
        node.cpu_utilization = min(1.0, node.cpu_utilization + cpu_demand)
        node.mem_utilization = min(1.0, node.mem_utilization + mem_demand)

    def decay_nodes(self, nodes: List[ClusterNode], factor: float) -> None:
        for node in nodes:
            if not node.active:
                node.cpu_utilization = 0.0
                node.mem_utilization = 0.0
                continue
            node.cpu_utilization = max(0.0, node.cpu_utilization - factor)
            node.mem_utilization = max(0.0, node.mem_utilization - factor * 0.6)

    def elastic_scale(self, nodes: List[ClusterNode], predicted_load: float, max_up: int, max_down: int) -> Tuple[int, int]:
        efficient_nodes = [n for n in nodes if n.tier == "efficient"]
        active = [n for n in efficient_nodes if n.active]
        inactive = [n for n in efficient_nodes if not n.active]
        min_active_efficient = 6

        scale_up = 0
        scale_down = 0
        if predicted_load > 0.8 and inactive:
            for node in inactive[:max_up]:
                node.active = True
                scale_up += 1

        if predicted_load < 0.20 and len(active) > min_active_efficient:
            to_disable = min(max_down, len(active) - min_active_efficient)
            for node in sorted(active, key=lambda n: n.cpu_utilization)[:to_disable]:
                node.active = False
                node.cpu_utilization = 0.0
                node.mem_utilization = 0.0
                scale_down += 1

        return scale_up, scale_down
