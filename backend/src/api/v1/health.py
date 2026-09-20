"""Health check API endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Returns API status OK.",
    response_model=dict[str, str],
)
def get_health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "OK"}
