from fastapi import APIRouter
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/snapshot")
async def system_snapshot() -> dict:
    service = IngestionService()
    return await service.collect_all()
