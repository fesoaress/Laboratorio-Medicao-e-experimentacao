import csv
import json
import shutil
from pathlib import Path

import pytest

from lab02.trials.config import KATAS_DIR
from lab02.trials.prepare_trial import PreparationError, prepare_trial
from lab02.trials.run_trial import TrialError, execute_trial
from lab02.trials.storage import CYCLE_FIELDS, TRIAL_FIELDS, register_cycle, register_trial
from lab02.trials.test_runner import run_tests


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_prepare_trial_copies_only_stub_tests_and_manifest(tmp_path):
    workspace = prepare_trial(
        "Islayder",
        "kata1_normalizador_etiquetas",
        "AI",
        "#101",
        workspaces_dir=tmp_path,
    )

    assert sorted(path.name for path in workspace.iterdir()) == [
        "solucao.py",
        "test_solucao.py",
        "trial.json",
    ]
    manifest = json.loads((workspace / "trial.json").read_text(encoding="utf-8"))
    assert manifest["treatment"] == "IA"
    assert manifest["issue"] == "#101"
    assert manifest["status"] == "prepared"
    assert "gabarito" not in {path.name for path in workspace.rglob("*")}


def test_prepare_trial_enforces_islayder_allocation_and_no_overwrite(tmp_path):
    with pytest.raises(PreparationError, match="Alocação"):
        prepare_trial(
            "Islayder",
            "kata2_balanceamento_turnos",
            "IA",
            "102",
            workspaces_dir=tmp_path,
        )

    arguments = (
        "Islayder",
        "kata2_balanceamento_turnos",
        "Manual",
        "102",
    )
    prepare_trial(*arguments, workspaces_dir=tmp_path)
    with pytest.raises(PreparationError, match="não será sobrescrito"):
        prepare_trial(*arguments, workspaces_dir=tmp_path)


def test_prepare_trial_enforces_fernanda_allocation(tmp_path):
    with pytest.raises(PreparationError, match="Alocação"):
        prepare_trial(
            "Fernanda",
            "kata1_normalizador_etiquetas",
            "IA",
            "108",
            workspaces_dir=tmp_path,
        )

    prepare_trial(
        "Fernanda",
        "kata1_normalizador_etiquetas",
        "Manual",
        "108",
        workspaces_dir=tmp_path,
    )


def test_prepare_trial_rejects_issue_already_used_by_another_trial(tmp_path):
    prepare_trial(
        "Islayder",
        "kata1_normalizador_etiquetas",
        "IA",
        "107",
        workspaces_dir=tmp_path,
    )
    with pytest.raises(PreparationError, match="já está vinculada"):
        prepare_trial(
            "Fernanda",
            "kata1_normalizador_etiquetas",
            "Manual",
            "107",
            workspaces_dir=tmp_path,
        )


@pytest.mark.parametrize(
    ("kata", "total"),
    [
        ("kata1_normalizador_etiquetas", 10),
        ("kata2_balanceamento_turnos", 9),
        ("kata3_compactador_sensor", 9),
        ("kata4_manutencao_preditiva", 7),
    ],
)
def test_runner_counts_all_non_passing_stub_tests(kata, total):
    result = run_tests(KATAS_DIR / kata, timeout_seconds=10)
    assert result["passando"] == 0
    assert result["falhando"] == total
    assert result["total"] == total
    assert result["taxa_sucesso"] == 0.0
    assert result["green"] is False


def test_runner_treats_collection_error_as_non_passing(tmp_path):
    shutil.copy2(
        KATAS_DIR / "kata1_normalizador_etiquetas" / "test_solucao.py",
        tmp_path / "test_solucao.py",
    )
    (tmp_path / "solucao.py").write_text("def quebrada(:\n", encoding="utf-8")

    result = run_tests(tmp_path, timeout_seconds=10)

    assert result["passando"] == 0
    assert result["falhando"] == 10
    assert result["total"] == 10
    assert result["green"] is False
    assert result["erro_execucao"]


