# DATA CHARACTERIZATION — Almyros (Phase 2B)

**Characterization version:** `2b.1`  
**Input:** `almyros_normalized_v1` (`data/processed/almyros/observations.*`, transform `2a.1`)  
**Scope:** Characterize structure, coverage, quality flags, descriptive median relationships, and modeling readiness. No decision engine, scoring, prediction, or dashboard.

---

## 1. Purpose

Determine what the **normalized Almyros table** actually supports before designing the Scout quantitative engine.

This phase answers:

- What is in the table (profile, coverage, units)?
- Where are gaps and quality issues?
- Which indicators are reasonable **candidates** vs **limited** vs **exclude** for future engine design?

It does **not** claim scientific validation of measurements, causal relationships, or readiness for operational early-warning deployment.

---

## 2. Methods

| Analysis | Method | Notes |
|----------|--------|-------|
| Dataset profile | Counts of rows, kinds, statistics, years | VERIFIED from input table |
| Indicator / temporal coverage | `indicator × year × statistic_type` presence | Absent component = no row (structural missingness; not imputed) |
| Statistic coverage | Per `source_observation_id` present/missing companions | Reuses Phase 2A `quality_flags` |
| Units | Distinct `unit_original` / `unit_normalized` per indicator | Flag multi-unit inconsistency |
| Scale anomalies | Row/obs counts; recompute `|mean|/|median|` where both exist | Values **never** rewritten |
| Relationships | Spearman ρ on **annual medians** only; require ≥4 overlapping years | Exploratory / descriptive — **not** causal or predictive |
| Modeling readiness | Rule-based `candidate` \| `limited` \| `exclude` | Interpretive judgment with explicit rules |

**Primary statistic for annual chemistry:** `median` (per Phase 1 audit and Phase 2A docs).  
**Never primary:** `mean`, `minimum`, `maximum` while `scale_anomaly` remains unresolved.  
**Point samples:** characterized separately; not pooled with annual medians.

Implementation: `backend/app/services/characterize_almyros.py`  
CLI: `scripts/characterize_almyros.py`

---

## 3. VERIFIED structure (from Phase 2A table)

| Metric | Value |
|--------|-------|
| Rows | **587** |
| Source observations | **135** |
| Indicators | **28** |
| Annual summary rows | **583** |
| Point sample rows | **4** |
| Years present | 2013, 2014, 2015, 2018, 2019, 2020, 2024, 2025 |
| `scale_anomaly` rows | **448** |
| `missing_companion_stats` rows | **11** (3 annual observations lack median among expected companions) |
| Statistic counts | mean/min/max 131 each; median 128; std_dev 62; point 4 |

**Units:** All indicators have a single `unit_normalized` value. Electrical conductivity retains dual originals (`mS/cm` + `uS/cm`) but normalized to `uS/cm` via verified Phase 2A conversion only.

**Geographic / corpus boundaries:** Almyros (`Loc-Almyros`) only. No Resilience Map or Giofyros merge.

---

## 4. Temporal and missingness patterns

- Annual chemistry concentrates in **2013–2015** and **2018–2020** (gap **2016–2017**).
- Point samples are **2024-11-21** and **2025-04-14** for water temperature and conductivity only (2 dates × 2 indicators = 4 rows).
- Uneven longevity: e.g. zinc only 2013–2014 medians; several major ions / phosphates / bicarbonate only 2018–2020; pH medians only 2013–2015 (later years lack median components).
- Missingness is **structural**: if a FSH component was absent, Phase 2A emitted no row. Characterization does not invent years or statistics.

---

## 5. Scale anomalies

- **448 / 587** rows carry `scale_anomaly` (`|mean|/|median| ≥ 10` on the source observation).
- **101** annual observations are flagged.
- For many indicators the median of `|mean|/|median|` is on the order of **10³–10⁴** under the same UCUM code (e.g. DO, chloride, nitrate).
- Indicators with **no** scale-anomaly rows in this corpus include: ammonium, carbonates, mercury_dissolved, nitrite, total_phosphates (others may still need median preference for consistency).
- **Action for future phases:** use **median** series; do not “fix” mean/min/max; do not treat flagged companions as validated until OAH clarifies.

---

## 6. Descriptive relationships (exploratory)

- **171** indicator pairs with ≥4 overlapping annual-median years.
- Correlations are labeled `exploratory_descriptive_not_causal` in `median_spearman.csv`.
- Small *n* (often 4–6 years) ⇒ ranks are fragile; do not use as predictive models or causal claims.
- Examples of strong |ρ| in this sample (illustrative only): chloride–electrical_conductivity; ammonium–nitrite; dissolved_oxygen–nitrate (negative). Treat as hypotheses for later work, not validated ecology.

---

## 7. Modeling readiness rules (interpretive)

| Class | Rule |
|-------|------|
| **candidate** | ≥4 annual median years; consistent `unit_normalized`; usable without treating mean/min/max as primary |
| **limited** | 1–3 annual median years (short span), or point-only sparse samples |
| **exclude** | No usable median series and insufficient point depth, or inconsistent normalized units |

`primary_statistic` is always `median`, `point`, or `none` — **never** mean/min/max.

### Results (`2b.1`)

**Candidate (19):** aluminium_dissolved, ammonium, arsenic_dissolved, cadmium_dissolved, chloride, chromium_6, chromium_dissolved, copper_dissolved, dissolved_oxygen, electrical_conductivity, iron_dissolved, lead_dissolved, manganese_dissolved, mercury_dissolved, nickel_dissolved, nitrate, nitrite, sulphate, water_temperature

**Limited (9):** bicarbonate_hco3, calcium, carbonates, magnesium, ph, potassium, sodium, total_phosphates, zinc_dissolved

**Exclude (0):** none under current rules (all indicators have at least a short median series)

---

## 8. Outputs and provenance

| Artifact | Path |
|----------|------|
| Profile | `data/processed/almyros/characterization/dataset_profile.json` |
| Coverage / temporal / stats / units / anomalies / Spearman / readiness | `data/processed/almyros/characterization/*.csv` |
| Provenance | `data/provenance/almyros_characterization.yaml` (`data_class: derived`) |
| Short summary | `analysis/almyros_characterization_summary.md` |

Chain:

```
OAH FSH (observed raw)
  → almyros_normalized_v1 (derived, 2A)
  → characterization summaries (derived, 2B)
```

---

## 9. Limitations and non-claims

- No scientific validation of measurement quality beyond flagging.
- Spearman results are not causal, not predictive, and not information-gain scores.
- Candidate ≠ approved for operational early warning.
- Does not implement risk, anomaly detection models, uncertainty, ranking, simulation, UI, or LLM.
- Does not join other OAH corpora.

---

## How to run

```bash
source .venv/bin/activate
python scripts/characterize_almyros.py
pytest
```
