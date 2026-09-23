#!/usr/bin/env python3
"""Coleta métricas estruturais (RQ3) sobre o código final de um trial.

Uso:
  python lab02/metrics/run_metrics.py <caminho_do_trial> \\
      --participant Fernanda --kata kata1 --treatment IA

Saídas (formato padronizado):
  - JSON detalhado por trial em lab02/metrics/results/
  - CSV consolidado (uma linha por trial) em lab02/metrics/results/metrics.csv

Métricas principais (Pandas / RQ3):
  participant, kata, treatment, loc, avg_cyclomatic_complexity, duplication_percentage
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METRICS_DIR = Path(__file__).resolve().parent
REPO_ROOT = METRICS_DIR.parent.parent
JSCPD_CONFIG = METRICS_DIR / ".jscpd.json"
DEFAULT_RESULTS_DIR = METRICS_DIR / "results"
DEFAULT_CSV_NAME = "metrics.csv"
FINAL_TRIAL_SOLUTIONS_DIR = REPO_ROOT / "lab02" / "trials" / "results" / "solutions"

# Colunas do CSV consolidado — ordem fixa para leitura com Pandas.
CSV_COLUMNS: list[str] = [
    "participant",
    "kata",
    "treatment",
    "trial_id",
    "issue",
    "loc",
    "avg_cyclomatic_complexity",
    "duplication_percentage",
    "cyclomatic_complexity_max",
    "duplicated_lines",
    "duplicated_blocks",
    "analyzed_functions",
    "analysis_error",
    "solution_path",
    "collected_at",
    "json_path",
    "source_kind",
]

TRIAL_KEY_FIELDS = ("participant", "kata", "treatment")


def to_repo_relative(path: Path) -> str:
    """Normaliza path para relativo à raiz do repo (portável no CSV/JSON)."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


class MetricsError(Exception):
    """Erro recuperável da coleta (mensagem clara para o usuário)."""


