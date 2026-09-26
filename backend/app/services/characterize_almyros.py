"""Characterize normalized Almyros observations for modeling readiness (Phase 2B).

Does not score risk, predict, rank next observations, or rewrite values.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.core.config import REPO_ROOT
from app.models.provenance import DataClass, ProvenanceRecord, save_provenance
from app.schemas.normalized_observation import PROVENANCE_DATASET_ID, TRANSFORM_VERSION

CHARACTERIZATION_VERSION = "2b.1"
MIN_MEDIAN_YEARS_CANDIDATE = 4
MIN_OVERLAP_YEARS_SPEARMAN = 4
EXPECTED_ANNUAL_STATS = ("mean", "median", "minimum", "maximum")

DEFAULT_INPUT_CSV = REPO_ROOT / "data" / "processed" / "almyros" / "observations.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "processed" / "almyros" / "characterization"
DEFAULT_PROVENANCE_PATH = REPO_ROOT / "data" / "provenance" / "almyros_characterization.yaml"


def load_observations(path: Path) -> pd.DataFrame:
    """Load Phase 2A long-format table; fail loudly if missing or empty."""
    if not path.exists():
        raise FileNotFoundError(f"Normalized Almyros table not found: {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Normalized Almyros table is empty: {path}")
    required = {
        "row_id",
        "source_observation_id",
        "indicator_id",
        "observation_kind",
        "statistic_type",
        "time_start",
        "value_original",
        "value_normalized",
        "unit_original",
        "unit_normalized",
        "quality_flags",
        "data_class",
        "provenance_dataset_id",
        "transform_version",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return df.copy()


def _year_series(df: pd.DataFrame) -> pd.Series:
    return df["time_start"].astype(str).str[:4].astype(int)


def _has_flag(flags: Any, name: str) -> bool:
    if flags is None or (isinstance(flags, float) and pd.isna(flags)):
        return False
    return name in str(flags).split("|")


def dataset_profile(df: pd.DataFrame) -> Dict[str, Any]:
    years = _year_series(df)
    scale_rows = int(df["quality_flags"].map(lambda f: _has_flag(f, "scale_anomaly")).sum())
    missing_companion = int(
        df["quality_flags"].map(lambda f: _has_flag(f, "missing_companion_stats")).sum()
    )
    return {
        "characterization_version": CHARACTERIZATION_VERSION,
        "input_provenance_dataset_id": PROVENANCE_DATASET_ID,
        "input_transform_version": TRANSFORM_VERSION,
        "row_count": int(len(df)),
        "source_observation_count": int(df["source_observation_id"].nunique()),
        "indicator_count": int(df["indicator_id"].nunique()),
        "indicators": sorted(df["indicator_id"].unique().tolist()),
        "observation_kind_counts": {
            str(k): int(v) for k, v in df["observation_kind"].value_counts().items()
        },
        "statistic_type_counts": {
            str(k): int(v) for k, v in df["statistic_type"].value_counts().items()
        },
        "time_span": {
            "min_time_start": str(df["time_start"].min()),
            "max_time_start": str(df["time_start"].max()),
            "years_present": sorted(years.unique().tolist()),
        },
        "scale_anomaly_rows": scale_rows,
        "missing_companion_stats_rows": missing_companion,
        "site_ids": sorted(df["site_id"].unique().tolist()) if "site_id" in df.columns else [],
        "data_classes": sorted(df["data_class"].dropna().unique().tolist()),
        "notes": (
            "Primary annual series for readiness is statistic_type=median. "
            "Mean/min/max under scale_anomaly are profiled but not modeling candidates. "
            "Point samples are characterized separately and not pooled with annual medians."
        ),
    }


def indicator_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Long matrix: indicator_id × year × statistic_type presence."""
    work = df.copy()
    work["year"] = _year_series(work)
    grouped = (
        work.groupby(["indicator_id", "year", "statistic_type"], dropna=False)
        .agg(
            row_count=("row_id", "count"),
            observation_kind=("observation_kind", "first"),
        )
        .reset_index()
    )
    grouped["present"] = True
    return grouped.sort_values(["indicator_id", "year", "statistic_type"]).reset_index(drop=True)


