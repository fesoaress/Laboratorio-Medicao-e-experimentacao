"""Leitura e preparo das tabelas agregadas de Q1/Q2/Q3 (Issues #81 e #82) para G3 e G4.

Esquema esperado (o mesmo de ``lab04/src/s02_experiments.py``):
n, p0, alpha, seed, p_true, effect_pp, repetitions, z_rejections, binomial_rejections,
z_rejection_rate, binomial_rejection_rate, z_monte_carlo_se, binomial_monte_carlo_se.

Arquivos lidos (se existirem) em ``lab04/results/`` ou em ``$LAB04_RESULTS_DIR``:
``s02_q1_q2.csv`` (condição de referência) e ``s02_q3.csv`` (condição de pressuposto
problemático). Nenhum valor é embutido no código: tudo vem das tabelas.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = (
    "n", "p0", "alpha", "seed", "p_true", "effect_pp", "repetitions",
    "z_rejections", "binomial_rejections", "z_rejection_rate",
    "binomial_rejection_rate", "z_monte_carlo_se", "binomial_monte_carlo_se",
)
TABLE_FILES = {"q1_q2": "s02_q1_q2.csv", "q3": "s02_q3.csv"}
DEFAULT_DIR = Path(__file__).resolve().parents[1] / "results"


def results_dir() -> Path:
    return Path(os.environ.get("LAB04_RESULTS_DIR", DEFAULT_DIR))


def validate_s02_table(df: pd.DataFrame, name: str = "tabela") -> pd.DataFrame:
    """Valida colunas, tipos e coerência (taxa = rejeições / repetições). Levanta ValueError."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: colunas ausentes: {', '.join(missing)}")
    if df.empty:
        raise ValueError(f"{name}: tabela vazia")
    out = df[list(REQUIRED_COLUMNS)].copy()
    try:
        out = out.astype(float)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name}: valores não numéricos ({exc})") from exc
    if not out.map(math.isfinite).all().all():
        raise ValueError(f"{name}: valores não finitos")
    for rate, count in (("z_rejection_rate", "z_rejections"),
                        ("binomial_rejection_rate", "binomial_rejections")):
        if not ((out[rate] >= 0) & (out[rate] <= 1)).all():
            raise ValueError(f"{name}: {rate} fora de [0, 1]")
        if not ((out[rate] - out[count] / out["repetitions"]).abs() < 1e-9).all():
            raise ValueError(f"{name}: {rate} não confere com rejeições/repetições")
    for col in ("n", "p0", "alpha", "repetitions"):
        if out[col].nunique() != 1:
            raise ValueError(f"{name}: '{col}' deve ser único dentro de uma condição")
    if not (out["effect_pp"].abs() < 1e-8).any():
        raise ValueError(f"{name}: falta o cenário de efeito zero (H0 verdadeira)")
    return out.sort_values("effect_pp").reset_index(drop=True)


def condition_label(n: float, p0: float) -> str:
    return f"n = {int(n)} (n·p0 = {str(f'{n * p0:g}').replace('.', ',')})"


def normal_approx_ok(n: float, p0: float) -> bool:
    """Mesma heurística de ``stat_tests``: n·p0 ≥ 5 e n·(1−p0) ≥ 5."""
    return n * p0 >= 5 and n * (1 - p0) >= 5


def load_s02_tables(directory: str | Path | None = None) -> dict[str, pd.DataFrame | None]:
    """Lê as tabelas disponíveis; ausente → None. Tabela inválida levanta ValueError."""
    base = Path(directory) if directory is not None else results_dir()
    tables: dict[str, pd.DataFrame | None] = {}
    for key, filename in TABLE_FILES.items():
        path = base / filename
        tables[key] = validate_s02_table(pd.read_csv(path), filename) if path.exists() else None
    return tables


def combine_conditions(tables: list[pd.DataFrame]) -> pd.DataFrame:
    """Junta tabelas validadas e rotula cada condição pelos próprios parâmetros (n, n·p0).

    Se duas tabelas trouxerem o mesmo (n, p0, alpha, p_true), a primeira prevalece.
    """
    frames = []
    for t in tables:
        t = t.copy()
        t["condition"] = [condition_label(n, p0) for n, p0 in zip(t["n"], t["p0"])]
        t["normal_ok"] = [normal_approx_ok(n, p0) for n, p0 in zip(t["n"], t["p0"])]
        frames.append(t)
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["n", "p0", "alpha", "p_true"], keep="first")
    order = combined.groupby("condition", sort=False)["n"].first().sort_values(ascending=False).index
    combined["condition"] = pd.Categorical(combined["condition"], categories=list(order), ordered=True)
    return combined.sort_values(["condition", "effect_pp"]).reset_index(drop=True)


def classify_type1(rate: float, alpha: float, repetitions: float) -> str:
    """Compara a taxa sob H0 com α usando o erro-padrão de Monte Carlo sob α (1,96 EP)."""
    se0 = math.sqrt(alpha * (1 - alpha) / repetitions)
    if abs(rate - alpha) <= 1.96 * se0:
        return "compatível com α"
    return "liberal" if rate > alpha else "conservador"


def type1_table(cond: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por condição: taxas sob H0 (efeito 0), EP de Monte Carlo e classificação."""
    zero = cond[cond["effect_pp"].abs() < 1e-8]
    rows = []
    for c, g in zero.groupby("condition", observed=True, sort=False):
        r = g.iloc[0]
        rows.append({
            "condition": str(c), "n": int(r["n"]), "alpha": r["alpha"], "repetitions": int(r["repetitions"]),
            "z_rate": r["z_rejection_rate"], "binomial_rate": r["binomial_rejection_rate"],
            "z_se": r["z_monte_carlo_se"], "binomial_se": r["binomial_monte_carlo_se"],
            "z_status": classify_type1(r["z_rejection_rate"], r["alpha"], r["repetitions"]),
            "binomial_status": classify_type1(r["binomial_rejection_rate"], r["alpha"], r["repetitions"]),
            "normal_ok": bool(r["normal_ok"]),
        })
    return pd.DataFrame(rows)


def power_table(cond: pd.DataFrame) -> pd.DataFrame:
    """Curvas completas (efeito 0 incluído) com nomes curtos de coluna."""
    out = cond.rename(columns={"z_rejection_rate": "z_rate", "binomial_rejection_rate": "binomial_rate",
                               "z_monte_carlo_se": "z_se", "binomial_monte_carlo_se": "binomial_se"})
    out["condition"] = out["condition"].astype(str)
    return out[["condition", "n", "alpha", "repetitions", "p_true", "effect_pp",
                "z_rate", "binomial_rate", "z_se", "binomial_se", "normal_ok"]].reset_index(drop=True)