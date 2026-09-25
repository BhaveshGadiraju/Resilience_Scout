"""Phase 2A: Almyros normalization tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.models.provenance import DataClass, load_provenance
from app.schemas.normalized_observation import (
    NormalizedObservation,
    ObservationKind,
    StatisticType,
    TimePrecision,
)
from app.services.fsh_observation_parser import parse_fsh_file, parse_observation_block
from app.services.indicator_mapping import (
    apply_verified_unit_conversion,
    map_indicator,
)
from app.services.normalize_almyros import (
    expand_observation,
    file_sha256,
    normalize_observations,
    run_normalization,
)

FIXTURE = Path(__file__).parent / "fixtures" / "almyros_excerpt.fsh"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_fsh_parser_almyros_fixture():
    obs = parse_fsh_file(FIXTURE)
    ids = {o.source_observation_id for o in obs}
    assert "Obs-Almyros-AluminiumDissolved-2018" in ids
    alum = next(o for o in obs if o.source_observation_id == "Obs-Almyros-AluminiumDissolved-2018")
    codes = {c.statistic_code for c in alum.components}
    assert codes == {"average", "maximum", "minimum", "median"}


def test_statistic_preservation():
    obs = parse_fsh_file(FIXTURE)
    alum = next(o for o in obs if o.source_observation_id == "Obs-Almyros-AluminiumDissolved-2018")
    rows = expand_observation(alum)
    stats = {r.statistic_type for r in rows}
    assert stats == {
        StatisticType.mean,
        StatisticType.median,
        StatisticType.minimum,
        StatisticType.maximum,
    }
    point = next(o for o in obs if o.source_observation_id == "Obs-WaterTemp-Almyros-2025-04-14")
    point_rows = expand_observation(point)
    assert len(point_rows) == 1
    assert point_rows[0].statistic_type == StatisticType.point
    assert point_rows[0].observation_kind == ObservationKind.point_sample


def test_indicator_mapping():
    assert map_indicator("Water temperature").indicator_id == "water_temperature"
    assert map_indicator("Temperature (water)").indicator_id == "water_temperature"
    assert map_indicator("Conductivity").indicator_id == "electrical_conductivity"
    assert map_indicator("Electrical conductivity").indicator_id == "electrical_conductivity"


def test_unit_conversion_conductivity():
    v, u, conv = apply_verified_unit_conversion(18.4, "mS/cm", "uS/cm")
    assert v == 18400.0
    assert u == "uS/cm"
    assert conv == "mS/cm_to_uS/cm_x1000"

    obs = parse_fsh_file(FIXTURE)
    ec = next(o for o in obs if o.source_observation_id == "Obs-EC-Almyros-2024-11-21")
    rows = expand_observation(ec)
    assert rows[0].value_original == 18.4
    assert rows[0].unit_original == "mS/cm"
    assert rows[0].value_normalized == 18400.0
    assert rows[0].unit_normalized == "uS/cm"


def test_no_silent_metal_unit_change():
    v, u, conv = apply_verified_unit_conversion(10.0, "ug/L", "ug/L")
    assert v == 10.0
    assert u == "ug/L"
    assert conv is None
    # Must not invent mg/L conversion
    v2, u2, conv2 = apply_verified_unit_conversion(10.0, "ug/L", "mg/L")
    assert v2 == 10.0
    assert u2 == "ug/L"
    assert conv2 is None


def test_schema_validation():
    with pytest.raises(Exception):
        NormalizedObservation(
            row_id="x::point",
            source_observation_id="",
            source_file="f.fsh",
            site_id="Loc-Almyros",
            indicator_id="water_temperature",
            indicator_name_raw="Water temperature",
            observation_kind=ObservationKind.point_sample,
            statistic_type=StatisticType.point,
            time_start=date(2025, 4, 14),
            time_end=None,
            time_precision=TimePrecision.day,
            value_original=16.2,
            unit_original="Cel",
            value_normalized=16.2,
            unit_normalized="Cel",
        )


def test_almyros_filter():
    obs = parse_fsh_file(FIXTURE)
    rows = normalize_observations(obs)
    assert all(r.site_id == "Loc-Almyros" for r in rows)
    assert not any("Benevento" in r.source_observation_id for r in rows)


def test_raw_immutable_and_provenance(tmp_path: Path):
    fsh_dir = tmp_path / "fsh"
    fsh_dir.mkdir()
    # Copy fixture as the three expected filenames (gov chem + water + ec content combined)
    content = FIXTURE.read_text(encoding="utf-8")
    for name in ("almyros_gov_chem.fsh", "water_tmp.fsh", "ec_tmp.fsh"):
        (fsh_dir / name).write_text(content, encoding="utf-8")

    hashes_before = {p.name: file_sha256(p) for p in fsh_dir.glob("*.fsh")}
    out = tmp_path / "out"
    prov = tmp_path / "prov.yaml"
    summary = run_normalization(fsh_dir=fsh_dir, output_dir=out, provenance_path=prov)
    hashes_after = {p.name: file_sha256(p) for p in fsh_dir.glob("*.fsh")}
    assert hashes_before == hashes_after
    assert (out / "observations.csv").exists()
    rec = load_provenance(prov)
    assert rec.data_class == DataClass.derived
    assert summary["source_observation_count"] >= 3


def test_observed_derived_separation():
    raw_prov = REPO_ROOT / "data" / "provenance" / "oah_fhir_ig_examples.yaml"
    proc_prov = REPO_ROOT / "data" / "provenance" / "almyros_normalized.yaml"
    assert raw_prov.exists()
    assert proc_prov.exists()
    assert load_provenance(raw_prov).data_class == DataClass.observed
    assert load_provenance(proc_prov).data_class == DataClass.derived


def test_full_pipeline_almyros_counts():
    """Integration check against real downloaded FSH (if present)."""
    fsh = REPO_ROOT / "data" / "raw" / "oah_fhir_ig_examples" / "github_fsh" / "almyros_gov_chem.fsh"
    if not fsh.exists():
        pytest.skip("raw Almyros FSH not present")
    out_csv = REPO_ROOT / "data" / "processed" / "almyros" / "observations.csv"
    assert out_csv.exists()
    import pandas as pd

    df = pd.read_csv(out_csv)
    assert set(df["site_id"].unique()) == {"Loc-Almyros"}
    assert df["source_observation_id"].nunique() == 135
    assert {"point", "mean", "median", "minimum", "maximum", "std_dev"} <= set(df["statistic_type"])
    assert (df["data_class"] == "derived").all()
