# SCOUT MATHEMATICAL SPECIFICATION — Phase 3A

**Status:** Phase 3A COMPLETE (specification only)  
**Spec version:** `3a.1`  
**Input evidence:** Phase 2A Almyros normalized table + Phase 2B characterization  
**Does not implement:** recommendation engine, scoring code, UI, LLM, simulation runtime

---

## Problem Definition

### Decision problem

Given the environmental information currently available at Almyros, determine which **additional environmental observation** would provide the greatest useful information for understanding the current aquatic environmental state.

**Resilience Scout** is an uncertainty-aware measurement prioritization tool that can support early-warning monitoring by identifying which observation would most reduce uncertainty in the current environmental state.

Scout is **not** itself an early-warning system, a health-outcome predictor, or a weighted “resilience score” calculator.

### Formal objects

| Object | Definition |
|--------|------------|
| **Current information** \(I_T\) | All annual-median values of eligible indicators with calendar year \(< T\), plus any already-known coordinates of year \(T\) |
| **Environmental state** \(\mathbf{x}_T\) | Z-scored annual-median vector of the **core panel** (possibly partially observed) |
| **Candidate observation** | An indicator \(i\) whose coordinate \(x_{T,i}\) is missing at decision time, and that is eligible under readiness rules below |
| **Action** | “Measure indicator \(i\) next” = reveal \(x_{T,i}\) (annual-median semantics for chemistry) |
| **Outcome** | Expected reduction in uncertainty about the **unobserved remainder** of \(\mathbf{x}_T\), measured by Gaussian expected information gain (EIG) |

---

## Available Evidence

From verified Almyros Phase 2A/2B artifacts:

| Fact | Value |
|------|-------|
| Site | `Loc-Almyros` only |
| Long-format rows | 587 |
| Source observations | 135 |
| Primary statistic for annual chemistry | `median` |
| Core panel complete years | **6** (`2013–2015`, `2018–2020`) |
| Full 19 Phase 2B candidates complete years | **4** (`2013–2014`, `2018–2019`) |
| `scale_anomaly` rows | 448 (companions; values not rewritten) |
| Phase 2B readiness | 19 candidate, 9 limited, 0 exclude |
| Point samples | 4 rows (2024–2025 temp/EC only); not pooled with annual medians |
| Linked health endpoints in Almyros table | none |
| Verified ecological thresholds in-repo | none |

Sources: `data/processed/almyros/observations.*`, `docs/DATA_CHARACTERIZATION.md`, `modeling_readiness.csv`.

---

## Environmental State

### Selected representation

\[
\mathbf{x}_t \in \mathbb{R}^{d},\quad
x_{t,j} = \frac{m_{t,j} - \hat\mu_j}{\hat\sigma_j}
\]

where \(m_{t,j}\) is the annual **median** of indicator \(j\) in year \(t\), and \((\hat\mu_j,\hat\sigma_j)\) are estimated only from training years \(< T\) (leakage-safe).

**Core panel (\(d=8\)), 6 complete years:**

- `ammonium`
- `chloride`
- `dissolved_oxygen`
- `electrical_conductivity`
- `nitrate`
- `nitrite`
- `sulphate`
- `water_temperature`

Model family for v1:

\[
\mathbf{x}_t \sim \mathcal{N}(\boldsymbol{\mu}, \Sigma),\qquad
\Sigma_\lambda = \hat\Sigma + \lambda I
\]

\(\lambda > 0\) is a numerical ridge (not an indicator importance weight).

### Alternatives considered

| Representation | Why not selected for v1 |
|----------------|-------------------------|
| Full 19-candidate complete vectors | Only 4 complete years → worse identification of \(\Sigma\) |
| Latent “resilience factor” | Invents an unobserved construct; conflicts with “no arbitrary resilience score” |
| Independent per-indicator variances only | Ignores co-variation structure Phase 2B Spearman explored |
| Mixing point samples into \(\mathbf{x}_t\) | Different temporal semantics (`day` vs `year`) |

---

## Candidate Observations

### Eligible for v1 ranking (core)

