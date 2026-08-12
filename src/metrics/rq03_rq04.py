"""Cálculo das métricas das RQ03 e RQ04."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.metrics.rq01_rq02 import _parse_github_datetime


def normalize_release_count(total_count: Any) -> int:
    """Normaliza o total de releases retornado pela API."""
    if total_count is None:
        raise ValueError("Total de releases não pode ser nulo.")

    release_count = int(total_count)
    if release_count < 0:
        raise ValueError("Total de releases não pode ser negativo.")

    return release_count


def calculate_days_since_last_update(
    pushed_at: str,
    *,
    reference_datetime: datetime | None = None,
) -> int:
    """Calcula quantos dias se passaram desde o último push (pushedAt)."""
    if not pushed_at:
        raise ValueError("pushedAt não pode estar vazio.")

    last_push_datetime = _parse_github_datetime(pushed_at)
    reference = reference_datetime or datetime.now(timezone.utc)

    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)

    days_since = (reference - last_push_datetime).days
    if days_since < 0:
        raise ValueError("pushedAt não pode estar no futuro.")

    return days_since
