
"""System capability/status endpoint. Never returns secrets."""
from fastapi import APIRouter
from config.capabilities import get_capabilities

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/capabilities")
async def capabilities() -> dict:
    return get_capabilities()