def temporal_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Per-indicator temporal span for annual medians and point samples."""
    rows: List[Dict[str, Any]] = []
    all_years = sorted(_year_series(df).unique().tolist())
    year_set = set(all_years)
    for indicator_id, g in df.groupby("indicator_id"):
        med = g[g["statistic_type"] == "median"]
        pts = g[g["statistic_type"] == "point"]
        med_years = sorted(_year_series(med).unique().tolist()) if not med.empty else []
        point_dates = sorted(pts["time_start"].astype(str).unique().tolist()) if not pts.empty else []
        if med_years:
            full_span = list(range(med_years[0], med_years[-1] + 1))
            gaps = [y for y in full_span if y not in set(med_years)]
        else:
            gaps = []
        dataset_gaps = [y for y in year_set if y not in set(med_years)] if med_years else list(year_set)
        rows.append(
            {
                "indicator_id": indicator_id,
                "annual_median_year_count": len(med_years),
                "annual_median_years": ";".join(str(y) for y in med_years) if med_years else None,
                "annual_median_gaps_within_span": ";".join(str(y) for y in gaps) if gaps else None,
                "point_sample_count": int(len(pts)),
                "point_sample_dates": ";".join(point_dates) if point_dates else None,
                "observation_kinds": ";".join(sorted(g["observation_kind"].unique())),
            }
        )
    return pd.DataFrame(rows).sort_values("indicator_id").reset_index(drop=True)


def statistic_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Per source observation: which annual statistics are present/absent."""
    annual = df[df["observation_kind"] == "annual_summary"].copy()
    if annual.empty:
        return pd.DataFrame(
            columns=[
                "source_observation_id",
                "indicator_id",
                "year",
                "stats_present",
                "stats_missing",
                "has_median",
                "has_std_dev",
                "scale_anomaly",
                "missing_companion_stats",
            ]
        )
    annual["year"] = _year_series(annual)
    rows: List[Dict[str, Any]] = []
    for obs_id, g in annual.groupby("source_observation_id"):
        present = sorted(g["statistic_type"].unique().tolist())
        present_set = set(present)
        missing = [s for s in EXPECTED_ANNUAL_STATS if s not in present_set]
        flags = g["quality_flags"].dropna().astype(str)
        flag_union = set()
        for f in flags:
            flag_union.update(x for x in f.split("|") if x)
        rows.append(
            {
                "source_observation_id": obs_id,
                "indicator_id": g["indicator_id"].iloc[0],
                "year": int(g["year"].iloc[0]),
                "stats_present": ";".join(present),
                "stats_missing": ";".join(missing) if missing else None,
                "has_median": "median" in present_set,
                "has_std_dev": "std_dev" in present_set,
                "scale_anomaly": "scale_anomaly" in flag_union,
                "missing_companion_stats": "missing_companion_stats" in flag_union,
            }
        )
    return pd.DataFrame(rows).sort_values(["indicator_id", "year"]).reset_index(drop=True)


