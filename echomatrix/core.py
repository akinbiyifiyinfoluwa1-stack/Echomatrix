"""Deterministic market intelligence, simulation, and Deriv execution primitives.

The module deliberately keeps paper-account state separate from broker state.  A
Deriv order is only possible when the deployment operator explicitly enables it
and supplies a token through the environment.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import math
import os
import random
import statistics
from collections import deque
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrategyStage(str, Enum):
    IDEA = "IDEA"; PROTOTYPE = "PROTOTYPE"; BACKTEST = "BACKTEST"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE TEST"; STRESS_TEST = "STRESS TEST"
    SIMULATION = "SIMULATION"; CANDIDATE = "CANDIDATE"; VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"; RETIRED = "RETIRED"


_STAGES = list(StrategyStage)


@dataclass
class Candle:
    epoch: int
    open: float
    high: float
    low: float
    close: float
    source: str = "simulation"


@dataclass
class MarketState:
    instrument: str = "R_100"
    price: float = 100.0
    ema_fast: float = 100.0
    ema_slow: float = 100.0
    momentum: float = 0.0
    volatility: float = 0.15
    regime: str = "RANGE / TRANSITION"
    timestamp: str = field(default_factory=now)
    source: str = "deterministic simulation"
    data_version: str = "v1"
    confidence: float = 0.6


class MarketDataValidator:
    """Reject invalid OHLC data and expose gaps instead of fabricating candles."""
    def validate(self, candles: list[Candle]) -> tuple[list[Candle], list[str]]:
        accepted: list[Candle] = []; issues: list[str] = []; seen: set[int] = set()
        previous: int | None = None
        for candle in sorted(candles, key=lambda c: c.epoch):
            if candle.epoch in seen:
                issues.append(f"duplicate timestamp {candle.epoch}"); continue
            if candle.low > min(candle.open, candle.close) or candle.high < max(candle.open, candle.close) or candle.low > candle.high:
                issues.append(f"invalid OHLC at {candle.epoch}"); continue
            if previous is not None and candle.epoch - previous > 120:
                issues.append(f"data gap before {candle.epoch}")
            accepted.append(candle); seen.add(candle.epoch); previous = candle.epoch
        return accepted, issues


class WorldModel:
    def __init__(self) -> None:
        self.state = MarketState()
        self.returns: deque[float] = deque(maxlen=120)
        self.validator = MarketDataValidator()
        self.data_issues: deque[str] = deque(maxlen=50)

    def step(self) -> MarketState:
        s = self.state; delta = random.gauss(0.04, 0.42)
        s.price = round(max(0.0001, s.price + delta), 5)
        s.momentum = delta / max(s.price, 1.0); self.returns.append(s.momentum)
        s.ema_fast = round(.78 * s.ema_fast + .22 * s.price, 5); s.ema_slow = round(.94 * s.ema_slow + .06 * s.price, 5)
        s.volatility = round(max(.01, min(.8, statistics.pstdev(self.returns) * math.sqrt(60) if len(self.returns) > 2 else .15)), 4)
        gap = s.ema_fast - s.ema_slow
        s.regime = "BULLISH TREND" if gap > .12 else "BEARISH TREND" if gap < -.12 else "HIGH VOLATILITY / TRANSITION" if s.volatility > .35 else "RANGE / TRANSITION"
        s.timestamp = now(); return s


class ModelCouncil:
    def evaluate(self, s: MarketState) -> dict[str, Any]:
        direction = max(.01, min(.99, .5 + (s.ema_fast - s.ema_slow) / max(s.price, 1) * 8 + s.momentum * 10))
        momentum = max(.01, min(.99, .5 + s.momentum * 14))
        anomaly = max(.01, min(.99, abs(s.momentum) * 25 + max(0, s.volatility - .25)))
        opportunity = max(0., min(1., .5 * direction + .25 * momentum + .25 * (1 - s.volatility)))
        agreement = .55 + .45 * (1 - abs(direction - momentum))
        return {"regime_model": s.regime, "direction_probability": round(direction, 3), "volatility_model": round(s.volatility, 3), "momentum_model": round(momentum, 3), "anomaly_model": round(anomaly, 3), "opportunity_score": round(opportunity, 3), "uncertainty": round(1 - agreement, 3), "agreement": round(agreement, 3), "evidence": ["EMA structure", "recent price momentum", "realized volatility"], "model_version": "baseline-statistical-v1"}


class RiskGovernor:
    def __init__(self, max_positions: int = 5, max_drawdown: float = .20) -> None:
        self.max_positions, self.max_drawdown = max_positions, max_drawdown
    def evaluate(self, balance: float, starting: float, positions: int) -> dict[str, Any]:
        drawdown = max(0., (starting - balance) / starting)
        status = "EMERGENCY STOP" if drawdown >= self.max_drawdown else "WARNING" if drawdown >= .1 or positions >= self.max_positions - 1 else "NORMAL"
        return {"state": status, "drawdown": round(drawdown, 4), "open_positions": positions, "max_open_positions": self.max_positions}


class VirtualAccount:
    def __init__(self, balance: float = 10_000.) -> None:
        self.starting_balance = balance; self.balance = balance; self.positions: list[dict[str, Any]] = []; self.history: list[dict[str, Any]] = []; self.memory: list[dict[str, Any]] = []
    def open(self, price: float, side: str = "LONG", quantity: float = 1.) -> dict[str, Any]:
        p = {"id": f"SIM-{len(self.history) + len(self.positions) + 1}", "symbol": "R_100", "side": side, "quantity": quantity, "entry": price, "mark": price, "pnl": 0., "opened_at": now()}; self.positions.append(p); return p
    def mark(self, price: float) -> None:
        for p in self.positions:
            p["mark"] = price; p["pnl"] = round((price - p["entry"]) * p["quantity"] * (1 if p["side"] == "LONG" else -1), 4)
    def close(self, position_id: str) -> dict[str, Any] | None:
        p = next((item for item in self.positions if item["id"] == position_id), None)
        if not p: return None
        self.positions.remove(p); self.balance = round(self.balance + p["pnl"], 4); closed = {**p, "closed_at": now()}; self.history.append(closed)
        self.memory.append({"event": "simulation_outcome", "position_id": position_id, "pnl": p["pnl"], "lesson": "Outcome retained for evaluation; simulation is not broker execution.", "timestamp": now()}); return closed


class StrategyRegistry:
    def __init__(self) -> None:
        self.items = [{"id": "STRAT-001", "name": "Regime Momentum", "purpose": "Trend following", "instruments": ["R_100"], "timeframes": ["1m"], "status": StrategyStage.VALIDATED.value, "score": 78, "transitions": []}]
    def list(self) -> list[dict[str, Any]]: return self.items
    def transition(self, strategy_id: str, target: StrategyStage, metrics: dict[str, float] | None = None) -> dict[str, Any]:
        item = next((x for x in self.items if x["id"] == strategy_id), None)
        if not item: raise KeyError(strategy_id)
        current = StrategyStage(item["status"])
        if current == StrategyStage.RETIRED:
            raise ValueError("a retired strategy cannot transition")
        expected = _STAGES[_STAGES.index(current) + 1] if current != StrategyStage.ACTIVE else None
        if target != StrategyStage.RETIRED and target != expected:
            raise ValueError(f"invalid lifecycle transition: {current.value} → {target.value}")
        item["status"] = target.value; item["transitions"].append({"from": current.value, "to": target.value, "metrics": metrics or {}, "timestamp": now()}); return item


class DerivClient:
    """Small synchronous client for Deriv's official WebSocket API protocol."""
    endpoint = "wss://ws.derivws.com/websockets/v3"
    def __init__(self) -> None:
        self.token = os.getenv("DERIV_API_TOKEN", ""); self.app_id = os.getenv("DERIV_APP_ID", "1089")
        self.enabled = os.getenv("ECHOMATRIX_ENABLE_LIVE_EXECUTION", "").lower() == "true"
    @property
    def configured(self) -> bool: return bool(self.token)
    def status(self) -> dict[str, Any]:
        return {"configured": self.configured, "live_execution_enabled": self.enabled, "endpoint": "Deriv WebSocket API", "account": self._request({"authorize": self.token}) if self.configured else None}
    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import websocket  # imported only when live connectivity is requested
            ws = websocket.create_connection(f"{self.endpoint}?app_id={self.app_id}", timeout=15)
            ws.send(json.dumps(payload)); result = json.loads(ws.recv()); ws.close()
        except Exception as exc:
            raise RuntimeError("Could not reach Deriv. Check network, app ID, and token configuration.") from exc
        if "error" in result: raise RuntimeError(result["error"].get("message", "Deriv rejected the request"))
        return result
    def require_enabled(self) -> None:
        if not self.configured: raise PermissionError("DERIV_API_TOKEN is not configured")
        if not self.enabled: raise PermissionError("Live execution is disabled. Set ECHOMATRIX_ENABLE_LIVE_EXECUTION=true only after reviewing the target account.")
    def proposal(self, symbol: str, contract_type: str, amount: float, duration: int, duration_unit: str) -> dict[str, Any]:
        self.require_enabled(); return self._request({"proposal": 1, "amount": amount, "basis": "stake", "contract_type": contract_type, "currency": os.getenv("DERIV_CURRENCY", "USD"), "duration": duration, "duration_unit": duration_unit, "symbol": symbol})
    def buy(self, proposal_id: str, price: float) -> dict[str, Any]: self.require_enabled(); return self._request({"buy": proposal_id, "price": price})
    def sell(self, contract_id: int, price: float = 0) -> dict[str, Any]: self.require_enabled(); return self._request({"sell": contract_id, "price": price})


def state_dict(state: MarketState) -> dict[str, Any]: return asdict(state)
