"""Normalize Almyros OAH FHIR observations into long-format analysis tables."""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd

from app.core.config import REPO_ROOT
from app.models.provenance import DataClass, ProvenanceRecord, save_provenance
from app.schemas.normalized_observation import (
    PROVENANCE_DATASET_ID,
    TRANSFORM_VERSION,
    NormalizedObservation,
    ObservationKind,
    ParsedObservation,
    StatisticType,
    TimePrecision,
)
from app.services.fsh_observation_parser import filter_site, parse_fsh_paths
from app.services.indicator_mapping import (
    apply_verified_unit_conversion,
    map_indicator,
    map_statistic_code,
)

DEFAULT_FSH_FILES = (
    "almyros_gov_chem.fsh",
    "water_tmp.fsh",
    "ec_tmp.fsh",
)

SCALE_ANOMALY_RATIO = 10.0
ALMYROS_SITE = "Loc-Almyros"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _flags_for_observation(obs: ParsedObservation) -> Set[str]:
    flags: Set[str] = set()
    by_code = {c.statistic_code: c for c in obs.components}
    mean_c = by_code.get("average") or by_code.get("mean")
    median_c = by_code.get("median")
    if mean_c and median_c and mean_c.value is not None and median_c.value not in (None, 0):
        if abs(mean_c.value) / abs(median_c.value) >= SCALE_ANOMALY_RATIO:
            flags.add("scale_anomaly")
    # Expected companions for annual summaries
    if obs.effective_period_start is not None:
        present = {c.statistic_code for c in obs.components}
        expected = {"average", "maximum", "minimum", "median"}
        if not expected.issubset(present):
            flags.add("missing_companion_stats")
    return flags


def expand_observation(obs: ParsedObservation) -> List[NormalizedObservation]:
    if not obs.indicator_name_raw:
        raise ValueError(f"Missing indicator for {obs.source_observation_id}")
    if not obs.site_id:
        raise ValueError(f"Missing site for {obs.source_observation_id}")

    spec = map_indicator(obs.indicator_name_raw)
    flags = _flags_for_observation(obs)
    flag_str = "|".join(sorted(flags)) if flags else None
    rows: List[NormalizedObservation] = []

    # Point sample
    if obs.effective_datetime is not None and obs.value_quantity is not None:
        v_norm, u_norm, conv = apply_verified_unit_conversion(
            obs.value_quantity, obs.value_unit, spec.canonical_unit
        )
        rows.append(
            NormalizedObservation(
                row_id=f"{obs.source_observation_id}::point",
                source_observation_id=obs.source_observation_id,
                source_file=obs.source_file,
                site_id=obs.site_id,
                indicator_id=spec.indicator_id,
                indicator_name_raw=obs.indicator_name_raw,
                observation_kind=ObservationKind.point_sample,
                statistic_type=StatisticType.point,
                time_start=obs.effective_datetime,
                time_end=None,
                time_precision=TimePrecision.day,
                value_original=obs.value_quantity,
                unit_original=obs.value_unit,
                value_normalized=v_norm,
                unit_normalized=u_norm,
                unit_conversion_applied=conv,
                quality_flags=flag_str,
            )
        )

    # Annual summary components
    if obs.effective_period_start is not None:
        if obs.effective_period_end is None:
            raise ValueError(f"Annual observation missing period end: {obs.source_observation_id}")
        for comp in obs.components:
            stat = StatisticType(map_statistic_code(comp.statistic_code))
            v_norm, u_norm, conv = apply_verified_unit_conversion(
                comp.value, comp.unit, spec.canonical_unit
            )
            rows.append(
                NormalizedObservation(
                    row_id=f"{obs.source_observation_id}::{stat.value}",
                    source_observation_id=obs.source_observation_id,
                    source_file=obs.source_file,
                    site_id=obs.site_id,
                    indicator_id=spec.indicator_id,
                    indicator_name_raw=obs.indicator_name_raw,
                    observation_kind=ObservationKind.annual_summary,
                    statistic_type=stat,
                    time_start=obs.effective_period_start,
                    time_end=obs.effective_period_end,
                    time_precision=TimePrecision.year,
                    value_original=comp.value,
                    unit_original=comp.unit,
                    value_normalized=v_norm,
                    unit_normalized=u_norm,
                    unit_conversion_applied=conv,
                    quality_flags=flag_str,
                )
            )

    if not rows:
        raise ValueError(f"No measurable values extracted for {obs.source_observation_id}")
    return rows


def normalize_observations(observations: Sequence[ParsedObservation]) -> List[NormalizedObservation]:
    almyros = filter_site(observations, ALMYROS_SITE)
    rows: List[NormalizedObservation] = []
    for obs in almyros:
        rows.extend(expand_observation(obs))
    return rows


