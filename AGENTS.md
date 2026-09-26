# AGENTS.md — Resilience Scout

Guidance for humans and AI agents working on this repository.

## Project purpose

**Resilience Scout** is an adaptive environmental decision-support concept for the IEEE OneAquaHealth (OAH) Global Hackathon 2026.

It is an uncertainty-aware measurement prioritization tool that can support early-warning monitoring by identifying which observation would most reduce uncertainty in the current environmental state, using a **quantitative decision engine** — not an LLM — as the core mechanism (engine specified in Phase 3A; not implemented until Phase 3B).

## Track 6: Resilience Informatics

Solutions must enable:

- early warning
- resilience planning
- predictive environmental tools
- predictive dashboards
- alerts
- resilience tools

## Architecture principles

1. **Quantitative engine first.** Scoring, uncertainty, and “next best observation” logic are deterministic/statistical code under `backend/app/services/`. An LLM may later *explain* outputs; it must not choose the recommendation.
2. **Real OAH data only for claims of “observed.”** Fabricated or invented environmental values are forbidden.
3. **Provenance always.** Every imported dataset has a sidecar under `data/provenance/` with source URL, retrieval date, and data class.
4. **Raw is immutable.** Never overwrite `data/raw/`. Derived products go to `data/processed/` with new provenance.
5. **Phase discipline.** Do not implement Phase N+1 features during Phase N unless explicitly requested.

### Phase 1 (complete)

- Project foundation
- Data audit of real OAH sources
- Indicator registry
- Provenance + inspection tooling
- Tests for foundation code

### Phase 2A (complete)

- Almyros long-format normalization (`data/processed/almyros/`)
- Statistic preservation (point/mean/median/min/max/std_dev)
- See `docs/DATA_NORMALIZATION.md`

### Phase 2B (complete)

- Almyros environmental data characterization (`data/processed/almyros/characterization/`)
- Coverage, units, scale-anomaly profile, exploratory median Spearman, modeling readiness
- See `docs/DATA_CHARACTERIZATION.md`

### Phase 3A (complete)

- Scout mathematical specification only (`docs/SCOUT_MATHEMATICAL_SPEC.md`)
- Selected formulation: Gaussian EIG on annual-median core panel (no engine code)
- See `analysis/scout_math_spec_summary.md`

### Explicitly out of Phase 3A (and earlier)

- Recommendation / expected-value **implementation**
- Anomaly/risk/uncertainty **runtime** models
- Dashboard UI
- LLM explanation layer
- Fake OAH API endpoints
- Invented environmental time series

## Coding standards

- Prefer small, focused modules and clear names
- Type-annotate public functions
- Fail loudly on missing provenance or unlabeled data classes
- Do not add heavy dependencies without need
- Tests live in `backend/tests/`; run with `pytest` from repo root

## Testing expectations

- Every new validation/inspection helper should have unit tests
- Fixtures must use **real** OAH example fragments (copied from official sources) or clearly labeled synthetic *schema* fixtures that do not claim to be OAH observations
- Do not invent observation values and present them as OAH data in fixtures

## VERIFIED vs UNVERIFIED

When documenting data:

- **VERIFIED** — you have inspected the official source and can cite URL/evidence
- **UNVERIFIED — DO NOT BUILD AROUND THIS YET** — assumption, marketing claim, or untested export

Never silently upgrade UNVERIFIED to VERIFIED.

---

## DATA INTEGRITY

1. **Never fabricate OAH observations.**
2. **Never present simulated data as real OAH data.**
3. **Every external dataset must have a source URL and provenance note.**
4. **Store raw source data separately from processed data** (`data/raw/` vs `data/processed/`).
5. **Preserve original values.** Do not “fix” source numbers silently; flag anomalies in notes.
6. **Clearly label:**
   - `observed`
   - `derived`
   - `predicted`
   - `simulated`
7. **Never claim scientific validation that we have not performed.**

---

## Data provenance requirements

Each import records at minimum:

| Field | Meaning |
|-------|---------|
| `source` | Human-readable source name |
| `source_url` | Official URL |
| `retrieval_date` | ISO date of download |
| `original_filename_or_api` | File or API path used |
| `license` | Stated license / usage note |
| `data_class` | observed \| derived \| predicted \| simulated |
| `processing_steps` | Ordered list of what we did |
| `preserves_original_values` | true for raw tree |

Schema: `backend/app/models/provenance.py`. Sidecars: `data/provenance/*.yaml`.

## Indicator registry

Machine-readable candidates: `data/indicator_registry.yaml`.

- Do not fill unknown fields with guesses — use `null`
- Framework-only indicators (HAF) may be listed with `observation_type: framework_definition` and `available_sites: null` until site series are verified

## Communication

When summarizing data work, separate:

1. Verified facts (with links)
2. Limitations
3. Explicit UNVERIFIED items