The 8 core indicators above, when missing at decision time \(T\).

### Extended candidates (lower confidence)

Phase 2B `candidate` indicators **not** in the core (11 metals / ions with ≥4 median years). Eligible only when:

- calibration years containing that indicator ≥ 4, and
- ridge-stable ranking procedures succeed.

Explanations must mark extended candidates as lower confidence.

### Excluded from v1 ranking

| Category | Treatment |
|----------|-----------|
| Phase 2B **LIMITED** (9) | Exclude from ranking; secondary evidence / future extension only |
| `mean` / `minimum` / `maximum` | Never primary inputs while scale anomalies unresolved |
| Point samples (2024–2025) | Not joint-state coordinates; may appear only in narrative context |
| Indicators outside Almyros normalized table | Out of scope |
| HAF framework-only registry entries | No Almyros time series |

### LIMITED indicator list (excluded from ranking)

`bicarbonate_hco3`, `calcium`, `carbonates`, `magnesium`, `ph`, `potassium`, `sodium`, `total_phosphates`, `zinc_dissolved`

---

## Mathematical Formulations

### A. Information gain (Gaussian EIG) — **SELECTED**

For missing set \(M\) and candidate \(i \in M\), under Gaussian \(\Sigma_\lambda\):

\[
\mathrm{EIG}(i \mid I_T)
= \tfrac{1}{2}\log\det\Sigma_{M}
- \tfrac{1}{2}\log\det\Sigma_{M \setminus \{i\} \mid i}
\]

where conditional covariances follow standard Gaussian conditioning on already-observed coordinates at \(T\).

| Aspect | Assessment |
|--------|------------|
| Assumptions | Approximate joint normality of z-scored annual medians; stationarity of \(\Sigma\) across years; missing-at-random within year for masked coords |
| Data needs | Overlapping annual medians; enough years to estimate \(\Sigma\) |
| Almyros support | **Yes** for core panel (6 complete years); thin but demonstrable |
| Advantages | No hand indicator weights; interpretable; handles partial observation |
| Limitations | Small \(n\); Gaussian misspecification; ridge dependence |
| Interpretability | High (log-det uncertainty before/after) |
| Hackathon feasibility | High |
| Misleading-risk | Medium if \(\lambda\)-sensitivity ignored (mitigated by mandatory sensitivity + unstable flag) |

### B. Trace uncertainty reduction — secondary metric

\[
\Delta_{\mathrm{tr}}(i)
= \mathrm{tr}(\Sigma_M) - \mathrm{tr}(\Sigma_{M\setminus\{i\}\mid i})
\]

Same assumptions as A; less sensitive to joint volume; use as secondary evaluation, not primary ranking objective.

### C. Risk / exceedance value of information — **not primary**

Would score expected improvement in identifying “concerning” conditions relative to thresholds.

| Aspect | Assessment |
|--------|------------|
| Almyros support | **No** verified ecological thresholds or linked health outcomes in this corpus |
| Risk | Inventing thresholds would create false early-warning claims |
| Future | Optional sensitivity **only if** thresholds become VERIFIED from official OAH/HAF sources |

### Rejected formulations

- Weighted resilience index / arbitrary indicator scores
- Deep latent ML / black-box predictors (\(n \approx 6\) insufficient)
- Pooling point and annual series without temporal separation

---

## Selected Formulation

**Gaussian expected information gain (determinant form) on the z-scored annual-median core panel**, with ridge \(\Sigma_\lambda = \hat\Sigma + \lambda I\).

Pipeline:

```text
Normalized Almyros observations (medians only)
        ↓
Comparable historical feature set (core panel, years < T)
        ↓
Current environmental state x_T (partially observed, z-scored)
        ↓
Uncertainty representation N(μ, Σ_λ)
        ↓
Candidate observations (missing core / eligible extended)
        ↓
Expected information gain EIG(i)
        ↓
Observation ranking
        ↓
Recommended next measurement (+ ridge-stability flag)
```

---

## Assumptions

