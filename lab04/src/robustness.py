"""Lab04 S02 Q3: small-sample check of the one-sided Z and exact tests.

The Monte Carlo engine and CSV schema are shared with Q1/Q2 (#81).  Q3 writes
only the critical condition (n=30); the dashboard reads the n=200 reference
from s02_q1_q2.csv and combines the two conditions itself (#83).
"""

from __future__ import annotations

import argparse
import math

import numpy as np
from scipy.stats import binom, norm

from lab04.src.s02_experiments import (
    DEFAULT_P_VALUES,
    run_experiments,
    write_results_csv,
)

CRITICAL_N = 30
REFERENCE_N = 200
P0 = 0.05
ALPHA = 0.05
REPETITIONS = 10_000
SEED = 42


def run_robustness(repetitions: int = REPETITIONS, seed: int = SEED) -> list[dict]:
    """Repeat Q1/Q2 at n=30, reusing the simulation engine and CSV schema.

    The n=200 reference was already simulated by #81 and is stored in
    s02_q1_q2.csv. Both tests see the same failure count in each replication.
    """
    return run_experiments(
        n=CRITICAL_N, p_values=DEFAULT_P_VALUES, repetitions=repetitions,
        seed=seed, p0=P0, alpha=ALPHA,
    )


def null_rejection_regions(n: int, p0: float = P0, alpha: float = ALPHA) -> dict[str, int | float]:
    """Find each test's first rejected count and its exact size under p=p0.

    This enumerates possible counts rather than simulating them.  The exact
    sizes explain whether Monte Carlo rates above/below alpha are structural
    consequences of the discrete rejection boundaries or simulation noise.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    if not (math.isfinite(p0) and 0 < p0 < 1):
        raise ValueError("p0 must be strictly between 0 and 1")
    if not (math.isfinite(alpha) and 0 < alpha < 1):
        raise ValueError("alpha must be strictly between 0 and 1")

    counts = np.arange(n + 1)
    null_se = math.sqrt(p0 * (1 - p0) / n)
    z_p = norm.sf((counts / n - p0) / null_se)
    exact_p = binom.sf(counts - 1, n, p0)
    z_rejected = np.flatnonzero(z_p < alpha)
    exact_rejected = np.flatnonzero(exact_p < alpha)
    z_first = int(z_rejected[0]) if z_rejected.size else n + 1
    exact_first = int(exact_rejected[0]) if exact_rejected.size else n + 1
    return {
        "n": n,
        "expected_failures": n * p0,
        "z_first_rejected_k": z_first,
        "binomial_first_rejected_k": exact_first,
        "z_actual_null_rejection": float(binom.sf(z_first - 1, n, p0)),
        "binomial_actual_null_rejection": float(binom.sf(exact_first - 1, n, p0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab04 S02 Q3: small-sample robustness")
    parser.add_argument("--repetitions", type=int, default=REPETITIONS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", default="lab04/results/s02_q3.csv")
    args = parser.parse_args()

    rows = run_robustness(repetitions=args.repetitions, seed=args.seed)
    destination = write_results_csv(rows, args.output)
    print(f"Saved {len(rows)} critical scenarios to {destination}")
    null = rows[0]
    region = null_rejection_regions(CRITICAL_N)
    print(
        f"n={CRITICAL_N}: n*p0={region['expected_failures']:g}, "
        f"Z={null['z_rejection_rate']:.4f} (K>={region['z_first_rejected_k']}), "
        f"exact={null['binomial_rejection_rate']:.4f} "
        f"(K>={region['binomial_first_rejected_k']})"
    )


if __name__ == "__main__":
    main()
