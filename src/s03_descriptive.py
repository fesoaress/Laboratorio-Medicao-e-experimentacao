"""RQ01–04: unidades por repositório e categorias DORA do protocolo (#62, #63)."""

import math

import numpy as np
import pandas as pd

CATEGORIES = ("Low", "Medium", "High", "Elite")
METRICS = {
    "df": ("deployment_frequency_per_week", "releases/week", "RQ01"),
    "lt_release": ("lead_time_release_median_hours", "hours", "RQ02(a)"),
    "lt_commit": ("lead_time_commit_median_hours", "hours", "RQ02(b)"),
    "cfr_a": ("cfr_ci", "fraction", "RQ03(a)"),
    "cfr_b": ("cfr_delivery", "fraction", "RQ03(b)"),
    "recovery": ("recovery_time_median_hours", "hours", "RQ04"),
}


def load_data(path):
    data = pd.read_csv(path, keep_default_na=False)
    if data.empty or data.full_name.str.casefold().duplicated().any():
        raise ValueError("População vazia ou duplicada.")
    for field in [v[0] for v in METRICS.values()] + ["deployment_frequency_per_month", "stargazers_count", "contributors_count", "repo_age_days"]:
        data[field] = pd.to_numeric(data[field].replace("", np.nan), errors="raise")
        valid = data[field].dropna()
        if (~np.isfinite(valid)).any() or (valid < 0).any():
            raise ValueError(f"Valor inválido: {field}")
    for field in ("cfr_ci", "cfr_delivery"):
        if (data[field].dropna() > 1).any():
            raise ValueError("CFR deve ser fração entre 0 e 1.")
    return data


def describe(values):
    values = np.asarray(values, dtype=float)
    valid = values[np.isfinite(values)]
    if not len(valid):
        return dict(n=0, missing=len(values), median=None, q1=None, q3=None, iqr=None, minimum=None, maximum=None)
    q1, median, q3 = np.quantile(valid, [.25, .5, .75], method="linear")
    return dict(n=len(valid), missing=len(values) - len(valid), median=median, q1=q1, q3=q3,
                iqr=q3 - q1, minimum=min(valid), maximum=max(valid))


def category(metric, value, monthly=None):
    if pd.isna(value):
        return None
    if value < 0 or not math.isfinite(value):
        raise ValueError("Métrica DORA inválida.")
    if metric == "df":
        if monthly is None or pd.isna(monthly) or monthly < 0 or not math.isfinite(monthly):
            raise ValueError("DF requer frequência mensal válida.")
        score = 4 if value >= 7 else 3 if value >= 1 else 2 if monthly >= 1 else 1
    elif metric in ("lt_release", "lt_commit"):
        score = 4 if value < 24 else 3 if value < 168 else 2 if value < 720 else 1
    elif metric in ("cfr_a", "cfr_b"):
        if value > 1:
            raise ValueError("CFR acima de 1.")
        score = 4 if value <= .15 else 3 if value <= .30 else 2 if value <= .45 else 1
    elif metric == "recovery":
        score = 4 if value < 1 else 3 if value < 24 else 2 if value < 168 else 1
    else:
        raise ValueError("Métrica desconhecida.")
    return CATEGORIES[score - 1]


def general(categories):
    if len(categories) != 4:
        raise ValueError("Categoria geral exige quatro métricas.")
    if any(v is None or pd.isna(v) for v in categories):
        return None
    return CATEGORIES[math.floor(np.median([CATEGORIES.index(v) + 1 for v in categories])) - 1]


def classify(data):
    output = data[["full_name"]].copy()
    for key, (field, _, _) in METRICS.items():
        output[key] = [category(key, v, month) for v, month in zip(data[field], data.deployment_frequency_per_month)]
    output["general"] = [general(row) for row in output[["df", "lt_release", "cfr_a", "recovery"]].itertuples(index=False, name=None)]
    return output


def run(data):
    descriptions = pd.DataFrame([{"metric": key, "unit": unit, "rq": rq, **describe(data[field])}
                                 for key, (field, unit, rq) in METRICS.items()])
    classes = classify(data)
    distribution = pd.DataFrame([{"metric": key, "category": cat, "n": int((classes[key] == cat).sum()),
        "valid": int(classes[key].notna().sum()), "missing": int(classes[key].isna().sum())}
        for key in [*METRICS, "general"] for cat in CATEGORIES])
    return descriptions, classes, distribution