1. Annual medians are the scientifically preferred Almyros summary statistic for v1.
2. Z-scored medians are approximately jointly Gaussian for ranking purposes (working model, not proven).
3. Historical covariance estimated on years \(< T\) is a usable proxy for uncertainty at \(T\).
4. Within a year, masked indicators are treated as missing for decision evaluation (historical replay).
5. Ridge \(\lambda\) is for numerical stability only; it is not domain preference.
6. Correlation structure is associative, not causal.
7. Almyros results do not transfer to other sites without new evidence.
8. LLM (if any later) explains structured quantitative outputs; it never chooses the ranking.

---

## Limitations

- Only **6** complete core years → covariance and EIG estimates are fragile.
- Gap years 2016–2017; uneven extended-indicator coverage.
- Widespread `scale_anomaly` on mean/min/max companions.
- No verified thresholds → cannot claim calibrated ecological “risk.”
- No health outcomes in Almyros chemistry table.
- Spearman relationships from Phase 2B are exploratory, not causal.
- Point samples cannot yet join the annual joint state.

---

## Validation Strategy

**Leakage-safe rolling-origin / leave-future-year-out** on \(\{2013,2014,2015,2018,2019,2020\}\):

1. Train \(\hat\mu,\hat\Sigma\) on years strictly \(< T\).
2. At year \(T\), mask one or more coordinates; compute rankings.
3. Reveal held-out values; measure **realized** log-det / MSE reduction.
4. Never use years \(> T\) or held-out same-year values inside \(\Sigma\).

Feasible but thin. Report qualitative stability and baseline comparisons—not operational certification.

---

## Evaluation Metrics

### Primary / secondary (supportable)

1. Realized log-det reduction after reveal (primary).
2. Trace MSE reduction on masked coordinates (secondary).
3. Rank quality vs oracle (which mask gave largest realized reduction).
4. Top-1 stability across folds.
5. Ridge \(\lambda\) ranking stability (mandatory in Phase 3B).

### Phase 3B mandatory evaluation outputs

- EIG vs baseline **realized** log-det reduction
- Top-1 recommendation stability (across folds and across \(\lambda\))
- Ridge sensitivity results
- Per-fold results
- Explicit limitations from **n = 6 complete years**

### Mandatory baselines (same leakage-safe replay)

1. Random candidate selection
2. Highest marginal variance
3. Strongest correlation with currently observed indicators
4. Gaussian EIG Scout (selected formulation)

### Not used

- Subjective resilience scores
- Health-outcome prediction accuracy (no linked endpoints)

---

## Scale Anomaly Treatment

| Rule | Detail |
|------|--------|
| Do not alter values | Raw and normalized medians unchanged |
| Exclude from calibration | `mean`, `minimum`, `maximum` (and do not rank on them) |
| Keep for calibration | `median` rows even if parent observation carries `scale_anomaly` (flag targets companion scale inconsistency) |
| Document | Risk register + explanations note unresolved OAH scale issues |

---

## Sparse Indicator Treatment

Phase 2B **LIMITED** indicators:

- **Excluded from v1 Scout ranking**
- May appear in documentation as secondary evidence / future extension
- Not used to invent imputed state coordinates

---

## Interpretability

Quantitative engine must emit structured evidence **without** an LLM deciding the rank, e.g.:

```text
Recommended observation: <indicator_id>
EIG: <value>
Prior uncertainty (log-det): <value>
Expected posterior uncertainty: <value>
Ridge λ: <value>
Ridge stability: stable | unstable
n_train_years: <int>
Top associated indicators (from Σ): ...
Readiness class: candidate_core | candidate_extended
Limitations: small-n; Gaussian assumption; ...
```

An optional later LLM may paraphrase this structure; it must not change the recommendation.

---

## Future Simulation

Preferred: **historical replay** (mask → recommend → reveal held-out real median).

Synthetic “observe” draws (for UI demos later) must be labeled `data_class: simulated` and never presented as OAH observed values.

Recommend → Observe → Update loop (future):

```text
Current dataset / I_T
      ↓
Scout recommendation (EIG rank)
      ↓
New observation (held-out real or labeled simulated)
      ↓
Update partial state x_T
      ↓
Recalculate Σ-conditional uncertainty
      ↓
Compare before/after log-det
```

