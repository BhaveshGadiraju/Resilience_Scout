"""Application configuration loaded from environment / .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: backend/app/core/config.py -> parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for Resilience Scout (Phase 1)."""

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Resilience Scout"
    app_env: str = "development"
    debug: bool = True

    data_raw_dir: Path = REPO_ROOT / "data" / "raw"
    data_processed_dir: Path = REPO_ROOT / "data" / "processed"
    data_provenance_dir: Path = REPO_ROOT / "data" / "provenance"
    indicator_registry_path: Path = REPO_ROOT / "data" / "indicator_registry.yaml"

    @property
    def repo_root(self) -> Path:
        return REPO_ROOT


def get_settings() -> Settings:
    return Settings()
