"""Validate and load the indicator registry YAML."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class IndicatorRecord(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    OAH_framework_reference: Optional[str] = None
    available_sites: Optional[List[str]] = None
    temporal_resolution: Optional[str] = None
    observation_type: Optional[str] = None
    candidate_for_next_observation: Optional[bool] = None
    notes: Optional[str] = None


class IndicatorRegistry(BaseModel):
    version: str = "0.1.0"
    indicators: List[IndicatorRecord] = Field(default_factory=list)


def load_indicator_registry(path: Path) -> IndicatorRegistry:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return IndicatorRegistry()
    if isinstance(data, list):
        return IndicatorRegistry(indicators=[IndicatorRecord.model_validate(i) for i in data])
    return IndicatorRegistry.model_validate(data)
