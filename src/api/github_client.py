"""Comunicação HTTP com a API GraphQL do GitHub."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
TOKEN_ENV_VAR = "GITHUB_TOKEN"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GitHubClientError(RuntimeError):
    """Erro ao comunicar com a API do GitHub."""


class GitHubGraphQLError(GitHubClientError):
    """Erro retornado pela execução da query GraphQL."""


def load_github_token() -> str:
    """Obtém o token do GitHub após carregar o arquivo .env local."""
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError as error:
        raise GitHubClientError(
            "Dependência python-dotenv não instalada. Execute pip install -r requirements.txt."
        ) from error

    load_dotenv(PROJECT_ROOT / ".env")
    token = (os.getenv(TOKEN_ENV_VAR) or "").strip()
    if not token:
        raise GitHubClientError(
            "Erro: GITHUB_TOKEN não configurado. Defina o token no arquivo .env."
        )
    return token


def execute_graphql_query(
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    token: str | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Envia uma query GraphQL ao GitHub e retorna o campo data da resposta."""
    github_token = token or load_github_token()
    payload = json.dumps(
        {
            "query": query,
            "variables": variables or {},
        }
    ).encode("utf-8")

    request = Request(
        GITHUB_GRAPHQL_ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "lab01-medicao-experimentacao",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise GitHubClientError(f"Erro HTTP {error.code} ao consultar o GitHub: {detail}") from error
    except URLError as error:
        raise GitHubClientError(f"Erro de conexão ao consultar o GitHub: {error.reason}") from error

    try:
        decoded_response = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise GitHubClientError("A API do GitHub retornou uma resposta JSON inválida.") from error

    if decoded_response.get("errors"):
        raise GitHubGraphQLError("A consulta GraphQL falhou. Verifique os erros retornados pela API.")

    data = decoded_response.get("data")
    if not isinstance(data, dict):
        raise GitHubClientError("A resposta da API do GitHub não contém um campo data válido.")

    return data
