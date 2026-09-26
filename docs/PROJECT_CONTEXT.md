# PROJECT_CONTEXT.md — Resilience Scout

Persistent handoff document for future Cursor agents.

**Last updated:** after Phase 3A completion.  
**Do not treat future features as implemented.** Read this file together with `AGENTS.md` before any work.

---

# 1. Project

**Name:** Resilience Scout

**Purpose:** Resilience Scout is a hackathon project for the IEEE OneAquaHealth (OAH) Global Hackathon 2026, aimed at **Track 6 — Resilience Informatics**. The intended product is an adaptive environmental decision-support concept that helps identify which environmental observation or measurement would provide the greatest useful information for understanding potential ecosystem stress and resilience, in support of early warning and resilience planning.

**Core concept (intended):** Use **real OAH environmental data** and a **quantitative decision engine** to recommend a next-best observation. An LLM, if used later, may only **explain** quantitative results—it must not select the recommendation.

**Implemented today:** Project foundation, OAH data audit, Almyros normalization + characterization, Scout **mathematical specification** (Phase 3A docs), provenance, indicator registry, inspection/normalize/characterize scripts, and tests.  
**Not implemented:** recommendation engine runtime, dashboard, simulation loop, risk/uncertainty scoring code, or LLM explanation layer.

---

# 2. Hackathon

**Event:** OneAquaHealth Global Hackathon 2026 (IEEE / OneAquaHealth ecosystem).

**Track:** Track 6 — Resilience Informatics

**Challenge:** Enable early warning and resilience planning.

**Expected solution types include:**

- predictive dashboards
- alerts
- resilience tools
- predictive environmental tools (track framing)

**Judging criteria (as used in project planning):**

| Criterion | Weight |
|-----------|--------|
| Impact & Alignment with OneAquaHealth mission | 30% |
| Innovation & Creativity | 20% |
| Technical Implementation | 20% |
| Usability & User Experience | 15% |
| Feasibility & Scalability | 15% |

**Submission requirements (as used in project planning):**

- track alignment
- project description
- 3–5 minute demo video
- public code repository
- working prototype / mockup / proof of concept
- submission before deadline

The project does **not** require a physical product.

Public OAH digital assets referenced during Phase 1 include the Citizen Science App, Resilience Map, Diptera Forecasting App, City Dashboards, GEOSSIP, Health Assessment Framework materials, and the OAH FHIR Implementation Guide. Only some of these have verified reusable public data for this repo (see §5 and `docs/DATA_AUDIT.md`).

---

# 3. Product concept

**Envisioned product:** An adaptive environmental decision-support system that, given current observations and uncertainty about ecosystem threat/resilience, recommends which observation would most improve early warning—then can optionally incorporate a new (or simulated) observation and update the assessment.

**Core future interaction (NOT implemented):**

```
Current environmental observations
→ environmental state / uncertainty
→ candidate observations
→ quantitative selection of a next-best observation
→ human-readable explanation
→ optional simulated observation
→ updated assessment
```

**IMPORTANT — does not exist yet:**

- recommendation engine **runtime**
- dashboard / frontend app
- simulation system
- LLM explanation layer
- anomaly detection / risk scoring / information-gain **implementation**

What exists is a **data, provenance, characterization, and mathematical-specification foundation** centered on verified Almyros aquatic FHIR examples, plus audited secondary OAH sources documented but not merged into the Almyros analysis table.

---

# 4. Development methodology

This project is built **incrementally**.

**Workflow:**

```
Plan → review → implement → test → acceptance gate → Git checkpoint → next phase
```

Rules:

- Never implement future phases automatically.
- Each phase must have explicit acceptance criteria.
- Agents must stop at the phase acceptance gate.
- Prefer smallest correct change; do not redesign completed phases.

---

# 5. Completed phases

## Phase 1 — Data Audit

**STATUS: COMPLETE**  
**Tests:** 13 passed (Phase 1 foundation suite; full suite later grew with Phase 2A).

