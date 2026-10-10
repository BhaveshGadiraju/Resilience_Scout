"""Standardization, covariance, Gaussian conditioning, EIG (Phase 3B, Features 2-4).

All z-scoring statistics are fit on TRAINING rows only and passed explicitly.
Model in z-space: x ~ N(0, Sigma_lambda), Sigma_lambda = Sigma_hat + lambda*I.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

STD_EPS = 1e-12


@dataclass(frozen=True, eq=False)
class Standardizer:
    indicators: tuple[str, ...]
    mean: np.ndarray
    std: np.ndarray
    degenerate: tuple[str, ...]

    @classmethod
    def fit(cls, X: np.ndarray, indicators) -> "Standardizer":
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[0] < 2:
            raise ValueError("need >= 2 training rows to standardize")
        if np.isnan(X).any():
            raise ValueError("NaN in training matrix; no imputation is performed")
        mean = X.mean(axis=0)
        std = X.std(axis=0, ddof=1)
        degenerate = tuple(i for i, s in zip(indicators, std) if s <= STD_EPS)
        std = np.where(std <= STD_EPS, 1.0, std)
        return cls(tuple(indicators), mean, std, degenerate)

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (np.asarray(X, dtype=float) - self.mean) / self.std

    def inverse_transform(self, Z: np.ndarray) -> np.ndarray:
        return np.asarray(Z, dtype=float) * self.std + self.mean


def sample_covariance(Z: np.ndarray) -> np.ndarray:
    return np.atleast_2d(np.cov(np.asarray(Z, dtype=float), rowvar=False, ddof=1))


def ridge_covariance(S_hat: np.ndarray, ridge: float) -> np.ndarray:
    if ridge <= 0:
        raise ValueError("ridge must be > 0 (numerical stabilizer, not a weight)")
    return S_hat + ridge * np.eye(S_hat.shape[0])


def correlation_from_cov(S: np.ndarray) -> np.ndarray:
    d = np.sqrt(np.clip(np.diag(S), 0.0, None))
    d = np.where(d <= STD_EPS, 1.0, d)
    return S / np.outer(d, d)


def logdet(A: np.ndarray) -> float:
    if A.size == 0:
        return 0.0
    sign, ld = np.linalg.slogdet(A)
    if sign <= 0:
        raise ValueError("matrix not positive definite")
    return float(ld)


def conditional_cov(S: np.ndarray, target, given) -> np.ndarray:
    t = [int(i) for i in target]
    g = [int(i) for i in given]
    if not t:
        return np.zeros((0, 0))
    Stt = S[np.ix_(t, t)]
    if not g:
        return Stt.copy()
    Stg = S[np.ix_(t, g)]
    Sgg = S[np.ix_(g, g)]
    C = Stt - Stg @ np.linalg.solve(Sgg, Stg.T)
    return (C + C.T) / 2.0


def conditional_mean(S: np.ndarray, target, given, x_given) -> np.ndarray:
    """Zero-mean z-space: E[x_t | x_g] = S_tg S_gg^-1 x_g."""
    t = [int(i) for i in target]
    g = [int(i) for i in given]
    if not t:
        return np.zeros(0)
    if not g:
        return np.zeros(len(t))
    return S[np.ix_(t, g)] @ np.linalg.solve(S[np.ix_(g, g)], np.asarray(x_given, float))


def eig_remainder(S: np.ndarray, observed, missing, i: int) -> float:
    """Mutual information (nats) between x_i and the OTHER missing coordinates,
    given observed: 0.5*logdet(S_{R|O}) - 0.5*logdet(S_{R|O,i}), R = missing \\ {i}.
    """
    rest = [j for j in missing if j != i]
    if not rest:
        return 0.0
    before = conditional_cov(S, rest, observed)
    after = conditional_cov(S, rest, list(observed) + [i])
    return 0.5 * (logdet(before) - logdet(after))


def literal_spec_value(S: np.ndarray, observed, missing, i: int) -> float:
    """The Phase 3A formula as literally written: 0.5*logdet(S_{M|O}) - 0.5*logdet(S_{M\\i|O,i}).
    Algebraically equals 0.5*log Var(x_i | O) (variance baseline). Kept for diagnostics/tests."""
    rest = [j for j in missing if j != i]
    before = conditional_cov(S, list(missing), observed)
    after = conditional_cov(S, rest, list(observed) + [i])
    return 0.5 * (logdet(before) - logdet(after))


def rank_candidates(S: np.ndarray, observed, missing) -> list[tuple[int, float]]:
    scored = [(int(j), eig_remainder(S, observed, missing, j)) for j in missing]
    scored.sort(key=lambda t: (-round(t[1], 12), t[0]))
    return scored