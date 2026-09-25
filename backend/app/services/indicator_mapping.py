"""Canonical indicator and unit mapping for Almyros OAH FHIR observations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class IndicatorSpec:
    indicator_id: str
    canonical_unit: Optional[str]
    notes: Optional[str] = None


# Raw FSH code.text / TemporaryOahSystem display → canonical id + preferred unit
INDICATOR_MAP: Dict[str, IndicatorSpec] = {
    "Water temperature": IndicatorSpec("water_temperature", "Cel"),
    "Temperature (water)": IndicatorSpec("water_temperature", "Cel"),
    "Conductivity": IndicatorSpec("electrical_conductivity", "uS/cm"),
    "Electrical conductivity": IndicatorSpec("electrical_conductivity", "uS/cm"),
    "Dissolved Oxygen": IndicatorSpec("dissolved_oxygen", "mg/L"),
    "pH": IndicatorSpec("ph", "pH"),
    "Nitrate": IndicatorSpec("nitrate", "mg/L"),
    "Nitrite": IndicatorSpec("nitrite", "mg/L"),
    "Ammonium": IndicatorSpec("ammonium", "mg/L"),
    "Total phosphates": IndicatorSpec("total_phosphates", "mg/L"),
    "Chloride": IndicatorSpec("chloride", "mg/L"),
    "Sulphate": IndicatorSpec("sulphate", "mg/L"),
    "Calcium": IndicatorSpec("calcium", "mg/L"),
    "Magnesium": IndicatorSpec("magnesium", "mg/L"),
    "Sodium": IndicatorSpec("sodium", "mg/L"),
    "Potassium": IndicatorSpec("potassium", "mg/L"),
    "Carbonates": IndicatorSpec("carbonates", "mg/L"),
    "Hydrogen carbonate (Bicarbonate) HCO3": IndicatorSpec("bicarbonate_hco3", "mg/L"),
    "Aluminium dissolved": IndicatorSpec("aluminium_dissolved", "ug/L"),
    "Arsenic dissolved": IndicatorSpec("arsenic_dissolved", "ug/L"),
    "Cadmium dissolved": IndicatorSpec("cadmium_dissolved", "ug/L"),
    "Chromium 6+": IndicatorSpec("chromium_6", "ug/L"),
    "Chromium dissolved": IndicatorSpec("chromium_dissolved", "ug/L"),
    "Copper dissolved": IndicatorSpec("copper_dissolved", "ug/L"),
    "Iron dissolved": IndicatorSpec("iron_dissolved", "ug/L"),
    "Lead dissolved": IndicatorSpec("lead_dissolved", "ug/L"),
    "Manganese dissolved": IndicatorSpec("manganese_dissolved", "ug/L"),
    "Mercury dissolved": IndicatorSpec("mercury_dissolved", "ug/L"),
    "Nickel dissolved": IndicatorSpec("nickel_dissolved", "ug/L"),
    "Zinc dissolved": IndicatorSpec("zinc_dissolved", "ug/L"),
}

# FHIR observation-statistics codes → StatisticType values
STATISTIC_CODE_MAP: Dict[str, str] = {
    "average": "mean",
    "mean": "mean",
    "median": "median",
    "minimum": "minimum",
    "maximum": "maximum",
    "std-dev": "std_dev",
    "std": "std_dev",
    "standard-deviation": "std_dev",
}

# Verified unit conversions only: (from_unit, to_unit) → (factor, conversion_id)
VERIFIED_UNIT_CONVERSIONS: Dict[Tuple[str, str], Tuple[float, str]] = {
    ("mS/cm", "uS/cm"): (1000.0, "mS/cm_to_uS/cm_x1000"),
}


def map_indicator(raw_name: str) -> IndicatorSpec:
    if raw_name not in INDICATOR_MAP:
        raise KeyError(f"Unmapped Almyros indicator name: {raw_name!r}")
    return INDICATOR_MAP[raw_name]


def map_statistic_code(code: str) -> str:
    if code not in STATISTIC_CODE_MAP:
        raise KeyError(f"Unknown statistic code: {code!r}")
    return STATISTIC_CODE_MAP[code]


def apply_verified_unit_conversion(
    value: Optional[float],
    unit_original: Optional[str],
    canonical_unit: Optional[str],
) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Return (value_normalized, unit_normalized, conversion_id).

    Only applies conversions listed in VERIFIED_UNIT_CONVERSIONS.
    Otherwise preserves originals unchanged.
    """
    if value is None:
        return None, unit_original, None
    if unit_original is None:
        return value, canonical_unit or unit_original, None
    if canonical_unit and unit_original == canonical_unit:
        return value, unit_original, None
    key = (unit_original, canonical_unit) if canonical_unit else None
    if key and key in VERIFIED_UNIT_CONVERSIONS:
        factor, conv_id = VERIFIED_UNIT_CONVERSIONS[key]
        return value * factor, canonical_unit, conv_id
    # No verified conversion: keep original unit (do not invent)
    return value, unit_original, None
