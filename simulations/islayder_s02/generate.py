"""Gera um cenário inteiramente sintético da S02, separado dos dados oficiais.

Os números abaixo são fixtures escolhidas para exercitar a análise. Nenhum
trial, teste de aceitação ou coletor de métricas é executado por este script.
"""

from __future__ import annotations

import csv
from pathlib import Path

from lab02.trials.config import KATAS_DIR
from lab02.trials.test_runner import count_expected_tests


OUTPUT_DIR = Path(__file__).resolve().parent
SOURCE_KIND = "observed_simulated"
PARTICIPANT_LABEL = "SIMULACAO_ISLAYDER"

# (Issue, kata, tratamento planejado, desfecho hipotético, ciclos (s, passando),
#  LOC hipotético, CC média hipotética, duplicação hipotética %).
SCENARIOS = (
    (21, "kata1_normalizador_etiquetas", "IA", "green", ((120, 4), (250, 8), (420, 10)), 18, 5.0, 0.0),
    (24, "kata2_balanceamento_turnos", "Manual", "green", ((300, 3), (600, 7), (900, 9)), 8, 3.0, 0.0),
    (25, "kata3_compactador_sensor", "IA", "green", ((180, 4), (360, 8), (510, 9)), 20, 3.5, 4.0),
    (26, "kata4_manutencao_preditiva", "Manual", "time-box", ((450, 2), (900, 4), (1500, 6), (2100, 6)), 14, 4.0, 0.0),
)

TRIAL_COLUMNS = (
    "simulation_id", "source_kind", "issue", "participant_label", "kata",
    "planned_treatment", "hypothetical_status", "simulated_duration_seconds",
    "simulated_passed", "simulated_failed", "total_tests",
    "simulated_success_rate", "simulated_cycles",
)
CYCLE_COLUMNS = (
    "simulation_id", "source_kind", "issue", "participant_label", "kata",
    "planned_treatment", "cycle", "simulated_elapsed_seconds",
    "simulated_passed", "simulated_failed", "total_tests",
    "simulated_success_rate",
)
METRIC_COLUMNS = (
    "simulation_id", "source_kind", "issue", "participant_label", "kata",
    "planned_treatment", "simulated_loc", "simulated_avg_cyclomatic_complexity",
    "simulated_duplication_percentage",
)


def success_rate(passed: int, total: int) -> float:
    return round(100 * passed / total, 2)


def write_csv(name: str, columns: tuple[str, ...], rows: list[dict]) -> None:
    with (OUTPUT_DIR / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    trials: list[dict] = []
    cycles: list[dict] = []
    metrics: list[dict] = []

    for issue, kata, treatment, outcome, planned_cycles, loc, cc, duplication in SCENARIOS:
        total = count_expected_tests(KATAS_DIR / kata / "test_solucao.py")
        assert planned_cycles and all(0 <= passed <= total for _, passed in planned_cycles)
        assert all(previous[0] < current[0] for previous, current in zip(planned_cycles, planned_cycles[1:]))
        assert planned_cycles[-1][0] <= 2100
        assert (planned_cycles[-1][1] == total) == (outcome == "green")

        simulation_id = f"SIM-S02-I{issue}"
        common = {
            "simulation_id": simulation_id,
            "source_kind": SOURCE_KIND,
            "issue": f"#{issue}",
            "participant_label": PARTICIPANT_LABEL,
            "kata": kata,
            "planned_treatment": treatment,
        }
        for number, (elapsed, passed) in enumerate(planned_cycles, 1):
            cycles.append({
                **common,
                "cycle": number,
                "simulated_elapsed_seconds": elapsed,
                "simulated_passed": passed,
                "simulated_failed": total - passed,
                "total_tests": total,
                "simulated_success_rate": success_rate(passed, total),
            })

        duration, passed = planned_cycles[-1]
        trials.append({
            **common,
            "hypothetical_status": outcome,
            "simulated_duration_seconds": duration,
            "simulated_passed": passed,
            "simulated_failed": total - passed,
            "total_tests": total,
            "simulated_success_rate": success_rate(passed, total),
            "simulated_cycles": len(planned_cycles),
        })
        metrics.append({
            **common,
            "simulated_loc": loc,
            "simulated_avg_cyclomatic_complexity": cc,
            "simulated_duplication_percentage": duplication,
        })

    write_csv("simulated_trials.csv", TRIAL_COLUMNS, trials)
    write_csv("simulated_trial_cycles.csv", CYCLE_COLUMNS, cycles)
    write_csv("simulated_metrics.csv", METRIC_COLUMNS, metrics)


if __name__ == "__main__":
    main()
