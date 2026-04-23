from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol

import numpy as np

from .models import ClusterNode


class TelemetryProvider(Protocol):
    def list_nodes(self) -> List[ClusterNode]:
        ...

    def publish_allocations(self, nodes: List[ClusterNode]) -> None:
        ...


@dataclass
class SimulatedProvider:
    provider_name: str
    efficient_count: int
    fallback_count: int
    rng_seed: int = 42

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.rng_seed)
        self._nodes: List[ClusterNode] = []
        for i in range(self.efficient_count):
            self._nodes.append(
                ClusterNode(
                    node_id=f"{self.provider_name}-eff-{i:02d}",
                    provider=self.provider_name,
                    tier="efficient",
                    cpu_capacity=1.0,
                    mem_capacity_gb=4.0,
                    idle_power_w=2.0,
                    max_power_w=11.6,
                )
            )
        for i in range(self.fallback_count):
            self._nodes.append(
                ClusterNode(
                    node_id=f"{self.provider_name}-fb-{i:02d}",
                    provider=self.provider_name,
                    tier="fallback",
                    cpu_capacity=1.0,
                    mem_capacity_gb=8.0,
                    idle_power_w=2.0,
                    max_power_w=14.1,
                )
            )

    def list_nodes(self) -> List[ClusterNode]:
        return self._nodes

    def publish_allocations(self, nodes: List[ClusterNode]) -> None:
        for node in nodes:
            if not node.active:
                node.cpu_utilization = 0.0
                node.mem_utilization = 0.0
                continue
            node.cpu_utilization = max(0.0, node.cpu_utilization + self._rng.normal(0.0, 0.012))
            node.mem_utilization = max(0.0, node.mem_utilization + self._rng.normal(0.0, 0.008))


class AWSCloudWatchProvider:
    """
    Production adapter scaffold for AWS EC2/CloudWatch.
    Uses lazy imports so local simulation works without cloud SDKs.
    """

    def __init__(self, region: str) -> None:
        self.region = region
        self._client = None

    def _ensure_client(self) -> None:
        if self._client is None:
            import boto3  # type: ignore

            self._client = boto3.client("cloudwatch", region_name=self.region)

    def list_nodes(self) -> List[ClusterNode]:
        self._ensure_client()
        raise NotImplementedError(
            "Wire this adapter to EC2 inventory + CloudWatch metrics in your account."
        )

    def publish_allocations(self, nodes: List[ClusterNode]) -> None:
        del nodes


class KubernetesMetricsProvider:
    """
    Production adapter scaffold for Kubernetes Metrics API.
    """

    def __init__(self, context: str | None = None) -> None:
        self.context = context

    def list_nodes(self) -> List[ClusterNode]:
        from kubernetes import client, config  # type: ignore

        if self.context:
            config.load_kube_config(context=self.context)
        else:
            config.load_kube_config()
        core = client.CoreV1Api()
        nodes = core.list_node().items
        del nodes
        raise NotImplementedError(
            "Wire node allocatable resources and metrics-server utilization into ClusterNode objects."
        )

    def publish_allocations(self, nodes: List[ClusterNode]) -> None:
        del nodes
