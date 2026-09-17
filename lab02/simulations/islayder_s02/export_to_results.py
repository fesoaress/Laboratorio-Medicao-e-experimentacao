"""Inclui cenários sintéticos rotulados nos CSVs consolidados para ensaio do pipeline.

Essas linhas não são trials observados e devem ser excluídas da análise empírica.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from lab02.metrics.run_metrics import DEFAULT_RESULTS_DIR, upsert_csv_row
from lab02.trials.config import CYCLES_CSV, TRIALS_CSV
from lab02.trials.storage import register_cycle, register_trial


SOURCE_DIR = Path(__file__).resolve().parent
SOURCE_KIND = "observed_simulated"
PARTICIPANT = "Islayder"
NOTE = "CENARIO_SINTETICO: valores hipoteticos; nao houve execucao humana cronometrada"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def export_issue(
    issue_number: int,
    *,
    source_dir: Path = SOURCE_DIR,
    trials_csv: Path = TRIALS_CSV,
    cycles_csv: Path = CYCLES_CSV,
    metrics_csv: Path = DEFAULT_RESULTS_DIR / "metrics.csv",
) -> str:
    issue = f"#{issue_number}"
    trials = [row for row in read_csv(source_dir / "simulated_trials.csv") if row["issue"] == issue]
    cycles = [row for row in read_csv(source_dir / "simulated_trial_cycles.csv") if row["issue"] == issue]
    metrics = [row for row in read_csv(source_dir / "simulated_metrics.csv") if row["issue"] == issue]
    if len(trials) != 1 or len(metrics) != 1:
        raise ValueError(f"Esperado um cenário e uma métrica para {issue}.")

    trial = trials[0]
    metric = metrics[0]
    trial_id = trial["simulation_id"]
    common = ("simulation_id", "source_kind", "issue", "participant_label", "kata", "planned_treatment")
    if any(metric[field] != trial[field] for field in common):
        raise ValueError(f"Métricas sintéticas inconsistentes para {issue}.")
    if trial_id != f"SIM-S02-I{issue_number}" or trial["source_kind"] != SOURCE_KIND:
        raise ValueError(f"Identificação sintética inválida para {issue}.")
    if len(cycles) != int(trial["simulated_cycles"]):
        raise ValueError(f"Quantidade de ciclos sintéticos inconsistente para {issue}.")
    cycles.sort(key=lambda row: int(row["cycle"]))
    if [int(row["cycle"]) for row in cycles] != list(range(1, len(cycles) + 1)):
        raise ValueError(f"Sequência de ciclos sintéticos inválida para {issue}.")
    if any(any(row[field] != trial[field] for field in common) for row in cycles):
        raise ValueError(f"Metadados de ciclos sintéticos inconsistentes para {issue}.")
    last = cycles[-1]
    for source, target in (
        ("simulated_elapsed_seconds", "simulated_duration_seconds"),
        ("simulated_passed", "simulated_passed"),
        ("simulated_failed", "simulated_failed"),
        ("total_tests", "total_tests"),
        ("simulated_success_rate", "simulated_success_rate"),
    ):
        if float(last[source]) != float(trial[target]):
            raise ValueError(f"Ciclo final sintético diverge do cenário {issue}: {source}.")

    register_trial(
        {
            "trial_id": trial_id,
            "issue": issue,
            "participante": PARTICIPANT,
            "kata": trial["kata"],
            "tratamento": trial["planned_treatment"],
            "tempo_segundos": trial["simulated_duration_seconds"],
            "testes_passando": trial["simulated_passed"],
            "testes_falhando": trial["simulated_failed"],
            "total_testes": trial["total_tests"],
            "taxa_sucesso": trial["simulated_success_rate"],
            "ciclos": trial["simulated_cycles"],
            "status": f"simulated-{trial['hypothetical_status']}",
            "codigo_path": "",
            "iniciado_em": "",
            "finalizado_em": "",
            "erro_execucao": NOTE,
            "source_kind": SOURCE_KIND,
        },
        trials_csv,
    )
    for cycle in cycles:
        register_cycle(
            {
                "trial_id": trial_id,
                "issue": issue,
                "participante": PARTICIPANT,
                "kata": trial["kata"],
                "tratamento": trial["planned_treatment"],
                "ciclo": cycle["cycle"],
                "tempo_segundos": cycle["simulated_elapsed_seconds"],
                "testes_passando": cycle["simulated_passed"],
                "testes_falhando": cycle["simulated_failed"],
                "total_testes": cycle["total_tests"],
                "taxa_sucesso": cycle["simulated_success_rate"],
                "pytest_exit_code": "",
                "erro_execucao": NOTE,
                "source_kind": SOURCE_KIND,
            },
            cycles_csv,
        )
    upsert_csv_row(
        metrics_csv,
        {
            "participant": PARTICIPANT,
            "kata": trial["kata"],
            "treatment": trial["planned_treatment"],
            "trial_id": trial_id,
            "issue": issue,
            "loc": metric["simulated_loc"],
            "avg_cyclomatic_complexity": metric["simulated_avg_cyclomatic_complexity"],
            "duplication_percentage": metric["simulated_duplication_percentage"],
            "cyclomatic_complexity_max": "",
            "duplicated_lines": "",
            "duplicated_blocks": "",
            "analyzed_functions": "",
            "analysis_error": NOTE,
            "solution_path": "",
            "collected_at": "",
            "json_path": "",
            "source_kind": SOURCE_KIND,
        },
    )
    return trial_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", type=int, required=True, choices=(21, 24, 25, 26))
    args = parser.parse_args()
    print(export_issue(args.issue))


if __name__ == "__main__":
    main()
