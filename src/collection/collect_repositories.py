"""CLI para coleta dos repositorios populares do Lab01."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.github_client import GitHubClientError
from src.collection.collector import (
    CollectionConfig,
    RateLimitPaused,
    collect_popular_repositories,
)


def format_integer(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,}".replace(",", ".")


def format_percentage(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2%}".replace(".", ",")


def truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


def print_collection_summary(result: Any) -> None:
    validation = result.validation
    statistics = validation["statistics"]
    line = "-" * 118
    print()
    print("=" * 118)
    print("LAB01 - COLETA")
    print("=" * 118)
    print(f"Repositorios coletados : {statistics['collected_count']}")
    print(f"Repositorios unicos    : {statistics['unique_count']}")
    print(f"Duplicados             : {statistics['duplicate_count']}")
    print(f"Paginas consultadas    : {result.pages_collected}")
    print(f"Validacao              : {'OK' if validation['is_valid'] else 'FALHOU'}")
    print(f"CSV                    : {result.output_path}")
    print(f"Checkpoint             : {result.checkpoint_path}")
    print(f"Rate limit custo       : {result.last_rate_limit.get('cost', '-')}")
    print(f"Rate limit restante    : {result.last_rate_limit.get('remaining', '-')}")
    print(f"Rate limit reset       : {result.last_rate_limit.get('resetAt', '-')}")
    print(
        "Linguagem nao informada: "
        f"{statistics['primary_language_not_informed']}"
    )
    print(
        "RQ06 indefinida        : "
        f"{statistics['rq06_undefined_total_issues_zero']}"
    )
    print()
    print("RQ05 - TOP 15 LINGUAGENS")
    print(line)
    language_distribution = statistics.get("language_distribution") or {}
    print(f"Linguagens distintas   : {language_distribution.get('unique_languages', '-')}")
    for entry in language_distribution.get("top_languages", []):
        print(
            f"  {entry['language']:<20} {entry['count']:>5}  ({entry['percentage']:5.2f}%)"
        )
    print()
    print("RQ06 - DISTRIBUICAO DA RAZAO DE ISSUES FECHADAS")
    print(line)
    ratio_distribution = statistics.get("closed_issues_ratio_distribution") or {}
    if ratio_distribution.get("count_defined"):
        print(f"Repositorios com razao definida : {ratio_distribution['count_defined']}")
        print(f"Minimo                           : {ratio_distribution['min']:.2%}")
        print(f"Maximo                           : {ratio_distribution['max']:.2%}")
        print(f"Media                            : {ratio_distribution['mean']:.2%}")
        print(f"Mediana                          : {ratio_distribution['median']:.2%}")
        print(f"Q1 / Q3                          : {ratio_distribution['q1']:.2%} / {ratio_distribution['q3']:.2%}")
        print(
            "Outliers (regra IQR)             : "
            f"{ratio_distribution['outlier_count']} ({ratio_distribution['outlier_pct']:.2f}%)"
        )
    else:
        print("Nenhum valor definido de razao de issues fechadas encontrado.")
    if validation["errors"]:
        print()
        print("ERROS DE VALIDACAO")
        print(line)
        for error in validation["errors"]:
            print(f"- {error}")
    print()
    print("AMOSTRA TOP 10")
    print(line)
    print(
        f"{'#':<4}"
        f"{'Repo':<34}"
        f"{'Stars':>10}"
        f"{'RQ01':>8}"
        f"{'RQ02':>10}"
        f"{'RQ03':>8}"
        f"{'RQ04':>8}"
        f"{'RQ05':<18}"
        f"{'RQ06':>9}"
    )
    print(line)
    for position, repository in enumerate(validation["sample"], start=1):
        print(
            f"{position:<4}"
            f"{truncate_text(repository['name_with_owner'], 32):<34}"
            f"{format_integer(repository['stargazer_count']):>10}"
            f"{format_integer(repository['repository_age_days']):>8}"
        f"{format_integer(repository['merged_pull_requests']):>10}"
        f"{format_integer(repository['release_count']):>8}"
        f"{format_integer(repository['days_since_last_update']):>8}"
        f"  {truncate_text(repository['primary_language'], 16):<16}"
        f"{format_percentage(repository['closed_issues_ratio']):>9}"
        )
    print(line)
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Coleta repositorios populares para RQ01-RQ06."
    )
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "repositories_s02.csv",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=PROJECT_ROOT
        / "data"
        / "raw"
        / "repositories_s02.checkpoint.json",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--rate-limit-threshold", type=int, default=100)
    parser.add_argument("--rate-limit-wait-seconds", type=int, default=0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = CollectionConfig(
        limit=args.limit,
        page_size=args.page_size,
        output_path=args.output,
        checkpoint_path=args.checkpoint,
        resume=args.resume,
        overwrite=args.overwrite,
        rate_limit_threshold=args.rate_limit_threshold,
        max_rate_limit_wait_seconds=args.rate_limit_wait_seconds,
    )
    try:
        result = collect_popular_repositories(config)
    except FileExistsError as error:
        raise SystemExit(f"Coleta nao executada: {error}") from error
    except RateLimitPaused as error:
        raise SystemExit(f"Coleta pausada: {error}") from error
    except GitHubClientError as error:
        raise SystemExit(f"Coleta nao executada: {error}") from error
    except ValueError as error:
        raise SystemExit(f"Erro ao processar os dados: {error}") from error
    print_collection_summary(result)
    if not result.validation["is_valid"]:
        raise SystemExit(
            "Coleta interrompida: os dados retornados nao passaram na validacao."
        )


if __name__ == "__main__":
    main()