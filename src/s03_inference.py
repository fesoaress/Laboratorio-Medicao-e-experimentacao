"""RQ05–06: correlações, grupos independentes, Holm e efeitos (#64, #65)."""

from numbers import Integral

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from .s03_descriptive import METRICS, describe

FACTORS = ("stargazers_count", "contributors_count", "repo_age_days")


def spearman(x, y, permutations=9999, seed=42):
    if isinstance(permutations, (bool, np.bool_)) or not isinstance(permutations, Integral) or permutations < 1:
        raise ValueError("O número de permutações deve ser um inteiro positivo.")
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape:
        raise ValueError("Spearman exige vetores unidimensionais de mesmo tamanho.")
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    result = dict(n=len(x), rho=None, p=None, p_permutation=None, permutations=permutations, seed=seed, status="insufficient_or_constant")
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return result
    rho, p = stats.spearmanr(x, y)
    a, b = stats.rankdata(x), stats.rankdata(y)
    a, b = a - a.mean(), b - b.mean()
    divisor = np.linalg.norm(a) * np.linalg.norm(b)
    rng = np.random.default_rng(seed)
    extreme = sum(abs(np.dot(a, rng.permutation(b)) / divisor) >= abs(rho) - 1e-14 for _ in range(permutations))
    result.update(rho=float(rho), p=float(p), p_permutation=(extreme + 1) / (permutations + 1), status="calculated")
    return result


def holm(rows, field="p", output="p_holm"):
    indices = [i for i, r in enumerate(rows) if r.get(field) is not None and np.isfinite(r[field])]
    if any(not 0 <= rows[i][field] <= 1 for i in indices):
        raise ValueError("Holm exige p-valores finitos entre 0 e 1.")
    for row in rows:
        row[output] = None
    if indices:
        adjusted = multipletests([rows[i][field] for i in indices], method="holm")[1]
        for i, value in zip(indices, adjusted):
            rows[i][output] = float(value)
    return rows


def groups_for(values):
    """Cortes globais tipo 7; empates não são divididos por ordenação artificial."""
    values = np.asarray(values, dtype=float)
    valid = values[np.isfinite(values)]
    cuts = np.unique(np.quantile(valid, [.25, .5, .75])) if len(valid) else np.array([])
    labels = np.full(len(values), -1, dtype=int)
    mask = np.isfinite(values)
    labels[mask] = np.searchsorted(cuts, values[mask], side="left")
    return labels, cuts


def compare_groups(groups):
    groups = [np.asarray(g, float)[np.isfinite(g)] for g in groups]
    groups = [g for g in groups if len(g)]
    n = sum(map(len, groups))
    output = dict(test="", statistic=None, p=None, effect=None, effect_name="", n=n, groups=len(groups), status="insufficient_groups")
    if len(groups) < 2:
        return output
    if len(groups) == 2:
        if np.ptp(np.concatenate(groups)) == 0:
            output.update(test="Mann–Whitney", status="constant")
            return output
        statistic, p = stats.mannwhitneyu(*groups, alternative="two-sided", method="asymptotic")
        output.update(test="Mann–Whitney", statistic=float(statistic), p=float(p),
                      effect=2 * statistic / (len(groups[0]) * len(groups[1])) - 1, effect_name="Cliff_delta", status="calculated")
    elif min(map(len, groups)) < 5:
        output.update(test="Kruskal–Wallis", status="insufficient_group_size_min5")
    elif np.ptp(np.concatenate(groups)) == 0:
        output.update(test="Kruskal–Wallis", status="constant")
    else:
        statistic, p = stats.kruskal(*groups)
        output.update(test="Kruskal–Wallis", statistic=float(statistic), p=float(p),
                      effect=statistic / (n - 1), effect_name="epsilon_squared_H_over_n_minus_1", status="calculated")
    return output


def run(data, permutations=9999, seed=42):
    correlations = [{"outcome": key, **spearman(data[METRICS["df"][0]], data[METRICS[key][0]], permutations, seed)}
                    for key in ("cfr_a", "cfr_b")]
    holm(correlations, "p_permutation", "p_permutation_holm")
    tests, details, boundaries = [], [], []
    for factor in FACTORS:
        labels, cuts = groups_for(data[factor])
        boundaries.append({"factor": factor, "q25": cuts[0] if len(cuts) else None,
                           "cutpoints": "|".join(map(str, cuts)), "tie_policy": "right_closed; never split equal values"})
        for metric in ("df", "lt_release", "cfr_a", "recovery", "cfr_b"):
            values = data[METRICS[metric][0]].to_numpy(float)
            groups = []
            for group in range(len(cuts) + 1):
                selected = values[labels == group]
                groups.append(selected)
                details.append({"factor": factor, "metric": metric, "group": group + 1, **describe(selected)})
            tests.append({"factor": factor, "metric": metric, "family": "supplementary_3" if metric == "cfr_b" else "primary_12",
                          **compare_groups(groups)})
    for family in ("primary_12", "supplementary_3"):
        holm([row for row in tests if row["family"] == family])
    return pd.DataFrame(correlations), pd.DataFrame(tests), pd.DataFrame(details), pd.DataFrame(boundaries)
