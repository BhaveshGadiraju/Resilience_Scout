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
    routes = {r.path for r in app.routes}
    assert "/health" in routes
