"""Dataset inspection helpers for local files under data/raw/."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def _is_fhir_observation(obj: dict[str, Any]) -> bool:
    return obj.get("resourceType") == "Observation"


def _parse_fhir_effective(obs: dict[str, Any]) -> str | None:
    if "effectiveDateTime" in obs:
        return str(obs["effectiveDateTime"])
    period = obs.get("effectivePeriod") or {}
    start = period.get("start")
    end = period.get("end")
    if start and end:
        return f"{start}/{end}"
    return start or end


def _fhir_indicator(obs: dict[str, Any]) -> str | None:
    coding = (obs.get("code") or {}).get("coding") or []
    if coding:
        display = coding[0].get("display") or coding[0].get("code")
        if display:
            return str(display)
    text = (obs.get("code") or {}).get("text")
    return str(text) if text else None


def _fhir_site(obs: dict[str, Any]) -> str | None:
    subject = obs.get("subject") or {}
    if subject.get("display"):
        return str(subject["display"])
    if subject.get("reference"):
        return str(subject["reference"])
    return None


def _fhir_numeric_values(obs: dict[str, Any]) -> list[float]:
    values: list[float] = []
    qty = obs.get("valueQuantity") or {}
    if "value" in qty:
        try:
            values.append(float(qty["value"]))
        except (TypeError, ValueError):
            pass
    for comp in obs.get("component") or []:
        cq = comp.get("valueQuantity") or {}
        if "value" in cq:
            try:
                values.append(float(cq["value"]))
            except (TypeError, ValueError):
                pass
    return values


def load_fhir_observations(path: Path) -> list[dict[str, Any]]:
    """Load Observation resources from a JSON file or directory of JSON files."""
    files: list[Path]
    if path.is_file():
        files = [path]
    else:
        files = sorted(path.rglob("*.json"))

    observations: list[dict[str, Any]] = []
    for fp in files:
        try:
            with fp.open(encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and _is_fhir_observation(data):
            observations.append(data)
        elif isinstance(data, dict) and data.get("resourceType") == "Bundle":
            for entry in data.get("entry") or []:
                res = (entry or {}).get("resource") or {}
                if _is_fhir_observation(res):
                    observations.append(res)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and _is_fhir_observation(item):
                    observations.append(item)
    return observations


def fhir_observations_to_records(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for obs in observations:
        records.append(
            {
                "id": obs.get("id"),
                "indicator": _fhir_indicator(obs),
                "site": _fhir_site(obs),
                "effective": _parse_fhir_effective(obs),
                "status": obs.get("status"),
                "numeric_values": _fhir_numeric_values(obs),
            }
        )
    return records


def _infer_temporal_frequency(dates: list[pd.Timestamp]) -> str | None:
    if len(dates) < 2:
        return None
    sorted_dates = sorted(dates)
    deltas = [
        (sorted_dates[i] - sorted_dates[i - 1]).days
        for i in range(1, len(sorted_dates))
        if (sorted_dates[i] - sorted_dates[i - 1]).days > 0
    ]
    if not deltas:
        return "unknown_or_overlapping"
    median_days = sorted(deltas)[len(deltas) // 2]
    if 350 <= median_days <= 400:
        return "approx_annual"
    if 25 <= median_days <= 40:
        return "approx_monthly"
    if 5 <= median_days <= 10:
        return "approx_weekly"
    if median_days <= 2:
        return "approx_daily"
    return f"median_gap_days_{median_days}"


def inspect_dataframe(df: pd.DataFrame, site_cols: list[str] | None = None,
                      indicator_cols: list[str] | None = None,
                      date_cols: list[str] | None = None) -> dict[str, Any]:
    """Inspect a tabular dataset."""
    site_cols = site_cols or [c for c in ("site", "location", "subject") if c in df.columns]
    indicator_cols = indicator_cols or [
        c for c in ("indicator", "parameter", "code", "variable") if c in df.columns
    ]
    date_cols = date_cols or [
        c
        for c in df.columns
        if c.lower() in {"date", "effective", "effectivedatetime", "datetime", "timestamp"}
        or c.lower().startswith("effective")
        or c.lower().endswith("_date")
        or c.lower().endswith("date")
    ]

    missing = {col: int(df[col].isna().sum()) for col in df.columns}
    numeric = df.select_dtypes(include="number")
    numeric_ranges = {
        col: {"min": float(numeric[col].min()), "max": float(numeric[col].max())}
        for col in numeric.columns
        if numeric[col].notna().any()
    }

    unique_sites: list[Any] = []
    for col in site_cols:
        unique_sites.extend(df[col].dropna().unique().tolist())
    unique_sites = sorted({str(s) for s in unique_sites})

    unique_indicators: list[Any] = []
    for col in indicator_cols:
        unique_indicators.extend(df[col].dropna().unique().tolist())
    unique_indicators = sorted({str(i) for i in unique_indicators})

    min_date = max_date = None
    frequency = None
    parsed_dates: list[pd.Timestamp] = []
    for col in date_cols:
        series = pd.to_datetime(df[col], errors="coerce", utc=True)
        parsed_dates.extend(series.dropna().tolist())
    if parsed_dates:
        min_date = min(parsed_dates).isoformat()
        max_date = max(parsed_dates).isoformat()
        frequency = _infer_temporal_frequency(parsed_dates)

    dup_count = int(df.duplicated().sum())

    return {
        "row_count": int(len(df)),
        "column_names": list(df.columns),
        "missing_values": missing,
        "unique_sites": unique_sites,
        "indicators": unique_indicators,
        "min_date": min_date,
        "max_date": max_date,
        "temporal_frequency": frequency,
        "numeric_ranges": numeric_ranges,
        "duplicate_records": dup_count,
    }


def inspect_fhir_path(path: Path) -> dict[str, Any]:
    observations = load_fhir_observations(path)
    records = fhir_observations_to_records(observations)
    if not records:
        return {
            "format": "fhir_observation",
            "row_count": 0,
            "column_names": [],
            "missing_values": {},
            "unique_sites": [],
            "indicators": [],
            "min_date": None,
            "max_date": None,
            "temporal_frequency": None,
            "numeric_ranges": {},
            "duplicate_records": 0,
            "resource_count": 0,
        }

    df = pd.DataFrame(records)
    # Expand first numeric for range summary
    df["first_numeric"] = df["numeric_values"].apply(
        lambda xs: xs[0] if isinstance(xs, list) and xs else None
    )
    report = inspect_dataframe(
        df.drop(columns=["numeric_values"]),
        site_cols=["site"],
        indicator_cols=["indicator"],
        date_cols=["effective"],
    )
    report["format"] = "fhir_observation"
    report["resource_count"] = len(observations)
    # Duplicate by id if present
    if "id" in df.columns:
        report["duplicate_records"] = int(df["id"].duplicated().sum())
    return report


def inspect_csv(path: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    report = inspect_dataframe(df)
    report["format"] = "csv"
    return report


def inspect_json_table(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        df = pd.DataFrame(data)
        report = inspect_dataframe(df)
        report["format"] = "json_records"
        return report
    if isinstance(data, dict) and _is_fhir_observation(data):
        return inspect_fhir_path(path)
    raise ValueError(f"Unsupported JSON structure for inspection: {path}")


def inspect_path(path: Path) -> dict[str, Any]:
    """Inspect a file or directory; prefer FHIR if Observations found."""
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    if path.is_dir():
        fhir_report = inspect_fhir_path(path)
        if fhir_report.get("resource_count", 0) > 0:
            fhir_report["path"] = str(path)
            return fhir_report
        csvs = list(path.rglob("*.csv"))
        if csvs:
            report = inspect_csv(csvs[0])
            report["path"] = str(csvs[0])
            report["note"] = f"Inspected first CSV of {len(csvs)} found"
            return report
        raise ValueError(f"No FHIR Observations or CSV files found under {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        report = inspect_csv(path)
    elif suffix == ".json":
        # Try FHIR first
        fhir_report = inspect_fhir_path(path)
        if fhir_report.get("resource_count", 0) > 0:
            report = fhir_report
        else:
            report = inspect_json_table(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    report["path"] = str(path)
    return report


def format_report(report: dict[str, Any]) -> str:
    lines = [
        f"path: {report.get('path', '')}",
        f"format: {report.get('format', 'unknown')}",
        f"row_count: {report.get('row_count')}",
        f"resource_count: {report.get('resource_count', report.get('row_count'))}",
        f"columns: {report.get('column_names')}",
        f"missing_values: {report.get('missing_values')}",
        f"unique_sites ({len(report.get('unique_sites') or [])}): {report.get('unique_sites')}",
        f"indicators ({len(report.get('indicators') or [])}): {report.get('indicators')}",
        f"min_date: {report.get('min_date')}",
        f"max_date: {report.get('max_date')}",
        f"temporal_frequency: {report.get('temporal_frequency')}",
        f"numeric_ranges: {report.get('numeric_ranges')}",
        f"duplicate_records: {report.get('duplicate_records')}",
    ]
    if report.get("note"):
        lines.append(f"note: {report['note']}")
    return "\n".join(lines)
