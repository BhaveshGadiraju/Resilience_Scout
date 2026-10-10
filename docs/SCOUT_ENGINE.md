# SCOUT ENGINE - Phase 3B

**Engine version:** `3b.1` (implements spec `3a.1`). Deterministic; no LLM; `data_class: derived`.

Code: `backend/app/services/scout/{panel,model,engine,backtest}.py`
CLI: `scripts/scout_recommend.py`, `scripts/run_scout_backtest.py`. Output: `analysis/scout_engine/`.

## Deviation from the Phase 3A formula (intentional)
The spec writes EIG(i) = 0.5 log det S_M - 0.5 log det S_{M\i|i}. By the determinant chain rule
this equals 0.5 log Var(x_i | observed), i.e. the variance baseline, not information about the rest of the state.
Scout implements the mutual-information form over R = M \ {i}:
EIG(i) = 0.5 log det S_{R|O} - 0.5 log det S_{R|O,i}. `literal_spec_value` is kept only for diagnostics/tests.

## Choices
- Panel: annual medians only, 8 core indicators, complete years only (no imputation).
- z-score and covariance fit on complete years strictly < target year. Default ridge 0.1; grid 0.01-1.0.
- Gaussian posterior covariance is value-independent, so the backtest's realized metric is MSE reduction
  on the remaining hidden coordinates; log-det reduction is reported as model-implied.
- Folds need >= 3 earlier complete years (test years 2018, 2019, 2020).
- Random baseline = exact expectation. Variance baseline = conditional variance given observed.

## Not in this phase
Backend endpoints, simulation, UI, LLM, extended (non-core) candidates.