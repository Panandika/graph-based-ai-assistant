from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is running and healthy.",
)
async def health_check() -> dict[str, str]:
    """Return health status of the API."""
    return {"status": "healthy"}
