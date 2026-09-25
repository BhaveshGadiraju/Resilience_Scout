# Architecture — Resilience Scout

## Goal

Recommend the **next observation** that most reduces uncertainty / improves early warning for an emerging ecosystem threat, using **real OneAquaHealth (OAH) data**.

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
| 2A | Current | Almyros normalization → analysis-ready long table |
| Later | Not started | Risk/uncertainty, next-best ranking, dashboard, LLM explain |

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

## Backend layout

| Path | Role |
|------|------|
| `backend/app/main.py` | FastAPI app |
| `backend/app/api/` | HTTP routes (Phase 1: health) |
| `backend/app/core/config.py` | Settings |
| `backend/app/models/` | Provenance models |
| `backend/app/schemas/` | Normalized observation schemas (2A) |
| `backend/app/services/` | Inspection, FSH parse, Almyros normalize |

## Data classes

| Class | Meaning |
|-------|---------|
| `observed` | Values from OAH / official monitoring as published |
| `derived` | Transformed from observed (reshape, verified unit convert) without inventing measurements |
| `predicted` | Model output |
| `simulated` | Hypothetical observation for what-if loops — **never labeled observed** |

## Future phases (not implemented)

1. ~~Normalize verified series → `data/processed/`~~ (2A: Almyros done)
2. Risk / anomaly + uncertainty signals
3. Expected resilience value / next-observation ranking
4. API + Next.js dashboard
5. Optional LLM explanation of the ranked recommendation

## References

- [DATA_AUDIT.md](DATA_AUDIT.md)
- [DATA_NORMALIZATION.md](DATA_NORMALIZATION.md)
- [PROVENANCE.md](PROVENANCE.md)
- [AGENTS.md](../AGENTS.md)
- OAH FHIR IG: https://build.fhir.org/ig/hl7-eu/oah/
- Resilience Map: https://apps.oneaquahealth.eu/resmap/v2
