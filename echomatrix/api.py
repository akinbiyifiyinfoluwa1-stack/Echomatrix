"""HTTP API for EchoMatrix.  Simulation and broker execution have distinct routes."""
from __future__ import annotations

import os
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .core import DerivClient, ModelCouncil, RiskGovernor, StrategyRegistry, StrategyStage, VirtualAccount, WorldModel, state_dict

app = FastAPI(title="EchoMatrix", version="2.0.0")
world, council, risk, account = WorldModel(), ModelCouncil(), RiskGovernor(), VirtualAccount()
strategies, deriv = StrategyRegistry(), DerivClient()

class SimulationOrder(BaseModel):
    side: Literal["LONG", "SHORT"] = "LONG"
    quantity: float = Field(1, gt=0, le=100)

class LiveOrder(BaseModel):
    symbol: str = Field("R_100", min_length=1, max_length=32)
    contract_type: Literal["CALL", "PUT"]
    stake: float = Field(..., gt=0, le=10_000)
    duration: int = Field(..., ge=1, le=365)
    duration_unit: Literal["t", "s", "m", "h", "d"] = "m"

class CloseLiveOrder(BaseModel):
    contract_id: int = Field(..., gt=0)
    price: float = Field(0, ge=0)

class StrategyTransition(BaseModel):
    stage: StrategyStage
    metrics: dict[str, float] = {}

def dashboard() -> dict:
    s = world.state; models = council.evaluate(s); governor = risk.evaluate(account.balance, account.starting_balance, len(account.positions))
    equity = account.balance + sum(p["pnl"] for p in account.positions)
    return {"world": {**state_dict(s), "models": models, "provenance": {"source": s.source, "data_version": s.data_version, "confidence": s.confidence}, "data_issues": list(world.data_issues)}, "balance": round(account.balance, 2), "equity": round(equity, 2), "positions": account.positions, "history": account.history[-20:], "memory": account.memory[-20:], "strategies": strategies.list(), "risk": governor, "providers": {"gemini": bool(os.getenv("GEMINI_API_KEY")), "groq": bool(os.getenv("GROQ_API_KEY"))}, "execution": {"configured": deriv.configured, "enabled": deriv.enabled, "mode": "LIVE" if deriv.enabled else "LOCKED"}}

@app.get("/api/health")
def health():
    return {"status": "ok", "services": {"api": "online", "world_model": "online", "model_council": "online", "risk_governor": "online", "simulation": "online", "memory": "online", "deriv_execution": "enabled" if deriv.enabled else "locked"}}

@app.get("/api/dashboard")
def get_dashboard(): return dashboard()

@app.post("/api/simulator/open")
def open_simulation(order: SimulationOrder):
    governor = risk.evaluate(account.balance, account.starting_balance, len(account.positions))
    if governor["state"] == "EMERGENCY STOP" or len(account.positions) >= risk.max_positions:
        return {"accepted": False, "reason": "Risk Governor blocked simulation event", "risk": governor}
    return {"accepted": True, "position": account.open(world.state.price, order.side, order.quantity)}

@app.post("/api/simulator/step")
def simulation_step():
    world.step(); account.mark(world.state.price); return dashboard()

@app.post("/api/simulator/close/{position_id}")
def close_simulation(position_id: str):
    closed = account.close(position_id)
    if not closed: raise HTTPException(404, "Simulation position not found")
    return {"accepted": True, "closed": closed}

@app.get("/api/strategies")
def get_strategies(): return strategies.list()

@app.post("/api/strategies/{strategy_id}/transition")
def transition_strategy(strategy_id: str, request: StrategyTransition):
    try: return strategies.transition(strategy_id, request.stage, request.metrics)
    except KeyError: raise HTTPException(404, "Strategy not found")
    except ValueError as exc: raise HTTPException(409, str(exc))

@app.get("/api/memory")
def get_memory(): return account.memory

@app.get("/api/risk")
def get_risk(): return risk.evaluate(account.balance, account.starting_balance, len(account.positions))

@app.get("/api/execution/status")
def execution_status():
    try: return deriv.status()
    except RuntimeError as exc: raise HTTPException(502, str(exc))

@app.post("/api/execution/quote")
def live_quote(order: LiveOrder):
    try: return deriv.proposal(order.symbol, order.contract_type, order.stake, order.duration, order.duration_unit)
    except PermissionError as exc: raise HTTPException(423, str(exc))
    except RuntimeError as exc: raise HTTPException(502, str(exc))

@app.post("/api/execution/buy")
def live_buy(order: LiveOrder):
    """Request a fresh Deriv proposal and immediately buy it; never use cached quotes."""
    try:
        quote = deriv.proposal(order.symbol, order.contract_type, order.stake, order.duration, order.duration_unit)
        proposal = quote["proposal"]
        result = deriv.buy(proposal["id"], proposal["ask_price"])
        buy = result.get("buy", {})
        account.memory.append({"event": "live_order_executed", "contract_id": buy.get("contract_id"), "transaction_id": buy.get("transaction_id"), "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "lesson": "Deriv is the source of truth for this broker order."})
        return {"accepted": True, "quote": {"id": proposal["id"], "ask_price": proposal["ask_price"]}, "execution": result}
    except PermissionError as exc: raise HTTPException(423, str(exc))
    except (RuntimeError, KeyError) as exc: raise HTTPException(502, str(exc))

@app.post("/api/execution/sell")
def live_sell(order: CloseLiveOrder):
    try: return {"accepted": True, "execution": deriv.sell(order.contract_id, order.price)}
    except PermissionError as exc: raise HTTPException(423, str(exc))
    except RuntimeError as exc: raise HTTPException(502, str(exc))
