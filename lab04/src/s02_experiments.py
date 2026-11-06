"""Lab04 S02 Q1/Q2: Monte Carlo comparison of Z and exact-binomial tests.

Both tests receive the same simulated number of failures for every
replication. Under iid Bernoulli CI outcomes, K ~ Binomial(n, p).
"""
from __future__ import annotations

import argparse
import csv
import math
from numbers import Integral, Real
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.stats import binom, norm

DEFAULT_P_VALUES = (0.05, 0.075, 0.10, 0.125, 0.15, 0.20)
OUTPUT_COLUMNS = (
    "n", "p0", "alpha", "seed", "p_true", "effect_pp", "repetitions",
    "z_rejections", "binomial_rejections", "z_rejection_rate",
    "binomial_rejection_rate", "z_monte_carlo_se", "binomial_monte_carlo_se",
)


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _probability(value: object, name: str, *, strict: bool) -> float:
    if (isinstance(value, bool) or not isinstance(value, Real)
            or not math.isfinite(value)):
        raise ValueError(f"{name} must be a finite probability")
    if not (0 < value < 1 if strict else 0 <= value <= 1):
        raise ValueError(f"{name} must be {'strictly ' if strict else ''}between 0 and 1")
    return float(value)


def run_experiments(
    n: int,
    p_values: Iterable[float],
    repetitions: int = 10_000,
    seed: int = 42,
    p0: float = 0.05,
    alpha: float = 0.05,
) -> list[dict[str, int | float]]:
    """Simulate Q1 (p_true=p0) and Q2 (increasing p_true).

    In each experiment, the same number K of failures is evaluated by
    both tests. A single RNG stream is used across p_values, avoiding
    resetting the random sequence for each scenario.

    Drawing K directly from Binomial(n,p_true) is mathematically
    equivalent to drawing n iid Bernoulli outcomes and summing them.
    """
    n = _positive_integer(n, "n")
    repetitions = _positive_integer(repetitions, "repetitions")
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    p0 = _probability(p0, "p0", strict=True)
    alpha = _probability(alpha, "alpha", strict=True)
    try:
        probabilities = tuple(p_values)
    except (TypeError, ValueError) as exc:
        raise ValueError("p_values must be a non-empty iterable of probabilities") from exc
    if not probabilities:
        raise ValueError("p_values must contain at least one probability")
    probabilities = tuple(
        _probability(value, f"p_values[{i}]", strict=False)
        for i, value in enumerate(probabilities)
    )

    rng = np.random.default_rng(int(seed))
    null_se = math.sqrt(p0 * (1 - p0) / n)
    rows: list[dict[str, int | float]] = []
    for p_true in probabilities:
        failures = rng.binomial(n, p_true, size=repetitions)
        z_statistic = (failures / n - p0) / null_se
        z_p_values = norm.sf(z_statistic)
        exact_p_values = binom.sf(failures - 1, n, p0)
        z_rejections = int(np.count_nonzero(z_p_values < alpha))
        exact_rejections = int(np.count_nonzero(exact_p_values < alpha))
        z_rate = z_rejections / repetitions
        exact_rate = exact_rejections / repetitions

        rows.append({
            "n": n,
            "p0": p0,
            "alpha": alpha,
            "seed": int(seed),
            "p_true": p_true,
            "effect_pp": round(100 * (p_true - p0), 10),
            "repetitions": repetitions,
            "z_rejections": z_rejections,
            "binomial_rejections": exact_rejections,
            "z_rejection_rate": z_rate,
            "binomial_rejection_rate": exact_rate,
            "z_monte_carlo_se": math.sqrt(z_rate * (1 - z_rate) / repetitions),
            "binomial_monte_carlo_se": math.sqrt(exact_rate * (1 - exact_rate) / repetitions),
        })

    return rows


def write_results_csv(rows: Iterable[dict], path: str | Path) -> Path:
    """Write the stable schema for dashboard G3 and G4."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab04 S02 Q1/Q2 Monte Carlo experiments")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--repetitions", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--p0", type=float, default=0.05)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument(
        "--p-values", nargs="+", type=float, default=list(DEFAULT_P_VALUES),
        help="True failure rates; include p0 for Q1 and zero-effect Q2",
    )
    parser.add_argument("--output", default="lab04/results/s02_q1_q2.csv")
    args = parser.parse_args()
    rows = run_experiments(
        n=args.n, p_values=args.p_values, repetitions=args.repetitions,
        seed=args.seed, p0=args.p0, alpha=args.alpha,
    )
    path = write_results_csv(rows, args.output)
    print(f"Saved {len(rows)} scenarios to {path}")
    print("p_true   effect_pp   Z_rejection_rate   binomial_rejection_rate")
    for row in rows:
        print(f"{row['p_true']:.3f}      {row['effect_pp']:5.1f}          "
              f"{row['z_rejection_rate']:.4f}             "
              f"{row['binomial_rejection_rate']:.4f}")


if __name__ == "__main__":
    main()
