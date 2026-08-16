"""Validacoes de registros e do dataset coletado."""
from __future__ import annotations

import statistics
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

TOP_LANGUAGES_LIMIT = 15


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


def build_language_distribution(
    repositories: list[dict[str, Any]],
) -> dict[str, Any]:
    """Distribuicao de frequencia da linguagem primaria (RQ05)."""
    languages = [
        repository.get("primary_language", "") for repository in repositories
    ]
    counts = Counter(languages)
    total = len(repositories)
    top_languages = [
        {
            "language": language,
            "count": count,
            "percentage": (count / total * 100) if total else 0.0,
        }
        for language, count in counts.most_common(TOP_LANGUAGES_LIMIT)
    ]
    return {
        "unique_languages": len(counts),
        "top_languages": top_languages,
    }


def build_closed_issues_ratio_distribution(
    repositories: list[dict[str, Any]],
) -> dict[str, Any]:
    """Estatisticas de distribuicao e outliers da razao de issues fechadas (RQ06)."""
    ratios = [
        float(repository["closed_issues_ratio"])
        for repository in repositories
        if repository.get("closed_issues_ratio") is not None
    ]
    if not ratios:
        return {
            "count_defined": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "q1": None,
            "q3": None,
            "outlier_count": 0,
            "outlier_pct": 0.0,
        }
    sorted_ratios = sorted(ratios)
    q1 = statistics.quantiles(sorted_ratios, n=4)[0]
    q3 = statistics.quantiles(sorted_ratios, n=4)[2]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = [
        ratio for ratio in ratios if ratio < lower_bound or ratio > upper_bound
    ]
    return {
        "count_defined": len(ratios),
        "min": min(ratios),
        "max": max(ratios),
        "mean": statistics.mean(ratios),
        "median": statistics.median(ratios),
        "q1": q1,
        "q3": q3,
        "outlier_count": len(outliers),
        "outlier_pct": len(outliers) / len(ratios) * 100,
    }


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
        "language_distribution": build_language_distribution(repositories),
        "closed_issues_ratio_distribution": build_closed_issues_ratio_distribution(
            repositories
        ),
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
    statistics_data = build_collection_statistics(repositories)
    if statistics_data["duplicate_count"] > 0:
        errors.append(
            "Dataset contem repositorios duplicados: "
            f"{statistics_data['duplicate_count']}."
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
        "statistics": statistics_data,
    }