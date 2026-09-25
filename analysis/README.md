# Analysis

Notebooks and exploratory analysis for Resilience Scout.

**Phase 1:** use `scripts/inspect_dataset.py` on files under `data/raw/`. Do not invent observations.

**Rules:**

- Work from provenance-tracked imports only
- Write derived outputs to `data/processed/` with a new provenance sidecar
- Never overwrite `data/raw/`
- Label observed / derived / predicted / simulated clearly