def normalize_treatment(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in {"ia", "ai"}:
        return "IA"
    if normalized == "manual":
        return "Manual"
    raise argparse.ArgumentTypeError("use IA ou Manual")


def safe_filename_part(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise MetricsError(f"{field} não pode ficar vazio.")
    ascii_value = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", ascii_value).strip("-_")
    if not slug:
        raise MetricsError(f"{field} não contém caracteres válidos.")
    return slug


def normalize_issue(value: str) -> str:
    if not value.strip():
        return ""
    number = value.strip().removeprefix("#")
    if not number.isdigit() or int(number) <= 0:
        raise MetricsError("issue inválida; informe apenas o número positivo.")
    return f"#{int(number)}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Coleta LOC, complexidade ciclomática e duplicação (RQ3)."
    )
    parser.add_argument(
        "trial_path",
        type=Path,
        help="Arquivo solucao.py ou pasta do trial que o contenha.",
    )
    parser.add_argument(
        "--participant",
        required=True,
        help="Identificador do participante (ex.: Fernanda).",
    )
    parser.add_argument(
        "--kata",
        required=True,
        help="Identificador do kata (ex.: kata1).",
    )
    parser.add_argument(
        "--treatment",
        required=True,
        type=normalize_treatment,
        help="Tratamento experimental: IA ou Manual (AI é aceito como alias).",
    )
    parser.add_argument(
        "--trial-id",
        default="",
        help="trial_id de trials.csv (obrigatório para dados reais da S02).",
    )
    parser.add_argument(
        "--issue",
        default="",
        help="Número da Issue vinculada ao trial (ex.: 23).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help=f"Pasta para JSON + CSV (default: {DEFAULT_RESULTS_DIR}).",
    )
    parser.add_argument(
        "--csv-name",
        default=DEFAULT_CSV_NAME,
        help=f"Nome do CSV consolidado (default: {DEFAULT_CSV_NAME}).",
    )
    parser.add_argument(
        "--source-kind",
        choices=(
            "observed",
            "technical_preparatory",
            "agent_delegated_codex_work",
        ),
        default="observed",
        help=(
            "Proveniência da medição. Use technical_preparatory somente para "
            "validações do instrumento que não são dados experimentais."
        ),
    )
    return parser.parse_args(argv)


def resolve_solution_file(trial_path: Path) -> Path:
    path = trial_path.resolve()
    if not path.exists():
        raise MetricsError(f"Caminho não encontrado: {path}")

    if path.is_file():
        if path.name != "solucao.py":
            raise MetricsError(
                f"Esperado arquivo chamado solucao.py, recebido: {path.name}"
            )
        return path

    candidate = path / "solucao.py"
    if not candidate.is_file():
        raise MetricsError(
            f"Pasta do trial sem solucao.py: {path}\n"
            "Passe o arquivo solucao.py ou a pasta que o contenha."
        )
    return candidate


def run_command(command: list[str], *, cwd: Path | None = None) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise MetricsError(
            f"Comando não encontrado: {command[0]!r}. "
            "Verifique se a ferramenta está instalada (Etapa 4)."
        ) from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or f"exit code {completed.returncode}"
        raise MetricsError(
            "Falha ao executar:\n"
            f"  {' '.join(command)}\n"
            f"Detalhe: {detail}"
        )
    return completed.stdout


def require_radon() -> list[str]:
    """Retorna o comando base do Radon (preferindo o mesmo Python do script)."""
    module_cmd = [sys.executable, "-m", "radon"]
    probe = subprocess.run(
        module_cmd + ["--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if probe.returncode == 0:
        return module_cmd

    radon_bin = shutil.which("radon")
    if radon_bin:
        return [radon_bin]

    raise MetricsError(
        "Radon não encontrado.\n"
        "Instale com:\n"
        "  pip install -r lab02/metrics/requirements.txt"
    )


def require_jscpd_runner() -> list[str]:
    """Prefere o binário local em node_modules; cai para npx."""
    if not JSCPD_CONFIG.is_file():
        raise MetricsError(f"Configuração jscpd ausente: {JSCPD_CONFIG}")

    local_bin_win = METRICS_DIR / "node_modules" / ".bin" / "jscpd.cmd"
    local_bin_unix = METRICS_DIR / "node_modules" / ".bin" / "jscpd"
    if local_bin_win.is_file():
        return [str(local_bin_win)]
    if local_bin_unix.is_file():
        return [str(local_bin_unix)]

    npx = shutil.which("npx")
    if npx:
        return [npx, "--no-install", "jscpd"]

    raise MetricsError(
        "jscpd não encontrado em lab02/metrics/node_modules.\n"
        "Na pasta lab02/metrics execute:\n"
        "  npm ci"
    )


def collect_cyclomatic(solution: Path, radon_cmd: list[str]) -> dict[str, Any]:
    raw_json = run_command(radon_cmd + ["cc", "-s", "-j", str(solution)])
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise MetricsError("Radon cc não retornou JSON válido.") from exc

    # Radon usa a chave com o path passado; pegamos o único arquivo.
    if not payload:
        blocks: list[dict[str, Any]] = []
    else:
        blocks = next(iter(payload.values()))

    if isinstance(blocks, dict) and blocks.get("error"):
        return {
            "analyzed_functions": 0,
            "avg_cyclomatic_complexity": None,
            "cyclomatic_complexity_max": None,
            "cyclomatic_complexity_total": None,
            "functions": [],
            "error": str(blocks["error"]),
            "raw": payload,
        }
    if not isinstance(blocks, list):
        raise MetricsError("Formato inesperado no JSON de Radon cc.")

    # A unidade operacional é função/método. O Radon também devolve uma
    # entrada agregada para cada classe; incluí-la distorceria a média e
    # contaria a mesma estrutura duas vezes.
    callables: list[dict[str, Any]] = []
    for block in blocks:
        # No JSON do Radon, métodos já aparecem como blocos de primeiro nível;
        # a classe traz apenas uma visão agregada e deve ser descartada.
        if block.get("methods") is None:
            callables.append(block)

    complexities = [int(block["complexity"]) for block in callables]
    analyzed = len(complexities)
    average = round(sum(complexities) / analyzed, 4) if analyzed else None
    maximum = max(complexities) if complexities else None
    total = sum(complexities) if complexities else 0

    return {
        "analyzed_functions": analyzed,
        "avg_cyclomatic_complexity": average,
        "cyclomatic_complexity_max": maximum,
        "cyclomatic_complexity_total": total,
        "error": "",
        "functions": [
            {
                "name": block.get("name"),
                "type": block.get("type"),
                "complexity": block.get("complexity"),
                "lineno": block.get("lineno"),
            }
            for block in callables
        ],
        "raw": payload,
    }


def collect_loc(solution: Path, radon_cmd: list[str]) -> dict[str, Any]:
    raw_json = run_command(radon_cmd + ["raw", "-j", str(solution)])
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise MetricsError("Radon raw não retornou JSON válido.") from exc

    if not payload:
        raise MetricsError("Radon raw retornou objeto vazio.")

    stats = next(iter(payload.values()))
    if isinstance(stats, dict) and stats.get("error"):
        return {
            "loc": None,
            "lloc": None,
            "sloc": None,
            "loc_physical": None,
            "blank": None,
            "comments": None,
            "multi": None,
            "error": str(stats["error"]),
            "raw": payload,
        }
    return {
        "loc": int(stats["lloc"]),  # definição operacional (Etapa 2)
        "lloc": int(stats["lloc"]),
        "sloc": int(stats["sloc"]),
        "loc_physical": int(stats["loc"]),
        "blank": int(stats["blank"]),
        "comments": int(stats.get("comments", 0)),
        "multi": int(stats.get("multi", 0)),
        "error": "",
        "raw": payload,
    }


def collect_duplication(solution: Path, jscpd_cmd: list[str]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="jscpd_rq3_") as tmp:
        output_dir = Path(tmp)
        command = jscpd_cmd + [
            "--config",
            str(JSCPD_CONFIG),
            "--reporters",
            "json",
            "--output",
            str(output_dir),
            str(solution),
        ]
        # jscpd escreve o relatório em arquivo; stdout pode ser vazio com reporter json.
        run_command(command, cwd=METRICS_DIR)

        report_path = output_dir / "jscpd-report.json"
        if not report_path.is_file():
            raise MetricsError(
                "jscpd não gerou jscpd-report.json no diretório temporário. "
                "Verifique a instalação (npm ci em lab02/metrics)."
            )

        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MetricsError("Relatório jscpd não é JSON válido.") from exc

    total = report.get("statistics", {}).get("total", {})
    sources = int(total.get("sources", 0))
    # O jscpd reporta sources=0 quando o arquivo é menor que a janela fixa
    # minTokens/minLines. Como resolve_solution_file já garante um solucao.py
    # real e o path é passado explicitamente, isso significa "nenhum clone
    # comparável", não falha de coleta. LOC continua sendo medido pelo Radon.

    return {
        "duplication_percentage": float(total.get("percentage", 0.0)),
        "duplicated_lines": int(total.get("duplicatedLines", 0)),
        "duplicated_blocks": int(total.get("clones", 0)),
        "lines_analyzed": int(total.get("lines", 0)),
        "sources_analyzed": sources,
        "raw": report,
    }


def build_result(
    *,
    solution: Path,
    args: argparse.Namespace,
    cc: dict[str, Any],
    loc: dict[str, Any],
    dup: dict[str, Any],
) -> dict[str, Any]:
    analysis_error = "; ".join(
        error
        for error in (
            f"radon cc: {cc['error']}" if cc.get("error") else "",
            f"radon raw: {loc['error']}" if loc.get("error") else "",
        )
        if error
    )
    return {
        "schema_version": 1,
        "participant": args.participant,
        "kata": args.kata,
        "treatment": args.treatment,
        "trial_id": args.trial_id,
        "issue": args.issue,
        "source_kind": args.source_kind,
        "solution_path": to_repo_relative(solution),
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "loc": loc["loc"],
            "avg_cyclomatic_complexity": cc["avg_cyclomatic_complexity"],
            "duplication_percentage": dup["duplication_percentage"],
            "cyclomatic_complexity_max": cc["cyclomatic_complexity_max"],
            "cyclomatic_complexity_total": cc["cyclomatic_complexity_total"],
            "analyzed_functions": cc["analyzed_functions"],
            "duplicated_lines": dup["duplicated_lines"],
            "duplicated_blocks": dup["duplicated_blocks"],
            "analysis_error": analysis_error,
        },
        "details": {
            "loc": {k: v for k, v in loc.items() if k != "raw"},
            "cyclomatic": {
                "functions": cc["functions"],
                "analyzed_functions": cc["analyzed_functions"],
                "error": cc.get("error", ""),
            },
            "duplication": {
                "lines_analyzed": dup["lines_analyzed"],
                "sources_analyzed": dup["sources_analyzed"],
                "duplicated_lines": dup["duplicated_lines"],
                "duplicated_blocks": dup["duplicated_blocks"],
                "duplication_percentage": dup["duplication_percentage"],
            },
        },
        "tool_raw": {
            "radon_cc": cc["raw"],
            "radon_raw": loc["raw"],
            "jscpd": dup["raw"],
        },
    }


def result_to_csv_row(result: dict[str, Any], json_path: Path) -> dict[str, Any]:
    metrics = result["metrics"]
    return {
        "participant": result["participant"],
        "kata": result["kata"],
        "treatment": result["treatment"],
        "trial_id": result["trial_id"],
        "issue": result["issue"],
        "loc": metrics["loc"],
        "avg_cyclomatic_complexity": metrics["avg_cyclomatic_complexity"],
        "duplication_percentage": metrics["duplication_percentage"],
        "cyclomatic_complexity_max": metrics["cyclomatic_complexity_max"],
        "duplicated_lines": metrics["duplicated_lines"],
        "duplicated_blocks": metrics["duplicated_blocks"],
        "analyzed_functions": metrics["analyzed_functions"],
        "analysis_error": metrics["analysis_error"],
        "solution_path": result["solution_path"],
        "collected_at": result["collected_at"],
        "json_path": to_repo_relative(json_path),
        "source_kind": result["source_kind"],
    }


def trial_key(row: dict[str, Any]) -> tuple[str, ...]:
    trial_id = str(row.get("trial_id", "")).strip()
    if trial_id:
        return ("trial_id", trial_id)
    return (
        "legacy",
        str(row.get("participant", "")),
        str(row.get("kata", "")),
        str(row.get("treatment", "")),
    )


def load_csv_rows(csv_path: Path) -> list[dict[str, Any]]:
    if not csv_path.is_file():
        return []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        missing = [col for col in CSV_COLUMNS[:-1] if col not in reader.fieldnames]
        if missing:
            raise MetricsError(
                f"CSV existente com colunas incompatíveis ({csv_path}).\n"
                f"Colunas ausentes: {', '.join(missing)}\n"
                "Apague o arquivo ou alinhe o cabeçalho antes de continuar."
            )
        rows = list(reader)
        for row in rows:
            row.setdefault("source_kind", "observed")
        return rows


def upsert_csv_row(csv_path: Path, new_row: dict[str, Any]) -> None:
    """Insere ou substitui a linha do mesmo participant+kata+treatment."""
    rows = load_csv_rows(csv_path)
    key = trial_key(new_row)
    updated = False
    merged: list[dict[str, Any]] = []
    for row in rows:
        if trial_key(row) == key:
            if not updated:
                merged.append(new_row)
                updated = True
        else:
            # Garante todas as colunas na ordem oficial.
            merged.append({col: row.get(col, "") for col in CSV_COLUMNS})
    if not updated:
        merged.append(new_row)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".metrics-", suffix=".csv.tmp", dir=csv_path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for row in merged:
                writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, csv_path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def print_summary(result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    avg = metrics["avg_cyclomatic_complexity"]
    avg_display = "n/a (0 funções)" if avg is None else avg

    print("Analyzing trial...")
    print(f"  file: {result['solution_path']}")
    print(
        "  meta:"
        f" participant={result['participant']}"
        f" kata={result['kata']}"
        f" treatment={result['treatment']}"
    )
    loc_display = "n/a" if metrics["loc"] is None else metrics["loc"]
    print(f"LOC (lloc): {loc_display}")
    print(f"Average Cyclomatic Complexity: {avg_display}")
    print(f"Analyzed functions: {metrics['analyzed_functions']}")
    print(f"Duplicated Lines: {metrics['duplicated_lines']}")
    print(f"Duplication: {metrics['duplication_percentage']}%")
    if metrics["analysis_error"]:
        print(f"Structural analysis warning: {metrics['analysis_error']}")


def save_json_result(result: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    participant = safe_filename_part(result["participant"], "participant")
    kata = safe_filename_part(result["kata"], "kata")
    treatment = safe_filename_part(result["treatment"], "treatment")
    trial_suffix = (
        "_" + safe_filename_part(result["trial_id"], "trial_id")
        if result.get("trial_id")
        else ""
    )
    unique_suffix = uuid.uuid4().hex[:8]
    filename = (
        f"{participant}_{kata}_{treatment}{trial_suffix}_{stamp}_{unique_suffix}.json"
    )
    out_path = output_dir / filename
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        args.participant = args.participant.strip()
        args.kata = args.kata.strip()
        args.trial_id = args.trial_id.strip()
        args.issue = normalize_issue(args.issue)
        safe_filename_part(args.participant, "participant")
        safe_filename_part(args.kata, "kata")
        solution = resolve_solution_file(args.trial_path)
        if bool(args.trial_id) != bool(args.issue):
            raise MetricsError("--trial-id e --issue devem ser informados juntos.")
        if solution.is_relative_to(FINAL_TRIAL_SOLUTIONS_DIR.resolve()) and not args.trial_id:
            raise MetricsError(
                "Snapshots reais da S02 exigem --trial-id e --issue para rastreabilidade."
            )
        if args.trial_id:
            safe_filename_part(args.trial_id, "trial_id")
        radon_cmd = require_radon()
        jscpd_cmd = require_jscpd_runner()

        cc = collect_cyclomatic(solution, radon_cmd)
        loc = collect_loc(solution, radon_cmd)
        dup = collect_duplication(solution, jscpd_cmd)
        result = build_result(solution=solution, args=args, cc=cc, loc=loc, dup=dup)

        print_summary(result)

        output_dir = args.output_dir.resolve()
        json_path = save_json_result(result, output_dir)
        csv_path = output_dir / args.csv_name
        upsert_csv_row(csv_path, result_to_csv_row(result, json_path))

        print("\nResults saved to:")
        print(f"  JSON: {json_path}")
        print(f"  CSV:  {csv_path}")
        return 0
    except MetricsError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
