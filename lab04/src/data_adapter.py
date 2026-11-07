"""Carrega os dados reais de CI (Issue #77) para o dashboard.

Lê ``lab04/data/ci_runs.csv`` por meio de ``lab04.src.real_data.load_ci_runs``, que valida
o arquivo (uma única workflow, sem duplicatas, só success/failure). Não há mais fallback
provisório: se o arquivo não existir, o erro é explícito. Para gerar o arquivo:
``python -m lab04.src.collect_ci_runs``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REAL_CSV = DATA_DIR / "ci_runs.csv"


def get_real_dataset() -> tuple[pd.DataFrame, str]:
    """Retorna (DataFrame validado, descrição da fonte)."""
    from lab04.src.real_data import load_ci_runs

    if not REAL_CSV.exists():
        raise FileNotFoundError(
            f"{REAL_CSV} não encontrado. Gere com: python -m lab04.src.collect_ci_runs"
        )
    return load_ci_runs(REAL_CSV), f"{REAL_CSV.name} (coleta da Issue #77, API pública do GitHub)"


def get_real_outcomes() -> tuple[np.ndarray, bool, str]:
    """Retorna (outcomes 0/1, é_provisório, fonte). ``é_provisório`` é sempre False."""
    df, source = get_real_dataset()
    return df["failed"].to_numpy(dtype=np.int8), False, source