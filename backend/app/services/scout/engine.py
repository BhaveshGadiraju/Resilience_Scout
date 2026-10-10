"""Scout recommendation engine (Phase 3B, Features 4-6). Deterministic; no LLM."""
from __future__ import annotations

import numpy as np

from .model import (
    Standardizer,
    conditional_cov,
    correlation_from_cov,
    logdet,
    rank_candidates,
    ridge_covariance,
    sample_covariance,
)
from .panel import AnnualPanel

ENGINE_VERSION = "3b.1"
SPEC_VERSION = "3a.1"
DEFAULT_RIDGE = 0.1
DEFAULT_RIDGE_GRID = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
MIN_TRAIN_YEARS = 3


def _spearman(a, b) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if len(a) < 2:
        return 1.0
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    if ra.std() == 0 or rb.std() == 0:
        return 1.0
    return float(np.corrcoef(ra, rb)[0, 1])


def ridge_sensitivity(S_hat, observed, missing, grid, default) -> dict:
    lams = sorted(set(grid) | {default})
    tops, vecs = {}, {}
    for lam in lams:
        ranked = rank_candidates(ridge_covariance(S_hat, lam), observed, missing)
        tops[lam] = ranked[0][0]
        d = dict(ranked)
        vecs[lam] = np.array([d[j] for j in missing])
    base = vecs[default]
    rows = [
        {
            "ridge": float(lam),
            "top1_index": int(tops[lam]),
            "rank_spearman_vs_default": _spearman(base, vecs[lam]),
        }
        for lam in lams
    ]
    return {
        "grid": rows,
        "top1_stable": len(set(tops.values())) == 1,
        "min_rank_spearman": min(r["rank_spearman_vs_default"] for r in rows),
    }


def recommend(
    panel: AnnualPanel,
    target_year: int,
    observed: list[str],
    ridge: float = DEFAULT_RIDGE,
    ridge_grid=DEFAULT_RIDGE_GRID,
    min_train_years: int = MIN_TRAIN_YEARS,
) -> dict:
    """Rank missing core indicators by Gaussian EIG. Training uses complete years < target_year only."""
    names = panel.indicators
    unknown = [o for o in observed if o not in names]
    if unknown:
        raise ValueError(f"unknown/non-core indicators: {unknown}")
    obs_idx = [names.index(o) for o in dict.fromkeys(observed)]
    missing = [j for j in range(len(names)) if j not in obs_idx]
    if not missing:
        raise ValueError("no missing indicators: nothing to recommend")

    train_years = [y for y in panel.complete_years() if y < target_year]
    if len(train_years) < min_train_years:
        raise ValueError(
            f"only {len(train_years)} complete training years < {target_year}; "
            f"need >= {min_train_years}"
        )
    Xtr = panel.matrix(train_years)
    std = Standardizer.fit(Xtr, names)
    S_hat = sample_covariance(std.transform(Xtr))
    S = ridge_covariance(S_hat, ridge)
    corr = correlation_from_cov(S_hat)

    ranked = rank_candidates(S, obs_idx, missing)
    sens = ridge_sensitivity(S_hat, obs_idx, missing, ridge_grid, ridge)
    top, top_eig = ranked[0]

    rest = [j for j in missing if j != top]
    cov_before = conditional_cov(S, rest, obs_idx)
    cov_after = conditional_cov(S, rest, obs_idx + [top])
    tr_b, tr_a = float(np.trace(cov_before)), float(np.trace(cov_after))
    assoc = sorted(
        (j for j in range(len(names)) if j != top),
        key=lambda j: -abs(corr[top, j]),
    )[:3]

    limitations = [
        f"small historical sample: {len(train_years)} training years for {len(names)} indicators; "
        "sample covariance is rank-deficient and the ridge strongly shapes results",
        "annual medians only; no sub-annual dynamics",
        "Almyros-only; not transferable to other sites",
        "Gaussian working assumption; associations are not causal",
        "scale anomalies exist in OAH mean/min/max companions (medians used, values unmodified)",
        "recommendation is measurement prioritization, not ecological diagnosis",
    ]
    if not sens["top1_stable"]:
        limitations.insert(0, "UNSTABLE: top-1 recommendation changes across the ridge grid")

    return {
        "data_class": "derived",
        "engine_version": ENGINE_VERSION,
        "spec_version": SPEC_VERSION,
        "target_year": target_year,
        "training_years": train_years,
        "n_train_years": len(train_years),
        "observed": [names[j] for j in obs_idx],
        "ridge": ridge,
        "recommendation": names[top],
        "rankings": [
            {"indicator": names[j], "eig": float(e), "rank": r + 1}
            for r, (j, e) in enumerate(ranked)
        ],
        "ridge_stability": "stable" if sens["top1_stable"] else "unstable",
        "ridge_sensitivity": {
            "top1_stable": sens["top1_stable"],
            "min_rank_spearman": sens["min_rank_spearman"],
            "grid": [
                {
                    "ridge": r["ridge"],
                    "top1": names[r["top1_index"]],
                    "rank_spearman_vs_default": r["rank_spearman_vs_default"],
                }
                for r in sens["grid"]
            ],
        },
        "explanation": {
            "recommended_observation": names[top],
            "eig_nats": float(top_eig),
            "remainder_uncertainty_logdet_before": 0.5 * logdet(cov_before),
            "remainder_uncertainty_logdet_after": 0.5 * logdet(cov_after),
            "trace_reduction_fraction": (1.0 - tr_a / tr_b) if tr_b > 0 else 0.0,
            "top_associated_indicators": [
                {"indicator": names[j], "correlation": float(corr[top, j])}
                for j in assoc
            ],
            "readiness_class": "candidate_core",
            "limitations": limitations,
            "note": (
                "EIG is Gaussian mutual information between the candidate and the other "
                "missing indicators. Under a Gaussian model the posterior covariance does "
                "not depend on the observed value."
            ),
        },
    }