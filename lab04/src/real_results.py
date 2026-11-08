"""Results of the Lab04 tests on validated, observed CI runs (Issue #85)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lab04.src.real_data import summarize_ci_runs
from lab04.src.stat_tests import evaluate_tests


def calculate_real_results(
    runs: pd.DataFrame, p0: float = 0.05, alpha: float = 0.05,
) -> dict:
    """Validate real runs and evaluate both tests on their sufficient counts.

    For one-proportion tests, n and k completely determine the statistic and
    p-value. Reconstructing a fixed 0/1 array from validated counts does not
    resample or simulate observations; it lets us reuse the statistical core.
    """
    summary = summarize_ci_runs(runs)  # Also rejects malformed or duplicate runs.
    n, k = summary["n"], summary["k"]
    outcomes = np.concatenate((np.zeros(n - k, dtype=np.int8), np.ones(k, dtype=np.int8)))
    tests = evaluate_tests(outcomes, p0=p0, alpha=alpha)
    effect_pp = 100 * (summary["p_hat"] - tests["p0"])

    return {
        "n": n,
        "k": k,
        "p_hat": summary["p_hat"],
        "p0": tests["p0"],
        "alpha": tests["alpha"],
        "effect_pp": effect_pp,  # Signed, unstandardized difference in percentage points.
        "effect_magnitude_pp": abs(effect_pp),
        "tests": tests,
        "table_rows": [
            {
                "test": "Z para uma proporção",
                "statistic_name": "Z",
                "statistic": tests["z_statistic"],
                "p_value": tests["z_p_value"],
                "effect_pp": effect_pp,
                "reject_h0": tests["reject_z"],
            },
            {
                "test": "Binomial exato",
                "statistic_name": "K (falhas)",
                "statistic": k,
                "p_value": tests["binomial_p_value"],
                "effect_pp": effect_pp,
                "reject_h0": tests["reject_binomial"],
            },
        ],
    }


def interpret_real_results(result: dict) -> str:
    """State the observed decision without treating non-rejection as proof of H0."""
    z = result["tests"]["reject_z"]
    exact = result["tests"]["reject_binomial"]
    target = f"{result['p0']:.0%}"
    level = f"{result['alpha']:.0%}"
    if z and exact:
        decision = f"Ambos os testes encontraram evidência de taxa de falha acima de {target} (α={level})."
    elif not z and not exact:
        decision = (
            f"Nenhum dos testes encontrou evidência de taxa de falha acima de {target} "
            f"(α={level}); isso não comprova que a taxa verdadeira seja menor ou igual à meta."
        )
    else:
        decision = (
            f"Os testes chegaram a decisões diferentes para a meta de {target} (α={level}); "
            "a aproximação normal deve ser examinada antes de interpretar o Z."
        )
    signed = f"{result['effect_pp']:+.2f}".replace(".", ",")
    magnitude = f"{result['effect_magnitude_pp']:.2f}".replace(".", ",")
    return (
        f"{decision} A diferença observada p̂−p₀ foi {signed} p.p. "
        f"(magnitude {magnitude} p.p.)."
    )
