"""Web Dashboard for Strict.

Provides a simple web interface for monitoring and interacting with Strict.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from strict.config import get_settings

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

templates = Jinja2Templates(directory="src/strict/dashboard/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request) -> HTMLResponse:
    """Render the dashboard home page."""
    settings = get_settings()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "settings": {
                "debug": settings.debug,
                "log_level": settings.log_level,
                "ollama_base_url": str(settings.ollama_base_url),
            },
        },
    )


@router.get("/health", response_class=HTMLResponse)
async def health_status(request: Request) -> HTMLResponse:
    """Render the health status page."""
    return templates.TemplateResponse(
        "health.html",
        {
            "request": request,
            "status": "healthy",
        },
    )


@router.get("/api/docs")
async def api_docs() -> dict[str, str]:
    """Get API documentation links."""
    return {
        "swagger": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }
