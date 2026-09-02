from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime, timezone
import math, random, os

app=FastAPI(title='EchoMatrix',version='1.0.0')
price=100.0
balance=10000.0
positions=[]
history=[]
memory=[]
strategies=[{'id':'STRAT-001','name':'Regime Momentum','status':'Validated','score':78},{'id':'STRAT-002','name':'Volatility Compression','status':'Experimental','score':71},{'id':'STRAT-003','name':'Structure Reversion','status':'Candidate','score':69}]

class Order(BaseModel):
    symbol:str='DEMO/USD'; side:str='LONG'; quantity:float=1.0

def world():
    global price
    momentum=random.uniform(-.02,.025); fast=price*(1+momentum*.4); slow=price*(1-momentum*.2)
    direction=max(.01,min(.99,.5+momentum*12)); vol=random.uniform(.08,.32)
    regime='BULLISH TREND' if direction>.58 else 'BEARISH TREND' if direction<.42 else 'RANGE / TRANSITION'
    return {'version':int(datetime.now().timestamp()),'instrument':'DEMO/USD','price':round(price,5),'ema_fast':round(fast,5),'ema_slow':round(slow,5),'momentum':round(momentum,5),'volatility':round(vol,4),'regime':regime,'models':{'regime_model':round(direction,3),'direction_model':round(direction,3),'volatility_model':round(vol,3),'momentum_model':round(max(.01,min(.99,.5+momentum*10)),3),'anomaly_model':round(random.uniform(.03,.18),3),'opportunity_score':round(.55*direction+.45*(1-vol),3)},'uncertainty':round(1-(.55*direction+.45*(1-vol)),3),'provenance':'deterministic simulation market generator'}

def risk():
    dd=max(0,(10000-balance)/10000); n=len(positions)
    status='EMERGENCY STOP' if dd>=.2 else 'WARNING' if dd>=.1 or n>=4 else 'NORMAL'
    return {'state':status,'daily_loss':round(dd,4),'drawdown':round(dd,4),'open_positions':n,'max_open_positions':5}

@app.get('/api/health')
def health(): return {'status':'ok','services':{'api':'online','world_model':'online','ai_engine':'ready','strategy_brain':'online','simulation':'online','risk_governor':'online','memory':'online','research':'ready','data':'simulation-feed'}}
@app.get('/api/dashboard')
def dashboard():
    w=world(); pnl=sum(p['pnl'] for p in positions)
    return {'world':w,'balance':round(balance,2),'equity':round(balance+pnl,2),'positions':positions,'history':history[-10:],'strategies':strategies,'risk':risk(),'memory':memory[-5:],'research':[],'providers':{'gemini':bool(os.getenv('GEMINI_API_KEY')),'groq':bool(os.getenv('GROQ_API_KEY'))}}
@app.post('/api/simulator/open')
def open_sim(o:Order):
    if len(positions)>=5 or risk()['state']=='EMERGENCY STOP': return {'accepted':False,'reason':'Risk Governor blocked simulation event'}
    positions.append({'id':f'SIM-{len(history)+len(positions)+1}','symbol':o.symbol,'side':o.side.upper(),'quantity':o.quantity,'entry':price,'mark':price,'pnl':0.0,'opened_at':datetime.now(timezone.utc).isoformat()})
    return {'accepted':True,'position':positions[-1]}
@app.post('/api/simulator/step')
def step():
    global price
    price=round(price+random.gauss(.05,.45),5)
    for p in positions:
        p['mark']=price; p['pnl']=round((price-p['entry'])*p['quantity']*(1 if p['side']=='LONG' else -1),4)
    return dashboard()
@app.post('/api/simulator/close/{pid}')
def close(pid:str):
    global balance
    p=next((x for x in positions if x['id']==pid),None)
    if not p:return {'accepted':False,'reason':'Position not found'}
    positions.remove(p); balance=round(balance+p['pnl'],4); history.append({**p,'closed_at':datetime.now(timezone.utc).isoformat()}); memory.append({'event':'simulation_outcome','lesson':'Outcome recorded for validation','pnl':p['pnl']})
    return {'accepted':True,'closed':p}
@app.get('/api/strategies')
def get_strategies():return strategies
@app.get('/api/memory')
def get_memory():return memory
@app.get('/api/risk')
def get_risk():return risk()