**Deliverables:** repo scaffold (FastAPI stub + frontend placeholder), `AGENTS.md`, `docs/DATA_AUDIT.md`, `docs/ARCHITECTURE.md`, `docs/PROVENANCE.md`, `data/indicator_registry.yaml`, fetch/inspect scripts, provenance sidecars, tests.

### Verified sources (safe to reference)

| Source | Notes |
|--------|-------|
| OAH FHIR FSH examples (`hl7-eu/oah`) | Almyros, Giofyros, Benevento, Oslo examples; stored under `data/raw/oah_fhir_ig_examples/` |
| Resilience Map UI | `https://apps.oneaquahealth.eu/resmap/v2` — public UI; CSV via client-side Blob |
| Resilience Map API (`api.enora-oah.eu`) | cities/sites, health-risks, urban-parameters, weather (with params) |
| HAF factsheets / IndicatorsOah | Methodology / candidate indicator definitions (Zenodo + FSH logical model), not Almyros time series |

### Unverified — DO NOT BUILD AROUND WITHOUT FUTURE VERIFICATION

- GEOSSIP public downloads
- Citizen Science App bulk observation dump/API
- Live public FHIR REST search server
- Resilience Map Earth Observation public time-series API
- Combining ResMap five-city sites with Crete (Almyros/Giofyros) FHIR as one spatial frame

Details: `docs/DATA_AUDIT.md`.

## Phase 2A — Almyros Normalization

**STATUS: COMPLETE**  
**Tests:** 23 passed (full suite including Phase 2A).

**Scope:** Almyros only (`Loc-Almyros`). Raw data untouched. Deterministic FSH parsing.

| Metric | Value |
|--------|-------|
| Source observations | **135** |
| Normalized long-format rows | **587** |
| Source | Official OAH FHIR FSH (`almyros_gov_chem.fsh`, Almyros rows in `water_tmp.fsh` / `ec_tmp.fsh`) |
| `scale_anomaly` flagged rows | **448** (not rewritten) |

**Pipeline:**

```
FSH → FHIR Observation parsing → Loc-Almyros filter → expansion
  → indicator mapping → verified unit normalization (mS/cm→uS/cm only)
  → quality flags → long-format output
```

**Statistics preserved:**

- `point`
- `mean`
- `median`
- `minimum`
- `maximum`
- `std_dev`

**Outputs:**

- `data/processed/almyros/observations.csv`
- `data/processed/almyros/observations.parquet`
- `data/provenance/almyros_normalized.yaml` (`data_class: derived`)
- `docs/DATA_NORMALIZATION.md`
- `analysis/almyros_normalization_summary.md`
- CLI: `scripts/normalize_almyros.py`

**Note:** Phase 1 `data/processed/oah_fhir_observation_inventory.csv` is a historical derived inventory that largely kept medians/points only—it is **not** the Phase 2A analysis foundation.

## Phase 2B — Almyros Characterization

**STATUS: COMPLETE**  
**Tests:** 31 passed (full suite including Phase 2B).

**Scope:** Characterize normalized Almyros only. No risk scoring, ranking, prediction, UI, or LLM.

| Metric | Value |
|--------|-------|
| Input rows | **587** |
| Indicators | **28** |
| Modeling readiness | **19 candidate**, **9 limited**, **0 exclude** |
| Exploratory median Spearman pairs (≥4 yrs) | **171** |
| Primary statistic for annual chemistry | **median** |

**Outputs:**

- `data/processed/almyros/characterization/` (profile JSON + coverage/readiness CSVs)
- `data/provenance/almyros_characterization.yaml` (`data_class: derived`)
- `docs/DATA_CHARACTERIZATION.md`
- `analysis/almyros_characterization_summary.md`
- CLI: `scripts/characterize_almyros.py`

**Not done in 2B:** decision engine, imputation, unit conversion, ResMap/Giofyros joins.

## Phase 3A — Scout Mathematical Specification

