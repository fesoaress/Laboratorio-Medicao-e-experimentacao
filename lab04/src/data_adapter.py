"""Carrega os dados reais de CI (Issue #77) com fallback para CSV provisório.

Ordem de busca:
1. ``lab04/data/ci_runs.csv`` (arquivo real entregue pela Fernanda), validado por
   ``lab04.src.real_data.load_ci_runs`` antes de chegar ao dashboard.
2. ``lab04/data/provisional_ci_runs.csv`` — SOMENTE PARA DESENVOLVIMENTO. O dashboard
   exibe um aviso enquanto este arquivo estiver em uso.

Formato esperado: coluna ``outcome`` (0 = sucesso, 1 = falha). Também aceita
``failed``/``failure``/``is_failure`` (booleano) ou ``conclusion`` (success/failure).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REAL_CSV = DATA_DIR / "ci_runs.csv"
PROVISIONAL_CSV = DATA_DIR / "provisional_ci_runs.csv"


def _to_binary(df: pd.DataFrame) -> np.ndarray:
    for col in ("outcome", "failed", "failure", "is_failure"):
        if col in df.columns:
            return df[col].astype(int).to_numpy(dtype=np.int8)
    if "conclusion" in df.columns:
        return (df["conclusion"].astype(str).str.lower() == "failure").astype(np.int8).to_numpy()
    raise ValueError("CSV precisa de uma coluna 'outcome' (0=sucesso, 1=falha)")


def _load_real(path: Path) -> np.ndarray:
    from lab04.src.real_data import load_ci_runs

    return _to_binary(load_ci_runs(path))


def get_real_outcomes() -> tuple[np.ndarray, bool, str]:
    """Retorna (outcomes 0/1, é_provisório, descrição da fonte)."""
    if REAL_CSV.exists():
        data = _load_real(REAL_CSV)
        return data, False, f"{REAL_CSV.name} (coleta da Issue #77)"
    data = _to_binary(pd.read_csv(PROVISIONAL_CSV))
    return data, True, f"{PROVISIONAL_CSV.name} (PROVISÓRIO — remover antes da entrega)"