HTML='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>EchoMatrix</title><style>body{margin:0;background:#071018;color:#eaf2f8;font:14px system-ui}header{padding:22px;border-bottom:1px solid #20303b}.wrap{max-width:1300px;margin:auto;padding:20px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{background:#0d1821;border:1px solid #213541;border-radius:14px;padding:16px}.wide{grid-column:span 2}.big{font-size:27px;font-weight:800;margin:7px 0}.muted{color:#8ca0ad}.row{display:flex;justify-content:space-between;margin:8px 0}.btn{padding:9px;border:1px solid #315568;background:#10232e;color:white;border-radius:8px}.log{max-height:180px;overflow:auto}@media(max-width:800px){.grid{grid-template-columns:1fr 1fr}.wide{grid-column:span 2}}@media(max-width:520px){.grid{grid-template-columns:1fr}.wide{grid-column:span 1}}</style></head><body><header><b style="font-size:24px">◈ EchoMatrix</b><div class="muted">AI-native market intelligence · strategy research · simulation</div></header><main class="wrap"><div class="grid"><div class="card"><div class="muted">MARKET REGIME</div><div id="regime" class="big">—</div><div id="opp" class="muted">—</div></div><div class="card"><div class="muted">SIMULATOR EQUITY</div><div id="eq" class="big">—</div><div id="bal" class="muted">—</div></div><div class="card"><div class="muted">RISK GOVERNOR</div><div id="risk" class="big">—</div><div id="rm" class="muted">—</div></div><div class="card"><div class="muted">AI PROVIDERS</div><div class="row">Gemini <b id="gem">—</b></div><div class="row">Groq <b id="groq">—</b></div></div><div class="card wide"><h3>World Model</h3><div id="world"></div></div><div class="card wide"><h3>Model Council · Evidence Fusion</h3><div id="models"></div></div><div class="card"><h3>Simulator</h3><button class="btn" onclick="openP()">Open virtual position</button> <button class="btn" onclick="step()">Market step</button><div id="pos" class="log"></div></div><div class="card"><h3>Strategy Brain</h3><div id="strat" class="log"></div></div><div class="card"><h3>Memory</h3><div id="mem" class="log"></div></div><div class="card"><h3>System Pipeline</h3><div class="muted">Data → World Model → Model Council → Evidence Fusion → Strategy Brain → Risk Governor → Simulation → Outcome → Memory</div></div></div></main><script>const q=s=>document.querySelector(s);async function api(u,o){return (await fetch(u,o)).json()}async function refresh(){let d=await api('/api/dashboard'),w=d.world; q('#regime').textContent=w.regime;q('#opp').textContent='Opportunity '+w.models.opportunity_score+' · uncertainty '+w.uncertainty;q('#eq').textContent='$'+d.equity.toFixed(2);q('#bal').textContent='Balance $'+d.balance.toFixed(2);q('#risk').textContent=d.risk.state;q('#rm').textContent='Open '+d.risk.open_positions+' / '+d.risk.max_open_positions;q('#gem').textContent=d.providers.gemini?'READY':'CONFIGURE';q('#groq').textContent=d.providers.groq?'READY':'CONFIGURE';q('#world').innerHTML=['price','ema_fast','ema_slow','momentum','volatility'].map(k=>'<div class="row"><span>'+k+'</span><b>'+w[k]+'</b></div>').join('');q('#models').innerHTML=Object.entries(w.models).map(x=>'<div class="row"><span>'+x[0]+'</span><b>'+x[1]+'</b></div>').join('');q('#pos').innerHTML=d.positions.length?d.positions.map(p=>'<div class="row"><span>'+p.symbol+' '+p.side+'</span><b>'+p.pnl.toFixed(2)+' <button class="btn" onclick="closeP(\''+p.id+'\')">Close</button></b></div>').join(''):'No open virtual positions';q('#strat').innerHTML=d.strategies.map(s=>'<div class="row"><span>'+s.name+'</span><b>'+s.status+' · '+s.score+'</b></div>').join('');q('#mem').innerHTML=d.memory.length?d.memory.map(m=>'<div>'+m.lesson+' · '+m.pnl+'</div>').join(''):'No recorded outcomes yet'}async function openP(){await api('/api/simulator/open',{method:'POST',headers:{'content-type':'application/json'},body:'{}'});refresh()}async function step(){await api('/api/simulator/step',{method:'POST'});refresh()}async function closeP(id){await api('/api/simulator/close/'+id,{method:'POST'});refresh()}refresh();setInterval(refresh,3000)</script></body></html>'''
@app.get('/',response_class=HTMLResponse)
def home():return HTML
