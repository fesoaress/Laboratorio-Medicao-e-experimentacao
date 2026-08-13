"""Orquestração da coleta dos repositórios populares."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

QUERY_PATH = (
    PROJECT_ROOT
    / "src"
    / "api"
    / "queries"
    / "repositories.graphql"
)

DEFAULT_SEARCH_QUERY = "stars:>0 sort:stars-desc"

# Sprint 1: coletar 100 repositórios.
SPRINT_1_REPOSITORY_LIMIT = 100

# Número de repositórios buscados em cada requisição GraphQL.
# 10 páginas x 10 repositórios = 100 repositórios.
PAGE_SIZE = 10

# Quantos repositórios serão exibidos na amostra de validação.
VALIDATION_SAMPLE_SIZE = 10

# Retry para erros temporários do GitHub, como HTTP 502/504.
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# IMPORTAÇÕES DO PROJETO
# =============================================================================

from src.api.github_client import (
    GitHubClientError,
    execute_graphql_query,
)

from src.metrics.rq01_rq02 import (
    calculate_repository_age_days,
    normalize_merged_pull_requests,
)

from src.metrics.rq03_rq04 import (
    calculate_days_since_last_update,
    normalize_release_count,
)

from src.metrics.rq05_rq06 import (
    normalize_repository_rq05_rq06,
)


# =============================================================================
# QUERY / API
# =============================================================================


def load_repositories_query() -> str:
    """Carrega a query GraphQL usada na coleta de repositórios."""

    return QUERY_PATH.read_text(
        encoding="utf-8",
    )


def fetch_popular_repositories(
    first: int,
    after: str | None = None,
) -> dict[str, Any]:
    """
    Executa uma página da consulta dos repositórios mais populares.

    Em caso de erro temporário 502/504, tenta novamente automaticamente.
    """

    query = load_repositories_query()

    variables = {
        "first": first,
        "after": after,
        "queryString": DEFAULT_SEARCH_QUERY,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = execute_graphql_query(
                query,
                variables,
            )

            search_data = data.get("search")

            if not isinstance(search_data, dict):
                raise ValueError(
                    "Resposta GraphQL não contém "
                    "o campo search esperado."
                )

            return search_data

        except GitHubClientError as error:
            error_message = str(error)

            is_temporary_error = (
                "502" in error_message
                or "504" in error_message
            )

            if (
                not is_temporary_error
                or attempt == MAX_RETRIES
            ):
                raise

            wait_seconds = (
                RETRY_DELAY_SECONDS * attempt
            )

            print(
                f"GitHub retornou erro temporário. "
                f"Nova tentativa em {wait_seconds}s "
                f"({attempt}/{MAX_RETRIES})..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        "Não foi possível concluir a consulta."
    )


# =============================================================================
# NORMALIZAÇÃO / MÉTRICAS
# =============================================================================


def normalize_repository(
    repository: dict[str, Any],
) -> dict[str, Any]:
    """
    Normaliza um repositório e calcula as métricas
    necessárias para RQ01–RQ06.
    """

    # -------------------------------------------------------------------------
    # RQ01
    # Sistemas populares são maduros/antigos?
    #
    # Campo da API:
    # createdAt
    #
    # Métrica:
    # idade do repositório em dias.
    # -------------------------------------------------------------------------

    created_at = repository.get(
        "createdAt"
    )

    repository_age_days = (
        calculate_repository_age_days(
            created_at
        )
    )

    # -------------------------------------------------------------------------
    # RQ02
    # Sistemas populares recebem muita contribuição?
    #
    # Campo:
    # pullRequests(states: MERGED)
    #
    # Métrica:
    # total de PRs aceitas/merged.
    # -------------------------------------------------------------------------

    pull_requests = (
        repository.get("pullRequests")
        or {}
    )

    merged_pull_requests = (
        normalize_merged_pull_requests(
            pull_requests.get("totalCount")
        )
    )

    # -------------------------------------------------------------------------
    # RQ03
    # Sistemas populares lançam releases frequentemente?
    #
    # Campo:
    # releases.totalCount
    #
    # Métrica:
    # total de releases.
    # -------------------------------------------------------------------------

    releases = (
        repository.get("releases")
        or {}
    )

    release_count = (
        normalize_release_count(
            releases.get("totalCount")
        )
    )

    # -------------------------------------------------------------------------
    # RQ04
    # Sistemas populares são atualizados frequentemente?
    #
    # Campo:
    # pushedAt
    #
    # Métrica:
    # dias desde o último push.
    # -------------------------------------------------------------------------

    pushed_at = repository.get(
        "pushedAt"
    )

    days_since_last_update = (
        calculate_days_since_last_update(
            pushed_at
        )
    )

    # -------------------------------------------------------------------------
    # RQ05 / RQ06
    #
    # RQ05:
    # linguagem primária.
    #
    # RQ06:
    # percentual de issues fechadas.
    # -------------------------------------------------------------------------

    rq05_rq06_fields = (
        normalize_repository_rq05_rq06(
            repository
        )
    )

    # -------------------------------------------------------------------------
    # REGISTRO PADRONIZADO
    # -------------------------------------------------------------------------

    return {
        "name_with_owner": (
            repository.get(
                "nameWithOwner"
            )
        ),

        "stargazer_count": int(
            repository.get(
                "stargazerCount"
            )
            or 0
        ),

        # RQ01
        "created_at": created_at,
        "repository_age_days": (
            repository_age_days
        ),

        # RQ02
        "merged_pull_requests": (
            merged_pull_requests
        ),

        # RQ03
        "release_count": (
            release_count
        ),

        # RQ04
        "pushed_at": pushed_at,
        "days_since_last_update": (
            days_since_last_update
        ),

        # RQ05 / RQ06
        **rq05_rq06_fields,
    }


# =============================================================================
# COLETA
# =============================================================================


def collect_repositories(
    limit: int = SPRINT_1_REPOSITORY_LIMIT,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
]:
    """
    Coleta os repositórios populares usando paginação automática.

    Para a Sprint 1:

        página 1  -> 1–10
        página 2  -> 11–20
        ...
        página 10 -> 91–100

    O usuário executa somente um comando.
    """

    repositories: list[
        dict[str, Any]
    ] = []

    after: str | None = None

    last_page_info: dict[
        str,
        Any,
    ] = {}

    pages_collected = 0

    while len(repositories) < limit:

        remaining = (
            limit
            - len(repositories)
        )

        current_page_size = min(
            PAGE_SIZE,
            remaining,
        )

        search_data = (
            fetch_popular_repositories(
                first=current_page_size,
                after=after,
            )
        )

        pages_collected += 1

        nodes = (
            search_data.get("nodes")
            or []
        )

        page_repositories = [
            normalize_repository(node)
            for node in nodes
            if (
                isinstance(node, dict)
                and node.get(
                    "nameWithOwner"
                )
            )
        ]

        repositories.extend(
            page_repositories
        )

        last_page_info = (
            search_data.get(
                "pageInfo"
            )
            or {}
        )

        # Já atingimos a quantidade desejada.
        if len(repositories) >= limit:
            break

        # GitHub informou que não existem
        # mais páginas.
        if not last_page_info.get(
            "hasNextPage"
        ):
            break

        # Cursor usado para iniciar
        # a próxima página.
        after = last_page_info.get(
            "endCursor"
        )

        if not after:
            break

    # Metadado interno apenas para
    # exibição do resumo.
    last_page_info[
        "pagesCollected"
    ] = pages_collected

    return (
        repositories[:limit],
        last_page_info,
    )


# =============================================================================
# VALIDAÇÃO
# =============================================================================


def validate_collection(
    repositories: list[
        dict[str, Any]
    ],
    *,
    expected_count: int = (
        SPRINT_1_REPOSITORY_LIMIT
    ),
    sample_size: int = (
        VALIDATION_SAMPLE_SIZE
    ),
) -> dict[str, Any]:
    """
    Valida condições básicas dos 100 repositórios
    e prepara uma amostra de 10 para inspeção.
    """

    errors: list[str] = []

    # -------------------------------------------------------------------------
    # QUANTIDADE
    # -------------------------------------------------------------------------

    if len(repositories) != expected_count:
        errors.append(
            "Quantidade coletada esperada: "
            f"{expected_count}; "
            f"obtida: {len(repositories)}."
        )

    # -------------------------------------------------------------------------
    # CAMPOS / MÉTRICAS
    # -------------------------------------------------------------------------

    for index, repository in enumerate(
        repositories,
        start=1,
    ):

        if not repository.get(
            "name_with_owner"
        ):
            errors.append(
                f"Repositório {index}: "
                "nome ausente."
            )

        if not repository.get(
            "created_at"
        ):
            errors.append(
                f"Repositório {index}: "
                "createdAt ausente."
            )

        if (
            repository.get(
                "stargazer_count",
                -1,
            )
            < 0
        ):
            errors.append(
                f"Repositório {index}: "
                "estrelas negativas."
            )

        # RQ01
        if (
            repository.get(
                "repository_age_days",
                -1,
            )
            < 0
        ):
            errors.append(
                f"Repositório {index}: "
                "idade negativa."
            )

        # RQ02
        if (
            repository.get(
                "merged_pull_requests",
                -1,
            )
            < 0
        ):
            errors.append(
                f"Repositório {index}: "
                "pull requests aceitas negativas."
            )

        # RQ03
        if (
            repository.get(
                "release_count",
                -1,
            )
            < 0
        ):
            errors.append(
                f"Repositório {index}: "
                "total de releases negativo."
            )

        # RQ04
        if not repository.get(
            "pushed_at"
        ):
            errors.append(
                f"Repositório {index}: "
                "pushedAt ausente."
            )

        if (
            repository.get(
                "days_since_last_update",
                -1,
            )
            < 0
        ):
            errors.append(
                f"Repositório {index}: "
                "dias desde última "
                "atualização negativos."
            )

        # RQ05
        if not repository.get(
            "primary_language"
        ):
            errors.append(
                f"Repositório {index}: "
                "linguagem primária inválida."
            )

        # RQ06
        if (
            repository.get(
                "total_issues",
                -1,
            )
            < 0
        ):
            errors.append(
                f"Repositório {index}: "
                "total de issues negativo."
            )

        if (
            repository.get(
                "closed_issues",
                -1,
            )
            < 0
        ):
            errors.append(
                f"Repositório {index}: "
                "issues fechadas negativas."
            )

        if (
            repository.get(
                "closed_issues",
                0,
            )
            >
            repository.get(
                "total_issues",
                0,
            )
        ):
            errors.append(
                f"Repositório {index}: "
                "issues fechadas maior "
                "que o total de issues."
            )

        ratio = repository.get(
            "closed_issues_ratio"
        )

        if (
            ratio is not None
            and not 0 <= ratio <= 1
        ):
            errors.append(
                f"Repositório {index}: "
                "percentual de issues "
                "fechadas inválido."
            )

    # -------------------------------------------------------------------------
    # ORDENAÇÃO POR ESTRELAS
    # -------------------------------------------------------------------------

    for previous, current in zip(
        repositories,
        repositories[1:],
    ):
        if (
            previous[
                "stargazer_count"
            ]
            <
            current[
                "stargazer_count"
            ]
        ):
            errors.append(
                "Ordenação por estrelas "
                "não está em ordem decrescente."
            )
            break

    # -------------------------------------------------------------------------
    # AMOSTRA TOP 10
    # -------------------------------------------------------------------------

    ordered_repositories = sorted(
        repositories,
        key=lambda repository: (
            repository.get(
                "stargazer_count",
                0,
            )
        ),
        reverse=True,
    )

    sample = [
        {
            "name_with_owner": (
                repository[
                    "name_with_owner"
                ]
            ),

            "stargazer_count": (
                repository[
                    "stargazer_count"
                ]
            ),

            # RQ01
            "repository_age_days": (
                repository[
                    "repository_age_days"
                ]
            ),

            # RQ02
            "merged_pull_requests": (
                repository[
                    "merged_pull_requests"
                ]
            ),

            # RQ03
            "release_count": (
                repository[
                    "release_count"
                ]
            ),

            # RQ04
            "days_since_last_update": (
                repository[
                    "days_since_last_update"
                ]
            ),

            # RQ05
            "primary_language": (
                repository[
                    "primary_language"
                ]
            ),

            # RQ06
            "closed_issues_ratio": (
                repository[
                    "closed_issues_ratio"
                ]
            ),
        }

        for repository
        in ordered_repositories[
            :sample_size
        ]
    ]

    return {
        "is_valid": not errors,
        "errors": errors,
        "sample": sample,
    }


# =============================================================================
# FORMATAÇÃO DA SAÍDA
# =============================================================================


def format_integer(
    value: int | None,
) -> str:
    """Formata inteiro com separador de milhar."""

    if value is None:
        return "-"

    return (
        f"{value:,}"
        .replace(",", ".")
    )


def format_percentage(
    value: float | None,
) -> str:
    """
    Formata uma razão entre 0 e 1 como porcentagem.

    None representa repositórios sem issues.
    """

    if value is None:
        return "N/A"

    return (
        f"{value:.2%}"
        .replace(".", ",")
    )


def truncate_text(
    value: str,
    max_length: int,
) -> str:
    """Evita que textos longos destruam a tabela."""

    if len(value) <= max_length:
        return value

    return (
        value[: max_length - 3]
        + "..."
    )


def print_collection_summary(
    repositories: list[
        dict[str, Any]
    ],
    page_info: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    """
    Exibe um resumo organizado da coleta
    e uma amostra das métricas RQ01–RQ06.
    """

    separator = "=" * 130
    line = "-" * 130

    # -------------------------------------------------------------------------
    # RESUMO
    # -------------------------------------------------------------------------

    print()
    print(separator)

    print(
        "LAB01 - COLETA DE REPOSITÓRIOS POPULARES"
        .center(130)
    )

    print(separator)

    print(
        f"Repositórios coletados : "
        f"{len(repositories)}"
    )

    print(
        f"Páginas consultadas     : "
        f"{page_info.get('pagesCollected', '-')}"
    )

    print(
        f"Tamanho por página      : "
        f"{PAGE_SIZE}"
    )

    print(
        "Validação              : "
        f"{'OK' if validation['is_valid'] else 'FALHOU'}"
    )

    print(
        "Próxima página         : "
        f"{'Sim' if page_info.get('hasNextPage') else 'Não'}"
    )

    print(
        "Cursor final           : "
        f"{page_info.get('endCursor') or '-'}"
    )

    # -------------------------------------------------------------------------
    # ERROS
    # -------------------------------------------------------------------------

    if validation["errors"]:

        print()
        print("ERROS DE VALIDAÇÃO")
        print(line)

        for error in validation[
            "errors"
        ]:
            print(
                f"- {error}"
            )

    # -------------------------------------------------------------------------
    # AMOSTRA
    # -------------------------------------------------------------------------

    print()
    print(
        "AMOSTRA DE VALIDAÇÃO - TOP 10 POR ESTRELAS"
    )

    print(line)

    header = (
        f"{'#':<4}"
        f"{'Repositório':<35}"
        f"{'Estrelas':>11}"
        f"{'RQ01(d)':>10}"
        f"{'RQ02 PRs':>11}"
        f"{'RQ03 Rel.':>11}"
        f"{'RQ04(d)':>10}"
        f"{'RQ05 Linguagem':<18}"
        f"{'RQ06':>10}"
    )

    print(header)
    print(line)

    for position, repository in enumerate(
        validation["sample"],
        start=1,
    ):

        name = truncate_text(
            repository[
                "name_with_owner"
            ],
            33,
        )

        language = truncate_text(
            repository[
                "primary_language"
            ],
            16,
        )

        stars = format_integer(
            repository[
                "stargazer_count"
            ]
        )

        age = format_integer(
            repository[
                "repository_age_days"
            ]
        )

        pull_requests = format_integer(
            repository[
                "merged_pull_requests"
            ]
        )

        releases = format_integer(
            repository[
                "release_count"
            ]
        )

        update_days = format_integer(
            repository[
                "days_since_last_update"
            ]
        )

        issues_ratio = format_percentage(
            repository[
                "closed_issues_ratio"
            ]
        )

        print(
            f"{position:<4}"
            f"{name:<35}"
            f"{stars:>11}"
            f"{age:>10}"
            f"{pull_requests:>11}"
            f"{releases:>11}"
            f"{update_days:>10}"
            f"{language:<18}"
            f"{issues_ratio:>10}"
        )

    print(line)

    # -------------------------------------------------------------------------
    # LEGENDA
    # -------------------------------------------------------------------------

    print()
    print("LEGENDA DAS QUESTÕES DE PESQUISA")

    print(
        "RQ01(d)        = "
        "idade do repositório em dias"
    )

    print(
        "RQ02 PRs       = "
        "total de pull requests com status MERGED"
    )

    print(
        "RQ03 Rel.      = "
        "total de releases"
    )

    print(
        "RQ04(d)        = "
        "dias desde o último push"
    )

    print(
        "RQ05 Linguagem = "
        "linguagem primária do repositório"
    )

    print(
        "RQ06           = "
        "percentual de issues fechadas"
    )

    print(
        "N/A na RQ06    = "
        "repositório sem issues; "
        "razão não é definida"
    )

    print(separator)
    print()


# =============================================================================
# PERSISTÊNCIA OPCIONAL
# =============================================================================


def save_raw_output(
    repositories: list[
        dict[str, Any]
    ],
    output_path: Path,
) -> None:
    """
    Salva a coleta normalizada em JSON,
    sem sobrescrever arquivos existentes.
    """

    if output_path.exists():
        raise FileExistsError(
            "O arquivo de saída já existe: "
            f"{output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            repositories,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# =============================================================================
# EXECUÇÃO
# =============================================================================


def main() -> None:
    """Executa a coleta e a validação da Sprint 1."""

    parser = argparse.ArgumentParser(
        description=(
            "Coleta os 100 repositórios "
            "populares para RQ01–RQ06."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Caminho opcional para salvar "
            "a coleta normalizada em JSON."
        ),
    )

    args = parser.parse_args()

    try:
        repositories, page_info = (
            collect_repositories()
        )

    except GitHubClientError as error:
        raise SystemExit(
            "Coleta não executada: "
            f"{error}"
        )

    except ValueError as error:
        raise SystemExit(
            "Erro ao processar os dados: "
            f"{error}"
        )

    validation = (
        validate_collection(
            repositories
        )
    )

    print_collection_summary(
        repositories,
        page_info,
        validation,
    )

    if not validation[
        "is_valid"
    ]:
        raise SystemExit(
            "Coleta interrompida: "
            "os dados retornados não "
            "passaram na validação."
        )

    if args.output:

        save_raw_output(
            repositories,
            args.output,
        )

        print(
            "Coleta salva em: "
            f"{args.output}"
        )


if __name__ == "__main__":
    main()