from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from strict.api.routes import router as api_router
from strict.config import settings
from strict.observability.logging import configure_logging
from strict.observability.metrics import configure_metrics
from strict.dashboard.routes import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan events for the FastAPI application."""
    configure_logging()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Strict API",
        description="High-Integrity Signal Processing Engine API",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    configure_metrics(app)

    # Configure CORS from settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(dashboard_router)

    return app


app = create_app()
