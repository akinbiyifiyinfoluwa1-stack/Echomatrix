"""External provider adapters for market intelligence feeds."""
from app.core.settings import get_settings
from app.integrations.base import BaseAPIClient

settings = get_settings()


class NewsAPIClient(BaseAPIClient):
    def __init__(self) -> None:
        super().__init__("https://newsapi.org")

    async def fetch_headlines(self, query: str = "forex OR crypto OR stocks") -> dict:
        return await self.get(
            "/v2/everything",
            params={"q": query, "apiKey": settings.news_api_key, "sortBy": "publishedAt", "language": "en"},
        )


class CryptoPanicClient(BaseAPIClient):
    def __init__(self) -> None:
        super().__init__("https://cryptopanic.com")

    async def fetch_posts(self) -> dict:
        return await self.get("/api/v1/posts/", params={"auth_token": settings.cryptopanic_api_key})


class BinanceClient(BaseAPIClient):
    def __init__(self) -> None:
        super().__init__("https://api.binance.com")

    async def fetch_ticker(self, symbol: str = "BTCUSDT") -> dict:
        return await self.get("/api/v3/ticker/24hr", params={"symbol": symbol})
