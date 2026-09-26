# Resilience Scout

Adaptive environmental decision-support for the **IEEE OneAquaHealth Global Hackathon 2026**, Track 6: Resilience Informatics.

> Resilience Scout is an uncertainty-aware measurement prioritization tool that can support early-warning monitoring by identifying which observation would most reduce uncertainty in the current environmental state.

## Phase status

**Phase 1 complete** (foundation + OAH data audit).  
**Phase 2A complete** (Almyros normalization).  
**Phase 2B complete** (Almyros characterization / modeling readiness).  
**Phase 3A complete** (Scout mathematical specification — docs only). No recommendation engine runtime. No dashboard. No fabricated OAH data.

Current deliverables:

- Lean FastAPI backend (health check + config)
- Frontend placeholder for later phases
- Data integrity rules (`AGENTS.md`)
- OAH data audit (`docs/DATA_AUDIT.md`)
- Almyros normalized table (`data/processed/almyros/`, `docs/DATA_NORMALIZATION.md`)
- Almyros characterization (`data/processed/almyros/characterization/`, `docs/DATA_CHARACTERIZATION.md`)
- Scout math spec (`docs/SCOUT_MATHEMATICAL_SPEC.md`)
- Indicator registry (`data/indicator_registry.yaml`)
- Provenance format + fetch / inspect / normalize / characterize scripts

## Core loop (future)

```
REAL OAH DATA
→ characterize / represent environmental state uncertainty
→ evaluate candidate observations (Gaussian EIG)
→ recommend the next best observation
→ receive/simulate the new observation
→ update the assessment
→ show whether uncertainty changed
```

**The LLM is not the decision engine.** A quantitative engine will own recommendations; an LLM may later explain them in plain language.

## Quick start

```bash
# From repo root
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Health API
uvicorn app.main:app --app-dir backend --reload

# Inspect a local dataset under data/raw/
python scripts/inspect_dataset.py data/raw/oah_fhir_ig_examples

# Normalize Almyros FHIR → analysis-ready long table
python scripts/normalize_almyros.py

# Characterize normalized Almyros (coverage / readiness)
python scripts/characterize_almyros.py

# Tests
pytest
```

## Layout

```
backend/          FastAPI app
frontend/         Next.js placeholder (later phases)
data/raw/         Immutable imported sources
data/processed/   Derived outputs (labeled)
data/provenance/  Provenance sidecars
docs/             Architecture + data + Scout math spec
scripts/          Fetch + inspect + normalize + characterize
analysis/         Exploratory summaries
```

## Data integrity

See [AGENTS.md](AGENTS.md). Never fabricate OAH observations. Separate **VERIFIED FACTS** from assumptions. Label observed / derived / predicted / simulated.

## Docs

- [AGENTS.md](AGENTS.md) — rules for humans and AI agents
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DATA_AUDIT.md](docs/DATA_AUDIT.md)
- [docs/DATA_NORMALIZATION.md](docs/DATA_NORMALIZATION.md)
- [docs/DATA_CHARACTERIZATION.md](docs/DATA_CHARACTERIZATION.md)
- [docs/SCOUT_MATHEMATICAL_SPEC.md](docs/SCOUT_MATHEMATICAL_SPEC.md)
- [docs/PROVENANCE.md](docs/PROVENANCE.md)
- [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)
