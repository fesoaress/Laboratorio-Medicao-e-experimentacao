"""Coleta do estado do GitHub Projects para geração dos snapshots."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUERIES_DIR = PROJECT_ROOT / "src" / "api" / "queries"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "snapshots"
ITEMS_PAGE_SIZE = 100
STATUS_FIELD_NAME = "Status"
OWNER_TYPE_ORGANIZATION = "organization"
OWNER_TYPE_USER = "user"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.github_client import GitHubClientError, execute_graphql_query, load_github_token


class ProjectSnapshotError(RuntimeError):
    """Erro ao coletar snapshot do GitHub Projects."""


def _load_dotenv() -> None:
    """Garante que variáveis do .env local estejam disponíveis."""
    load_github_token()


def load_project_config() -> dict[str, str | int]:
    """Carrega owner, número e tipo do projeto a partir do .env."""
    _load_dotenv()

    owner = (os.getenv("GITHUB_PROJECT_OWNER") or "").strip()
    number_raw = (os.getenv("GITHUB_PROJECT_NUMBER") or "").strip()
    owner_type = (os.getenv("GITHUB_PROJECT_OWNER_TYPE") or OWNER_TYPE_ORGANIZATION).strip().lower()

    if not owner:
        raise ProjectSnapshotError(
            "GITHUB_PROJECT_OWNER não configurado. Defina o login da organização ou usuário no .env."
        )
    if not number_raw:
        raise ProjectSnapshotError(
            "GITHUB_PROJECT_NUMBER não configurado. Use o número visível na URL do projeto."
        )
    if owner_type not in {OWNER_TYPE_ORGANIZATION, OWNER_TYPE_USER}:
        raise ProjectSnapshotError(
            "GITHUB_PROJECT_OWNER_TYPE inválido. Use 'organization' ou 'user'."
        )

    try:
        project_number = int(number_raw)
    except ValueError as error:
        raise ProjectSnapshotError("GITHUB_PROJECT_NUMBER deve ser um número inteiro.") from error

    if project_number <= 0:
        raise ProjectSnapshotError("GITHUB_PROJECT_NUMBER deve ser maior que zero.")

    return {
        "owner": owner,
        "project_number": project_number,
        "owner_type": owner_type,
    }


def load_project_snapshot_query(owner_type: str) -> str:
    """Carrega a query GraphQL conforme o tipo de owner."""
    if owner_type == OWNER_TYPE_USER:
        query_path = QUERIES_DIR / "project_snapshot_user.graphql"
    else:
        query_path = QUERIES_DIR / "project_snapshot_organization.graphql"
    return query_path.read_text(encoding="utf-8")


def _extract_project_container(data: dict[str, Any], owner_type: str) -> dict[str, Any]:
    """Obtém o container organization/user e valida existência."""
    container_key = "organization" if owner_type == OWNER_TYPE_ORGANIZATION else "user"
    container = data.get(container_key)
    if not isinstance(container, dict):
        raise ProjectSnapshotError(f"Owner '{container_key}' não encontrado ou sem acesso.")
    return container


def fetch_project_page(
    *,
    owner: str,
    project_number: int,
    owner_type: str,
    after: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Busca uma página de items do GitHub Projects."""
    query = load_project_snapshot_query(owner_type)
    variables = {
        "owner": owner,
        "number": project_number,
        "first": ITEMS_PAGE_SIZE,
        "after": after,
    }
    data = execute_graphql_query(query, variables)
    container = _extract_project_container(data, owner_type)
    project = container.get("projectV2")
    if not isinstance(project, dict):
        raise ProjectSnapshotError(
            f"Projeto número {project_number} não encontrado para o owner informado."
        )
    items = project.get("items") or {}
    return project, items


def normalize_project_item(item: dict[str, Any]) -> dict[str, str | int | None]:
    """Normaliza um item do board para exportação."""
    content = item.get("content") or {}
    content_type = content.get("__typename") or item.get("type") or "UNKNOWN"

    status_field = item.get("fieldValueByName") or {}
    status = status_field.get("name") if isinstance(status_field, dict) else None

    number: int | None = content.get("number")
    title = content.get("title") or ""
    state = content.get("state")
    url = content.get("url")

    if content_type == "DraftIssue":
        number = None
        state = "DRAFT"
        url = None

    return {
        "item_type": str(content_type),
        "number": number,
        "title": title,
        "state": state,
        "status": status,
        "url": url,
    }


