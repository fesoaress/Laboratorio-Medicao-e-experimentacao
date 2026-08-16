"""Paginacao GraphQL, retry/backoff e leitura do rate limit."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from src.api.github_client import (
    GitHubClientError,
    GitHubGraphQLError,
    execute_graphql_query,
)


DEFAULT_SEARCH_QUERY = "stars:>0 sort:stars-desc"
TRANSIENT_ERROR_MARKERS = (
    "502",
    "503",
    "504",
    "erro de conex",
    "timed out",
    "timeout",
    "tempor",
)


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 2.0


@dataclass(frozen=True)
class RepositoryPage:
    nodes: list[dict[str, Any]]
    page_info: dict[str, Any]
    rate_limit: dict[str, Any]
    repository_count: int | None


GraphQLExecutor = Callable[[str, dict[str, Any]], dict[str, Any]]
Sleeper = Callable[[float], None]


def is_transient_github_error(error: GitHubClientError) -> bool:
    """Classifica erros que podem ser tentados novamente."""

    if isinstance(error, GitHubGraphQLError):
        return False

    message = str(error).lower()
    return any(marker in message for marker in TRANSIENT_ERROR_MARKERS)


def fetch_repository_page(
    query: str,
    *,
    first: int,
    after: str | None,
    query_string: str = DEFAULT_SEARCH_QUERY,
    retry_config: RetryConfig | None = None,
    execute_query: GraphQLExecutor = execute_graphql_query,
    sleeper: Sleeper = time.sleep,
) -> RepositoryPage:
    """Busca uma pagina da query de repositorios com retry limitado."""

    retry = retry_config or RetryConfig()
    variables = {
        "first": first,
        "after": after,
        "queryString": query_string,
    }

    for attempt in range(1, retry.max_attempts + 1):
        try:
            data = execute_query(query, variables)
            search = data.get("search")
            if not isinstance(search, dict):
                raise ValueError("Resposta GraphQL sem o campo search esperado.")

            raw_nodes = search.get("nodes") or []
            nodes = [node for node in raw_nodes if isinstance(node, dict)]
            page_info = search.get("pageInfo") or {}
            rate_limit = data.get("rateLimit") or {}
            repository_count = search.get("repositoryCount")

            return RepositoryPage(
                nodes=nodes,
                page_info=page_info,
                rate_limit=rate_limit,
                repository_count=(
                    int(repository_count)
                    if repository_count is not None
                    else None
                ),
            )
        except GitHubClientError as error:
            if (
                not is_transient_github_error(error)
                or attempt == retry.max_attempts
            ):
                raise

            sleeper(retry.base_delay_seconds * attempt)

    raise RuntimeError("Nao foi possivel concluir a consulta.")
