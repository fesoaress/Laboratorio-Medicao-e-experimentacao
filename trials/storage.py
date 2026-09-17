"""Persistência idempotente e atômica dos resultados dos trials."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from .config import CYCLES_CSV, TRIALS_CSV


TRIAL_FIELDS = [
    "trial_id",
    "issue",
    "participante",
    "kata",
    "tratamento",
    "tempo_segundos",
    "testes_passando",
    "testes_falhando",
    "total_testes",
    "taxa_sucesso",
    "ciclos",
    "status",
    "codigo_path",
    "iniciado_em",
    "finalizado_em",
    "erro_execucao",
    "source_kind",
]

CYCLE_FIELDS = [
    "trial_id",
    "issue",
    "participante",
    "kata",
    "tratamento",
    "ciclo",
    "tempo_segundos",
    "testes_passando",
    "testes_falhando",
    "total_testes",
    "taxa_sucesso",
    "pytest_exit_code",
    "erro_execucao",
    "source_kind",
]


class StorageError(RuntimeError):
    """CSV ausente ou incompatível com o schema atual."""


def _read_rows(path: Path, fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames not in (fields, fields[:-1]):
            raise StorageError(
                f"Cabeçalho incompatível em {path}. Faça backup do arquivo antes de migrar."
            )
        rows = list(reader)
        for row in rows:
            row.setdefault("source_kind", "observed")
        return rows


def _atomic_write(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _upsert(path: Path, fields: list[str], row: dict, key_fields: tuple[str, ...]) -> None:
    rows = _read_rows(path, fields)
    row = {**row, "source_kind": row.get("source_kind") or "observed"}
    key = tuple(str(row.get(field, "")) for field in key_fields)
    kept = [
        existing
        for existing in rows
        if tuple(str(existing.get(field, "")) for field in key_fields) != key
    ]
    kept.append(row)
    _atomic_write(path, fields, kept)


def ensure_files(
    trials_csv: Path = TRIALS_CSV, cycles_csv: Path = CYCLES_CSV
) -> None:
    trials_csv.parent.mkdir(parents=True, exist_ok=True)
    if not trials_csv.exists():
        _atomic_write(trials_csv, TRIAL_FIELDS, [])
    if not cycles_csv.exists():
        _atomic_write(cycles_csv, CYCLE_FIELDS, [])


def register_trial(data: dict, csv_path: Path = TRIALS_CSV) -> None:
    _upsert(csv_path, TRIAL_FIELDS, data, ("trial_id",))


def register_cycle(data: dict, csv_path: Path = CYCLES_CSV) -> None:
    _upsert(csv_path, CYCLE_FIELDS, data, ("trial_id", "ciclo"))


# Compatibilidade nominal com a implementação da S01.
garantir_arquivos = ensure_files
registrar_trial = register_trial
registrar_ciclo = register_cycle
