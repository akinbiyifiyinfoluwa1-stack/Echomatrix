from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math, random

@dataclass
class MarketState:
    instrument: str = "DEMO/USD"
    price: float = 100.0
    ema_fast: float = 100.0
    ema_slow: float = 100.0
    momentum: float = 0.0
    volatility: float = 0.15
    regime: str = "RANGE / TRANSITION"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WorldModel:
    def __init__(self):
        self.state = MarketState()

    def step(self) -> MarketState:
        s = self.state
        delta = random.gauss(0.04, 0.42)
        s.price = round(max(1.0, s.price + delta), 5)
        s.momentum = round(delta / max(s.price, 1.0), 5)
        s.ema_fast = round(0.78 * s.ema_fast + 0.22 * s.price, 5)
        s.ema_slow = round(0.94 * s.ema_slow + 0.06 * s.price, 5)
        s.volatility = round(max(0.01, min(0.80, 0.94 * s.volatility + 0.06 * abs(delta))), 4)
        gap = s.ema_fast - s.ema_slow
        if gap > 0.12: s.regime = "BULLISH TREND"
        elif gap < -0.12: s.regime = "BEARISH TREND"
        elif s.volatility > 0.35: s.regime = "HIGH VOLATILITY / TRANSITION"
        else: s.regime = "RANGE / TRANSITION"
        s.timestamp = datetime.now(timezone.utc).isoformat()
        return s

class ModelCouncil:
    def evaluate(self, s: MarketState) -> dict:
        direction = max(0.01, min(0.99, 0.5 + (s.ema_fast-s.ema_slow)/max(s.price,1)*8 + s.momentum*10))
        momentum = max(0.01, min(0.99, 0.5 + s.momentum*14))
        anomaly = max(0.01, min(0.99, abs(s.momentum)*25 + max(0,s.volatility-0.25)))
        opportunity = max(0.0, min(1.0, 0.50*direction + 0.25*momentum + 0.25*(1-s.volatility)))
        return {
            "regime_model": s.regime,
            "direction_model": round(direction,3),
            "volatility_model": round(s.volatility,3),
            "momentum_model": round(momentum,3),
            "anomaly_model": round(anomaly,3),
            "opportunity_score": round(opportunity,3),
            "uncertainty": round(1-opportunity,3),
            "agreement": round(0.55 + 0.45*(1-abs(direction-momentum)),3),
            "evidence": ["EMA structure", "price momentum", "realized simulation volatility"],
        }

class RiskGovernor:
    def __init__(self):
        self.max_positions=5
        self.max_drawdown=0.20
    def evaluate(self, balance: float, starting: float, positions: int) -> dict:
        dd=max(0.0,(starting-balance)/starting)
        state="EMERGENCY STOP" if dd>=self.max_drawdown else "WARNING" if dd>=0.10 or positions>=4 else "NORMAL"
        return {"state":state,"drawdown":round(dd,4),"open_positions":positions,"max_open_positions":self.max_positions}

class VirtualAccount:
    def __init__(self, balance=10000.0):
        self.starting_balance=balance; self.balance=balance; self.positions=[]; self.history=[]; self.memory=[]
    def open(self, price, side="LONG", quantity=1.0):
        p={"id":f"SIM-{len(self.history)+len(self.positions)+1}","symbol":"DEMO/USD","side":side,"quantity":quantity,"entry":price,"mark":price,"pnl":0.0}
        self.positions.append(p); return p
    def mark(self, price):
        for p in self.positions:
            p["mark"]=price; direction=1 if p["side"]=="LONG" else -1
            p["pnl"]=round((price-p["entry"])*p["quantity"]*direction,4)
    def close(self, pid):
        p=next((x for x in self.positions if x["id"]==pid),None)
        if not p: return None
        self.positions.remove(p); self.balance=round(self.balance+p["pnl"],4)
        self.history.append(p.copy()); self.memory.append({"event":"simulation_outcome","position_id":pid,"pnl":p["pnl"],"lesson":"Outcome retained for evaluation and future research."})
        return p
