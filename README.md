# Resilience Scout

Adaptive environmental decision-support for the **IEEE OneAquaHealth Global Hackathon 2026**, Track 6: Resilience Informatics.

> **Resilience Scout** determines which observation/measurement would provide the greatest value for improving early warning of an emerging ecosystem threat.

## Phase status

**Phase 1 complete** (foundation + OAH data audit).  
**Phase 2A complete** (Almyros normalization). No recommendation algorithm. No dashboard. No fabricated OAH data.

Current deliverables:

- Lean FastAPI backend (health check + config)
- Frontend placeholder for later phases
- Data integrity rules (`AGENTS.md`)
- OAH data audit (`docs/DATA_AUDIT.md`)
- Almyros normalized table (`data/processed/almyros/`, `docs/DATA_NORMALIZATION.md`)
- Indicator registry (`data/indicator_registry.yaml`)
- Provenance format + dataset inspection / normalize scripts

## Core loop (future)

```
REAL OAH DATA
→ detect potential anomaly/risk
→ identify uncertainty
→ evaluate candidate observations
→ calculate expected resilience value
→ recommend the next best observation
→ receive/simulate the new observation
→ update the assessment
→ show whether uncertainty/risk changed
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

# Tests
pytest
```

## Layout

```
backend/          FastAPI app
frontend/         Next.js placeholder (Phase 2+)
data/raw/         Immutable imported sources
data/processed/   Derived outputs (labeled)
data/provenance/  Provenance sidecars
docs/             Architecture + DATA_AUDIT
scripts/          Fetch + inspect utilities
analysis/         Exploratory work
```

## Data integrity

See [AGENTS.md](AGENTS.md). Never fabricate OAH observations. Separate **VERIFIED FACTS** from assumptions. Label observed / derived / predicted / simulated.

## Docs

- [AGENTS.md](AGENTS.md) — rules for humans and AI agents
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DATA_AUDIT.md](docs/DATA_AUDIT.md)
