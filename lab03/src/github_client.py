"""Cliente REST mínimo, substituível pela futura camada da issue #44."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Iterator, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"


class APIError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


class RateLimitError(APIError):
    """Interrompe a coleta sem implementar retry/backoff ou cache."""


@dataclass(frozen=True)
class APIResponse:
    data: Any
    headers: Mapping[str, str]
    status: int = 200


class Client(Protocol):
    def get(self, path: str, params: Mapping[str, Any] | None = None) -> APIResponse: ...


def header(headers: Mapping[str, str], name: str) -> str:
    return next((v for k, v in headers.items() if k.lower() == name.lower()), "")


def parse_links(value: str) -> dict[str, str]:
    """Extrai relações RFC Link, sem depender de ordem ou capitalização."""
    links = {}
    for target, attributes in re.findall(r"<([^>]+)>([^,]*)", value):
        match = re.search(r'\brel\s*=\s*(?:"([^"]+)"|([^;\s]+))', attributes, re.I)
        if match:
            for relation in (match.group(1) or match.group(2)).split():
                links[relation.lower()] = target
    return links


class GitHubClient:
    def __init__(self, *, timeout: float = 30):
        self.timeout = timeout

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> APIResponse:
        url = path if path.startswith("https://") else API_ROOT + path
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise APIError("Endpoint fora de https://api.github.com.")
        if params:
            url += ("&" if parsed.query else "?") + urlencode(params)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "lab03-s01-repository-selection",
        }
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
                body = response.read()
                data = json.loads(body) if body else None
                return APIResponse(data, dict(response.headers), response.status)
        except HTTPError as error:
            remaining = error.headers.get("X-RateLimit-Remaining", "unknown")
            reset = error.headers.get("X-RateLimit-Reset", "unknown")
            retry_after = error.headers.get("Retry-After", "unknown")
            # Alguns limites secundários só são identificados na mensagem.
            # Examina o corpo sem jamais persisti-lo ou imprimi-lo.
            detail = error.read(4096).decode("utf-8", errors="replace").lower()
            error.close()
            if error.code == 429 or (error.code == 403 and (
                remaining == "0" or retry_after != "unknown" or "rate limit" in detail
            )):
                raise RateLimitError(
                    f"Rate limit: remaining={remaining}, reset={reset}, retry_after={retry_after}.",
                    status=error.code,
                ) from error
            # Não inclui corpo, request ou token na mensagem persistida.
            raise APIError(f"GitHub retornou HTTP {error.code} ({parsed.path}).", status=error.code) from error
        except (URLError, TimeoutError, OSError) as error:
            raise APIError(f"Falha de conexão com GitHub ({parsed.path}).") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise APIError(f"Resposta JSON inválida ({parsed.path}).") from error


def iter_pages(
    client: Client, path: str, params: Mapping[str, Any] | None = None,
    *, max_pages: int | None = None,
) -> Iterator[APIResponse]:
    """Segue rel=next, limitando buscas e detectando ciclos no servidor."""
    seen: set[str] = set()
    page = 0
    while path and (max_pages is None or page < max_pages):
        if path in seen:
            raise APIError("Paginação circular retornada pela API.")
        seen.add(path)
        response = client.get(path, params)
        yield response
        page += 1
        path = parse_links(header(response.headers, "Link")).get("next", "")
        params = None
