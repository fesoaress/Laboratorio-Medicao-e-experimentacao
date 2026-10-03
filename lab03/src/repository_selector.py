"""Seleção ordenada por estrelas, paginada e deduplicada entre fatias."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Any

from .config import SelectionConfig
from .github_client import APIError, Client, iter_pages


@dataclass
class SearchResult:
    repositories: list[dict[str, Any]] = field(default_factory=list)
    queries: list[dict[str, Any]] = field(default_factory=list)
    duplicates_skipped: int = 0
    errors: list[str] = field(default_factory=list)


def select_candidates(client: Client, config: SelectionConfig) -> SearchResult:
    result = SearchResult()
    seen_ids, seen_names = set(), set()
    for query in config.search_queries:
        report = {"query": query, "total_count": None, "incomplete_results": False,
                  "items_seen": 0, "search_cap": 1000}
        result.queries.append(report)
        try:
            pages = iter_pages(client, "/search/repositories", {
                "q": query + " is:public", "sort": "stars", "order": "desc",
                "per_page": config.per_page, "page": 1,
            }, max_pages=ceil(1000 / config.per_page))
            for response in pages:
                data = response.data
                if not isinstance(data, dict) or not isinstance(data.get("items"), list):
                    raise APIError("Busca retornou resposta sem lista items.")
                report["total_count"] = data.get("total_count")
                report["incomplete_results"] |= bool(data.get("incomplete_results", False))
                for repository in data["items"]:
                    if report["items_seen"] >= 1000:
                        break
                    report["items_seen"] += 1
                    if not isinstance(repository, dict) or not isinstance(repository.get("full_name"), str):
                        raise APIError("Candidato sem full_name válido.")
                    name, identifier = repository["full_name"].casefold(), repository.get("id")
                    if name in seen_names or (identifier is not None and identifier in seen_ids):
                        result.duplicates_skipped += 1
                        continue
                    seen_names.add(name)
                    if identifier is not None:
                        seen_ids.add(identifier)
                    result.repositories.append(repository)
                    if len(result.repositories) == config.sample_size:
                        return result
        except APIError as error:
            result.errors.append(str(error))
            break  # Não repetir chamadas após erro/rate limit.
    return result
