# DATA NORMALIZATION — Almyros (Phase 2A)

**Transform version:** `2a.1`  
**Dataset id:** `almyros_normalized_v1`  
**Scope:** Almyros aquatic OAH FHIR observations only. No recommendation engine, scoring, or dashboard.

---

## 1. Source schema

**Immutable inputs** (read-only):

| File | Role |
|------|------|
| `data/raw/oah_fhir_ig_examples/github_fsh/almyros_gov_chem.fsh` | Annual government chemical summaries |
| `data/raw/oah_fhir_ig_examples/github_fsh/water_tmp.fsh` | Point water temperature (Almyros rows) |
| `data/raw/oah_fhir_ig_examples/github_fsh/ec_tmp.fsh` | Point conductivity (Almyros rows) |

**Upstream:** [hl7-eu/oah FSH examples](https://github.com/hl7-eu/oah/tree/master/input/fsh/examples).

### FHIR Shorthand Observation shapes

**Point sample** (`ObservationIndicatorsOah`):

- `effectiveDateTime`
- `valueQuantity` (single numeric + UCUM unit)
- `subject = Reference(Loc-Almyros)`

**Annual summary** (`ObservationWithCompOah`):

- `effectivePeriod.start` / `effectivePeriod.end` (calendar year)
- Components with `observation-statistics#` codes:
  - `average` → mean
  - `median`
  - `minimum`
  - `maximum`
  - `std-dev` (when present)

**Important:** The Phase 1 file `data/processed/oah_fhir_observation_inventory.csv` only retained medians/point values. It is **not** the Phase 2A source of truth.

---

## 2. Target schema

**Outputs:**

- `data/processed/almyros/observations.csv`
- `data/processed/almyros/observations.parquet` (when pyarrow available)
- Provenance: `data/provenance/almyros_normalized.yaml`

**Grain:** one row = one measured quantity (point value **or** one summary statistic).

| Column | Description |
|--------|-------------|
| `row_id` | `{source_observation_id}::{statistic_type}` |
| `source_observation_id` | FSH Instance id |
| `source_file` | Origin `.fsh` filename |
| `site_id` | Always `Loc-Almyros` in this dataset |
| `indicator_id` | Canonical id (see mapping) |
| `indicator_name_raw` | Exact FSH indicator text |
| `observation_kind` | `point_sample` \| `annual_summary` |
| `statistic_type` | `point` \| `mean` \| `median` \| `minimum` \| `maximum` \| `std_dev` |
| `time_start` / `time_end` | ISO dates; `time_end` null for points |
| `time_precision` | `day` \| `year` |
| `value_original` / `unit_original` | Literals from FSH |
| `value_normalized` / `unit_normalized` | After verified conversion only |
| `unit_conversion_applied` | Conversion id or null |
| `data_class` | Always `derived` |
| `quality_flags` | Pipe-separated flags or null |
| `provenance_dataset_id` | `almyros_normalized_v1` |
| `transform_version` | `2a.1` |

---

## 3. Transformations

1. Parse FSH Observation instances (all components).
2. Filter `subject == Loc-Almyros`.
3. Expand each observation into long-format statistic rows.
4. Map `indicator_name_raw` → `indicator_id`.
5. Apply verified unit conversion (conductivity only).
6. Attach quality flags (no value rewriting).
7. Write processed table + provenance sidecar.

**Not done:** interpolation, year-gap filling, merging mean/median into one “value”, ResMap/Giofyros joins, anomaly models.

---

## 4. Unit conversions

| From | To | Factor | Id | When |
|------|----|--------|-----|------|
| `mS/cm` | `uS/cm` | ×1000 | `mS/cm_to_uS/cm_x1000` | Conductivity point samples → canonical `electrical_conductivity` |

All other units are preserved as published (`ug/L`, `mg/L`, `Cel`, `uS/cm`, empty pH units → normalized unit `pH` when original empty).

**Never:** silent `ug/L` ↔ `mg/L` conversion; never rescale anomalous averages to match medians.

---

## 5. Timestamp handling

| Kind | `time_start` | `time_end` | `time_precision` |
|------|--------------|------------|------------------|
| Point | `effectiveDateTime` | null | `day` |
| Annual | period start | period end | `year` |

No timezone conversion (source dates are calendar dates).

---

## 6. Statistic handling

| FSH code | `statistic_type` |
|----------|------------------|
| *(valueQuantity)* | `point` |
| `average` | `mean` |
| `median` | `median` |
| `minimum` | `minimum` |
| `maximum` | `maximum` |
| `std-dev` | `std_dev` |

Statistics remain **distinguishable**. Downstream analysis must filter by `statistic_type` (e.g. prefer `median` for annual chemistry until scale issues are resolved by OAH).

---

## 7. Missing-value handling

- Component absent in source → **no row** (not invented).
- Example: pH 2018–2020 lack `median` → only mean/min/max/(std_dev) rows.
- Empty UCUM string in FSH → `unit_original = null`.
- Numeric missing only if parse fails (should not occur for verified examples).

---

## 8. Invalid / anomalous values

| Flag | Rule | Action |
|------|------|--------|
| `scale_anomaly` | For an observation, `\|mean\| / \|median\| ≥ 10` (median ≠ 0) | Flag **all** rows of that observation; **do not** change numbers |
| `missing_companion_stats` | Annual summary missing one of average/max/min/median | Flag; still emit present components |

Known issue (Phase 1 audit): many annual avg/max/min values are orders of magnitude larger than medians under the same UCUM code. Treat as data quality, not as a conversion bug.

---

## 9. Provenance

Chain:

```
GitHub OAH FSH (observed raw)
  → data/raw/.../github_fsh/*.fsh
  → parse + expand + map + verified convert
  → data/processed/almyros/observations.* (derived)
```

Row traceability: `source_observation_id` + `source_file` + `transform_version`.  
Dataset sidecar: `data/provenance/almyros_normalized.yaml` (`data_class: derived`).

Raw provenance remains `observed` (`data/provenance/oah_fhir_ig_examples.yaml`).

---

## 10. Known limitations

- Year coverage is uneven (e.g. Zinc 2013–2014 only; several ions 2018–2020 only).
- `Water temperature` (point) and `Temperature (water)` (annual) share `indicator_id=water_temperature` but differ in `observation_kind` / `statistic_type`.
- Conductivity point vs annual originally used `mS/cm` vs `uS/cm`; normalized to `uS/cm` for points only via verified factor.
- pH annual components often lack median and use empty units with large numeric literals (scale_anomaly likely).
- Published FHIR IG HTML/JSON package was 404 at Phase 1 audit; FSH remains authoritative.
- No scientific validation of measurement quality beyond flagging.

---

## How to run

```bash
source .venv/bin/activate
python scripts/normalize_almyros.py
pytest
```

Implementation: `backend/app/services/normalize_almyros.py`, `fsh_observation_parser.py`, `indicator_mapping.py`.
