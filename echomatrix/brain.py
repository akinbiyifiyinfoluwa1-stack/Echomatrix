"""EchoMatrix decision brain.

Broker-agnostic intelligence: market evidence -> ranked decision state -> adaptive memory.
No broker credentials or execution calls live here.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    name: str
    value: float
    confidence: float
    weight: float = 1.0
    source: str = "internal"


@dataclass
class BrainDecision:
    action: str
    score: float
    confidence: float
    uncertainty: float
    regime: str
    reasons: list[str]
    evidence: list[dict[str, Any]]
    model_version: str = "brain-v1"
    timestamp: str = field(default_factory=utc_now)


class AdaptiveMemory:
    """Online outcome memory with deliberately slow adaptation."""
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.edge: dict[str, float] = {}

    def record(self, feature: str, pnl: float, context: dict[str, Any] | None = None) -> dict[str, Any]:
        sign = 1.0 if pnl > 0 else -1.0 if pnl < 0 else 0.0
        old = self.edge.get(feature, 0.0)
        self.edge[feature] = round(max(-1.0, min(1.0, old * 0.9 + sign * 0.1)), 5)
        item = {"feature": feature, "pnl": round(pnl, 6), "edge": self.edge[feature], "context": context or {}, "timestamp": utc_now()}
        self.records.append(item)
        self.records = self.records[-500:]
        return item

    def adjustment(self, feature: str) -> float:
        return self.edge.get(feature, 0.0)


class FeatureEngine:
    def extract(self, state: Any) -> list[Evidence]:
        price = max(float(state.price), 1e-9)
        trend = max(-1.0, min(1.0, (state.ema_fast - state.ema_slow) / price * 20.0))
        momentum = max(-1.0, min(1.0, float(state.momentum) * 20.0))
        vol = max(0.0, min(1.0, float(state.volatility)))
        regime_conf = 0.85 if "TREND" in state.regime else 0.60
        return [
            Evidence("trend", trend, regime_conf, 1.2, "ema_structure"),
            Evidence("momentum", momentum, 0.75, 1.0, "price_return"),
            Evidence("volatility", 1.0 - vol, 0.80, 0.8, "realized_volatility"),
        ]


class DecisionEngine:
    def __init__(self, memory: AdaptiveMemory | None = None) -> None:
        self.features = FeatureEngine()
        self.memory = memory or AdaptiveMemory()

    def decide(self, state: Any) -> BrainDecision:
        evidence = self.features.extract(state)
        weighted = sum(e.value * e.confidence * e.weight for e in evidence)
        weights = sum(e.confidence * e.weight for e in evidence) or 1.0
        raw = max(-1.0, min(1.0, weighted / weights))
        adjustment = self.memory.adjustment("trend") * 0.08 + self.memory.adjustment("momentum") * 0.06
        score = max(-1.0, min(1.0, raw + adjustment))
        agreement = 1.0 - min(1.0, mean(abs(e.value - raw) for e in evidence) / 2.0)
        confidence = max(0.0, min(1.0, (agreement + mean(e.confidence for e in evidence)) / 2.0))
        uncertainty = round(1.0 - confidence, 4)
        threshold = 0.22 + float(state.volatility) * 0.25
        action = "LONG" if score >= threshold else "SHORT" if score <= -threshold else "WAIT"
        reasons = [f"trend={evidence[0].value:.3f}", f"momentum={evidence[1].value:.3f}", f"volatility_quality={evidence[2].value:.3f}"]
        if adjustment:
            reasons.append(f"adaptive_memory_adjustment={adjustment:.3f}")
        return BrainDecision(action, round(score, 4), round(confidence, 4), uncertainty, state.regime, reasons, [e.__dict__ for e in evidence])


class Brain:
    """Top-level intelligence facade used by the API and future workers."""
    def __init__(self) -> None:
        self.memory = AdaptiveMemory()
        self.engine = DecisionEngine(self.memory)
        self.cycles = 0

    def cycle(self, state: Any) -> dict[str, Any]:
        self.cycles += 1
        decision = self.engine.decide(state)
        return {"cycle": self.cycles, "decision": decision.__dict__, "memory_size": len(self.memory.records)}

    def learn(self, feature: str, pnl: float, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.memory.record(feature, pnl, context)

    def status(self, state: Any) -> dict[str, Any]:
        decision = self.engine.decide(state)
        return {"cycles": self.cycles, "decision": decision.__dict__, "memory_records": len(self.memory.records), "adaptive_edges": dict(self.memory.edge)}
