# EchoMatrix

EchoMatrix is a FastAPI market-intelligence application with transparent baseline
models, a separate virtual-account simulator, strategy lifecycle controls, and a
guarded integration to the Deriv WebSocket API.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`. The default dashboard is simulation-only and no
broker request can be made without configuration.

## Deriv execution

Execution uses the Deriv API flow: authorize account, request a fresh proposal,
buy against that proposal, and sell using the broker-issued contract ID. The
Deriv account is the source of truth for broker positions and outcomes.

Set these server-side environment variables **only after rotating any credential
that may have been exposed**:

```bash
export DERIV_API_TOKEN='your Deriv token with Read, Trade, and Trading Information permissions'
export DERIV_APP_ID='your Deriv application id'          # defaults to 1089
export DERIV_CURRENCY='USD'                              # optional
export ECHOMATRIX_ENABLE_LIVE_EXECUTION='true'
```

`DERIV_API_TOKEN` is never returned from an API response or logged by the
application. The execution routes remain locked until both the token and the
explicit enablement flag are present. Before submitting an order, call
`GET /api/execution/status` and confirm the returned Deriv authorization details
match the intended demo or real account.

### Primary endpoints

* `GET /api/dashboard` — unified world model, simulation, risk, and execution state.
* `POST /api/simulator/open`, `/step`, `/close/{id}` — internal paper trading only.
* `GET /api/execution/status` — authorize and inspect the configured Deriv account.
* `POST /api/execution/quote` — obtain a fresh live Deriv proposal.
* `POST /api/execution/buy` — obtain a fresh proposal and submit a broker order.
* `POST /api/execution/sell` — request sale of a broker contract.

## Security boundary

Keep `DERIV_API_TOKEN`, `GEMINI_API_KEY`, and `GROQ_API_KEY` in deployment secret
storage or environment variables. Do not commit them, place them in browser
source, or put them in ordinary logs.
