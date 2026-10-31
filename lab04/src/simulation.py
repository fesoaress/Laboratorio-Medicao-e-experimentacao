"""Reproducible Bernoulli CI-run simulator for Lab04 (P4)."""

import math
from numbers import Integral, Real

import numpy as np


def simulate_runs(n: int, p: float, seed: int = 42) -> np.ndarray:
    """Generate n independent CI outcomes: 0=success, 1=failure.

    Parameters
    ----------
    n: positive number of completed CI executions
    p: true failure probability in [0, 1]
    seed: non-negative integer used to make the sample reproducible
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 1:
        raise ValueError("n must be a positive integer")
    if isinstance(p, bool) or not isinstance(p, Real) or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("p must be a finite probability between 0 and 1")
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    rng = np.random.default_rng(int(seed))
    return rng.binomial(1, float(p), size=int(n)).astype(np.int8)
