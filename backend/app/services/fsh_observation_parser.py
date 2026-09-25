"""Parse OAH FHIR Shorthand Observation instances, preserving all statistics."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Optional

from app.schemas.normalized_observation import ParsedComponent, ParsedObservation

_INSTANCE_SPLIT = re.compile(r"\n(?=Instance:)")
_OBS_PROFILES = (
    "ObservationWithCompOah",
    "ObservationIndicatorsOah",
    "InstanceOf: Observation",
)


def _parse_date(text: Optional[str]) -> Optional[date]:
    if not text:
        return None
    text = text.strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    if len(text) >= 7 and text[4] == "-":
        return datetime.strptime(text[:7], "%Y-%m").date()
    if len(text) >= 4 and text[:4].isdigit():
        return datetime.strptime(text[:4], "%Y").date()
    return None


def _is_observation_block(block: str) -> bool:
    if not block.strip().startswith("Instance:"):
        return False
    if re.search(r"^InstanceOf:\s*(Device|Location|Library|Group)\b", block, re.M):
        return False
    return any(p in block for p in _OBS_PROFILES)


def _extract_components(block: str) -> List[ParsedComponent]:
    """
    Parse component statistics from FSH.

    Pattern (typical):
      * component[+].code = http://.../observation-statistics#average "Average"
      * component[=].valueQuantity = 50000 'ug/L' "microgram per liter"

    Units may be empty (e.g. pH: 76800 '' "").
    """
    components: List[ParsedComponent] = []
    code_iter = list(
        re.finditer(
            r"\* component(?:\[\+\]|\[=\])\.code = [^\n]*?#([\w-]+)[^\n]*\n"
            r"\* component\[=\]\.valueQuantity = ([0-9.eE+-]+) '([^']*)'",
            block,
        )
    )
    for m in code_iter:
        unit = m.group(3)
        components.append(
            ParsedComponent(
                statistic_code=m.group(1),
                value=float(m.group(2)),
                unit=unit if unit != "" else None,
            )
        )
    return components


def parse_observation_block(block: str, source_file: str) -> Optional[ParsedObservation]:
    if not _is_observation_block(block):
        return None

    m_id = re.search(r"^Instance:\s*(\S+)", block, re.M)
    if not m_id:
        return None

    m_code_text = re.search(r'\* code\.text = "([^"]+)"', block)
    m_code_display = re.search(r'TemporaryOahSystem#[^\s]+ "([^"]+)"', block)
    indicator = (
        m_code_text.group(1)
        if m_code_text
        else (m_code_display.group(1) if m_code_display else None)
    )

    m_subj = re.search(r"\* subject = Reference\(([^)]+)\)", block)
    m_status = re.search(r"\* status = #(\w+)", block)
    m_eff = re.search(r'\* effectiveDateTime = "([^"]+)"', block)
    m_start = re.search(r'\* effectivePeriod\.start = "([^"]+)"', block)
    m_end = re.search(r'\* effectivePeriod\.end = "([^"]+)"', block)
    m_val = re.search(r"\* valueQuantity = ([0-9.eE+-]+) '([^']+)'", block)

    return ParsedObservation(
        source_observation_id=m_id.group(1),
        source_file=source_file,
        site_id=m_subj.group(1).strip() if m_subj else None,
        indicator_name_raw=indicator,
        status=m_status.group(1) if m_status else None,
        effective_datetime=_parse_date(m_eff.group(1) if m_eff else None),
        effective_period_start=_parse_date(m_start.group(1) if m_start else None),
        effective_period_end=_parse_date(m_end.group(1) if m_end else None),
        value_quantity=float(m_val.group(1)) if m_val else None,
        value_unit=m_val.group(2) if m_val else None,
        components=_extract_components(block),
    )


def parse_fsh_file(path: Path) -> List[ParsedObservation]:
    text = path.read_text(encoding="utf-8")
    results: List[ParsedObservation] = []
    for block in _INSTANCE_SPLIT.split(text):
        obs = parse_observation_block(block, path.name)
        if obs is not None:
            results.append(obs)
    return results


def parse_fsh_paths(paths: Iterable[Path]) -> List[ParsedObservation]:
    out: List[ParsedObservation] = []
    for path in paths:
        out.extend(parse_fsh_file(path))
    return out


def filter_site(observations: Iterable[ParsedObservation], site_id: str) -> List[ParsedObservation]:
    return [o for o in observations if o.site_id == site_id]
