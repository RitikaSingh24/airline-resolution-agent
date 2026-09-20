"""Main application entrypoint for FastAPI airline disruption resolution backend."""

import os
import sys

# Ensure src directory is in sys.path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

try:
    from api.v1.health import router as health_top_router
    from api.v1.router import router as api_v1_router
    from core.config import settings
    from core.exceptions import (
        AppException,
        BadRequestException,
        NotFoundException,
        app_exception_handler,
        http_exception_handler,
        unhandled_exception_handler,
        validation_exception_handler,
    )
    from core.logging import logger, setup_logging
    from db.base import Base
    from db.seed import seed_data
    from db.session import SessionLocal, engine
except ModuleNotFoundError:
    from src.api.v1.health import router as health_top_router
    from src.api.v1.router import router as api_v1_router
    from src.core.config import settings
    from src.core.exceptions import (
        AppException,
        BadRequestException,
        NotFoundException,
        app_exception_handler,
        http_exception_handler,
        unhandled_exception_handler,
        validation_exception_handler,
    )
    from src.core.logging import logger, setup_logging
    from src.db.base import Base
    from src.db.seed import seed_data
    from src.db.session import SessionLocal, engine

# Ensure models are loaded for table metadata creation
import models.action  # noqa: F401
import models.booking  # noqa: F401
import models.conversation  # noqa: F401
import models.customer  # noqa: F401
import models.escalation  # noqa: F401
import models.message  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle event handler."""
    # 1. Configure logging
    setup_logging()
    logger.info("Initializing database tables...")

    # 2. Create database tables if they do not exist
    Base.metadata.create_all(bind=engine)

    # 3. Run idempotent seed
    db = SessionLocal()
    try:
        seed_data(db)
        logger.info("Idempotent database seeding completed successfully.")
    except Exception as exc:
        logger.error("Error during database seeding: %s", exc)
    finally:
        db.close()

    yield

    logger.info("Application shutdown.")


app = FastAPI(
    title="Customer-facing Airline Disruption Resolution Agent",
    description="API for customer-facing airline disruption resolution.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Global Exception Handlers
app.add_exception_handler(NotFoundException, app_exception_handler)
app.add_exception_handler(BadRequestException, app_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Mount Routes
app.include_router(health_top_router)
app.include_router(api_v1_router, prefix="/api/v1")
