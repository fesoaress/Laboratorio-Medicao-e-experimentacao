"""Normalizacao dos registros de repositorios para RQ01-RQ06."""

from __future__ import annotations

from typing import Any

from src.metrics.rq01_rq02 import (
    calculate_repository_age_days,
    normalize_merged_pull_requests,
)
from src.metrics.rq03_rq04 import (
    calculate_days_since_last_update,
    normalize_release_count,
)
from src.metrics.rq05_rq06 import normalize_repository_rq05_rq06


def normalize_repository(repository: dict[str, Any]) -> dict[str, Any]:
    """Normaliza um node de Repository retornado pela API GraphQL."""

    created_at = repository.get("createdAt")
    pull_requests = repository.get("pullRequests") or {}
    releases = repository.get("releases") or {}
    pushed_at = repository.get("pushedAt")

    return {
        "name_with_owner": repository.get("nameWithOwner"),
        "stargazer_count": int(repository.get("stargazerCount") or 0),
        "created_at": created_at,
        "repository_age_days": calculate_repository_age_days(created_at),
        "merged_pull_requests": normalize_merged_pull_requests(
            pull_requests.get("totalCount")
        ),
        "release_count": normalize_release_count(releases.get("totalCount")),
        "pushed_at": pushed_at,
        "days_since_last_update": calculate_days_since_last_update(pushed_at),
        **normalize_repository_rq05_rq06(repository),
    }
