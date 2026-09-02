from __future__ import annotations

import math, os, random, statistics, time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="EchoMatrix", version="1.0.0")

# ---- Core state: deterministic engines + simulation ----
prices = deque(maxlen=500)
for i in range(120):
    prices.append(100 + i * 0.03 + math.sin(i / 7) * 1.2)

state: dict[str, Any] = {
    "regime": "TRENDING / NORMAL VOLATILITY",
    "regime_score": 0.74,
    "world_model_version": 1,
    "sim_balance": 10000.0,
    "sim_equity": 10000.0,
    "positions": [],
    "history": [],
    "memory": [],
    "research": [],
    "strategies": [
        {"id": "STRAT-001", "name": "Regime Momentum", "status": "Validated", "score": 78},
        {"id": "STRAT-002", "name": "Volatility Compression", "status": "Experimental", "score": 71},
        {"id": "STRAT-003", "name": "Structure Reversion", "status": "Candidate", "score": 69},
    ],
    "risk": {"state": "NORMAL", "daily_loss": 0.0, "drawdown": 0.0, "open_positions": 0},
}

class SimulationRequest(BaseModel):
    symbol: str = "DEMO/USD"
    side: str = "LONG"
    quantity: float = 1.0


def indicators() -> dict[str, float]:
    p = list(prices)
    ret = [(p[i] / p[i-1] - 1) for i in range(1, len(p))]
    fast = statistics.mean(p[-10:])
    slow = statistics.mean(p[-30:])
    vol = statistics.pstdev(ret[-30:]) * math.sqrt(252) if len(ret) >= 30 else 0.0
    momentum = (p[-1] / p[-20] - 1) if len(p) >= 20 else 0.0
    return {"price": p[-1], "ema_fast": fast, "ema_slow": slow, "momentum": momentum, "volatility": vol}


def model_council(ind: dict[str, float]) -> dict[str, Any]:
    trend = 0.5 + max(-0.49, min(0.49, ind["momentum"] * 8))
    vol = ind["volatility"]
    regime = "BULLISH TREND" if trend > 0.58 else "BEARISH TREND" if trend < 0.42 else "RANGE / TRANSITION"
    return {
        "regime_model": round(trend, 3),
        "direction_model": round(trend, 3),
        "volatility_model": round(min(0.99, vol * 8), 3),
        "momentum_model": round(max(0.01, min(0.99, 0.5 + ind["momentum"] * 10)), 3),
        "anomaly_model": round(random.uniform(0.03, 0.18), 3),
        "opportunity_score": round(0.55 * trend + 0.45 * (1 - min(1, vol * 4)), 3),
        "regime": regime,
    }


def risk_check() -> dict[str, Any]:
    r = state["risk"]
    if r["drawdown"] >= 0.20 or r["daily_loss"] >= 0.05:
        r["state"] = "EMERGENCY STOP"
    elif r["drawdown"] >= 0.10 or r["open_positions"] >= 4:
        r["state"] = "WARNING"
    else:
        r["state"] = "NORMAL"
    return r

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "services": {"api": "online", "world_model": "online", "simulation": "online", "risk": "online", "memory": "online", "ai_gateway": "configured"}}

@app.get("/api/world")
def world():
    ind = indicators(); models = model_council(ind)
    state["regime"] = models["regime"]
    state["world_model_version"] += 1
    return {"version": state["world_model_version"], "instrument": "DEMO/USD", "indicators": ind, "models": models, "uncertainty": round(1 - models["opportunity_score"], 3), "provenance": "deterministic demo market generator"}

@app.get("/api/dashboard")
def dashboard():
    world_state = world()
    risk = risk_check()
    return {"world": world_state, "balance": state["sim_balance"], "equity": state["sim_equity"], "positions": state["positions"], "history": state["history"][-10:], "strategies": state["strategies"], "risk": risk, "memory": state["memory"][-5:], "research": state["research"][-5:], "providers": {"gemini": bool(os.getenv("GEMINI_API_KEY")), "groq": bool(os.getenv("GROQ_API_KEY"))}}

