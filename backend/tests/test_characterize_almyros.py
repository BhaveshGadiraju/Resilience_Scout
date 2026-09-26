"""Phase 2B: Almyros characterization tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.models.provenance import DataClass, load_provenance
from app.services.characterize_almyros import (
    CHARACTERIZATION_VERSION,
    classify_readiness,
    dataset_profile,
    load_observations,
    median_spearman,
    modeling_readiness,
    run_characterization,
    scale_anomaly_summary,
    unit_inventory,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ALMYROS_CSV = REPO_ROOT / "data" / "processed" / "almyros" / "observations.csv"


@pytest.fixture
def almyros_df() -> pd.DataFrame:
    assert ALMYROS_CSV.exists(), "Phase 2A observations.csv required for Phase 2B tests"
    return load_observations(ALMYROS_CSV)


def test_profile_matches_known_2a_totals(almyros_df: pd.DataFrame):
    profile = dataset_profile(almyros_df)
    assert profile["row_count"] == 587
    assert profile["indicator_count"] == 28
    assert profile["scale_anomaly_rows"] == 448
    assert profile["observation_kind_counts"]["annual_summary"] == 583
    assert profile["observation_kind_counts"]["point_sample"] == 4


def test_characterization_does_not_mutate_values(almyros_df: pd.DataFrame, tmp_path: Path):
    before = almyros_df[["row_id", "value_original", "value_normalized"]].copy()
    out = tmp_path / "characterization"
    prov = tmp_path / "almyros_characterization.yaml"
    run_characterization(input_csv=ALMYROS_CSV, output_dir=out, provenance_path=prov)
    after = load_observations(ALMYROS_CSV)
    merged = before.merge(after, on="row_id", suffixes=("_b", "_a"))
    assert merged["value_original_b"].equals(merged["value_original_a"])
    assert merged["value_normalized_b"].equals(merged["value_normalized_a"])


def test_readiness_never_promotes_mean_min_max(almyros_df: pd.DataFrame):
    readiness = modeling_readiness(almyros_df)
    assert set(readiness["primary_statistic"].unique()) <= {"median", "point", "none"}
    assert not readiness["mean_min_max_eligible_as_primary"].any()
    # Explicit classifier contract
    cls, primary, _ = classify_readiness(
        indicator_id="x",
        median_year_count=6,
        point_count=0,
        unit_consistent=True,
        has_usable_median_series=True,
    )
    assert cls == "candidate"
    assert primary == "median"


def test_readiness_classes_cover_all_indicators(almyros_df: pd.DataFrame):
    readiness = modeling_readiness(almyros_df)
    assert len(readiness) == almyros_df["indicator_id"].nunique()
    assert set(readiness["readiness_class"]) <= {"candidate", "limited", "exclude"}
    assert (readiness["readiness_class"] == "candidate").sum() >= 1
    # Short-span zinc is limited, not candidate
    zinc = readiness.loc[readiness["indicator_id"] == "zinc_dissolved"].iloc[0]
    assert zinc["readiness_class"] == "limited"
    assert zinc["primary_statistic"] == "median"


def test_units_normalized_consistent(almyros_df: pd.DataFrame):
    units = unit_inventory(almyros_df)
    assert units["unit_consistent_for_modeling"].all()
    ec = units.loc[units["indicator_id"] == "electrical_conductivity"].iloc[0]
    assert "uS/cm" in str(ec["unit_normalized_values"])


def test_scale_anomaly_summary_preserves_flag_counts(almyros_df: pd.DataFrame):
    summary = scale_anomaly_summary(almyros_df)
    assert summary["values_rewritten"].eq(False).all()
    assert int(summary["scale_anomaly_rows"].sum()) == 448


def test_spearman_is_exploratory_and_requires_overlap(almyros_df: pd.DataFrame):
    pairs = median_spearman(almyros_df, min_overlap=4)
    assert len(pairs) >= 1
    assert pairs["n_overlapping_years"].min() >= 4
    assert (pairs["label"] == "exploratory_descriptive_not_causal").all()


def test_run_characterization_writes_artifacts_and_provenance(tmp_path: Path):
    out = tmp_path / "characterization"
    prov = tmp_path / "almyros_characterization.yaml"
    summary = run_characterization(
        input_csv=ALMYROS_CSV, output_dir=out, provenance_path=prov
    )
    expected = [
        "dataset_profile.json",
        "indicator_coverage.csv",
        "temporal_coverage.csv",
        "statistic_coverage.csv",
        "unit_inventory.csv",
        "scale_anomaly_summary.csv",
        "median_spearman.csv",
        "modeling_readiness.csv",
    ]
    for name in expected:
        assert (out / name).exists(), name
    assert summary["characterization_version"] == CHARACTERIZATION_VERSION
    assert summary["row_count"] == 587
    record = load_provenance(prov)
    assert record.data_class == DataClass.derived
    assert record.preserves_original_values is True
    assert "almyros_normalized_v1" in record.original_filename_or_api
