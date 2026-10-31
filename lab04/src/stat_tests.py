"""Right-tailed one-proportion Z and exact binomial tests for Lab04 P4."""

import math
from numbers import Real

import numpy as np
from scipy.stats import binomtest, norm


def evaluate_tests(data, p0: float = 0.05, alpha: float = 0.05) -> dict:
    """Compare H0: p <= p0 against H1: p > p0 on identical binary data.

    Tests are computed at the least-favorable null boundary p=p0.
    Returns plain Python values suitable for JSON and Streamlit.
    """
    if isinstance(p0, bool) or not isinstance(p0, Real) or not math.isfinite(p0) or not 0 < p0 < 1:
        raise ValueError("p0 must be strictly between 0 and 1")
    if isinstance(alpha, bool) or not isinstance(alpha, Real) or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between 0 and 1")

    observations = np.asarray(data)
    if observations.ndim != 1 or observations.size == 0 or not np.isin(observations, [0, 1]).all():
        raise ValueError("data must be a non-empty 1D sequence of binary outcomes (0 or 1)")

    n = int(observations.size)
    k = int(np.count_nonzero(observations))
    p_hat = k / n
    std_err_h0 = math.sqrt(float(p0) * (1 - float(p0)) / n)
    z = (p_hat - float(p0)) / std_err_h0
    z_p = float(norm.sf(z))
    exact_p = float(binomtest(k, n, float(p0), alternative="greater").pvalue)

    return {
        "n": n,
        "k": k,
        "p_hat": p_hat,
        "p0": float(p0),
        "alpha": float(alpha),
        "alternative": "greater",
        "z_statistic": float(z),
        "z_critical": float(norm.isf(alpha)),
        "z_p_value": z_p,
        "binomial_p_value": exact_p,
        "reject_z": bool(z_p < alpha),
        "reject_binomial": bool(exact_p < alpha),
        "z_expected_failures": float(n * p0),
        "z_expected_successes": float(n * (1 - p0)),
        "z_normal_approximation_caution": bool(n * p0 < 5 or n * (1 - p0) < 5),
    }
