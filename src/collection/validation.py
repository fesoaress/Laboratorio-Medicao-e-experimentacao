"""Validacoes de registros e do dataset coletado."""

from __future__ import annotations

from collections import Counter
from typing import Any

from src.metrics.rq05_rq06 import LANGUAGE_NOT_INFORMED


NUMERIC_FIELDS = [
    "stargazer_count",
    "repository_age_days",
    "merged_pull_requests",
    "release_count",
    "days_since_last_update",
    "total_issues",
    "closed_issues",
]

REQUIRED_FIELDS = [
    "name_with_owner",
    "created_at",
    "pushed_at",
    "primary_language",
]


def validate_repository_record(
    repository: dict[str, Any],
    *,
    index: int,
) -> list[str]:
    """Valida um registro normalizado."""

    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if repository.get(field) in (None, ""):
            errors.append(f"Repositorio {index}: campo ausente: {field}.")

    for field in NUMERIC_FIELDS:
        value = repository.get(field)
        if value is None:
            errors.append(f"Repositorio {index}: campo ausente: {field}.")
            continue
        if value < 0:
            errors.append(f"Repositorio {index}: valor negativo: {field}.")

    total_issues = repository.get("total_issues", 0)
    closed_issues = repository.get("closed_issues", 0)
    if closed_issues > total_issues:
        errors.append(
            f"Repositorio {index}: issues fechadas maior que o total."
        )

    ratio = repository.get("closed_issues_ratio")
    if total_issues == 0 and ratio is not None:
        errors.append(
            f"Repositorio {index}: RQ06 deveria ser indefinida."
        )
    if ratio is not None and not 0 <= ratio <= 1:
        errors.append(f"Repositorio {index}: RQ06 fora do intervalo 0-1.")

    return errors


def build_collection_statistics(
    repositories: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calcula indicadores globais do dataset para inspecao."""

    names = [
        repository.get("name_with_owner")
        for repository in repositories
        if repository.get("name_with_owner")
    ]
    counts = Counter(names)
    duplicated_names = sorted(
        name for name, count in counts.items() if count > 1
    )

    missing_field_count = 0
    for repository in repositories:
        for field in REQUIRED_FIELDS:
            if repository.get(field) in (None, ""):
                missing_field_count += 1

    def numeric_values(field: str) -> list[int]:
        return [
            int(repository[field])
            for repository in repositories
            if repository.get(field) is not None
        ]

    numeric_ranges = {}
    for field in NUMERIC_FIELDS:
        values = numeric_values(field)
        numeric_ranges[field] = {
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }

    return {
        "collected_count": len(repositories),
        "unique_count": len(counts),
        "duplicate_count": len(repositories) - len(counts),
        "duplicated_names": duplicated_names,
        "missing_names": len(repositories) - len(names),
        "missing_fields": missing_field_count,
        "primary_language_not_informed": sum(
            1
            for repository in repositories
            if repository.get("primary_language") == LANGUAGE_NOT_INFORMED
        ),
        "rq06_undefined_total_issues_zero": sum(
            1
            for repository in repositories
            if repository.get("total_issues") == 0
            and repository.get("closed_issues_ratio") is None
        ),
        "numeric_ranges": numeric_ranges,
    }


def validate_collection(
    repositories: list[dict[str, Any]],
    *,
    expected_count: int,
    sample_size: int = 10,
) -> dict[str, Any]:
    """Valida quantidade, unicidade, campos e ordenacao por estrelas."""

    errors: list[str] = []

    if len(repositories) != expected_count:
        errors.append(
            "Quantidade coletada esperada: "
            f"{expected_count}; obtida: {len(repositories)}."
        )

    for index, repository in enumerate(repositories, start=1):
        errors.extend(validate_repository_record(repository, index=index))

    for previous, current in zip(repositories, repositories[1:]):
        if previous["stargazer_count"] < current["stargazer_count"]:
            errors.append(
                "Ordenacao por estrelas nao esta em ordem decrescente."
            )
            break

    statistics = build_collection_statistics(repositories)
    if statistics["duplicate_count"] > 0:
        errors.append(
            "Dataset contem repositorios duplicados: "
            f"{statistics['duplicate_count']}."
        )

    sample = sorted(
        repositories,
        key=lambda repository: repository.get("stargazer_count", 0),
        reverse=True,
    )[:sample_size]

    return {
        "is_valid": not errors,
        "errors": errors,
        "sample": sample,
        "statistics": statistics,
    }