def unit_inventory(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for indicator_id, g in df.groupby("indicator_id"):
        orig = sorted({u for u in g["unit_original"].dropna().astype(str).unique()})
        norm = sorted({u for u in g["unit_normalized"].dropna().astype(str).unique()})
        conversions = sorted(
            {
                c
                for c in g.get("unit_conversion_applied", pd.Series(dtype=object))
                .dropna()
                .astype(str)
                .unique()
            }
        )
        multi_original = len(orig) > 1
        multi_normalized = len(norm) > 1
        rows.append(
            {
                "indicator_id": indicator_id,
                "unit_original_values": ";".join(orig) if orig else None,
                "unit_normalized_values": ";".join(norm) if norm else None,
                "unit_conversions_applied": ";".join(conversions) if conversions else None,
                "multi_unit_original": multi_original,
                "multi_unit_normalized": multi_normalized,
                "unit_consistent_for_modeling": not multi_normalized,
            }
        )
    return pd.DataFrame(rows).sort_values("indicator_id").reset_index(drop=True)


def scale_anomaly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-indicator scale anomaly impact; recomputes |mean|/|median| where both exist."""
    rows: List[Dict[str, Any]] = []
    for indicator_id, g in df.groupby("indicator_id"):
        total_rows = len(g)
        flagged_rows = int(g["quality_flags"].map(lambda f: _has_flag(f, "scale_anomaly")).sum())
        flagged_obs = g[g["quality_flags"].map(lambda f: _has_flag(f, "scale_anomaly"))][
            "source_observation_id"
        ].nunique()
        ratios: List[float] = []
        for obs_id, og in g.groupby("source_observation_id"):
            mean_rows = og[og["statistic_type"] == "mean"]
            med_rows = og[og["statistic_type"] == "median"]
            if mean_rows.empty or med_rows.empty:
                continue
            mean_v = mean_rows["value_normalized"].iloc[0]
            med_v = med_rows["value_normalized"].iloc[0]
            if pd.isna(mean_v) or pd.isna(med_v) or med_v == 0:
                continue
            ratios.append(abs(float(mean_v)) / abs(float(med_v)))
        rows.append(
            {
                "indicator_id": indicator_id,
                "total_rows": total_rows,
                "scale_anomaly_rows": flagged_rows,
                "scale_anomaly_observation_count": int(flagged_obs),
                "scale_anomaly_row_fraction": round(flagged_rows / total_rows, 4) if total_rows else 0.0,
                "mean_over_median_ratio_count": len(ratios),
                "mean_over_median_ratio_min": round(min(ratios), 4) if ratios else None,
                "mean_over_median_ratio_median": round(float(pd.Series(ratios).median()), 4)
                if ratios
                else None,
                "mean_over_median_ratio_max": round(max(ratios), 4) if ratios else None,
                "values_rewritten": False,
            }
        )
    return pd.DataFrame(rows).sort_values("indicator_id").reset_index(drop=True)


def annual_median_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Wide panel of annual median values (year × indicator). Point samples excluded."""
    med = df[df["statistic_type"] == "median"].copy()
    if med.empty:
        return pd.DataFrame()
    med["year"] = _year_series(med)
    # One median per indicator-year (source should already be unique)
    pivot = med.pivot_table(
        index="year",
        columns="indicator_id",
        values="value_normalized",
        aggfunc="first",
    )
    return pivot.sort_index()


def _spearman_rho(x: pd.Series, y: pd.Series) -> Optional[float]:
    """Pearson correlation of average ranks (no scipy dependency)."""
    if len(x) < 2:
        return None
    rx = x.rank(method="average")
    ry = y.rank(method="average")
    # Constant ranks → undefined correlation
    if rx.nunique() < 2 or ry.nunique() < 2:
        return None
    rho = rx.corr(ry, method="pearson")
    if pd.isna(rho):
        return None
    return float(rho)


def median_spearman(df: pd.DataFrame, min_overlap: int = MIN_OVERLAP_YEARS_SPEARMAN) -> pd.DataFrame:
    """Exploratory Spearman correlations among annual-median indicators with enough overlap."""
    panel = annual_median_panel(df)
    if panel.empty or panel.shape[1] < 2:
        return pd.DataFrame(
            columns=[
                "indicator_a",
                "indicator_b",
                "spearman_rho",
                "n_overlapping_years",
                "min_overlap_required",
                "label",
            ]
        )
    cols = list(panel.columns)
    pairs: List[Dict[str, Any]] = []
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            sub = panel[[a, b]].dropna()
            n = len(sub)
            if n < min_overlap:
                continue
            rho = _spearman_rho(sub[a], sub[b])
            pairs.append(
                {
                    "indicator_a": a,
                    "indicator_b": b,
                    "spearman_rho": round(rho, 6) if rho is not None else None,
                    "n_overlapping_years": n,
                    "min_overlap_required": min_overlap,
                    "label": "exploratory_descriptive_not_causal",
                }
            )
    out = pd.DataFrame(pairs)
    if out.empty:
        return out
    return out.sort_values(["indicator_a", "indicator_b"]).reset_index(drop=True)


def classify_readiness(
    indicator_id: str,
    median_year_count: int,
    point_count: int,
    unit_consistent: bool,
    has_usable_median_series: bool,
) -> Tuple[str, str, str]:
    """Return (readiness_class, primary_statistic, rationale).

    Classes: candidate | limited | exclude
    primary_statistic is never mean/minimum/maximum.
    """
    if not unit_consistent:
        return (
            "exclude",
            "none",
            "Inconsistent unit_normalized values; resolve before modeling.",
        )
    if has_usable_median_series and median_year_count >= MIN_MEDIAN_YEARS_CANDIDATE:
        return (
            "candidate",
            "median",
            f"≥{MIN_MEDIAN_YEARS_CANDIDATE} annual median years; use median only "
            "(ignore scale-anomalous mean/min/max).",
        )
    if has_usable_median_series and 1 <= median_year_count < MIN_MEDIAN_YEARS_CANDIDATE:
        return (
            "limited",
            "median",
            f"Only {median_year_count} annual median year(s); short span for Scout prototyping.",
        )
    if point_count > 0 and median_year_count == 0:
        return (
            "limited",
            "point",
            f"Point samples only (n={point_count}); do not pool with annual medians.",
        )
    return (
        "exclude",
        "none",
        "No usable annual median series and insufficient point depth for engine design.",
    )


def modeling_readiness(df: pd.DataFrame, units: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    units = units if units is not None else unit_inventory(df)
    unit_ok = {
        row["indicator_id"]: bool(row["unit_consistent_for_modeling"])
        for _, row in units.iterrows()
    }
    temporal = temporal_coverage(df)
    scale = scale_anomaly_summary(df)
    scale_frac = {
        row["indicator_id"]: float(row["scale_anomaly_row_fraction"]) for _, row in scale.iterrows()
    }
    rows: List[Dict[str, Any]] = []
    for _, t in temporal.iterrows():
        indicator_id = t["indicator_id"]
        med_years = int(t["annual_median_year_count"])
        point_count = int(t["point_sample_count"])
        consistent = unit_ok.get(indicator_id, True)
        has_median = med_years > 0
        readiness, primary_stat, rationale = classify_readiness(
            indicator_id=indicator_id,
            median_year_count=med_years,
            point_count=point_count,
            unit_consistent=consistent,
            has_usable_median_series=has_median,
        )
        # Document that mean/min/max are never primary even when scale_anomaly is widespread
        rows.append(
            {
                "indicator_id": indicator_id,
                "readiness_class": readiness,
                "primary_statistic": primary_stat,
                "annual_median_year_count": med_years,
                "point_sample_count": point_count,
                "unit_consistent": consistent,
                "scale_anomaly_row_fraction": scale_frac.get(indicator_id, 0.0),
                "mean_min_max_eligible_as_primary": False,
                "rationale": rationale,
            }
        )
    return pd.DataFrame(rows).sort_values(["readiness_class", "indicator_id"]).reset_index(drop=True)


def run_characterization(
    input_csv: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    provenance_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load normalized Almyros table, write characterization artifacts, return summary."""
    input_csv = input_csv or DEFAULT_INPUT_CSV
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    provenance_path = provenance_path or DEFAULT_PROVENANCE_PATH

    df = load_observations(input_csv)
    # Snapshot to prove we do not mutate observation values
    value_snapshot = df[["row_id", "value_original", "value_normalized"]].copy()

    profile = dataset_profile(df)
    coverage = indicator_coverage(df)
    temporal = temporal_coverage(df)
    stats = statistic_coverage(df)
    units = unit_inventory(df)
    anomalies = scale_anomaly_summary(df)
    spearman = median_spearman(df)
    readiness = modeling_readiness(df, units=units)

    # Confirm no mutation of source values during characterization
    compare = df[["row_id", "value_original", "value_normalized"]].merge(
        value_snapshot, on="row_id", suffixes=("", "_snap")
    )
    if not (
        compare["value_original"].equals(compare["value_original_snap"])
        and compare["value_normalized"].equals(compare["value_normalized_snap"])
    ):
        raise RuntimeError("Characterization mutated observation values")

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "dataset_profile": output_dir / "dataset_profile.json",
        "indicator_coverage": output_dir / "indicator_coverage.csv",
        "temporal_coverage": output_dir / "temporal_coverage.csv",
        "statistic_coverage": output_dir / "statistic_coverage.csv",
        "unit_inventory": output_dir / "unit_inventory.csv",
        "scale_anomaly_summary": output_dir / "scale_anomaly_summary.csv",
        "median_spearman": output_dir / "median_spearman.csv",
        "modeling_readiness": output_dir / "modeling_readiness.csv",
    }

    paths["dataset_profile"].write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    coverage.to_csv(paths["indicator_coverage"], index=False)
    temporal.to_csv(paths["temporal_coverage"], index=False)
    stats.to_csv(paths["statistic_coverage"], index=False)
    units.to_csv(paths["unit_inventory"], index=False)
    anomalies.to_csv(paths["scale_anomaly_summary"], index=False)
    spearman.to_csv(paths["median_spearman"], index=False)
    readiness.to_csv(paths["modeling_readiness"], index=False)

    save_provenance(
        ProvenanceRecord(
            source="Almyros normalized observations (characterization summaries)",
            source_url="https://github.com/hl7-eu/oah/tree/master/input/fsh/examples",
            retrieval_date=date.today(),
            original_filename_or_api=(
                f"{PROVENANCE_DATASET_ID} via data/processed/almyros/observations.csv"
            ),
            license="Derived from OAH FHIR IG source examples; same upstream terms.",
            data_class=DataClass.derived,
            processing_steps=[
                "Loaded Phase 2A long-format Almyros table (read-only values)",
                "Computed dataset profile, indicator/statistic/temporal coverage",
                "Inventoried units; summarized scale_anomaly without rewriting values",
                "Computed exploratory Spearman correlations on annual medians "
                f"(min overlap {MIN_OVERLAP_YEARS_SPEARMAN} years)",
                "Classified modeling readiness (candidate|limited|exclude) using median preference",
            ],
            preserves_original_values=True,
            notes=(
                f"characterization_version={CHARACTERIZATION_VERSION}; "
                f"input={PROVENANCE_DATASET_ID} transform={TRANSFORM_VERSION}. "
                "Summaries are derived analytics, not new observations. "
                "Spearman table is exploratory/descriptive, not causal or predictive. "
                "No risk scoring, imputation, or unit conversion in Phase 2B."
            ),
        ),
        provenance_path,
    )

    readiness_counts = {
        str(k): int(v) for k, v in readiness["readiness_class"].value_counts().items()
    }
    candidates = sorted(
        readiness.loc[readiness["readiness_class"] == "candidate", "indicator_id"].tolist()
    )
    limited = sorted(
        readiness.loc[readiness["readiness_class"] == "limited", "indicator_id"].tolist()
    )
    excluded = sorted(
        readiness.loc[readiness["readiness_class"] == "exclude", "indicator_id"].tolist()
    )

    return {
        "characterization_version": CHARACTERIZATION_VERSION,
        "row_count": profile["row_count"],
        "indicator_count": profile["indicator_count"],
        "scale_anomaly_rows": profile["scale_anomaly_rows"],
        "readiness_counts": readiness_counts,
        "candidates": candidates,
        "limited": limited,
        "excluded": excluded,
        "spearman_pair_count": int(len(spearman)),
        "output_dir": str(output_dir),
        "paths": {k: str(v) for k, v in paths.items()},
        "provenance_path": str(provenance_path),
        "input_csv": str(input_csv),
        "profile": profile,
        "readiness": readiness,
    }


def write_analysis_summary(summary: Dict[str, Any], path: Optional[Path] = None) -> Path:
    path = path or (REPO_ROOT / "analysis" / "almyros_characterization_summary.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = summary["profile"]
    lines = [
        "# Almyros characterization summary (Phase 2B)",
        "",
        f"- characterization_version: `{summary['characterization_version']}`",
        f"- input rows: **{summary['row_count']}**",
        f"- indicators: **{summary['indicator_count']}**",
        f"- scale_anomaly rows: **{summary['scale_anomaly_rows']}**",
        f"- years present: {profile['time_span']['years_present']}",
        f"- exploratory Spearman pairs (median, ≥{MIN_OVERLAP_YEARS_SPEARMAN} yrs): "
        f"**{summary['spearman_pair_count']}**",
        "",
        "## Modeling readiness (interpretive)",
        "",
        f"- **candidate** ({len(summary['candidates'])}): "
        + (", ".join(summary["candidates"]) if summary["candidates"] else "none"),
        f"- **limited** ({len(summary['limited'])}): "
        + (", ".join(summary["limited"]) if summary["limited"] else "none"),
        f"- **exclude** ({len(summary['excluded'])}): "
        + (", ".join(summary["excluded"]) if summary["excluded"] else "none"),
        "",
        "## Primary statistic rule",
        "",
        "- Prefer `median` for annual chemistry.",
        "- Never use `mean` / `minimum` / `maximum` as primary when designing the future engine "
        "while `scale_anomaly` remains unresolved.",
        "- Do not pool point samples with annual medians.",
        "",
        f"- output dir: `{summary['output_dir']}`",
        f"- provenance: `{summary['provenance_path']}`",
        "",
        "See `docs/DATA_CHARACTERIZATION.md`. No observation values were rewritten.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