@app.post("/api/simulator/open")
def open_sim(req: SimulationRequest):
    risk = risk_check()
    if risk["state"] in {"PAUSED", "EMERGENCY STOP"}:
        return {"accepted": False, "reason": "Risk Governor blocked the simulation event", "risk": risk}
    if len(state["positions"]) >= 5:
        return {"accepted": False, "reason": "Maximum simulated open positions reached", "risk": risk}
    px = indicators()["price"]
    pos = {"id": f"SIM-{int(time.time()*1000)}", "symbol": req.symbol, "side": req.side.upper(), "quantity": req.quantity, "entry": round(px, 5), "mark": round(px, 5), "pnl": 0.0, "opened_at": datetime.now(timezone.utc).isoformat()}
    state["positions"].append(pos); state["risk"]["open_positions"] = len(state["positions"])
    return {"accepted": True, "position": pos, "risk": risk_check()}

@app.post("/api/simulator/step")
def sim_step():
    last = prices[-1]
    new = last + random.gauss(0.04, 0.55)
    prices.append(new)
    total_pnl = 0.0
    for p in state["positions"]:
        p["mark"] = round(new, 5)
        direction = 1 if p["side"] == "LONG" else -1
        p["pnl"] = round((new - p["entry"]) * p["quantity"] * direction, 4)
        total_pnl += p["pnl"]
    state["sim_equity"] = round(state["sim_balance"] + total_pnl, 4)
    peak = max(10000.0, state["sim_equity"])
    state["risk"]["drawdown"] = max(0.0, round((peak - state["sim_equity"]) / peak, 4))
    return dashboard()

@app.post("/api/simulator/close/{position_id}")
def close_sim(position_id: str):
    pos = next((x for x in state["positions"] if x["id"] == position_id), None)
    if not pos: return {"accepted": False, "reason": "Position not found"}
    state["positions"].remove(pos); state["history"].append({**pos, "closed_at": datetime.now(timezone.utc).isoformat()})
    state["sim_balance"] = round(state["sim_balance"] + pos["pnl"], 4)
    state["sim_equity"] = state["sim_balance"]
    state["memory"].append({"type": "episodic", "event": "simulation_outcome", "lesson": "Outcome recorded for future validation", "pnl": pos["pnl"], "timestamp": datetime.now(timezone.utc).isoformat()})
    state["risk"]["open_positions"] = len(state["positions"])
    return {"accepted": True, "closed": pos, "risk": risk_check()}

@app.get("/api/strategies")
def strategies(): return state["strategies"]
@app.get("/api/memory")
def memory(): return state["memory"]
@app.get("/api/research")
def research(): return state["research"]
@app.get("/api/risk")
def risk(): return risk_check()

HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EchoMatrix</title><style>body{margin:0;background:#071018;color:#eaf2f8;font:14px system-ui}header{padding:22px 28px;border-bottom:1px solid #1b2a35;display:flex;justify-content:space-between}.brand{font-size:24px;font-weight:800}.wrap{padding:22px;max-width:1400px;margin:auto}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{background:#0c1720;border:1px solid #1d303d;border-radius:14px;padding:16px}.wide{grid-column:span 2}.big{font-size:28px;font-weight:800;margin-top:7px}.muted{color:#8499a8}.pill{display:inline-block;padding:5px 9px;border-radius:99px;background:#122733}.row{display:flex;justify-content:space-between;gap:12px;margin:8px 0}.btn{border:1px solid #315568;background:#10232e;color:#eaf2f8;padding:9px 12px;border-radius:9px;cursor:pointer}.log{max-height:180px;overflow:auto;font-size:12px}pre{white-space:pre-wrap}.ok{color:#7ee787}@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}.wide{grid-column:span 2}}@media(max-width:560px){.grid{grid-template-columns:1fr}.wide{grid-column:span 1}}</style></head><body><header><div><div class="brand">◈ EchoMatrix</div><div class="muted">AI-native market intelligence · simulation · research</div></div><div class="pill"><span class="ok">●</span> SYSTEM ONLINE</div></header><main class="wrap"><div class="grid"><section class="card"><div class="muted">MARKET REGIME</div><div id="regime" class="big">—</div><div id="score" class="muted">—</div></section><section class="card"><div class="muted">SIMULATOR EQUITY</div><div id="equity" class="big">—</div><div id="balance" class="muted">—</div></section><section class="card"><div class="muted">RISK GOVERNOR</div><div id="risk" class="big">—</div><div id="riskmeta" class="muted">—</div></section><section class="card"><div class="muted">AI GATEWAY</div><div class="row"><span>Gemini</span><b id="gemini">—</b></div><div class="row"><span>Groq</span><b id="groq">—</b></div></section><section class="card wide"><h3>World Model</h3><div id="world"></div></section><section class="card wide"><h3>Model Council · Evidence Fusion</h3><div id="models"></div></section><section class="card"><h3>Simulator</h3><button class="btn" onclick="openSim()">Open virtual position</button> <button class="btn" onclick="step()">Market step</button><div id="positions" class="log"></div></section><section class="card"><h3>Strategy Brain</h3><div id="strategies" class="log"></div></section><section class="card"><h3>Memory</h3><div id="memory" class="log"></div></section><section class="card"><h3>Research</h3><div class="muted">Research → evidence → hypothesis → experiment → validation → memory</div><div id="research" class="log"></div></section></div></main><script>async function j(u,o){let r=await fetch(u,o);return r.json()}function esc(x){return String(x).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}async function refresh(){let d=await j('/api/dashboard'),w=d.world,m=w.models;regime.textContent=esc(m.regime);score.textContent='Opportunity '+m.opportunity_score+' · uncertainty '+w.uncertainty;equity.textContent='$'+d.equity.toFixed(2);balance.textContent='Balance $'+d.balance.toFixed(2);risk.textContent=d.risk.state;riskmeta.textContent='Open '+d.risk.open_positions+' · DD '+(d.risk.drawdown*100).toFixed(2)+'%';gemini.textContent=d.providers.gemini?'READY':'CONFIGURE';groq.textContent=d.providers.groq?'READY':'CONFIGURE';world.innerHTML='<div class="row"><span>Price</span><b>'+w.indicators.price.toFixed(4)+'</b></div><div class="row"><span>EMA fast / slow</span><b>'+w.indicators.ema_fast.toFixed(3)+' / '+w.indicators.ema_slow.toFixed(3)+'</b></div><div class="row"><span>Momentum</span><b>'+w.indicators.momentum.toFixed(4)+'</b></div><div class="row"><span>Volatility</span><b>'+w.indicators.volatility.toFixed(4)+'</b></div>';models.innerHTML=Object.entries(m).filter(([k])=>k.endsWith('_model')||k==='opportunity_score').map(([k,v])=>'<div class="row"><span>'+k+'</span><b>'+v+'</b></div>').join('');positions.innerHTML=d.positions.length?d.positions.map(p=>'<div class="row"><span>'+p.symbol+' '+p.side+' · '+p.quantity+'</span><b>'+p.pnl.toFixed(2)+' <button class="btn" onclick="closeP(\''+p.id+'\')">Close</button></b></div>').join(''):'No open virtual positions';strategies.innerHTML=d.strategies.map(s=>'<div class="row"><span>'+esc(s.name)+'</span><b>'+s.status+' · '+s.score+'</b></div>').join('');memory.innerHTML=d.memory.map(x=>'<div>'+esc(x.lesson)+' · '+x.pnl+'</div>').join('')||'No recorded episodes yet';research.innerHTML=d.research.map(x=>'<div>'+esc(x.topic)+'</div>').join('')||'No research findings yet'}async function openSim(){await j('/api/simulator/open',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});refresh()}async function step(){await j('/api/simulator/step',{method:'POST'});refresh()}async function closeP(id){await j('/api/simulator/close/'+id,{method:'POST'});refresh()}refresh();setInterval(refresh,3000)</script></body></html>'''

@app.get("/", response_class=HTMLResponse)
def home(): return HTML
'''
