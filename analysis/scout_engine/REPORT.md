# Scout Phase 3B backtest report (data_class: derived)

Real Almyros annual medians (OAH). Rolling-origin replay, training on years strictly < T.
Folds (test years): [2018, 2019, 2020]. Hidden-set sizes k: [3, 4].
Scenarios per strategy: 378. Default ridge: 0.1.

## Overall (higher mean MSE reduction = better; rank 1 = best of the hidden candidates)

| strategy | mean_mse_reduction | mean_realized_rank | oracle_hit_rate | mean_model_eig | n_scenarios |
|---|---|---|---|---|---|
| scout | 0.9571 | 2.1667 | 0.2910 | 0.2337 | 378 |
| correlation | 0.2499 | 2.3095 | 0.2963 | 0.1161 | 378 |
| variance | 1.0978 | 2.2249 | 0.2831 | 0.2110 | 378 |
| random | 0.5153 | 2.2778 | 0.2870 | 0.1579 | 378 |

## Per fold

| fold_year | strategy | mean_mse_reduction | mean_realized_rank | oracle_hit_rate | mean_model_eig | n_scenarios |
|---|---|---|---|---|---|---|
| 2018 | scout | 2.4053 | 2.0238 | 0.3492 | 0.1278 | 126 |
| 2018 | correlation | 0.2477 | 2.4841 | 0.1905 | 0.0731 | 126 |
| 2018 | variance | 2.5978 | 2.0794 | 0.4444 | 0.1164 | 126 |
| 2018 | random | 1.2538 | 2.2778 | 0.2870 | 0.0903 | 126 |
| 2019 | scout | 0.2574 | 2.1825 | 0.2619 | 0.2461 | 126 |
| 2019 | correlation | 0.1052 | 2.3095 | 0.3413 | 0.1196 | 126 |
| 2019 | variance | 0.2114 | 2.2937 | 0.2063 | 0.2194 | 126 |
| 2019 | random | 0.1631 | 2.2778 | 0.2870 | 0.1622 | 126 |
| 2020 | scout | 0.2086 | 2.2937 | 0.2619 | 0.3272 | 126 |
| 2020 | correlation | 0.3968 | 2.1349 | 0.3571 | 0.1557 | 126 |
| 2020 | variance | 0.4843 | 2.3016 | 0.1984 | 0.2973 | 126 |
| 2020 | random | 0.1291 | 2.2778 | 0.2870 | 0.2213 | 126 |

## Ridge sensitivity (Scout)

| ridge | top1_agreement_with_default | mean_mse_reduction |
|---|---|---|
| 0.0100 | 0.9603 | 4.4892 |
| 0.0500 | 0.9815 | 1.6496 |
| 0.1000 | 1.0000 | 0.9571 |
| 0.2500 | 0.9497 | 0.5071 |
| 0.5000 | 0.8757 | 0.2817 |
| 1.0000 | 0.7857 | 0.1920 |

Scout top-1 agreement across folds (same hidden set): 0.5767195767195767

## Read this before quoting numbers

- Only 3 test folds with 3-5 training years each; no statistical significance is claimed.
- Realized metric = MSE reduction on the other hidden coordinates after revealing the pick. Gaussian log-det
  reduction (model_eig) does not depend on the revealed value, so it is model-implied, not realized.
- Random is the exact expectation over a uniform pick.
- Variance baseline uses conditional variance given observed coordinates (marginal variance is 1 for all in z-space).
- The Phase 3A EIG formula as written equals 0.5*log Var(x_i | observed); Scout uses the mutual-information
  form over the remaining missing coordinates (see docs/SCOUT_ENGINE.md).
- Sample covariance is rank-deficient (n < d); the ridge dominates. If top-1 agreement across the grid is low, treat recommendations as unstable.
- Almyros-only, annual medians, associations not causal.
