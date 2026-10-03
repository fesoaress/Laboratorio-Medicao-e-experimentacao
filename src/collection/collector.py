"""Orquestracao da coleta robusta da Sprint 2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.collection.normalization import normalize_repository
from src.collection.pagination import (
    DEFAULT_SEARCH_QUERY,
    RepositoryPage,
    RetryConfig,
    fetch_repository_page,
)
from src.collection.persistence import (
    append_repositories_to_csv,
    count_csv_records,
    load_checkpoint,
    prepare_output_file,
    read_existing_repository_names,
    read_repositories_from_csv,
    write_checkpoint,
)
from src.collection.validation import (
    validate_collection,
    validate_repository_record,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUERY_PATH = PROJECT_ROOT / "src" / "api" / "queries" / "repositories.graphql"
DEFAULT_LIMIT = 1000
DEFAULT_PAGE_SIZE = 10
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "repositories_s02.csv"
DEFAULT_CHECKPOINT_PATH = (
    PROJECT_ROOT / "data" / "raw" / "repositories_s02.checkpoint.json"
)
DEFAULT_RATE_LIMIT_THRESHOLD = 100


class RateLimitPaused(RuntimeError):
    """Sinaliza pausa segura por proximidade do rate limit."""


@dataclass(frozen=True)
class CollectionConfig:
    limit: int = DEFAULT_LIMIT
    page_size: int = DEFAULT_PAGE_SIZE
    output_path: Path = DEFAULT_OUTPUT_PATH
    checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH
    search_query: str = DEFAULT_SEARCH_QUERY
    resume: bool = False
    overwrite: bool = False
    retry_config: RetryConfig = RetryConfig()
    rate_limit_threshold: int = DEFAULT_RATE_LIMIT_THRESHOLD
    max_rate_limit_wait_seconds: int = 0


@dataclass(frozen=True)
class CollectionResult:
    repositories: list[dict[str, Any]]
    pages_collected: int
    output_path: Path
    checkpoint_path: Path
    validation: dict[str, Any]
    last_page_info: dict[str, Any]
    last_rate_limit: dict[str, Any]
    completed: bool


Sleeper = Callable[[float], None]


def load_repositories_query() -> str:
    """Carrega a query GraphQL dos repositorios populares."""

    return QUERY_PATH.read_text(encoding="utf-8")


def _parse_reset_at(reset_at: str | None) -> datetime | None:
    if not reset_at:
        return None
    return datetime.fromisoformat(reset_at.replace("Z", "+00:00"))


def _maybe_wait_or_pause_for_rate_limit(
    rate_limit: dict[str, Any],
    *,
    threshold: int,
    max_wait_seconds: int,
    sleeper: Sleeper,
) -> None:
    remaining = rate_limit.get("remaining")
    if remaining is None or int(remaining) > threshold:
        return

    reset_at = _parse_reset_at(rate_limit.get("resetAt"))
    if reset_at is None:
        raise RateLimitPaused(
            "Rate limit proximo do limite e resetAt indisponivel."
        )

    wait_seconds = max(
        0,
        int((reset_at - datetime.now(timezone.utc)).total_seconds()) + 5,
    )
    if wait_seconds <= max_wait_seconds:
        sleeper(wait_seconds)
        return

    raise RateLimitPaused(
        "Rate limit proximo do limite; checkpoint preservado para resume."
    )


def _initial_collection_state(
    config: CollectionConfig,
) -> tuple[str | None, int, set[str]]:
    if config.resume:
        checkpoint = load_checkpoint(config.checkpoint_path)
        if checkpoint is None:
            raise FileNotFoundError(
                "Checkpoint nao encontrado para resume: "
                f"{config.checkpoint_path}"
            )
        if Path(checkpoint.get("output_path", "")) != config.output_path:
            raise ValueError("Checkpoint pertence a outro arquivo CSV.")

        names = read_existing_repository_names(config.output_path)
        return (
            checkpoint.get("last_cursor"),
            count_csv_records(config.output_path),
            names,
        )

    prepare_output_file(config.output_path, overwrite=config.overwrite)
    return None, 0, set()


def collect_popular_repositories(
    config: CollectionConfig,
    *,
    fetch_page: Callable[..., RepositoryPage] = fetch_repository_page,
    sleeper: Sleeper = __import__("time").sleep,
) -> CollectionResult:
    """Coleta repositorios, persiste por pagina e atualiza checkpoint."""

    query = load_repositories_query()
    after, persisted_count, known_names = _initial_collection_state(config)
    repositories: list[dict[str, Any]] = []
    pages_collected = 0
    last_page_info: dict[str, Any] = {}
    last_rate_limit: dict[str, Any] = {}

    while persisted_count < config.limit:
        remaining = config.limit - persisted_count
        page_size = min(config.page_size, remaining)
        page = fetch_page(
            query,
            first=page_size,
            after=after,
            query_string=config.search_query,
            retry_config=config.retry_config,
            sleeper=sleeper,
        )
        pages_collected += 1
        last_page_info = page.page_info
        last_rate_limit = page.rate_limit

        page_records: list[dict[str, Any]] = []
        for node in page.nodes:
            if not node.get("nameWithOwner"):
                continue

            record = normalize_repository(node)
            name = record.get("name_with_owner")
            if name in known_names:
                continue

            record_errors = validate_repository_record(
                record,
                index=persisted_count + len(page_records) + 1,
            )
            if record_errors:
                raise ValueError("; ".join(record_errors))

            page_records.append(record)
            known_names.add(str(name))

        if page_records:
            written = append_repositories_to_csv(config.output_path, page_records)
            persisted_count += written
            repositories.extend(page_records)

        has_next_page = bool(last_page_info.get("hasNextPage"))
        after = last_page_info.get("endCursor")
        completed = persisted_count >= config.limit or not has_next_page

        write_checkpoint(
            config.checkpoint_path,
            output_path=config.output_path,
            limit=config.limit,
            page_size=config.page_size,
            search_query=config.search_query,
            collected_count=persisted_count,
            last_cursor=after,
            has_next_page=has_next_page,
            completed=completed,
            pages_collected=pages_collected,
            rate_limit=last_rate_limit,
        )

        if completed:
            break

        if not after:
            break

        _maybe_wait_or_pause_for_rate_limit(
            last_rate_limit,
            threshold=config.rate_limit_threshold,
            max_wait_seconds=config.max_rate_limit_wait_seconds,
            sleeper=sleeper,
        )

    persisted_repositories = read_repositories_from_csv(config.output_path)
    validation = validate_collection(
        persisted_repositories,
        expected_count=min(config.limit, persisted_count),
    )

    return CollectionResult(
        repositories=persisted_repositories,
        pages_collected=pages_collected,
        output_path=config.output_path,
        checkpoint_path=config.checkpoint_path,
        validation=validation,
        last_page_info=last_page_info,
        last_rate_limit=last_rate_limit,
        completed=persisted_count >= config.limit,
    )
