import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.scout.backtest import run_backtest  # noqa: E402
from app.services.scout.engine import recommend  # noqa: E402
from app.services.scout.model import (  # noqa: E402
    Standardizer, conditional_cov, eig_remainder, literal_spec_value, logdet,
    rank_candidates, ridge_covariance, sample_covariance,
)
from app.services.scout.panel import (  # noqa: E402
    CORE_INDICATORS, DEFAULT_OBSERVATIONS_PATH, AnnualPanel, load_annual_median_panel,
)


def _synthetic_panel(n=8, seed=0, years_start=2000):
    # SYNTHETIC SCHEMA FIXTURE for math tests. Not OAH data; makes no environmental claim.
    rng = np.random.default_rng(seed)
    base = rng.normal(size=(n, 3))
    vals = base @ rng.normal(size=(3, 8)) + 0.3 * rng.normal(size=(n, 8))
    return AnnualPanel(tuple(range(years_start, years_start + n)), CORE_INDICATORS, vals, {})


def _spd(d=6, seed=1):
    A = np.random.default_rng(seed).normal(size=(d, d))
    return A @ A.T + np.eye(d)


def test_mutual_information_identity():
    S = _spd()
    obs, miss, i = [0], [1, 2, 3, 4, 5], 2
    rest = [1, 3, 4, 5]
    var_i = conditional_cov(S, [i], obs)[0, 0]
    rhs = 0.5 * np.log(var_i * np.linalg.det(conditional_cov(S, rest, obs))
                       / np.linalg.det(conditional_cov(S, miss, obs)))
    assert eig_remainder(S, obs, miss, i) == pytest.approx(rhs)
    assert eig_remainder(S, obs, miss, i) >= 0


def test_literal_spec_formula_is_just_conditional_variance():
    S = _spd()
    obs, miss, i = [0], [1, 2, 3, 4, 5], 3
    var_i = conditional_cov(S, [i], obs)[0, 0]
    assert literal_spec_value(S, obs, miss, i) == pytest.approx(0.5 * np.log(var_i))


def test_conditional_cov_matches_precision_form():
    S = _spd()
    P = np.linalg.inv(S)
    got = conditional_cov(S, [0, 1], [2, 3, 4, 5])
    assert got == pytest.approx(np.linalg.inv(P[np.ix_([0, 1], [0, 1])]))


def test_ridge_lower_bounds_eigenvalues():
    X = np.random.default_rng(0).normal(size=(3, 8))  # n < d -> rank-deficient
    Sl = ridge_covariance(sample_covariance(X), 0.1)
    assert np.linalg.eigvalsh(Sl).min() >= 0.1 - 1e-9
    assert logdet(Sl) == pytest.approx(np.log(np.linalg.eigvalsh(Sl)).sum())


def test_standardizer_fit_uses_only_given_rows():
    X = np.random.default_rng(2).normal(size=(6, 8))
    a = Standardizer.fit(X[:4], CORE_INDICATORS)
    X2 = X.copy()
    X2[4:] += 100.0
    b = Standardizer.fit(X2[:4], CORE_INDICATORS)
    assert np.allclose(a.mean, b.mean) and np.allclose(a.std, b.std)
    assert np.allclose(a.inverse_transform(a.transform(X)), X)


def test_recommend_has_no_future_leakage():
    p1 = _synthetic_panel(seed=0)
    vals = p1.values.copy()
    vals[5:] = np.random.default_rng(99).normal(size=vals[5:].shape) * 50  # years >= 2005
    p2 = AnnualPanel(p1.years, p1.indicators, vals, {})
    obs = ["chloride", "nitrate"]
    r1 = recommend(p1, 2005, obs)
    r2 = recommend(p2, 2005, obs)
    assert r1["training_years"] == [2000, 2001, 2002, 2003, 2004]
    assert r1["rankings"] == r2["rankings"]


def test_recommend_only_ranks_missing_core_indicators():
    r = recommend(_synthetic_panel(), 2008, ["chloride", "nitrate"])
    ranked = {x["indicator"] for x in r["rankings"]}
    assert ranked.isdisjoint({"chloride", "nitrate"}) and len(ranked) == 6
    assert [x["rank"] for x in r["rankings"]] == list(range(1, 7))
    assert r["data_class"] == "derived" and r["explanation"]["limitations"]


def test_recommend_rejects_too_little_history():
    with pytest.raises(ValueError):
        recommend(_synthetic_panel(), 2002, ["chloride"])


def test_backtest_synthetic_runs_and_is_consistent():
    res = run_backtest(_synthetic_panel(n=7), k_missing_values=(3,))
    s = res["summary"]
    assert s["folds"] == [2003, 2004, 2005, 2006]
    row = res["ridge_table"][res["ridge_table"].ridge == 0.1].iloc[0]
    assert row.top1_agreement_with_default == 1.0
    scout = res["by_strategy"].set_index("strategy").loc["scout"]
    assert 1.0 <= scout.mean_realized_rank <= 3.0


@pytest.mark.skipif(not DEFAULT_OBSERVATIONS_PATH.exists(), reason="run normalize_almyros.py")
def test_real_almyros_core_panel_matches_spec():
    p = load_annual_median_panel()
    assert p.complete_years() == (2013, 2014, 2015, 2018, 2019, 2020)
    assert not np.isnan(p.matrix(p.complete_years())).any()


@pytest.mark.skipif(not DEFAULT_OBSERVATIONS_PATH.exists(), reason="run normalize_almyros.py")
def test_real_almyros_backtest_runs():
    p = load_annual_median_panel()
    res = run_backtest(p, k_missing_values=(3,))
    assert res["summary"]["folds"] == [2018, 2019, 2020]