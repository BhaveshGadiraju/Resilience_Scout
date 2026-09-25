"""Provenance metadata for imported datasets."""

from __future__ import annotations

from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class DataClass(str, Enum):
    """How values relate to real-world measurements."""

    observed = "observed"
    derived = "derived"
    predicted = "predicted"
    simulated = "simulated"


class ProvenanceRecord(BaseModel):
    """Sidecar schema for every dataset under data/raw or data/processed."""

    source: str = Field(..., description="Human-readable source name")
    source_url: str = Field(..., description="Official source URL")
    retrieval_date: date
    original_filename_or_api: str
    license: Optional[str] = None
    data_class: DataClass
    processing_steps: List[str] = Field(default_factory=list)
    preserves_original_values: bool = True
    notes: Optional[str] = None

    @field_validator("source_url")
    @classmethod
    def url_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_url must be non-empty")
        return v.strip()

    def to_yaml_dict(self) -> Dict[str, Any]:
        payload = self.model_dump(mode="json")
        payload["data_class"] = self.data_class.value
        payload["retrieval_date"] = self.retrieval_date.isoformat()
        return payload


def load_provenance(path: Path) -> ProvenanceRecord:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Provenance file must be a mapping: {path}")
    return ProvenanceRecord.model_validate(data)


def save_provenance(record: ProvenanceRecord, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            record.to_yaml_dict(),
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
