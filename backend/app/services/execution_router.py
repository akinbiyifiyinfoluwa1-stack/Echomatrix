"""Execution routing abstraction for MT5 bridge and future brokers."""
import httpx
from app.core.settings import get_settings

settings = get_settings()


class ExecutionRouter:
    async def submit_order(self, order: dict) -> dict:
        headers = {"Authorization": f"Bearer {settings.mt5_bridge_token}"} if settings.mt5_bridge_token else {}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{settings.mt5_bridge_url}/orders", json=order, headers=headers)
            response.raise_for_status()
            return response.json()
