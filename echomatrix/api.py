from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .core import WorldModel, ModelCouncil, RiskGovernor, VirtualAccount

app=FastAPI(title="EchoMatrix Core",version="0.2.0")
world=WorldModel(); council=ModelCouncil(); risk=RiskGovernor(); account=VirtualAccount()
strategies=[{"id":"STRAT-001","name":"Regime Momentum","status":"Validated","score":78},{"id":"STRAT-002","name":"Volatility Compression","status":"Experimental","score":71},{"id":"STRAT-003","name":"Structure Reversion","status":"Candidate","score":69}]

class Order(BaseModel):
    side: str = Field(default="LONG", pattern="^(LONG|SHORT)$")
    quantity: float = Field(default=1.0, gt=0, le=100)

@app.get("/api/health")
def health():
    return {"status":"ok","services":{"api":"online","world_model":"online","model_council":"online","risk_governor":"online","simulation":"online","memory":"online","data":"simulation-feed"}}

@app.get("/api/dashboard")
def dashboard():
    s=world.state; models=council.evaluate(s); r=risk.evaluate(account.balance,account.starting_balance,len(account.positions))
    return {"world":{**s.__dict__,"models":models,"provenance":"deterministic simulation market generator"},"balance":round(account.balance,2),"equity":round(account.balance+sum(p['pnl'] for p in account.positions),2),"positions":account.positions,"history":account.history[-20:],"memory":account.memory[-20:],"strategies":strategies,"risk":r,"providers":{"gemini":bool(__import__('os').getenv('GEMINI_API_KEY')),"groq":bool(__import__('os').getenv('GROQ_API_KEY'))}}

@app.post("/api/simulator/open")
def open_position(order:Order):
    r=risk.evaluate(account.balance,account.starting_balance,len(account.positions))
    if len(account.positions)>=risk.max_positions or r["state"]=="EMERGENCY STOP":
        return {"accepted":False,"reason":"Risk Governor blocked simulation event"}
    return {"accepted":True,"position":account.open(world.state.price,order.side,order.quantity)}

@app.post("/api/simulator/step")
def market_step():
    world.step(); account.mark(world.state.price); return dashboard()

@app.post("/api/simulator/close/{position_id}")
def close_position(position_id:str):
    p=account.close(position_id)
    if not p: raise HTTPException(404,"Position not found")
    return {"accepted":True,"closed":p}

@app.get("/api/strategies")
def get_strategies(): return strategies
@app.get("/api/memory")
def get_memory(): return account.memory
@app.get("/api/risk")
def get_risk(): return risk.evaluate(account.balance,account.starting_balance,len(account.positions))
