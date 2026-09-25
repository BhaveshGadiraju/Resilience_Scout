"""Provenance metadata validation tests."""

from datetime import date
from pathlib import Path

import pytest

from app.models.provenance import DataClass, ProvenanceRecord, load_provenance, save_provenance


def test_provenance_roundtrip(tmp_path: Path):
    record = ProvenanceRecord(
        source="Test source",
        source_url="https://example.org/data",
        retrieval_date=date(2026, 9, 25),
        original_filename_or_api="example.json",
        license="CC-BY-4.0",
        data_class=DataClass.observed,
        processing_steps=["downloaded"],
        preserves_original_values=True,
        notes="fixture",
    )
    path = tmp_path / "prov.yaml"
    save_provenance(record, path)
    loaded = load_provenance(path)
    assert loaded.source == "Test source"
    assert loaded.data_class == DataClass.observed
    assert loaded.retrieval_date == date(2026, 9, 25)


def test_provenance_rejects_empty_url():
    with pytest.raises(Exception):
        ProvenanceRecord(
            source="x",
            source_url="   ",
            retrieval_date=date.today(),
            original_filename_or_api="f",
            data_class=DataClass.derived,
        )


def test_repo_provenance_files_parse():
    root = Path(__file__).resolve().parents[2]
    prov_dir = root / "data" / "provenance"
    yaml_files = list(prov_dir.glob("*.yaml"))
    assert yaml_files, "expected provenance sidecars from Phase 1 import"
    for path in yaml_files:
        rec = load_provenance(path)
        assert rec.source_url
        assert rec.data_class in set(DataClass)