def test_storage_upserts_without_duplicate_rows(tmp_path):
    trials_csv = tmp_path / "trials.csv"
    cycles_csv = tmp_path / "cycles.csv"
    trial = {field: "" for field in TRIAL_FIELDS}
    trial.update({"trial_id": "abc", "status": "green"})
    register_trial(trial, trials_csv)
    trial["status"] = "time-box"
    register_trial(trial, trials_csv)

    cycle = {field: "" for field in CYCLE_FIELDS}
    cycle.update({"trial_id": "abc", "ciclo": 1, "testes_passando": 2})
    register_cycle(cycle, cycles_csv)
    cycle["testes_passando"] = 3
    register_cycle(cycle, cycles_csv)

    assert [row["status"] for row in read_csv(trials_csv)] == ["time-box"]
    assert [row["testes_passando"] for row in read_csv(cycles_csv)] == ["3"]


def test_end_to_end_green_uses_workspace_and_archives_solution(tmp_path):
    # Kata mínimo isolado: exercita o runner sem recorrer a soluções de referência.
    katas_dir = tmp_path / "katas"
    source = katas_dir / "kata1_normalizador_etiquetas"
    source.mkdir(parents=True)
    (source / "solucao.py").write_text(
        "def identidade(valor):\n    return valor\n", encoding="utf-8"
    )
    (source / "test_solucao.py").write_text(
        "from solucao import identidade\n\n"
        "def test_identidade():\n    assert identidade(7) == 7\n",
        encoding="utf-8",
    )
    workspace = prepare_trial(
        "Islayder",
        "kata1_normalizador_etiquetas",
        "IA",
        "103",
        katas_dir=katas_dir,
        workspaces_dir=tmp_path / "workspaces",
    )
    output = tmp_path / "results"

    result = execute_trial(
        workspace,
        time_box_seconds=10,
        wait_action=lambda _remaining: "enter",
        trials_csv=output / "trials.csv",
        cycles_csv=output / "trial_cycles.csv",
        solutions_dir=output / "solutions",
    )

    assert result["status"] == "green"
    assert result["testes_passando"] == 1
    assert result["testes_falhando"] == 0
    assert result["ciclos"] == 1
    assert (output / "solutions" / result["trial_id"] / "solucao.py").is_file()
    assert json.loads((workspace / "trial.json").read_text(encoding="utf-8"))["status"] == "green"


def test_time_box_records_final_cycle_and_censored_time(tmp_path):
    workspace = prepare_trial(
        "Islayder",
        "kata2_balanceamento_turnos",
        "Manual",
        "104",
        workspaces_dir=tmp_path / "workspaces",
    )
    output = tmp_path / "results"

    result = execute_trial(
        workspace,
        time_box_seconds=0.1,
        wait_action=lambda _remaining: "timeout",
        trials_csv=output / "trials.csv",
        cycles_csv=output / "trial_cycles.csv",
        solutions_dir=output / "solutions",
    )

    assert result["status"] == "time-box"
    assert result["tempo_segundos"] == 0.1
    assert result["testes_passando"] == 0
    assert result["testes_falhando"] == 9
    assert result["ciclos"] == 1


def test_ctrl_c_still_persists_consistent_trial(tmp_path):
    workspace = prepare_trial(
        "Islayder",
        "kata4_manutencao_preditiva",
        "Manual",
        "105",
        workspaces_dir=tmp_path / "workspaces",
    )
    output = tmp_path / "results"

    def interrupt(_remaining):
        raise KeyboardInterrupt

    result = execute_trial(
        workspace,
        time_box_seconds=10,
        wait_action=interrupt,
        trials_csv=output / "trials.csv",
        cycles_csv=output / "trial_cycles.csv",
        solutions_dir=output / "solutions",
    )

    assert result["status"] == "interrupted"
    assert result["ciclos"] == 1
    assert result["codigo_path"]
    assert "Ctrl+C" in result["erro_execucao"]
    assert len(read_csv(output / "trials.csv")) == 1


def test_modified_acceptance_tests_abort_before_timer(tmp_path):
    workspace = prepare_trial(
        "Islayder",
        "kata3_compactador_sensor",
        "IA",
        "106",
        workspaces_dir=tmp_path,
    )
    with (workspace / "test_solucao.py").open("a", encoding="utf-8") as handle:
        handle.write("\n# alteração indevida\n")

    with pytest.raises(TrialError, match="foi alterado"):
        execute_trial(workspace)
