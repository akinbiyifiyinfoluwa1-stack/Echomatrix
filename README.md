# Echo Matrix

Production-oriented AI trading infrastructure for multi-asset market intelligence and automated execution.

## Folder Structure

- `backend/` FastAPI backend and orchestration logic
- `frontend/` frontend app workspace
- `dashboard/` dashboard specification and UI assets
- `services/` service specs and bridge contracts
- `data_pipeline/` ingestion and normalization modules (expand next)
- `risk_engine/` strategy-agnostic risk modules (expand next)
- `signal_engine/` modular signal logic (expand next)
- `execution/` execution adapters and broker interfaces (expand next)
- `config/` runtime and environment configuration
- `logs/` log output mount
- `tests/` automated tests
- `docker/` container and compose definitions
- `docs/` architecture and roadmap

## Quick Start

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
2. Run with Docker:
   ```bash
   docker compose -f docker/docker-compose.yml up --build
   ```
3. Health check:
   ```bash
   curl http://localhost:8000/health
   ```

## API Endpoints
- `GET /health` basic service status
- `GET /api/v1/system/snapshot` ingestion snapshot from external providers

## Deployment (Oracle Cloud Ubuntu VM)

- Install Docker and Docker Compose plugin.
- Open ports 8000, 5432 (restricted), 6379 (restricted).
- Use systemd unit to auto-start Docker Compose stack.
- Place MT5 bridge host behind VPN/private subnet.

