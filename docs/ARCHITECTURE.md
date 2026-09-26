# Architecture — Resilience Scout

## Goal

Recommend which **next observation** would most reduce uncertainty about the current environmental state, using **real OneAquaHealth (OAH) data**.

Resilience Scout is an uncertainty-aware measurement prioritization tool that can support early-warning monitoring by identifying which observation would most reduce uncertainty in the current environmental state. It is **not** itself an early-warning system.

## Design rule

```
Quantitative decision engine  →  recommendation
Optional LLM (later)          →  natural-language explanation only
```

The LLM must **not** select the next observation.

## Phase status

| Phase | Status | Scope |
|-------|--------|-------|
| 1 | Complete | Foundation, OAH data audit, registry, inspection |
| 2A | Complete | Almyros normalization → analysis-ready long table |
| 2B | Complete | Almyros characterization → coverage, quality, readiness |
| 3A | Complete | Mathematical specification (Gaussian EIG) — docs only |
| 3B+ | Not started | Engine implementation, baselines, UI, LLM explain |

## Phase 1 components

```
Verified OAH sources → data/raw/ + provenance + indicator_registry
                    → inspect_dataset.py / FastAPI health
```

## Phase 2A components

```
data/raw/.../github_fsh (Almyros FSH, immutable)
  → fsh_observation_parser
  → indicator_mapping + normalize_almyros
  → data/processed/almyros/observations.csv|.parquet
  → data/provenance/almyros_normalized.yaml
```

See [DATA_NORMALIZATION.md](DATA_NORMALIZATION.md). **No** scoring, ranking, or UI in 2A.

## Phase 2B components

```
data/processed/almyros/observations.* (immutable input)
  → characterize_almyros
  → data/processed/almyros/characterization/*
  → data/provenance/almyros_characterization.yaml
```

See [DATA_CHARACTERIZATION.md](DATA_CHARACTERIZATION.md). **No** risk scoring, ranking, prediction, or UI in 2B.

## Phase 3A components

```
Phase 2B readiness + Almyros medians (evidence)
  → docs/SCOUT_MATHEMATICAL_SPEC.md (Gaussian EIG specification)
  → analysis/scout_math_spec_summary.md
```

See [SCOUT_MATHEMATICAL_SPEC.md](SCOUT_MATHEMATICAL_SPEC.md). **No** engine code in 3A.

## Backend layout

| Path | Role |
|------|------|
| `backend/app/main.py` | FastAPI app |
| `backend/app/api/` | HTTP routes (Phase 1: health) |
| `backend/app/core/config.py` | Settings |
| `backend/app/models/` | Provenance models |
| `backend/app/schemas/` | Normalized observation schemas (2A) |
| `backend/app/services/` | Inspection, FSH parse, Almyros normalize, characterize |

## Data classes

| Class | Meaning |
|-------|---------|
| `observed` | Values from OAH / official monitoring as published |
| `derived` | Transformed from observed (reshape, verified unit convert) without inventing measurements |
| `predicted` | Model output |
| `simulated` | Hypothetical observation for what-if loops — **never labeled observed** |

## Future phases (not implemented)

1. ~~Normalize verified series → `data/processed/`~~ (2A: Almyros done)
2. ~~Characterize Almyros structure / readiness~~ (2B done)
3. ~~Mathematical specification of Scout ranking~~ (3A done)
4. Phase 3B: Gaussian EIG engine + ridge sensitivity + baselines (not started)
5. API + Next.js dashboard
6. Optional LLM explanation of the ranked recommendation

## References

- [DATA_AUDIT.md](DATA_AUDIT.md)
- [DATA_NORMALIZATION.md](DATA_NORMALIZATION.md)
- [DATA_CHARACTERIZATION.md](DATA_CHARACTERIZATION.md)
- [SCOUT_MATHEMATICAL_SPEC.md](SCOUT_MATHEMATICAL_SPEC.md)
- [PROVENANCE.md](PROVENANCE.md)
- [AGENTS.md](../AGENTS.md)
- OAH FHIR IG: https://build.fhir.org/ig/hl7-eu/oah/
- Resilience Map: https://apps.oneaquahealth.eu/resmap/v2
