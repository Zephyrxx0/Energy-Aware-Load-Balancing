from __future__ import annotations

from dataclasses import asdict
from typing import Dict

from .config import RuntimeConfig
from .orchestrator import EnergyAwareOrchestrator
from .providers import SimulatedProvider
from .workload import generate_workload_trace


def run_simulation(
    hours: int = 24,
    step_minutes: int = 5,
    seed: int = 42,
    efficient_nodes: int = 12,
    fallback_nodes: int = 3,
) -> Dict[str, object]:
    provider = SimulatedProvider(
        provider_name="aws-ec2",
        efficient_count=efficient_nodes,
        fallback_count=fallback_nodes,
        rng_seed=seed,
    )
    runtime = RuntimeConfig()
    orchestrator = EnergyAwareOrchestrator(provider=provider, config=runtime)
    trace = generate_workload_trace(hours=hours, step_minutes=step_minutes, seed=seed)

    for sample in trace:
        orchestrator.process_step(sample)

    metrics = orchestrator.aggregate_metrics()
    return {
        "config": {
            "hours": hours,
            "step_minutes": step_minutes,
            "efficient_nodes": efficient_nodes,
            "fallback_nodes": fallback_nodes,
            "seed": seed,
        },
        "summary": asdict(metrics),
        "first_decisions": [asdict(x) for x in orchestrator.routing_log[:5]],
        "last_decisions": [asdict(x) for x in orchestrator.routing_log[-5:]],
        "scale_events": orchestrator.scale_events,
    }
