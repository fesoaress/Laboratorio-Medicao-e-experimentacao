"""Validação individual de RQ05 e RQ06 numa amostra de 5-10 repositórios.

Uso isolado (não depende do collect_repositories.py do grupo), conforme o
guia da Sprint 1: cada integrante testa e valida sua parte antes de integrar
ao script único de consulta. Depois de validado, os campos
`primaryLanguage`, `issues` e `closedIssues` (ver
repositories_rq05_rq06_sample.graphql) devem ser adicionados ao
repositories.graphql compartilhado, e a chamada a
`normalize_repository_rq05_rq06` deve ser incorporada ao
`normalize_repository` em collect_repositories.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUERY_PATH = PROJECT_ROOT / "src" / "api" / "queries" / "repositories_rq05_rq06_sample.graphql"
DEFAULT_SEARCH_QUERY = "stars:>0 sort:stars-desc"
DEFAULT_SAMPLE_SIZE = 10

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.github_client import GitHubClientError, execute_graphql_query
from src.metrics.rq05_rq06 import normalize_repository_rq05_rq06


def load_sample_query() -> str:
    """Carrega a query GraphQL de validação de RQ05/RQ06."""
    return QUERY_PATH.read_text(encoding="utf-8")


def fetch_sample_repositories(first: int = DEFAULT_SAMPLE_SIZE) -> list[dict[str, Any]]:
    """Executa a consulta e retorna os nodes brutos dos repositórios."""
    query = load_sample_query()
    variables = {
        "first": first,
        "after": None,
        "queryString": DEFAULT_SEARCH_QUERY,
    }
    data = execute_graphql_query(query, variables)
    search_data = data.get("search")
    if not isinstance(search_data, dict):
        raise ValueError("Resposta GraphQL não contém o campo search esperado.")
    return search_data.get("nodes") or []


def validate_sample(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    """Normaliza e valida os campos de RQ05/RQ06 na amostra."""
    errors: list[str] = []
    normalized: list[dict[str, Any]] = []

    for index, repository in enumerate(repositories, start=1):
        name = repository.get("nameWithOwner", f"<repo {index}>")
        try:
            fields = normalize_repository_rq05_rq06(repository)
        except ValueError as error:
            errors.append(f"{name}: {error}")
            continue
        normalized.append({"name_with_owner": name, **fields})

    return {
        "is_valid": not errors,
        "errors": errors,
        "sample": normalized,
    }


def print_validation_summary(validation: dict[str, Any]) -> None:
    """Exibe um resumo legível da validação."""
    print(f"Repositórios validados: {len(validation['sample'])}")
    print(f"Validação básica: {'ok' if validation['is_valid'] else 'falhou'}")
    if validation["errors"]:
        print("Erros de validação:")
        for error in validation["errors"]:
            print(f"- {error}")
    print("\nAmostra:")
    for repository in validation["sample"]:
        ratio = repository["closed_issues_ratio"]
        ratio_display = f"{ratio:.2%}" if ratio is not None else "indefinida (0 issues)"
        print(
            "- "
            f"{repository['name_with_owner']} | "
            f"linguagem={repository['primary_language']} | "
            f"issues_total={repository['total_issues']} | "
            f"issues_fechadas={repository['closed_issues']} | "
            f"razao_fechadas={ratio_display}"
        )


def main() -> None:
    """Executa a coleta e validação da amostra de RQ05/RQ06."""
    parser = argparse.ArgumentParser(
        description="Valida RQ05 (linguagem) e RQ06 (% issues fechadas) numa amostra de repositórios."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Quantidade de repositórios na amostra (padrão: 10).",
    )
    args = parser.parse_args()

    try:
        repositories = fetch_sample_repositories(args.sample_size)
    except GitHubClientError as error:
        raise SystemExit(f"Coleta não executada: {error}")

    validation = validate_sample(repositories)
    print_validation_summary(validation)

    if not validation["is_valid"]:
        raise SystemExit("Validação interrompida: verifique os erros acima.")


if __name__ == "__main__":
    main()