**STATUS: COMPLETE** (documentation only)  
**Tests:** existing suite still passes; no engine modules added.

**Selected formulation:** Gaussian expected information gain (EIG) on a z-scored annual-median **core panel** of 8 indicators (6 complete years), with ridge for numerical stability only—not a weighted resilience score.

**Deliverables:**

- `docs/SCOUT_MATHEMATICAL_SPEC.md`
- `analysis/scout_math_spec_summary.md`

**Not done in 3A:** recommendation engine code, baselines runtime, scoring services, UI, LLM.

---

# 6. Scientific / data constraints

These are critical and **MUST NOT** be violated.

## Raw data

Never modify `data/raw/`. Raw OAH imports remain immutable.

## Statistic semantics

Do not collapse `point`, `mean`, `median`, `minimum`, `maximum`, `std_dev` into one generic value.

## Original values

Preserve originals via `value_original` and `unit_original`. Do not introduce unverified unit conversions. Only verified conversion in 2A: conductivity `mS/cm` → `uS/cm` (×1000).

## Temporal semantics

Do not turn annual summaries into arbitrary point dates. Preserve `observation_kind`, `time_start` / `time_end`, and `time_precision` (`day` vs `year`).

## Provenance

Every processed row must remain traceable:

```
processed row → source_observation_id → source_file (FSH) → official OAH source URL
```

See `docs/PROVENANCE.md` and dataset sidecars under `data/provenance/`.

## Scale anomalies

Phase 2A flagged rows where `|mean| / median >= 10` (median ≠ 0): **448** rows. Values were **not** rewritten. Investigate before using affected statistics in modeling. Do **not** assume they are erroneous without evidence.

## Geographic separation

Do **not** silently combine Almyros FHIR data with Resilience Map data. They do not share a verified common spatial frame (Crete vs Coimbra/Toulouse/Ghent/Benevento/Oslo ResMap cities). ResMap may be a separate secondary experiment later—not Almyros observations.

---

# 7. Verified Almyros indicators

Aquatic indicators present in verified Almyros FHIR examples (coverage by year/statistic is uneven—do not assume equal modeling readiness):

- water temperature
- conductivity / electrical conductivity (EC)
- dissolved oxygen
- pH
- nitrate, nitrite, ammonium
- total phosphates
- chloride, sulphate
- major ions (calcium, magnesium, sodium, potassium, carbonates, bicarbonate HCO3)
- dissolved metals: Al, As, Cd, Cr, Cr6+, Cu, Fe, Pb, Mn, Hg, Ni, Zn

Canonical ids live in `data/indicator_registry.yaml` and `backend/app/services/indicator_mapping.py`. Temporal suitability and modeling readiness are documented in Phase 2B (`docs/DATA_CHARACTERIZATION.md` and `modeling_readiness.csv`)—do not assume equal readiness across indicators.

---

# 8. Other verified OAH data

Documented / partially imported, **not** merged into `data/processed/almyros/`:

**Giofyros (FHIR):** water temperature, conductivity (point samples).

**Benevento (FHIR):** Benzene, NO2, O3, PM10, PM2.5 (+ disease prevalence cohorts).

**Oslo (FHIR examples):** health prevalence (e.g. mental health)—not aquatic physico-chemistry.

**Resilience Map API (stored under `data/raw/resilience_map_api/`):** cities/sites; health-risk scores (pathogen/fecal/ARG); urban parameters; weather (e.g. site `C1`).

Treat these as separate corpora unless a future phase explicitly designs a join with verified keys.

---

# 9. Current repository structure

Verified important layout (not exhaustive of every FSH file):

