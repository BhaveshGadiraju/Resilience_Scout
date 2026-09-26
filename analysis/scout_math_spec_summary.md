# Scout mathematical specification summary (Phase 3A)

- spec_version: `3a.1`
- deliverable: `docs/SCOUT_MATHEMATICAL_SPEC.md` (**documentation only**)
- engine / scoring / UI / LLM: **not implemented**

## Selected formulation

Gaussian **expected information gain (EIG)** on a z-scored **annual-median core panel** (\(d=8\), 6 complete years), with ridge \(\Sigma_\lambda=\hat\Sigma+\lambda I\) for numerical stability only.

## Alternatives considered

- Trace uncertainty reduction — secondary metric
- Risk / exceedance VoI — not primary (no verified thresholds)
- Weighted resilience scores / deep ML — rejected

## Environmental state

Core: `ammonium`, `chloride`, `dissolved_oxygen`, `electrical_conductivity`, `nitrate`, `nitrite`, `sulphate`, `water_temperature`

## Candidates

- Rank: core (and optionally lower-confidence extended Phase 2B candidates)
- Exclude from v1 ranking: Phase 2B LIMITED (9); mean/min/max; point samples as joint state

## Scale anomalies / LIMITED

- Keep medians; exclude mean/min/max from calibration
- LIMITED indicators excluded from ranking

## Validation / metrics

Leakage-safe leave-future-year-out. Phase 3B must compare EIG vs random / max variance / max correlation baselines; report ridge sensitivity, top-1 stability, per-fold results, and n=6 limits; mark **unstable** if \(\lambda\)-sensitive.

## Track 6

Resilience Scout is an uncertainty-aware measurement prioritization tool that can support early-warning monitoring by identifying which observation would most reduce uncertainty in the current environmental state.

## Next

Phase 3B implementation only when explicitly authorized. See Phase 3B plan in the full spec.
