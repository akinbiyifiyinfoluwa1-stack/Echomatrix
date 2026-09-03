"""FastAPI entrypoint for Echo Matrix backend."""
from fastapi import FastAPI
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.system import router as system_router
from app.core.settings import get_settings
from app.logging.logger import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(health_router)
app.include_router(system_router, prefix="/api/v1")
