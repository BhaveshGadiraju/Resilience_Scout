"""FastAPI application entrypoint (Phase 1: health + config only)."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Adaptive environmental decision-support for next-best observation. "
        "Phase 1: foundation and data audit only — no recommendation engine."
    ),
    version="0.1.0",
)

app.include_router(health_router)
