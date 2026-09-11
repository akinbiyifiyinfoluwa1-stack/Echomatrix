# EchoMatrix

Production-oriented AI market intelligence system. EchoMatrix is being built **brain first, body later**: the intelligence layer must be able to observe, reason, quantify uncertainty, remember outcomes, and evaluate strategies before broker/execution adapters become the focus.

## Current build

- `echomatrix/brain.py` — broker-agnostic decision brain, evidence fusion, confidence/uncertainty, and adaptive outcome memory.
- `echomatrix/core.py` — market state, validation, model council, risk governor, virtual account, strategy lifecycle, and guarded Deriv boundary.
- `echomatrix/api.py` — FastAPI surface for intelligence cycles, brain status/learning, simulation, strategy lifecycle, risk, and execution boundary.
- `main.py` — lightweight dashboard UI.
- `tests/test_brain.py` — decision-brain regression tests.

## Brain loop

`Market State → Feature Engine → Evidence Fusion → Decision → Simulation Outcome → Adaptive Memory → Next Decision`

The brain does **not** contain broker credentials and does not directly place orders. Execution remains a separate boundary so the intelligence can be tested independently.

## API

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/brain`
- `POST /api/intelligence/cycle`
- `POST /api/brain/learn`
- `POST /api/simulator/open`
- `POST /api/simulator/step`
- `POST /api/simulator/close/{position_id}`
- `GET /api/strategies`
- `POST /api/strategies/{strategy_id}/transition`
- `GET /api/memory`
- `GET /api/risk`
- `GET /api/execution/status`

## Quick start

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
curl http://localhost:8000/api/health
```

## Execution boundary

Deriv connectivity remains explicitly gated by environment configuration. The intelligence brain can run entirely in simulation without a broker token. Live execution should only be enabled after the target account, token scope, stake limits, and operational controls have been reviewed.

## Roadmap

1. Brain foundation — **implemented**
2. Persistent memory and event store
3. Multi-asset data adapters and provenance
4. Backtesting and walk-forward evaluation
5. Strategy laboratory and model comparison
6. Gemini/Groq provider adapters for research/reasoning augmentation
7. Dashboard/body integrations
8. Broker/execution adapters after the intelligence layer is validated
