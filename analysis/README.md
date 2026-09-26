# Analysis

Notebooks and exploratory analysis for Resilience Scout.

**Phase 1:** use `scripts/inspect_dataset.py` on files under `data/raw/`. Do not invent observations.

**Phase 2A:** `scripts/normalize_almyros.py` → `data/processed/almyros/` + `analysis/almyros_normalization_summary.md`.

**Phase 2B:** `scripts/characterize_almyros.py` → `data/processed/almyros/characterization/` + `analysis/almyros_characterization_summary.md`. Methods: `docs/DATA_CHARACTERIZATION.md`.

**Phase 3A:** mathematical specification only — `docs/SCOUT_MATHEMATICAL_SPEC.md` + `analysis/scout_math_spec_summary.md`. No engine code.

**Rules:**

- Work from provenance-tracked imports only
- Write derived outputs to `data/processed/` with a new provenance sidecar
- Never overwrite `data/raw/`
- Label observed / derived / predicted / simulated clearly
