"""Data validation helpers."""

from pathlib import Path

from app.core.config import REPO_ROOT


def test_raw_and_processed_separated():
    raw = REPO_ROOT / "data" / "raw"
    processed = REPO_ROOT / "data" / "processed"
    assert raw.exists()
    assert processed.exists()
    assert raw.resolve() != processed.resolve()


def test_fhir_raw_present():
    fsh = REPO_ROOT / "data" / "raw" / "oah_fhir_ig_examples" / "github_fsh"
    assert fsh.exists()
    assert list(fsh.glob("*.fsh")), "expected downloaded FSH examples"


def test_resmap_raw_present():
    api = REPO_ROOT / "data" / "raw" / "resilience_map_api"
    assert (api / "api__cities__all.json").exists()
    assert (api / "api__sites__all.json").exists()
