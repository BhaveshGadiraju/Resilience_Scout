"""Leakage-safe rolling-origin replay with baselines + ridge sensitivity (Phase 3B).

For each test year T (complete years with >= min_train earlier complete years):
  train scaler + covariance on years < T only; hide k core coordinates of T;
  each strategy picks one hidden indicator; reveal real z-scored medians;
  realized metric = MSE reduction on the remaining hidden coordinates.
Random baseline is the exact expectation over a uniform pick (no RNG).
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from .engine import DEFAULT_RIDGE, DEFAULT_RIDGE_GRID, MIN_TRAIN_YEARS
from .model import (
    Standardizer,
    conditional_cov,
    conditional_mean,
    correlation_from_cov,
    rank_candidates,
    ridge_covariance,
    sample_covariance,
)
from .panel import AnnualPanel

STRATEGIES = ("scout", "correlation", "variance", "random")


def realized_mse_reduction(S, observed, missing, z, i) -> float:
    rest = [j for j in missing if j != i]
    if not rest:
        return 0.0
    before = conditional_mean(S, rest, observed, z[observed])
    after = conditional_mean(S, rest, observed + [i], z[observed + [i]])
    return float(np.sum((z[rest] - before) ** 2) - np.sum((z[rest] - after) ** 2))


def _pick_scout(S, corr, observed, missing) -> int:
    return rank_candidates(S, observed, missing)[0][0]


def _pick_variance(S, corr, observed, missing) -> int:
    # Marginal variance is constant (=1) in z-space, so use conditional variance given observed.
    cv = {j: float(conditional_cov(S, [j], observed)[0, 0]) for j in missing}
    return sorted(missing, key=lambda j: (-round(cv[j], 12), j))[0]


def _pick_correlation(S, corr, observed, missing) -> int:
    sc = {j: max(abs(corr[j, o]) for o in observed) for j in missing}
    return sorted(missing, key=lambda j: (-round(sc[j], 12), j))[0]


def run_backtest(
    panel: AnnualPanel,
    k_missing_values=(3, 4),
    ridge: float = DEFAULT_RIDGE,
    ridge_grid=DEFAULT_RIDGE_GRID,
    min_train_years: int = MIN_TRAIN_YEARS,
) -> dict:
    names = panel.indicators
    d = len(names)
    years = panel.complete_years()
    folds = [T for T in years if sum(1 for y in years if y < T) >= min_train_years]
    if not folds:
        raise ValueError("no eligible folds; reduce min_train_years")
    lams = sorted(set(ridge_grid) | {ridge})
    scen, sens = [], []

    for T in folds:
        train_years = [y for y in years if y < T]
        Xtr = panel.matrix(train_years)
        std = Standardizer.fit(Xtr, names)
        S_hat = sample_covariance(std.transform(Xtr))
        S_by = {lam: ridge_covariance(S_hat, lam) for lam in lams}
        S = S_by[ridge]
        corr = correlation_from_cov(S_hat)
        z = std.transform(panel.matrix([T])[0])

        for k in k_missing_values:
            if not (2 <= k <= d - 1):
                raise ValueError("k_missing must be in [2, d-1]")
            for miss in combinations(range(d), k):
                missing = list(miss)
                observed = [j for j in range(d) if j not in missing]
                mse = {i: realized_mse_reduction(S, observed, missing, z, i) for i in missing}
                eigs = dict(rank_candidates(S, observed, missing))
                picks = {
                    "scout": _pick_scout(S, corr, observed, missing),
                    "variance": _pick_variance(S, corr, observed, missing),
                    "correlation": _pick_correlation(S, corr, observed, missing),
                }
                label = "|".join(names[j] for j in missing)
                base = dict(fold_year=T, k_missing=k, missing=label)
                for strat, i in picks.items():
                    rank = 1 + sum(1 for j in missing if mse[j] > mse[i] + 1e-12)
                    scen.append({**base, "strategy": strat, "pick": names[i],
                                 "mse_reduction": mse[i], "realized_rank": rank,
                                 "oracle_hit": float(rank == 1), "model_eig": eigs[i]})
                scen.append({**base, "strategy": "random", "pick": "(expectation)",
                             "mse_reduction": float(np.mean(list(mse.values()))),
                             "realized_rank": (k + 1) / 2.0, "oracle_hit": 1.0 / k,
                             "model_eig": float(np.mean(list(eigs.values())))})
                for lam in lams:
                    top = rank_candidates(S_by[lam], observed, missing)[0][0]
                    sens.append({**base, "ridge": lam, "top1": names[top],
                                 "same_top1_as_default": float(top == picks["scout"]),
                                 "mse_reduction": realized_mse_reduction(
                                     S_by[lam], observed, missing, z, top)})

    df = pd.DataFrame(scen)
    sdf = pd.DataFrame(sens)
    order = {s: n for n, s in enumerate(STRATEGIES)}
    agg = dict(mean_mse_reduction=("mse_reduction", "mean"),
               mean_realized_rank=("realized_rank", "mean"),
               oracle_hit_rate=("oracle_hit", "mean"),
               mean_model_eig=("model_eig", "mean"),
               n_scenarios=("mse_reduction", "size"))
    by_strategy = df.groupby("strategy").agg(**agg).reset_index()
    by_strategy = by_strategy.sort_values("strategy", key=lambda c: c.map(order))
    by_fold = df.groupby(["fold_year", "strategy"]).agg(**agg).reset_index()
    by_fold = by_fold.sort_values(["fold_year", "strategy"],
                                  key=lambda c: c.map(order) if c.name == "strategy" else c)
    sens_sum = sdf.groupby("ridge").agg(
        top1_agreement_with_default=("same_top1_as_default", "mean"),
        mean_mse_reduction=("mse_reduction", "mean")).reset_index()

    piv = df[df.strategy == "scout"].pivot(
        index=["k_missing", "missing"], columns="fold_year", values="pick")
    pairs = list(combinations(piv.columns, 2))
    across = (float(np.mean([(piv[a] == piv[b]).mean() for a, b in pairs]))
              if pairs else None)

    summary = {
        "data_class": "derived",
        "folds": [int(f) for f in folds],
        "k_missing_values": list(k_missing_values),
        "ridge_default": ridge,
        "ridge_grid": [float(x) for x in lams],
        "n_scenarios_per_strategy": int(len(df) // len(STRATEGIES)),
        "scout_top1_agreement_across_folds": across,
        "by_strategy": by_strategy.to_dict(orient="records"),
        "by_fold": by_fold.to_dict(orient="records"),
        "ridge_sensitivity": sens_sum.to_dict(orient="records"),
    }
    return {"summary": summary, "scenarios": df, "sensitivity": sdf,
            "by_strategy": by_strategy, "by_fold": by_fold, "ridge_table": sens_sum}


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(
            f"{v:.4f}" if isinstance(v, float) else str(v) for v in r.values) + " |")
    return "\n".join(out)


def write_outputs(result: dict, out_dir: Path | str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    s = result["summary"]
    result["scenarios"].to_csv(out / "per_scenario.csv", index=False)
    result["sensitivity"].to_csv(out / "ridge_sensitivity_per_scenario.csv", index=False)
    result["by_fold"].to_csv(out / "by_fold.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(s, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
        encoding="utf-8")
    report = f"""# Scout Phase 3B backtest report (data_class: derived)

