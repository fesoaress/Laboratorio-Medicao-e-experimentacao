"""Transparent, reproducible S01 demonstration; does not use real CI data."""

import json

from lab04.src.simulation import simulate_runs
from lab04.src.stat_tests import evaluate_tests


def build_example() -> dict:
    n, true_p, seed = 30, 0.10, 42
    outcomes = simulate_runs(n=n, p=true_p, seed=seed)
    results = evaluate_tests(outcomes, p0=0.05, alpha=0.05)
    return {
        "dataset": "simulated (not real GitHub Actions observations)",
        "scenario": "One-sided increase in CI failure rate above 5%",
        "n": n,
        "true_failure_probability": true_p,
        "seed": seed,
        "outcomes_0_success_1_failure": outcomes.tolist(),
        "tests": results,
        "interpretation": {
            "z": ("Reject H0" if results["reject_z"] else "Do not reject H0"),
            "binomial": ("Reject H0" if results["reject_binomial"] else "Do not reject H0"),
            "note": "Neither p-value is the probability that H0 is true. One sample cannot establish which test is better; that requires the S02 simulation study.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_example(), indent=2, ensure_ascii=False))