```
Resilience_Scout/
  AGENTS.md
  README.md
  pyproject.toml
  .env.example
  backend/
    app/
      main.py, api/health.py, core/config.py
      models/provenance.py
      schemas/ (indicators, normalized_observation)
      services/ (inspection, fsh_observation_parser, indicator_mapping,
                normalize_almyros, characterize_almyros)
    tests/ (+ fixtures)
  frontend/                 # placeholder only (UI not built)
  data/
    raw/                    # immutable OAH FHIR FSH + ResMap API JSON
    processed/
      almyros/              # Phase 2A observations + Phase 2B characterization/
      oah_fhir_observation_inventory.*   # Phase 1 derived inventory
    provenance/             # YAML sidecars
    indicator_registry.yaml
  docs/
    ARCHITECTURE.md
    DATA_AUDIT.md
    DATA_NORMALIZATION.md
    DATA_CHARACTERIZATION.md
    SCOUT_MATHEMATICAL_SPEC.md
    PROVENANCE.md
    PROJECT_CONTEXT.md      # this file
  scripts/
    fetch_oah_fhir_examples.py
    inspect_dataset.py
    normalize_almyros.py
    characterize_almyros.py
  analysis/
    README.md
    almyros_normalization_summary.md
    almyros_characterization_summary.md
    scout_math_spec_summary.md
```

---

# 10. Current phase

**PHASE 3A COMPLETE**

**Next:** Phase 3B — implement Gaussian EIG ranking, ridge sensitivity, baselines, and leakage-safe evaluation (**not started**).

Do **not** implement Phase 3B unless explicitly authorized.

---

# 11. Phase 2B objective (completed)

**Purpose:** Determine what environmental structure, relationships, temporal information, missingness patterns, and data quality the **normalized Almyros dataset** actually supports **before** designing the Scout decision engine.

**Investigated:**

- dataset profile
- indicator coverage
- statistic coverage
- temporal coverage
- missingness
- units
- scale anomalies
- scientifically defensible indicator relationships (exploratory median Spearman)
- modeling readiness
- candidate modeling variables
- variables that should be limited/excluded

**Phase 2B did NOT implement:**

- risk scoring
- anomaly detection
- prediction / machine learning
- uncertainty scoring
- information gain
- next-best-observation ranking
- recommendation engine
- simulation
- dashboard / frontend
- LLM reasoning

---

# 12. Future architecture

**FUTURE / NOT IMPLEMENTED.**

Potential future flow:

```
Verified environmental data
→ normalized observations
→ environmental characterization
→ quantitative uncertainty/risk representation
→ candidate observations
→ next-best-observation ranking
→ explanation
→ user interaction
→ optional simulation
→ updated assessment
```

The quantitative decision engine remains separate from any LLM. The LLM explains quantitative results; it does not determine them.

---

# 13. Agent rules

Future Cursor agents **MUST**:

1. Read `AGENTS.md`.
2. Read `docs/PROJECT_CONTEXT.md`.
3. Read relevant phase documentation (`DATA_AUDIT`, `DATA_NORMALIZATION`, `DATA_CHARACTERIZATION`, `SCOUT_MATHEMATICAL_SPEC`, `ARCHITECTURE`, `PROVENANCE`, etc.).
4. Inspect the actual repository before modifying files.
5. Work only on the current authorized phase.
6. Never assume future functionality exists.
7. Never fabricate OAH data.
8. Never silently alter scientific values.
9. Never silently combine incompatible datasets.
10. Preserve provenance.
11. Run tests after implementation.
12. Stop at the phase acceptance gate.
13. Never automatically proceed to the next phase.

Also follow DATA INTEGRITY rules in `AGENTS.md` (raw vs processed, observed/derived/predicted/simulated labels, no false claims of scientific validation).

---

# 14. Current next action

**NEXT ACTION:**

Stop at the Phase 3A acceptance gate unless a human explicitly authorizes Phase 3B.

When starting Phase 3B, first read:

1. `AGENTS.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/SCOUT_MATHEMATICAL_SPEC.md`
4. `docs/DATA_CHARACTERIZATION.md`
5. `data/processed/almyros/characterization/modeling_readiness.csv`

Then produce a **Phase 3B plan for review** before implementing. Prefer **median** annual series and the core panel; do not silently use scale-anomalous mean/min/max as primary inputs.
