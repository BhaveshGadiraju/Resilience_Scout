"""Annual-median panel loader for the Almyros core panel (Phase 3B, Feature 1).

Reads data/processed/almyros/observations.csv (Phase 2A output). Uses ONLY
annual_summary rows with statistic_type == "median". Never mean/min/max, never
point samples (2024-2025). No imputation: missing stays NaN.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

CORE_INDICATORS: tuple[str, ...] = (
    "ammonium",
    "chloride",
    "dissolved_oxygen",
    "electrical_conductivity",
    "nitrate",
    "nitrite",
    "sulphate",
    "water_temperature",
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OBSERVATIONS_PATH = (
    REPO_ROOT / "data" / "processed" / "almyros" / "observations.csv"
)
REQUIRED_COLUMNS = {
    "indicator_id",
    "observation_kind",
    "statistic_type",
    "time_start",
    "value_original",
    "value_normalized",
}


@dataclass(frozen=True, eq=False)
class AnnualPanel:
    """Year x indicator matrix of annual medians in ORIGINAL (normalized-unit) scale."""

    years: tuple[int, ...]
    indicators: tuple[str, ...]
    values: np.ndarray  # shape (n_years, d); NaN = not published
    units: dict

    def complete_years(self) -> tuple[int, ...]:
        return tuple(
            y for y, row in zip(self.years, self.values) if not np.isnan(row).any()
        )

    def matrix(self, years) -> np.ndarray:
        idx = [self.years.index(y) for y in years]
        return self.values[idx]


def load_annual_median_panel(
    path: Path | str | None = None,
    indicators: tuple[str, ...] = CORE_INDICATORS,
) -> AnnualPanel:
    path = Path(path) if path else DEFAULT_OBSERVATIONS_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python scripts/normalize_almyros.py"
        )
    df = pd.read_csv(path)
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"observations table missing columns: {sorted(missing_cols)}")
    if "site_id" in df.columns and not (df["site_id"] == "Loc-Almyros").all():
        raise ValueError("non-Almyros rows present; refusing to mix sites")

    sel = df[
        (df["observation_kind"] == "annual_summary")
        & (df["statistic_type"] == "median")
        & (df["indicator_id"].isin(indicators))
    ].copy()
    sel["year"] = sel["time_start"].astype(str).str[:4].astype(int)
    sel["value"] = pd.to_numeric(
        sel["value_normalized"].where(
            sel["value_normalized"].notna(), sel["value_original"]
        ),
        errors="coerce",
    )
    sel = sel[sel["value"].notna()]
    dup = sel.duplicated(["year", "indicator_id"], keep=False)
    if dup.any():
        raise ValueError(
            "duplicate annual medians for: "
            f"{sel[dup][['year', 'indicator_id']].drop_duplicates().values.tolist()}"
        )

    wide = sel.pivot(index="year", columns="indicator_id", values="value")
    wide = wide.reindex(columns=list(indicators)).sort_index()

    units: dict = {}
    for ind in indicators:
        sub = sel[sel["indicator_id"] == ind]
        col = "unit_normalized" if "unit_normalized" in sub.columns else "unit_original"
        vals = sub[col].dropna().unique().tolist() if col in sub.columns else []
        units[ind] = vals[0] if len(vals) == 1 else (vals or None)

    return AnnualPanel(
        years=tuple(int(y) for y in wide.index),
        indicators=tuple(indicators),
        values=wide.to_numpy(dtype=float),
        units=units,
    )