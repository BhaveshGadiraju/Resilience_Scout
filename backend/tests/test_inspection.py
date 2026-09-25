"""Inspection service and registry tests."""

from pathlib import Path

import pandas as pd

from app.schemas.indicators import load_indicator_registry
from app.services.inspection import inspect_csv, inspect_fhir_path, inspect_path

FIXTURE = Path(__file__).parent / "fixtures" / "Obs-WaterTemp-Almyros-2025-04-14.json"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_inspect_fhir_fixture():
    report = inspect_fhir_path(FIXTURE)
    assert report["resource_count"] == 1
    assert report["row_count"] == 1
    assert "Water temperature" in report["indicators"]
    assert report["min_date"] is not None
    assert "Almyros" in " ".join(report["unique_sites"])


def test_inspect_csv(tmp_path: Path):
    csv_path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "site": ["A", "A", "B"],
            "indicator": ["nitrate", "nitrate", "pH"],
            "date": ["2020-01-01", "2021-01-01", "2021-01-01"],
            "value": [1.0, 2.0, 7.1],
        }
    ).to_csv(csv_path, index=False)
    report = inspect_csv(csv_path)
    assert report["row_count"] == 3
    assert report["duplicate_records"] == 0
    assert set(report["unique_sites"]) == {"A", "B"}
    assert "nitrate" in report["indicators"]


def test_inspect_path_fixture():
    report = inspect_path(FIXTURE)
    assert report["format"] == "fhir_observation"


def test_indicator_registry_loads():
    path = REPO_ROOT / "data" / "indicator_registry.yaml"
    registry = load_indicator_registry(path)
    assert registry.version
    assert len(registry.indicators) >= 5
    ids = {i.id for i in registry.indicators}
    assert "water_temperature" in ids
    # Framework-only entries must not invent sites
    framework = [i for i in registry.indicators if i.observation_type == "framework_definition"]
    assert framework
    for item in framework:
        assert item.available_sites is None


def test_processed_inventory_if_present():
    inv = REPO_ROOT / "data" / "processed" / "oah_fhir_observation_inventory.csv"
    if not inv.exists():
        return
    report = inspect_csv(inv)
    assert report["row_count"] >= 100
    assert "indicator" in report["column_names"]