def fetch_all_project_items(config: dict[str, str | int]) -> tuple[dict[str, Any], list[dict[str, str | int | None]]]:
    """Coleta todos os items do projeto, paginando quando necessário."""
    owner = str(config["owner"])
    project_number = int(config["project_number"])
    owner_type = str(config["owner_type"])

    cursor: str | None = None
    project_meta: dict[str, Any] | None = None
    normalized_items: list[dict[str, str | int | None]] = []

    while True:
        project, items_data = fetch_project_page(
            owner=owner,
            project_number=project_number,
            owner_type=owner_type,
            after=cursor,
        )
        if project_meta is None:
            project_meta = {
                "id": project.get("id"),
                "title": project.get("title"),
                "url": project.get("url"),
            }

        nodes = items_data.get("nodes") or []
        for node in nodes:
            if isinstance(node, dict):
                normalized_items.append(normalize_project_item(node))

        page_info = items_data.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break

    if project_meta is None:
        raise ProjectSnapshotError("Nenhum dado do projeto foi retornado pela API.")

    return project_meta, normalized_items


def validate_snapshot(items: list[dict[str, str | int | None]]) -> dict[str, Any]:
    """Valida o snapshot coletado e prepara um resumo."""
    errors: list[str] = []
    status_counts: dict[str, int] = {}

    for index, item in enumerate(items, start=1):
        if not item.get("title"):
            errors.append(f"Item {index}: título ausente.")
        status = item.get("status")
        if not status:
            errors.append(f"Item {index}: status ausente.")
        else:
            status_counts[str(status)] = status_counts.get(str(status), 0) + 1

    return {
        "is_valid": not errors,
        "errors": errors,
        "total_items": len(items),
        "status_counts": status_counts,
    }


def print_snapshot_summary(
    project_meta: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    """Exibe um resumo legível do snapshot."""
    print(f"Projeto: {project_meta.get('title')}")
    print(f"URL: {project_meta.get('url')}")
    print(f"Items coletados: {validation['total_items']}")
    print(f"Validação básica: {'ok' if validation['is_valid'] else 'falhou'}")

    if validation["errors"]:
        print("Erros de validação:")
        for error in validation["errors"]:
            print(f"- {error}")

    print("\nContagem por status:")
    for status, count in sorted(validation["status_counts"].items()):
        print(f"- {status}: {count}")


def default_output_path() -> Path:
    """Gera caminho padrão com timestamp UTC para o CSV."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_OUTPUT_DIR / f"s01_project_snapshot_{timestamp}.csv"


def export_snapshot_csv(items: list[dict[str, str | int | None]], output_path: Path) -> None:
    """Exporta o snapshot normalizado para CSV."""
    if output_path.exists():
        raise FileExistsError(f"O arquivo de saída já existe: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["item_type", "number", "title", "state", "status", "url"]

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def collect_project_snapshot() -> tuple[dict[str, Any], list[dict[str, str | int | None]], dict[str, Any]]:
    """Executa coleta completa e validação do snapshot."""
    config = load_project_config()
    project_meta, items = fetch_all_project_items(config)
    validation = validate_snapshot(items)
    return project_meta, items, validation


def main() -> None:
    """Executa a coleta do snapshot e exporta CSV."""
    parser = argparse.ArgumentParser(description="Exporta snapshot do GitHub Projects para CSV.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Caminho opcional para salvar o CSV do snapshot.",
    )
    args = parser.parse_args()

    try:
        project_meta, items, validation = collect_project_snapshot()
    except (GitHubClientError, ProjectSnapshotError) as error:
        raise SystemExit(f"Snapshot não executado: {error}")

    print_snapshot_summary(project_meta, validation)

    if not validation["is_valid"]:
        raise SystemExit("Snapshot interrompido: os dados retornados não passaram na validação.")

    output_path = args.output or default_output_path()
    export_snapshot_csv(items, output_path)
    print(f"\nSnapshot salvo em: {output_path}")


if __name__ == "__main__":
    main()
