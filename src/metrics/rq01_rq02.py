"""Cálculo das métricas das RQ01 e RQ02."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_github_datetime(value: str) -> datetime:
    """Converte uma data ISO 8601 do GitHub para datetime com fuso horário."""
    if not value:
        raise ValueError("createdAt não pode estar vazio.")

    normalized_value = value.replace("Z", "+00:00")
    parsed_value = datetime.fromisoformat(normalized_value)
    if parsed_value.tzinfo is None:
        return parsed_value.replace(tzinfo=timezone.utc)
    return parsed_value


def calculate_repository_age_days(
    created_at: str,
    *,
    reference_datetime: datetime | None = None,
) -> int:
    """Calcula a idade do repositório em dias a partir de createdAt."""
    created_datetime = _parse_github_datetime(created_at)
    reference = reference_datetime or datetime.now(timezone.utc)

    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)

    age_days = (reference - created_datetime).days
    if age_days < 0:
        raise ValueError("createdAt não pode estar no futuro.")

    return age_days


def normalize_merged_pull_requests(total_count: Any) -> int:
    """Normaliza o total de pull requests aceitas retornado pela API."""
    if total_count is None:
        raise ValueError("Total de pull requests aceitas não pode ser nulo.")

    merged_pull_requests = int(total_count)
    if merged_pull_requests < 0:
        raise ValueError("Total de pull requests aceitas não pode ser negativo.")

    return merged_pull_requests
