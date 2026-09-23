"""Execução isolada do pytest e normalização dos resultados de aceitação."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path


def count_expected_tests(test_file: Path) -> int:
    """Conta os testes simples usados pelos katas sem importar a solução."""
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
    except (OSError, SyntaxError) as exc:
        raise ValueError(f"Arquivo de teste inválido: {test_file}: {exc}") from exc

    count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count += node.name.startswith("test_")
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            count += sum(
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name.startswith("test_")
                for child in node.body
            )
    if count == 0:
        raise ValueError(f"Nenhum teste de aceitação encontrado em: {test_file}")
    return count


def extract_quantity(output: str, status: str) -> int:
    match = re.search(rf"(?<!\d)(\d+)\s+{re.escape(status)}\b", output)
    return int(match.group(1)) if match else 0


def summarize_error(output: str, returncode: int) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    relevant = [
        line
        for line in lines
        if "ERROR" in line or "error" in line.casefold() or "Traceback" in line
    ]
    detail = relevant[-1] if relevant else f"pytest terminou com código {returncode}"
    return detail[:500]


def run_tests(trial_path: Path | str, timeout_seconds: float | None = None) -> dict:
    """Executa apenas os testes presentes na cópia isolada do trial."""
    trial_dir = Path(trial_path).resolve()
    test_file = trial_dir / "test_solucao.py"
    solution_file = trial_dir / "solucao.py"
    if not trial_dir.is_dir():
        raise FileNotFoundError(f"Pasta do trial não encontrada: {trial_dir}")
    if not solution_file.is_file():
        raise FileNotFoundError(f"Solução do trial não encontrada: {solution_file}")
    if not test_file.is_file():
        raise FileNotFoundError(f"Arquivo de teste não encontrado: {test_file}")

    expected_total = count_expected_tests(test_file)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        test_file.name,
    ]
    try:
        process = subprocess.run(
            command,
            cwd=trial_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "passando": 0,
            "falhando": expected_total,
            "total": expected_total,
            "taxa_sucesso": 0.0,
            "green": False,
            "pytest_exit_code": None,
            "erro_execucao": "pytest excedeu o tempo restante do trial",
        }

    output = (process.stdout or "") + (process.stderr or "")
    passed = min(extract_quantity(output, "passed"), expected_total)
    failed_reported = extract_quantity(output, "failed")
    errors_reported = extract_quantity(output, "error") + extract_quantity(
        output, "errors"
    )
    not_passing = expected_total - passed
    execution_error = ""
    if process.returncode not in (0, 1) or errors_reported:
        execution_error = summarize_error(output, process.returncode)
    elif process.returncode == 1 and failed_reported == 0 and not_passing:
        execution_error = summarize_error(output, process.returncode)

    success_rate = round((passed / expected_total) * 100, 2)
    return {
        "passando": passed,
        "falhando": not_passing,
        "total": expected_total,
        "taxa_sucesso": success_rate,
        "green": process.returncode == 0 and passed == expected_total,
        "pytest_exit_code": process.returncode,
        "erro_execucao": execution_error,
    }


# Compatibilidade com chamadas existentes, agora exigindo o caminho do trial.
executar_testes = run_tests
