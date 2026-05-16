"""Asynchronous ingestion service orchestrating external data collection."""
import asyncio
import logging
from app.integrations.providers import NewsAPIClient, CryptoPanicClient, BinanceClient

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self) -> None:
        self.news = NewsAPIClient()
        self.cryptopanic = CryptoPanicClient()
        self.binance = BinanceClient()

    async def collect_all(self) -> dict:
        logger.info("ingestion_cycle_started")
        results = await asyncio.gather(
            self.news.fetch_headlines(),
            self.cryptopanic.fetch_posts(),
            self.binance.fetch_ticker(),
            return_exceptions=True,
        )
        payload = {
            "news": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
            "cryptopanic": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
            "binance": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
        }
        logger.info("ingestion_cycle_completed")
        return payload