---

## Track 6 Alignment

> Resilience Scout is an uncertainty-aware measurement prioritization tool that can support early-warning monitoring by identifying which observation would most reduce uncertainty in the current environmental state.

| Track theme | How this design relates |
|-------------|-------------------------|
| Early warning | Supports monitoring design; **Scout is not an early-warning system** |
| Resilience planning | Prioritizes measurements that reduce state uncertainty |
| Predictive environmental tools | Uses predictive Gaussian structure over annual medians |
| Alerts | Out of Phase 3A; future layers must not invent unverified thresholds |
| Environmental monitoring | Direct: actionable next-measurement ranking |

**Non-claims:** no demonstrated human-health impact from Almyros chemistry alone; no multi-city spatial resilience map merge.

---

## Weights and ridge

- **No** hand-tuned indicator importance weights.
- Ridge \(\lambda I\) only for invertibility / numerical stability.
- **Mandatory Phase 3B ridge sensitivity:** evaluate EIG rankings on a predefined \(\lambda\) grid; report top-1 and ranking stability; if highly sensitive, mark recommendation **`unstable`** rather than presenting false confidence.

---

## Mathematical risk register

| Risk | Evidence | Severity | Mitigation |
|------|----------|----------|------------|
| Sparse temporal data | 6 complete core years | High | Core panel only; report small-n limits; unstable flag |
| Annual aggregation | `time_precision=year` | Medium | Preserve annual semantics; do not fake daily series |
| Scale anomalies | 448 flagged rows | High | Median-only; exclude mean/min/max |
| Missingness | Uneven indicator years | Medium | Core complete years; no imputation of state |
| Small sample covariance | \(n \le 6\), \(d=8\) | High | Ridge + sensitivity; baselines |
| Correlation ≠ causation | Phase 2B Spearman exploratory | Medium | EIG uses association only; document non-causal |
| Data leakage | Future years in \(\Sigma\) | High | Strict year \(< T\) training |
| Overfitting | Fragile \(\Sigma\) | High | Baselines; ridge grid; per-fold reports |
| Arbitrary weighting | Tempting “resilience score” | High | Forbidden; ridge ≠ preference weights |
| Misleading uncertainty | Gaussian misspecification | Medium | Secondary metrics; caveats in explanations |
| Geographic limitation | Almyros only | High | No silent ResMap/Giofyros join |
| False early-warning claim | Track wording risk | High | Use Track 6 wording above; no threshold VoI without VERIFIED limits |

---

## Phase 3B Implementation Plan

**Do not implement in Phase 3A.** Exact next components when authorized:

1. Annual-median panel loader (core + optional extended) from `data/processed/almyros/observations.*`.
2. Leakage-safe estimator of \(\mu,\Sigma_\lambda\) with configurable \(\lambda\).
3. Gaussian EIG ranking + structured explanation dict (including ridge-stability flag).
4. **Ridge \(\lambda\) sensitivity analysis** across a predefined grid; mark unstable recommendations.
5. **Baselines** under identical replay: random; highest marginal variance; strongest correlation with observed; Gaussian EIG.
6. Evaluation report under `analysis/` with: EIG vs baselines (realized log-det), top-1 stability, ridge sensitivity, per-fold results, n=6 limitations.
7. CLI + unit tests on real Almyros medians (no fabricated observations).
8. Still no UI, no LLM decision layer, no ResMap merge, no invented thresholds.

---

## Phase 3A non-goals (confirmed)

- No recommendation engine code
- No scoring/ranking service modules
- No dashboard / frontend
- No LLM reasoning
- No fabricated environmental series

---

## References

- `docs/DATA_AUDIT.md`
- `docs/DATA_NORMALIZATION.md`
- `docs/DATA_CHARACTERIZATION.md`
- `docs/ARCHITECTURE.md`
- `docs/PROVENANCE.md`
- `docs/PROJECT_CONTEXT.md`
- `data/processed/almyros/characterization/modeling_readiness.csv`
- `AGENTS.md`
