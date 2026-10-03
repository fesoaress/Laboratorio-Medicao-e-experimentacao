"""Cálculo das métricas das RQ05 e RQ06."""
from __future__ import annotations

from typing import Any

LANGUAGE_NOT_INFORMED = "Não informado"


def normalize_primary_language(primary_language: dict[str, Any] | None) -> str:
    """Normaliza o nome da linguagem primária do repositório.

    O GitHub retorna `primaryLanguage: null` quando o repositório não tem
    uma linguagem detectável (ex.: repositórios só de documentação/config).
    """
    if not primary_language:
        return LANGUAGE_NOT_INFORMED
    name = primary_language.get("name")
    return name if name else LANGUAGE_NOT_INFORMED


def normalize_issue_counts(total_issues: Any, closed_issues: Any) -> tuple[int, int]:
    """Normaliza e valida os totais de issues (todas e fechadas)."""
    if total_issues is None:
        raise ValueError("Total de issues não pode ser nulo.")
    if closed_issues is None:
        raise ValueError("Total de issues fechadas não pode ser nulo.")

    total = int(total_issues)
    closed = int(closed_issues)

    if total < 0 or closed < 0:
        raise ValueError("Totais de issues não podem ser negativos.")
    if closed > total:
        raise ValueError("Issues fechadas não podem exceder o total de issues.")

    return total, closed


def calculate_closed_issues_ratio(total_issues: Any, closed_issues: Any) -> float | None:
    """Calcula a razão entre issues fechadas e total de issues.

    Retorna None quando o repositório não possui nenhuma issue (razão
    indefinida) — trate esse caso explicitamente na análise (RQ06), não
    como zero.
    """
    total, closed = normalize_issue_counts(total_issues, closed_issues)
    if total == 0:
        return None
    return closed / total


def normalize_repository_rq05_rq06(repository: dict[str, Any]) -> dict[str, Any]:
    """Normaliza os campos de RQ05/RQ06 a partir de um node da query GraphQL.

    Espera que o node do repositório tenha os campos:
        primaryLanguage { name }
        issues { totalCount }
        closedIssues: issues(states: CLOSED) { totalCount }
    """
    primary_language = normalize_primary_language(repository.get("primaryLanguage"))

    issues = repository.get("issues") or {}
    closed_issues = repository.get("closedIssues") or {}

    total_issues = issues.get("totalCount")
    closed_issues_count = closed_issues.get("totalCount")

    ratio = calculate_closed_issues_ratio(total_issues, closed_issues_count)

    return {
        "primary_language": primary_language,
        "total_issues": int(total_issues or 0),
        "closed_issues": int(closed_issues_count or 0),
        "closed_issues_ratio": ratio,
    }