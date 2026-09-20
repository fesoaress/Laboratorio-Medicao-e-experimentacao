"""Controla um trial time-boxed usando exclusivamente seu workspace isolado."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import shutil
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .config import (
    BASE_DIR,
    CYCLES_CSV,
    FINAL_SOLUTIONS_DIR,
    TIME_BOX_MINUTES,
    TIME_BOX_SECONDS,
    TRIALS_CSV,
)
from .storage import ensure_files, register_cycle, register_trial
from .test_runner import count_expected_tests, run_tests


class TrialError(RuntimeError):
    """Manifesto inválido, trial já usado ou artefato protegido alterado."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(BASE_DIR.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def load_manifest(workspace: Path) -> tuple[Path, dict]:
    workspace = workspace.resolve()
    manifest_path = workspace / "trial.json"
    if not manifest_path.is_file():
        raise TrialError(
            f"Manifesto não encontrado: {manifest_path}. "
            "Prepare o trial com python -m lab02.trials.prepare_trial."
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrialError(f"Manifesto inválido: {manifest_path}: {exc}") from exc

    required = {"participant", "kata", "treatment", "issue", "status", "test_sha256"}
    missing = sorted(required - manifest.keys())
    if missing:
        raise TrialError(f"Campos ausentes no manifesto: {', '.join(missing)}")
    if manifest["status"] != "prepared":
        raise TrialError(
            f"Trial não está disponível para início (status={manifest['status']!r}). "
            "Um workspace nunca deve ser reutilizado."
        )
    for filename in ("solucao.py", "test_solucao.py"):
        if not (workspace / filename).is_file():
            raise TrialError(f"Arquivo obrigatório ausente: {workspace / filename}")
    verify_test_integrity(workspace, manifest)
    return manifest_path, manifest


def write_manifest(path: Path, manifest: dict) -> None:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=".trial-", suffix=".json.tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def verify_test_integrity(workspace: Path, manifest: dict) -> None:
    test_file = workspace / "test_solucao.py"
    if sha256(test_file) != manifest["test_sha256"]:
        raise TrialError(
            "test_solucao.py foi alterado depois da preparação. "
            "Interrompa este trial e prepare outro workspace."
        )


def wait_for_enter(timeout_seconds: float) -> str:
    """Aguarda ENTER sem permitir que o prompt ultrapasse silenciosamente o limite."""
    responses: queue.Queue[str] = queue.Queue(maxsize=1)

    def read_input() -> None:
        try:
            input("\nPressione ENTER para executar os testes (Ctrl+C interrompe)...")
            responses.put_nowait("enter")
        except EOFError:
            responses.put_nowait("eof")

    threading.Thread(target=read_input, daemon=True).start()
    try:
        response = responses.get(timeout=max(0.0, timeout_seconds))
    except queue.Empty:
        return "timeout"
    if response == "eof":
        raise TrialError("Entrada padrão encerrada durante o trial.")
    return response


def archive_solution(
    workspace: Path, trial_id: str, solutions_dir: Path = FINAL_SOLUTIONS_DIR
) -> Path:
    destination = solutions_dir / trial_id
    solutions_dir.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise TrialError(f"Snapshot final já existe: {destination}")
    temporary = Path(tempfile.mkdtemp(prefix=f".{trial_id}-", dir=solutions_dir))
    try:
        shutil.copy2(workspace / "solucao.py", temporary / "solucao.py")
        shutil.copy2(workspace / "test_solucao.py", temporary / "test_solucao.py")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return destination


def execute_trial(
    workspace: Path | str,
    *,
    time_box_seconds: float = TIME_BOX_SECONDS,
    wait_action: Callable[[float], str] = wait_for_enter,
    test_executor: Callable[..., dict] = run_tests,
    trials_csv: Path = TRIALS_CSV,
    cycles_csv: Path = CYCLES_CSV,
    solutions_dir: Path = FINAL_SOLUTIONS_DIR,
    clock: Callable[[], float] = time.monotonic,
) -> dict:
    """Executa e persiste um trial; parâmetros extras permitem validação isolada."""
    workspace = Path(workspace).resolve()
    manifest_path, manifest = load_manifest(workspace)
    if time_box_seconds <= 0:
        raise TrialError("O time-box precisa ser positivo.")

    expected_total = count_expected_tests(workspace / "test_solucao.py")
    ensure_files(trials_csv, cycles_csv)
    trial_id = uuid.uuid4().hex
    started_at = utc_now()
    manifest.update({"status": "running", "trial_id": trial_id, "started_at": started_at})
    write_manifest(manifest_path, manifest)

    participant = manifest["participant"]
    kata = manifest["kata"]
    treatment = manifest["treatment"]
    issue = manifest["issue"]
    source_kind = manifest.get("source_kind", "observed")
    started = clock()
    cycle = 0
    status = "error"
    fatal_error = ""
    archived_dir: Path | None = None
    last_result = {
        "passando": 0,
        "falhando": expected_total,
        "total": expected_total,
        "taxa_sucesso": 0.0,
        "green": False,
        "pytest_exit_code": None,
        "erro_execucao": "nenhum ciclo executado",
    }

    print("\n=== Trial iniciado ===")
    print(f"Participante: {participant}")
    print(f"Issue: {issue}")
    print(f"Kata: {kata}")
    print(f"Tratamento: {treatment}")
    print(f"Time-box: {TIME_BOX_MINUTES} minutos")
    print(f"Workspace: {workspace}")

    def record_cycle(result: dict, elapsed: float) -> None:
        nonlocal cycle, last_result
        cycle += 1
        last_result = result
        register_cycle(
            {
                "trial_id": trial_id,
                "issue": issue,
                "participante": participant,
                "kata": kata,
                "tratamento": treatment,
                "ciclo": cycle,
                "tempo_segundos": round(min(elapsed, time_box_seconds), 2),
                "testes_passando": result["passando"],
                "testes_falhando": result["falhando"],
                "total_testes": result["total"],
                "taxa_sucesso": result["taxa_sucesso"],
                "pytest_exit_code": result["pytest_exit_code"],
                "erro_execucao": result["erro_execucao"],
                "source_kind": source_kind,
            },
            cycles_csv,
        )
        print(
            f"Ciclo {cycle}: {result['passando']}/{result['total']} testes "
            f"passando ({result['taxa_sucesso']}%)"
        )
        if result["erro_execucao"]:
            print(f"Aviso do pytest: {result['erro_execucao']}")

    try:
        while True:
            elapsed = clock() - started
            remaining = time_box_seconds - elapsed
            if remaining <= 0:
                status = "time-box"
                archived_dir = archive_solution(workspace, trial_id, solutions_dir)
                result = test_executor(archived_dir, timeout_seconds=60)
                record_cycle(result, time_box_seconds)
                break

            action = wait_action(remaining)
            if action == "timeout":
                status = "time-box"
                archived_dir = archive_solution(workspace, trial_id, solutions_dir)
                result = test_executor(archived_dir, timeout_seconds=60)
                record_cycle(result, time_box_seconds)
                break
            if action != "enter":
                raise TrialError(f"Ação desconhecida durante o trial: {action!r}")

            verify_test_integrity(workspace, manifest)
            remaining = max(0.01, time_box_seconds - (clock() - started))
            result = test_executor(workspace, timeout_seconds=remaining)
            elapsed = clock() - started
            record_cycle(result, elapsed)
            if elapsed >= time_box_seconds:
                status = "time-box"
                break
            if result["green"]:
                status = "green"
                break
    except KeyboardInterrupt:
        status = "interrupted"
        fatal_error = "trial interrompido com Ctrl+C"
        print("\nInterrupção recebida; salvando snapshot e resultado final...")
        try:
            verify_test_integrity(workspace, manifest)
            archived_dir = archive_solution(workspace, trial_id, solutions_dir)
            result = test_executor(archived_dir, timeout_seconds=60)
            record_cycle(result, clock() - started)
        except Exception as exc:  # preserva o registro mesmo se o pytest falhar
            fatal_error = f"{fatal_error}; falha no snapshot final: {exc}"
    except Exception as exc:
        status = "error"
        fatal_error = str(exc)

    if archived_dir is None:
        try:
            verify_test_integrity(workspace, manifest)
            archived_dir = archive_solution(workspace, trial_id, solutions_dir)
        except Exception as exc:
            fatal_error = "; ".join(filter(None, (fatal_error, str(exc))))
            status = "error"

    elapsed_final = (
        round(time_box_seconds, 2)
        if status == "time-box"
        else round(min(max(0.0, clock() - started), time_box_seconds), 2)
    )
    finished_at = utc_now()
    code_path = repo_relative(archived_dir / "solucao.py") if archived_dir else ""
    combined_error = "; ".join(
        filter(None, (fatal_error, last_result.get("erro_execucao", "")))
    )
    trial_data = {
        "trial_id": trial_id,
        "issue": issue,
        "participante": participant,
        "kata": kata,
        "tratamento": treatment,
        "tempo_segundos": elapsed_final,
        "testes_passando": last_result["passando"],
        "testes_falhando": last_result["falhando"],
        "total_testes": last_result["total"],
        "taxa_sucesso": last_result["taxa_sucesso"],
        "ciclos": cycle,
        "status": status,
        "codigo_path": code_path,
        "iniciado_em": started_at,
        "finalizado_em": finished_at,
        "erro_execucao": combined_error,
        "source_kind": source_kind,
    }
    register_trial(trial_data, trials_csv)

    manifest.update(
        {
            "status": status,
            "finished_at": finished_at,
            "final_solution_path": code_path,
        }
    )
    write_manifest(manifest_path, manifest)

    print("\n=== Trial encerrado ===")
    print(f"Status: {status}")
    print(f"Tempo registrado: {elapsed_final} segundos")
    print(f"Ciclos executados: {cycle}")
    print(f"Código final: {code_path}")
    return trial_data


# Nome em português preservado para compatibilidade com a S01.
executar_trial = execute_trial


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executa um trial preparado da S02.")
    parser.add_argument(
        "--workspace",
        required=True,
        type=Path,
        help="Pasta gerada por python -m lab02.trials.prepare_trial.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = execute_trial(args.workspace)
    except TrialError as exc:
        print(f"ERRO: {exc}")
        return 1
    if result["status"] == "interrupted":
        return 130
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
