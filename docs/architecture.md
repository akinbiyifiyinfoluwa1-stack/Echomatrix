# Echo Matrix V1 Architecture

## Core Layers
1. **Ingestion Layer** (`app/services/ingestion.py`, `app/integrations/*`): async data collection from market and intelligence providers.
2. **Signal Layer** (`app/services/signal_engine.py`): composable scoring and ranking modules.
3. **Risk Layer** (`app/services/risk_engine.py`): pre-trade guardrails and position constraints.
4. **Execution Layer** (`app/services/execution_router.py`): broker-agnostic order routing via MT5 bridge.
5. **Interface Layer** (`app/main.py`, API routes): dashboard-facing REST/WebSocket APIs.

## Deployment Topology
- Ubuntu Oracle VM runs API, workers, PostgreSQL, Redis, and dashboard.
- Windows host runs MT5 bridge with secured inbound endpoint.
- Communication over private network/VPN with token auth.

## Future Evolution
- Add strategy plugins under `signal_engine/` and `risk_engine/`.
- Add ML inference services in `services/ml/` with feature store.
- Introduce portfolio optimizer service and reinforcement learner.
