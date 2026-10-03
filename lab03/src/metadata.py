"""Metadados de candidatos, sem releases nem coleta de workflow runs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .github_client import Client, header, parse_links


class MetadataError(ValueError):
    """Campos obrigatórios ausentes ou inconsistentes na resposta."""


def parse_timestamp(value: str) -> datetime:
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise MetadataError("Timestamp sem fuso horário.")
    return instant.astimezone(timezone.utc)


def parse_metadata(repository: dict[str, Any], collected_at: str) -> dict[str, Any]:
    try:
        owner, name = repository["owner"]["login"], repository["name"]
        full_name, url = repository["full_name"], repository["html_url"]
        created_at, branch = repository["created_at"], repository["default_branch"]
        stars = repository["stargazers_count"]
        if not all(isinstance(value, str) and value.strip() for value in (owner, name, full_name, url, created_at)):
            raise MetadataError("Identidade, URL ou created_at inválidos.")
        if "/" in owner or "/" in name or full_name != f"{owner}/{name}":
            raise MetadataError("full_name não corresponde a owner/name.")
        if url != f"https://github.com/{full_name}":
            raise MetadataError("html_url não corresponde ao repositório.")
        if type(stars) is not int or stars < 0:
            raise MetadataError("stargazers_count inválido.")
        if not isinstance(branch, str):
            raise MetadataError("default_branch ausente ou inválido.")
        language = repository.get("language")
        if language is not None and not isinstance(language, str):
            raise MetadataError("language inválida.")
        age = (parse_timestamp(collected_at) - parse_timestamp(created_at)).days
        if age < 0:
            raise MetadataError("created_at posterior à coleta.")
    except MetadataError:
        raise
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise MetadataError("Metadados obrigatórios ausentes ou inconsistentes.") from error
    return {"repository_id": repository.get("id"), "owner": owner, "name": name,
            "full_name": full_name, "html_url": url, "stargazers_count": stars,
            "language": language, "created_at": created_at, "repo_age_days": age,
            "default_branch": branch, "collected_at": collected_at}


def count_contributors(client: Client, full_name: str) -> int:
    response = client.get(f"/repos/{full_name}/contributors", {"per_page": 1, "anon": "true"})
    if response.status == 204:
        return 0
    if not isinstance(response.data, list) or len(response.data) > 1:
        raise MetadataError("Resposta inesperada na contagem de contribuidores.")
    if not response.data:
        return 0
    links = parse_links(header(response.headers, "Link"))
    if "last" in links:
        try:
            count = int(parse_qs(urlsplit(links["last"]).query)["page"][0])
            if count < 1:
                raise ValueError
            return count
        except (KeyError, ValueError, IndexError) as error:
            raise MetadataError("Link last sem número de página válido.") from error
    if "next" in links:
        # Não representar uma contagem desconhecida como 1 nem baixar tudo.
        raise MetadataError("Contagem desconhecida: Link next presente sem last.")
    return len(response.data)


def check_actions(client: Client, full_name: str) -> bool:
    response = client.get(f"/repos/{full_name}/actions/workflows", {"per_page": 1})
    if not isinstance(response.data, dict):
        raise MetadataError("Resposta de workflows não é um objeto.")
    count = response.data.get("total_count")
    if type(count) is not int or count < 0:
        raise MetadataError("Workflows sem total_count válido.")
    return count > 0
