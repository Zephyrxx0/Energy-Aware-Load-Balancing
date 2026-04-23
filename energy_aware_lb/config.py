from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastConfig:
    window: int = 12
    horizon_steps: int = 3
    ewma_alpha: float = 0.35
    trend_strength: float = 0.8
    uncertainty_guardrail: float = 0.18


@dataclass(frozen=True)
class PolicyConfig:
    efficient_target_ratio: float = 0.98
    overload_threshold: float = 0.82
    fallback_headroom: float = 0.65
    sla_budget_ms: float = 120.0
    energy_weight: float = 1.0
    migration_weight: float = 0.35
    sla_weight: float = 0.65


@dataclass(frozen=True)
class OrchestratorConfig:
    control_interval_seconds: int = 60
    placement_decay: float = 0.05
    max_step_scale_up: int = 2
    max_step_scale_down: int = 1


@dataclass(frozen=True)
class RuntimeConfig:
    forecast: ForecastConfig = ForecastConfig()
    policy: PolicyConfig = PolicyConfig()
    orchestrator: OrchestratorConfig = OrchestratorConfig()
