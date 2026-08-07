"""Orquestração da coleta dos repositórios populares."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUERY_PATH = PROJECT_ROOT / "src" / "api" / "queries" / "repositories.graphql"
DEFAULT_SEARCH_QUERY = "stars:>0 sort:stars-desc"
SPRINT_1_REPOSITORY_LIMIT = 100
VALIDATION_SAMPLE_SIZE = 10

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.github_client import GitHubClientError, execute_graphql_query
from src.metrics.rq01_rq02 import (
    calculate_repository_age_days,
    normalize_merged_pull_requests,
)


def load_repositories_query() -> str:
    """Carrega a query GraphQL usada na coleta de repositórios."""
    return QUERY_PATH.read_text(encoding="utf-8")


def fetch_popular_repositories(first: int = SPRINT_1_REPOSITORY_LIMIT) -> dict[str, Any]:
    """Executa a consulta dos repositórios mais populares no GitHub."""
    query = load_repositories_query()
    variables = {
        "first": first,
        "after": None,
        "queryString": DEFAULT_SEARCH_QUERY,
    }
    data = execute_graphql_query(query, variables)
    search_data = data.get("search")
    if not isinstance(search_data, dict):
        raise ValueError("Resposta GraphQL não contém o campo search esperado.")
    return search_data


def normalize_repository(repository: dict[str, Any]) -> dict[str, Any]:
    """Normaliza os campos necessários para RQ01 e RQ02."""
    pull_requests = repository.get("pullRequests") or {}
    merged_pull_requests = normalize_merged_pull_requests(pull_requests.get("totalCount"))
    created_at = repository.get("createdAt")
    age_days = calculate_repository_age_days(created_at)

    return {
        "name_with_owner": repository.get("nameWithOwner"),
        "stargazer_count": int(repository.get("stargazerCount") or 0),
        "created_at": created_at,
        "repository_age_days": age_days,
        "merged_pull_requests": merged_pull_requests,
    }


def collect_repositories(limit: int = SPRINT_1_REPOSITORY_LIMIT) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Coleta e normaliza os repositórios populares da Sprint 1."""
    search_data = fetch_popular_repositories(limit)
    nodes = search_data.get("nodes") or []

    repositories = [
        normalize_repository(node)
        for node in nodes
        if isinstance(node, dict) and node.get("nameWithOwner")
    ]

    return repositories, search_data.get("pageInfo") or {}


def validate_collection(
    repositories: list[dict[str, Any]],
    *,
    expected_count: int = SPRINT_1_REPOSITORY_LIMIT,
    sample_size: int = VALIDATION_SAMPLE_SIZE,
) -> dict[str, Any]:
    """Valida condições básicas e prepara uma amostra para inspeção."""
    errors: list[str] = []

    if len(repositories) != expected_count:
        errors.append(f"Quantidade coletada esperada: {expected_count}; obtida: {len(repositories)}.")

    for index, repository in enumerate(repositories, start=1):
        if not repository.get("name_with_owner"):
            errors.append(f"Repositório {index}: nome ausente.")
        if not repository.get("created_at"):
            errors.append(f"Repositório {index}: createdAt ausente.")
        if repository.get("stargazer_count", -1) < 0:
            errors.append(f"Repositório {index}: estrelas negativas.")
        if repository.get("repository_age_days", -1) < 0:
            errors.append(f"Repositório {index}: idade negativa.")
        if repository.get("merged_pull_requests", -1) < 0:
            errors.append(f"Repositório {index}: pull requests aceitas negativas.")

    for previous, current in zip(repositories, repositories[1:]):
        if previous["stargazer_count"] < current["stargazer_count"]:
            errors.append("Ordenação por estrelas não está em ordem decrescente.")
            break

    sample = [
        {
            "name_with_owner": repository["name_with_owner"],
            "stargazer_count": repository["stargazer_count"],
            "created_at": repository["created_at"],
            "repository_age_days": repository["repository_age_days"],
            "merged_pull_requests": repository["merged_pull_requests"],
        }
        for repository in repositories[:sample_size]
    ]

    return {
        "is_valid": not errors,
        "errors": errors,
        "sample": sample,
    }


def print_collection_summary(
    repositories: list[dict[str, Any]],
    page_info: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    """Exibe um resumo legível da coleta e da validação."""
    print(f"Repositórios coletados: {len(repositories)}")
    print(f"Próxima página disponível: {page_info.get('hasNextPage')}")
    print(f"Cursor final: {page_info.get('endCursor')}")
    print(f"Validação básica: {'ok' if validation['is_valid'] else 'falhou'}")

    if validation["errors"]:
        print("Erros de validação:")
        for error in validation["errors"]:
            print(f"- {error}")

    print("\nAmostra de validação:")
    for repository in validation["sample"]:
        print(
            "- "
            f"{repository['name_with_owner']} | "
            f"estrelas={repository['stargazer_count']} | "
            f"createdAt={repository['created_at']} | "
            f"idade_dias={repository['repository_age_days']} | "
            f"prs_aceitas={repository['merged_pull_requests']}"
        )


def save_raw_output(repositories: list[dict[str, Any]], output_path: Path) -> None:
    """Salva a coleta normalizada em JSON, sem sobrescrever arquivos existentes."""
    if output_path.exists():
        raise FileExistsError(f"O arquivo de saída já existe: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(repositories, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    """Executa a coleta e a validação da Sprint 1."""
    parser = argparse.ArgumentParser(description="Coleta os 100 repositórios populares para RQ01 e RQ02.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Caminho opcional para salvar a coleta normalizada em JSON.",
    )
    args = parser.parse_args()

    try:
        repositories, page_info = collect_repositories()
    except GitHubClientError as error:
        raise SystemExit(f"Coleta não executada: {error}")

    validation = validate_collection(repositories)

    print_collection_summary(repositories, page_info, validation)

    if not validation["is_valid"]:
        raise SystemExit("Coleta interrompida: os dados retornados não passaram na validação.")

    if args.output:
        save_raw_output(repositories, args.output)
        print(f"\nColeta salva em: {args.output}")


if __name__ == "__main__":
    main()
