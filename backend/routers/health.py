from fastapi import APIRouter
from backend.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Public health check endpoint"""
    return {"status": "ok"}
