"""API v1 master router."""

from fastapi import APIRouter

from .chat import router as chat_router
from .customers import router as customers_router
from .escalations import router as escalations_router
from .health import router as health_router

router = APIRouter()

router.include_router(health_router)
router.include_router(customers_router)
router.include_router(chat_router)
router.include_router(escalations_router)
