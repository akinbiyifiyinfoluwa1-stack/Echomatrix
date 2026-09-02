from fastapi.responses import HTMLResponse
from echomatrix.api import app

HTML = '''<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-store">
<title>EchoMatrix Core</title>
<style>
body{margin:0;background:#071018;color:#eaf2f8;font:14px system-ui,sans-serif}
header{padding:22px;border-bottom:1px solid #20303b}.wrap{max-width:1300px;margin:auto;padding:20px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{background:#0d1821;border:1px solid #213541;border-radius:14px;padding:16px}
.wide{grid-column:span 2}.big{font-size:25px;font-weight:800;margin:7px 0}.muted{color:#8ca0ad}
.row{display:flex;justify-content:space-between;gap:12px;margin:8px 0}.btn{padding:10px 12px;border:1px solid #315568;background:#10232e;color:white;border-radius:8px;cursor:pointer}
.btn:active{transform:scale(.98)}.btn:disabled{opacity:.55}.log{max-height:190px;overflow:auto}.live{font-size:12px;margin-top:6px}.err{font-size:12px;min-height:18px;margin-top:8px}
@media(max-width:800px){.grid{grid-template-columns:1fr 1fr}.wide{grid-column:span 2}}
@media(max-width:520px){.grid{grid-template-columns:1fr}.wide{grid-column:span 1}}
</style>
</head>
<body>
<header>
<b style="font-size:24px">◈ EchoMatrix Core</b>
<div class="muted">AI-native market intelligence · strategy research · simulation</div>
<div class="live">● LIVE SIMULATION · <span id="tick">connecting…</span></div>
</header>
<main class="wrap"><div class="grid">
<div class="card"><div class="muted">MARKET REGIME</div><div id="regime" class="big">—</div><div id="opp" class="muted">—</div></div>
<div class="card"><div class="muted">SIMULATOR EQUITY</div><div id="eq" class="big">—</div><div id="bal" class="muted">—</div></div>
<div class="card"><div class="muted">RISK GOVERNOR</div><div id="risk" class="big">—</div><div id="rm" class="muted">—</div></div>
<div class="card"><div class="muted">AI / DATA STATUS</div><div class="row">Gemini <b id="gem">—</b></div><div class="row">Groq <b id="groq">—</b></div><div class="row">Feed <b>SIMULATED</b></div></div>
<div class="card wide"><h3>World Model</h3><div id="world"></div></div>
<div class="card wide"><h3>Model Council · Evidence Fusion</h3><div id="models"></div></div>
<div class="card"><h3>Simulator</h3>
<button id="openBtn" class="btn" type="button">Open virtual position</button>
<button id="stepBtn" class="btn" type="button">Step now</button>
<div id="pos" class="log"></div><div id="err" class="err muted"></div></div>
<div class="card"><h3>Strategy Brain</h3><div id="strat" class="log"></div></div>
<div class="card"><h3>Memory</h3><div id="mem" class="log"></div></div>
<div class="card"><h3>System Pipeline</h3><div class="muted">Market Data → World Model → Model Council → Evidence Fusion → Strategy Brain → Risk Governor → Simulation → Outcome → Memory</div><hr><div class="muted">Every automatic tick is simulation-only. No broker orders are enabled.</div></div>
</div></main>
<script>
(function(){
'use strict';
const q=s=>document.querySelector(s);
const esc=x=>String(x).replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
async function api(url,options){
  const r=await fetch(url,options||{}, {cache:'no-store'});
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}
function setBusy(v){q('#openBtn').disabled=v;q('#stepBtn').disabled=v;}
async function refresh(){
  try{
    const d=await api('/api/dashboard?_='+Date.now()); const w=d.world;
    q('#regime').textContent=w.regime;
    q('#opp').textContent='Opportunity '+w.models.opportunity_score+' · uncertainty '+w.models.uncertainty;
    q('#eq').textContent='VU '+Number(d.equity).toFixed(2);
    q('#bal').textContent='Balance VU '+Number(d.balance).toFixed(2);
    q('#risk').textContent=d.risk.state;
    q('#rm').textContent='Open '+d.risk.open_positions+' / '+d.risk.max_open_positions;
    q('#gem').textContent=d.providers.gemini?'READY':'CONFIGURE';
    q('#groq').textContent=d.providers.groq?'READY':'CONFIGURE';
    q('#world').innerHTML=['instrument','price','ema_fast','ema_slow','momentum','volatility','timestamp'].map(k=>'<div class="row"><span>'+esc(k)+'</span><b>'+esc(w[k])+'</b></div>').join('');
    q('#models').innerHTML=Object.entries(w.models).map(x=>'<div class="row"><span>'+esc(x[0])+'</span><b>'+esc(x[1])+'</b></div>').join('');
    q('#pos').innerHTML=d.positions.length?d.positions.map(p=>'<div class="row"><span>'+esc(p.symbol)+' '+esc(p.side)+' @ '+esc(p.entry)+'</span><b>'+Number(p.pnl).toFixed(3)+' <button class="btn closeBtn" data-id="'+esc(p.id)+'" type="button">Close</button></b></div>').join(''):'No open virtual positions';
    q('#strat').innerHTML=d.strategies.map(s=>'<div class="row"><span>'+esc(s.name)+'</span><b>'+esc(s.status)+' · '+esc(s.score)+'</b></div>').join('');
    q('#mem').innerHTML=d.memory.length?d.memory.map(m=>'<div>'+esc(m.lesson)+' · P&L '+esc(m.pnl)+'</div>').join(''):'No recorded outcomes yet';
    q('#err').textContent=''; q('#tick').textContent='active · '+new Date().toLocaleTimeString();
    document.querySelectorAll('.closeBtn').forEach(b=>b.addEventListener('click',()=>closeP(b.dataset.id)));
  }catch(e){q('#err').textContent='API error: '+e.message;}
}
async function openP(){
  setBusy(true); try{await api('/api/simulator/open',{method:'POST',headers:{'content-type':'application/json'},body:'{}'});await refresh();}catch(e){q('#err').textContent=e.message;}finally{setBusy(false);}
}
async function step(){
  setBusy(true); try{await api('/api/simulator/step',{method:'POST'});await refresh();}catch(e){q('#err').textContent=e.message;}finally{setBusy(false);}
}
async function closeP(id){
  try{await api('/api/simulator/close/'+encodeURIComponent(id),{method:'POST'});await refresh();}catch(e){q('#err').textContent=e.message;}
}
q('#openBtn').addEventListener('click',openP);
q('#stepBtn').addEventListener('click',step);
refresh();
setInterval(step,2000);
})();
</script>
</body></html>'''

@app.get('/', response_class=HTMLResponse)
def home():
    return HTML
