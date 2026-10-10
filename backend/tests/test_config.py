"""Tests for configuration and package imports."""

from app.core.config import REPO_ROOT, get_settings
from app.main import app


def test_settings_load():
    settings = get_settings()
    assert settings.app_name == "Resilience Scout"
    assert (REPO_ROOT / "pyproject.toml").exists()
    assert settings.indicator_registry_path.name == "indicator_registry.yaml"


def test_fastapi_app_imports():
    assert app.title
    # Newer FastAPI exposes _IncludedRouter objects in app.routes that have no .path,
    # so collect paths defensively and also from the OpenAPI schema.
    routes = {getattr(r, "path") for r in app.routes if hasattr(r, "path")}
    routes |= set(app.openapi().get("paths", {}))
    assert "/health" in routes