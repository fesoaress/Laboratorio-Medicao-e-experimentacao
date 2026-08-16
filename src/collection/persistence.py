"""Persistencia incremental em CSV e checkpoint de coleta."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CSV_FIELDS = [
    "name_with_owner",
    "stargazer_count",
    "created_at",
    "repository_age_days",
    "merged_pull_requests",
    "release_count",
    "pushed_at",
    "days_since_last_update",
    "primary_language",
    "total_issues",
    "closed_issues",
    "closed_issues_ratio",
]


def prepare_output_file(output_path: Path, *, overwrite: bool = False) -> None:
    """Cria o CSV com cabecalho antes da coleta."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            "Arquivo de saida ja existe. Use --resume ou --overwrite: "
            f"{output_path}"
        )

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()


def append_repositories_to_csv(
    output_path: Path,
    repositories: Iterable[dict[str, Any]],
) -> int:
    """Acrescenta registros ao CSV e retorna quantas linhas foram gravadas."""

    written = 0
    with output_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        for repository in repositories:
            row = {field: repository.get(field) for field in CSV_FIELDS}
            if row["closed_issues_ratio"] is None:
                row["closed_issues_ratio"] = ""
            writer.writerow(row)
            written += 1
    return written


def read_existing_repository_names(output_path: Path) -> set[str]:
    """Le nomes ja persistidos para evitar duplicatas no resume."""

    if not output_path.exists():
        return set()

    with output_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return {
            row["name_with_owner"]
            for row in reader
            if row.get("name_with_owner")
        }


def count_csv_records(output_path: Path) -> int:
    """Conta registros de dados existentes no CSV."""

    if not output_path.exists():
        return 0

    with output_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return sum(1 for _ in reader)


def read_repositories_from_csv(output_path: Path) -> list[dict[str, Any]]:
    """Le registros persistidos e reconverte tipos basicos."""

    if not output_path.exists():
        return []

    integer_fields = {
        "stargazer_count",
        "repository_age_days",
        "merged_pull_requests",
        "release_count",
        "days_since_last_update",
        "total_issues",
        "closed_issues",
    }
    repositories: list[dict[str, Any]] = []
    with output_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            repository: dict[str, Any] = dict(row)
            for field in integer_fields:
                repository[field] = int(repository[field])
            ratio = repository.get("closed_issues_ratio")
            repository["closed_issues_ratio"] = (
                None if ratio in (None, "") else float(ratio)
            )
            repositories.append(repository)
    return repositories


def load_checkpoint(checkpoint_path: Path) -> dict[str, Any] | None:
    """Carrega checkpoint JSON, quando existir."""

    if not checkpoint_path.exists():
        return None

    with checkpoint_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Checkpoint invalido.")
    return data


def write_checkpoint(
    checkpoint_path: Path,
    *,
    output_path: Path,
    limit: int,
    page_size: int,
    search_query: str,
    collected_count: int,
    last_cursor: str | None,
    has_next_page: bool,
    completed: bool,
    pages_collected: int,
    rate_limit: dict[str, Any] | None,
) -> None:
    """Grava o estado necessario para retomar a coleta."""

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "output_path": str(output_path),
        "limit": limit,
        "page_size": page_size,
        "search_query": search_query,
        "collected_count": collected_count,
        "last_cursor": last_cursor,
        "has_next_page": has_next_page,
        "completed": completed,
        "pages_collected": pages_collected,
        "rate_limit": rate_limit or {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    checkpoint_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