def rows_to_dataframe(rows: Sequence[NormalizedObservation]) -> pd.DataFrame:
    records = [r.model_dump(mode="json") for r in rows]
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values(
            ["indicator_id", "time_start", "statistic_type", "source_observation_id"]
        ).reset_index(drop=True)
    return df


def default_fsh_dir() -> Path:
    return REPO_ROOT / "data" / "raw" / "oah_fhir_ig_examples" / "github_fsh"


def default_output_dir() -> Path:
    return REPO_ROOT / "data" / "processed" / "almyros"


def run_normalization(
    fsh_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    provenance_path: Optional[Path] = None,
) -> Dict[str, object]:
    """
    Read raw FSH (immutable), write processed Almyros table + provenance.

    Returns a summary dict for CLI / analysis notes.
    """
    fsh_dir = fsh_dir or default_fsh_dir()
    output_dir = output_dir or default_output_dir()
    provenance_path = provenance_path or (
        REPO_ROOT / "data" / "provenance" / "almyros_normalized.yaml"
    )

    paths = [fsh_dir / name for name in DEFAULT_FSH_FILES]
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing FSH inputs: {missing}")

    raw_hashes = {p.name: file_sha256(p) for p in paths}

    parsed = parse_fsh_paths(paths)
    rows = normalize_observations(parsed)
    # Validate via model (already constructed); ensure foreign sites absent
    sites = {r.site_id for r in rows}
    if sites != {ALMYROS_SITE}:
        raise ValueError(f"Unexpected sites in output: {sites}")

    df = rows_to_dataframe(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "observations.csv"
    parquet_path = output_dir / "observations.parquet"
    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(parquet_path, index=False)
        parquet_written = True
    except Exception:
        # pyarrow/fastparquet may be absent; CSV is required
        parquet_written = False

    # Verify raw unchanged
    for p in paths:
        if file_sha256(p) != raw_hashes[p.name]:
            raise RuntimeError(f"Raw FSH modified during normalization: {p}")

    save_provenance(
        ProvenanceRecord(
            source="Almyros OAH FHIR FSH examples (normalized long-format)",
            source_url="https://github.com/hl7-eu/oah/tree/master/input/fsh/examples",
            retrieval_date=date.today(),
            original_filename_or_api=", ".join(DEFAULT_FSH_FILES),
            license="Derived from OAH FHIR IG source examples; same upstream terms.",
            data_class=DataClass.derived,
            processing_steps=[
                "Parsed FHIR Shorthand Observation instances from data/raw (read-only)",
                "Filtered subject Loc-Almyros",
                "Expanded each annual component (mean/median/min/max/std_dev) and point valueQuantity into long rows",
                "Mapped indicator aliases to canonical indicator_id",
                "Applied verified unit conversion mS/cm→uS/cm (×1000) for conductivity only",
                "Flagged scale_anomaly when |mean|/median ≥ 10; never rescaled source values",
            ],
            preserves_original_values=True,
            notes=(
                f"transform_version={TRANSFORM_VERSION}; provenance_dataset_id={PROVENANCE_DATASET_ID}. "
                "value_original/unit_original are literal FSH values. "
                "Phase 1 inventory CSV is incomplete for multi-statistic analysis — use this table instead. "
                "No interpolation of missing years or statistics."
            ),
        ),
        provenance_path,
    )

    summary = {
        "source_observation_count": len({r.source_observation_id for r in rows}),
        "row_count": len(rows),
        "indicators": sorted({r.indicator_id for r in rows}),
        "statistic_types": sorted({r.statistic_type.value for r in rows}),
        "scale_anomaly_rows": int(
            sum(1 for r in rows if r.quality_flags and "scale_anomaly" in r.quality_flags)
        ),
        "csv_path": str(csv_path),
        "parquet_path": str(parquet_path) if parquet_written else None,
        "provenance_path": str(provenance_path),
        "raw_hashes": raw_hashes,
        "transform_version": TRANSFORM_VERSION,
    }
    return summary


def write_analysis_summary(summary: Dict[str, object], path: Optional[Path] = None) -> Path:
    path = path or (REPO_ROOT / "analysis" / "almyros_normalization_summary.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Almyros normalization summary (Phase 2A)",
        "",
        f"- transform_version: `{summary['transform_version']}`",
        f"- source observations: **{summary['source_observation_count']}**",
        f"- long-format rows: **{summary['row_count']}**",
        f"- indicators: {', '.join(summary['indicators'])}",  # type: ignore[arg-type]
        f"- statistic types: {', '.join(summary['statistic_types'])}",  # type: ignore[arg-type]
        f"- rows with scale_anomaly flag: **{summary['scale_anomaly_rows']}**",
        f"- output CSV: `{summary['csv_path']}`",
        f"- output parquet: `{summary.get('parquet_path')}`",
        f"- provenance: `{summary['provenance_path']}`",
        "",
        "Raw FSH was not modified. See `docs/DATA_NORMALIZATION.md`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