Real Almyros annual medians (OAH). Rolling-origin replay, training on years strictly < T.
Folds (test years): {s['folds']}. Hidden-set sizes k: {s['k_missing_values']}.
Scenarios per strategy: {s['n_scenarios_per_strategy']}. Default ridge: {s['ridge_default']}.

## Overall (higher mean MSE reduction = better; rank 1 = best of the hidden candidates)

{_md(result['by_strategy'])}

## Per fold

{_md(result['by_fold'])}

## Ridge sensitivity (Scout)

{_md(result['ridge_table'])}

Scout top-1 agreement across folds (same hidden set): {s['scout_top1_agreement_across_folds']}

## Read this before quoting numbers

- Only {len(s['folds'])} test folds with 3-5 training years each; no statistical significance is claimed.
- Realized metric = MSE reduction on the other hidden coordinates after revealing the pick. Gaussian log-det
  reduction (model_eig) does not depend on the revealed value, so it is model-implied, not realized.
- Random is the exact expectation over a uniform pick.
- Variance baseline uses conditional variance given observed coordinates (marginal variance is 1 for all in z-space).
- The Phase 3A EIG formula as written equals 0.5*log Var(x_i | observed); Scout uses the mutual-information
  form over the remaining missing coordinates (see docs/SCOUT_ENGINE.md).
- Sample covariance is rank-deficient (n < d); the ridge dominates. If top-1 agreement across the grid is low, treat recommendations as unstable.
- Almyros-only, annual medians, associations not causal.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")