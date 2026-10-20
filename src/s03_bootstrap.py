"""Inovação: IC percentil 95%, reamostragem de repositórios (#67)."""

from numbers import Integral

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from .s03_descriptive import METRICS


def bootstrap(x, y=None, *, iterations=2000, seed=42):
    if isinstance(iterations, (bool, np.bool_)) or not isinstance(iterations, Integral) or iterations < 1000:
        raise ValueError("Bootstrap exige um inteiro de pelo menos 1000 reamostragens.")
    x = np.asarray(x, float)
    if y is not None:
        y = np.asarray(y, float)
        if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape:
            raise ValueError("Bootstrap pareado exige vetores unidimensionais de mesmo tamanho.")
    elif x.ndim != 1:
        raise ValueError("Bootstrap exige um vetor unidimensional de repositórios.")
    mask = np.isfinite(x)
    if y is not None:
        mask &= np.isfinite(y)
        y = y[mask]
    x = x[mask]
    result = dict(n=len(x), estimate=None, lower95=None, upper95=None, iterations=iterations,
                  valid_replicates=0, seed=seed, method="repository_percentile_95", status="insufficient")
    if len(x) < (3 if y is not None else 1):
        return result
    def statistic(a, b):
        if b is None:
            return float(np.median(a))
        if np.ptp(a) == 0 or np.ptp(b) == 0:
            return np.nan
        return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
    estimate = statistic(x, y)
    if not np.isfinite(estimate):
        result["status"] = "constant"
        return result
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(iterations):
        indices = rng.integers(0, len(x), len(x))
        value = statistic(x[indices], y[indices] if y is not None else None)
        if np.isfinite(value):
            samples.append(value)
    low, high = np.quantile(samples, [.025, .975])
    result.update(estimate=estimate, lower95=low, upper95=high, valid_replicates=len(samples), status="calculated")
    return result


def run(data, iterations=2000, seed=42):
    rows = [{"statistic": "median_" + key, **bootstrap(data[METRICS[key][0]], iterations=iterations, seed=seed)}
            for key in ("df", "cfr_a", "cfr_b")]
    rows += [{"statistic": "rho_df_" + key, **bootstrap(data[METRICS["df"][0]], data[METRICS[key][0]], iterations=iterations, seed=seed)}
             for key in ("cfr_a", "cfr_b")]
    return pd.DataFrame(rows)
