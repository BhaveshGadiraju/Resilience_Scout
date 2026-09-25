"""Pydantic schemas for Phase 2A normalized Almyros observations."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.provenance import DataClass


class ObservationKind(str, Enum):
    point_sample = "point_sample"
    annual_summary = "annual_summary"


class StatisticType(str, Enum):
    point = "point"
    mean = "mean"
    median = "median"
    minimum = "minimum"
    maximum = "maximum"
    std_dev = "std_dev"


class TimePrecision(str, Enum):
    day = "day"
    year = "year"


TRANSFORM_VERSION = "2a.1"
PROVENANCE_DATASET_ID = "almyros_normalized_v1"


class NormalizedObservation(BaseModel):
    """One measured quantity: a point value or one annual-summary statistic."""

    row_id: str
    source_observation_id: str
    source_file: str
    site_id: str
    indicator_id: str
    indicator_name_raw: str
    observation_kind: ObservationKind
    statistic_type: StatisticType
    time_start: date
    time_end: Optional[date] = None
    time_precision: TimePrecision
    value_original: Optional[float] = None
    unit_original: Optional[str] = None
    value_normalized: Optional[float] = None
    unit_normalized: Optional[str] = None
    unit_conversion_applied: Optional[str] = None
    data_class: DataClass = DataClass.derived
    quality_flags: Optional[str] = None
    provenance_dataset_id: str = PROVENANCE_DATASET_ID
    transform_version: str = TRANSFORM_VERSION

    @field_validator("source_observation_id", "source_file", "site_id", "indicator_id", "indicator_name_raw")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("required string field must be non-empty")
        return str(v).strip()

    @model_validator(mode="after")
    def kind_statistic_consistency(self) -> "NormalizedObservation":
        if self.observation_kind == ObservationKind.point_sample:
            if self.statistic_type != StatisticType.point:
                raise ValueError("point_sample rows must use statistic_type=point")
            if self.time_end is not None:
                raise ValueError("point_sample rows must have time_end=null")
            if self.time_precision != TimePrecision.day:
                raise ValueError("point_sample rows must use time_precision=day")
        if self.observation_kind == ObservationKind.annual_summary:
            if self.statistic_type == StatisticType.point:
                raise ValueError("annual_summary rows cannot use statistic_type=point")
            if self.time_end is None:
                raise ValueError("annual_summary rows require time_end")
            if self.time_precision != TimePrecision.year:
                raise ValueError("annual_summary rows must use time_precision=year")
        if self.data_class != DataClass.derived:
            raise ValueError("normalized table rows must be data_class=derived")
        return self


class ParsedComponent(BaseModel):
    """One statistic component extracted from an FSH Observation."""

    statistic_code: str  # average | median | maximum | minimum | std-dev
    value: Optional[float] = None
    unit: Optional[str] = None


class ParsedObservation(BaseModel):
    """Structured Observation before long-format expansion."""

    source_observation_id: str
    source_file: str
    site_id: Optional[str] = None
    indicator_name_raw: Optional[str] = None
    status: Optional[str] = None
    effective_datetime: Optional[date] = None
    effective_period_start: Optional[date] = None
    effective_period_end: Optional[date] = None
    value_quantity: Optional[float] = None
    value_unit: Optional[str] = None
    components: List[ParsedComponent] = Field(default_factory=list)
