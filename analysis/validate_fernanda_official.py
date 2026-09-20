"""Valida se os quatro novos trials oficiais de Fernanda estão prontos.

Retorna 0 somente quando há exatamente quatro trials elegíveis, dois por
tratamento, nos quatro katas e na ordem contrabalanceada. As tentativas antigas
documentadas como ensaio continuam no CSV bruto, mas nunca contam aqui.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from lab02.analysis.analyze_rq1_rq2 import (
    DOCUMENTED_EXCLUSIONS,
    RESULTS_DIR,
    load_and_audit,
)
from lab02.trials.config import FERNANDA_EXECUTION_ORDER


OUTPUT = RESULTS_DIR / "validacao_fernanda.csv"


def validation_rows(eligible: pd.DataFrame) -> list[dict[str, str]]:
    fernanda = eligible.loc[eligible.participante == "Fernanda"].copy()
    ordered = fernanda.sort_values("iniciado_em") if not fernanda.empty else fernanda
    actual_order = list(ordered.kata)
    treatment_counts = fernanda.tratamento.value_counts().to_dict()
    checks = [
        (
            "exatamente_4_trials",
            len(fernanda) == 4,
            f"encontrados={len(fernanda)}",
        ),
        (
            "dois_ia_dois_manual",
            treatment_counts.get("IA", 0) == 2
            and treatment_counts.get("Manual", 0) == 2,
            f"IA={treatment_counts.get('IA', 0)}; Manual={treatment_counts.get('Manual', 0)}",
        ),
        (
            "quatro_katas_unicos",
            set(fernanda.kata) == set(FERNANDA_EXECUTION_ORDER)
            and fernanda.kata.nunique() == 4,
            ";".join(sorted(fernanda.kata.unique())),
        ),
        (
            "ordem_contrabalanceada",
            actual_order == list(FERNANDA_EXECUTION_ORDER),
            ";".join(actual_order),
        ),
        (
            "issues_unicas",
            len(fernanda) == fernanda.issue.nunique(),
            ";".join(fernanda.issue),
        ),
        (
            "ensaios_antigos_excluidos",
            not set(fernanda.trial_id).intersection(DOCUMENTED_EXCLUSIONS),
            ";".join(sorted(set(fernanda.trial_id).intersection(DOCUMENTED_EXCLUSIONS))),
        ),
        (
            "status_final_valido",
            fernanda.status.isin(["green", "time-box"]).all() and len(fernanda) == 4,
            ";".join(fernanda.status),
        ),
    ]
    return [
        {
            "criterio": name,
            "status": "ok" if passed else "pendente",
            "evidencia": evidence,
        }
        for name, passed, evidence in checks
    ]


def write_validation(rows: list[dict[str, str]], output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["criterio", "status", "evidencia"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    _, eligible, _ = load_and_audit()
    rows = validation_rows(eligible)
    write_validation(rows)
    for row in rows:
        print(f"{row['status']}: {row['criterio']} ({row['evidencia']})")
    return 0 if all(row["status"] == "ok" for row in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
