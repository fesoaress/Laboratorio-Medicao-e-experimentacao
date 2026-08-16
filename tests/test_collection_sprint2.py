"""Testes dos componentes de coleta da Sprint 2."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from src.api.github_client import GitHubClientError, GitHubGraphQLError
from src.collection.collector import CollectionConfig, collect_popular_repositories
from src.collection.pagination import (
    RepositoryPage,
    RetryConfig,
    fetch_repository_page,
)
from src.collection.persistence import (
    count_csv_records,
    load_checkpoint,
    read_repositories_from_csv,
)
from src.collection.validation import validate_collection


def make_node(
    name: str,
    stars: int,
    *,
    language: dict[str, str] | None = None,
    total_issues: int = 10,
    closed_issues: int = 5,
) -> dict[str, Any]:
    return {
        "nameWithOwner": name,
        "stargazerCount": stars,
        "createdAt": "2020-01-01T00:00:00Z",
        "pullRequests": {"totalCount": 12},
        "releases": {"totalCount": 3},
        "pushedAt": "2026-01-01T00:00:00Z",
        "primaryLanguage": language,
        "issues": {"totalCount": total_issues},
        "closedIssues": {"totalCount": closed_issues},
    }


class PaginationTest(unittest.TestCase):
    def test_retry_transient_error_then_success(self) -> None:
        attempts: list[int] = []

        def fake_execute(query: str, variables: dict[str, Any]) -> dict[str, Any]:
            attempts.append(1)
            if len(attempts) == 1:
                raise GitHubClientError("Erro HTTP 502 ao consultar o GitHub")
            return {
                "rateLimit": {"cost": 1, "remaining": 4999, "resetAt": "2026-01-01T00:00:00Z"},
                "search": {
                    "repositoryCount": 1,
                    "pageInfo": {"hasNextPage": False, "endCursor": "cursor"},
                    "nodes": [make_node("owner/repo", 10)],
                },
            }

        page = fetch_repository_page(
            "query",
            first=1,
            after=None,
            retry_config=RetryConfig(max_attempts=2, base_delay_seconds=0),
            execute_query=fake_execute,
            sleeper=lambda seconds: None,
        )

        self.assertEqual(len(attempts), 2)
        self.assertEqual(page.rate_limit["remaining"], 4999)
        self.assertEqual(page.page_info["endCursor"], "cursor")

    def test_graphql_error_is_not_retried(self) -> None:
        attempts: list[int] = []

        def fake_execute(query: str, variables: dict[str, Any]) -> dict[str, Any]:
            attempts.append(1)
            raise GitHubGraphQLError("A consulta GraphQL falhou.")

        with self.assertRaises(GitHubGraphQLError):
            fetch_repository_page(
                "query",
                first=1,
                after=None,
                retry_config=RetryConfig(max_attempts=3, base_delay_seconds=0),
                execute_query=fake_execute,
                sleeper=lambda seconds: None,
            )

        self.assertEqual(len(attempts), 1)


class CollectorTest(unittest.TestCase):
    def test_collects_exact_limit_with_csv_checkpoint_and_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "repositories.csv"
            checkpoint = tmp_path / "repositories.checkpoint.json"
            page_sizes: list[int] = []
            after_values: list[str | None] = []

            pages = [
                RepositoryPage(
                    nodes=[make_node("a/one", 30), make_node("b/two", 20, language={"name": "Python"})],
                    page_info={"hasNextPage": True, "endCursor": "cursor-1"},
                    rate_limit={"cost": 1, "remaining": 5000, "resetAt": "2026-01-01T00:00:00Z"},
                    repository_count=3,
                ),
                RepositoryPage(
                    nodes=[make_node("c/three", 10, total_issues=0, closed_issues=0)],
                    page_info={"hasNextPage": False, "endCursor": "cursor-2"},
                    rate_limit={"cost": 1, "remaining": 4999, "resetAt": "2026-01-01T00:00:00Z"},
                    repository_count=3,
                ),
            ]

            def fake_fetch_page(query: str, **kwargs: Any) -> RepositoryPage:
                page_sizes.append(kwargs["first"])
                after_values.append(kwargs["after"])
                return pages.pop(0)

            result = collect_popular_repositories(
                CollectionConfig(
                    limit=3,
                    page_size=2,
                    output_path=output,
                    checkpoint_path=checkpoint,
                    overwrite=True,
                ),
                fetch_page=fake_fetch_page,
                sleeper=lambda seconds: None,
            )

            self.assertTrue(result.validation["is_valid"])
            self.assertEqual(page_sizes, [2, 1])
            self.assertEqual(after_values, [None, "cursor-1"])
            self.assertEqual(count_csv_records(output), 3)
            self.assertEqual(len(read_repositories_from_csv(output)), 3)
            self.assertTrue(load_checkpoint(checkpoint)["completed"])
            self.assertEqual(
                result.validation["statistics"]["rq06_undefined_total_issues_zero"],
                1,
            )

    def test_resume_uses_checkpoint_cursor_and_deduplicates_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "repositories.csv"
            checkpoint = tmp_path / "repositories.checkpoint.json"

            first_pages = [
                RepositoryPage(
                    nodes=[make_node("a/one", 30), make_node("b/two", 20)],
                    page_info={"hasNextPage": True, "endCursor": "cursor-1"},
                    rate_limit={"cost": 1, "remaining": 5000, "resetAt": "2026-01-01T00:00:00Z"},
                    repository_count=3,
                )
            ]

            collect_popular_repositories(
                CollectionConfig(
                    limit=2,
                    page_size=2,
                    output_path=output,
                    checkpoint_path=checkpoint,
                    overwrite=True,
                ),
                fetch_page=lambda query, **kwargs: first_pages.pop(0),
                sleeper=lambda seconds: None,
            )

            after_values: list[str | None] = []
            second_pages = [
                RepositoryPage(
                    nodes=[make_node("b/two", 20), make_node("c/three", 10)],
                    page_info={"hasNextPage": False, "endCursor": "cursor-2"},
                    rate_limit={"cost": 1, "remaining": 4999, "resetAt": "2026-01-01T00:00:00Z"},
                    repository_count=3,
                )
            ]

            def fake_fetch_page(query: str, **kwargs: Any) -> RepositoryPage:
                after_values.append(kwargs["after"])
                return second_pages.pop(0)

            result = collect_popular_repositories(
                CollectionConfig(
                    limit=3,
                    page_size=2,
                    output_path=output,
                    checkpoint_path=checkpoint,
                    resume=True,
                ),
                fetch_page=fake_fetch_page,
                sleeper=lambda seconds: None,
            )

            self.assertEqual(after_values, ["cursor-1"])
            self.assertEqual(count_csv_records(output), 3)
            self.assertEqual(result.validation["statistics"]["duplicate_count"], 0)

    def test_validation_reports_duplicates_and_missing_language_count(self) -> None:
        repositories = [
            {
                "name_with_owner": "a/one",
                "stargazer_count": 10,
                "created_at": "2020-01-01T00:00:00Z",
                "repository_age_days": 10,
                "merged_pull_requests": 1,
                "release_count": 1,
                "pushed_at": "2020-01-01T00:00:00Z",
                "days_since_last_update": 1,
                "primary_language": "Nao informado",
                "total_issues": 0,
                "closed_issues": 0,
                "closed_issues_ratio": None,
            },
            {
                "name_with_owner": "a/one",
                "stargazer_count": 9,
                "created_at": "2020-01-01T00:00:00Z",
                "repository_age_days": 10,
                "merged_pull_requests": 1,
                "release_count": 1,
                "pushed_at": "2020-01-01T00:00:00Z",
                "days_since_last_update": 1,
                "primary_language": "Python",
                "total_issues": 2,
                "closed_issues": 1,
                "closed_issues_ratio": 0.5,
            },
        ]

        validation = validate_collection(repositories, expected_count=2)

        self.assertFalse(validation["is_valid"])
        self.assertEqual(validation["statistics"]["duplicate_count"], 1)


if __name__ == "__main__":
    unittest.main()
