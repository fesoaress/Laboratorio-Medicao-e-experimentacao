"""Cache local, retomada e tratamento de rate limit/erros temporários (#44)."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .github_client import APIError, APIResponse, Client, RateLimitError

RETRYABLE_STATUS = range(500, 600)


def cache_key(path: str, params: Mapping[str, Any] | None) -> str:
    """Nome de arquivo determinístico para (path, params), independente da ordem das chaves."""
    payload = json.dumps({"path": path, "params": dict(params or {})}, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{digest}.json"


class CacheStore:
    """Um arquivo JSON por chamada de API, sob um único diretório."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def get(self, path: str, params: Mapping[str, Any] | None) -> APIResponse | None:
        target = self.directory / cache_key(path, params)
        if not target.is_file():
            return None
        payload = json.loads(target.read_text(encoding="utf-8"))
        return APIResponse(payload["data"], payload["headers"], payload["status"])

    def set(self, path: str, params: Mapping[str, Any] | None, response: APIResponse) -> None:
        target = self.directory / cache_key(path, params)
        payload = {"path": path, "params": dict(params or {}), "data": response.data,
                   "headers": dict(response.headers), "status": response.status}
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(target)  # atômico: nunca deixa cache parcial após interrupção


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 5          # tentativas totais por erro 5xx (1 inicial + 4 retries)
    base_delay: float = 1.0        # segundos; dobra a cada tentativa (1, 2, 4, 8...)
    max_rate_limit_waits: int = 20  # trava de segurança contra loop infinito em testes/erros persistentes
    default_wait_seconds: float = 60.0  # usado quando reset/retry_after vêm como "unknown"


class ResilientClient:
    """Envolve um Client real com cache, espera de rate limit e backoff em 5xx."""

    def __init__(self, client: Client, cache: CacheStore | None = None, *,
                 config: RetryConfig = RetryConfig(),
                 sleep: Callable[[float], None] = time.sleep,
                 now: Callable[[], float] = time.time):
        self.client = client
        self.cache = cache
        self.config = config
        self.sleep = sleep
        self.now = now

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> APIResponse:
        if self.cache is not None:
            cached = self.cache.get(path, params)
            if cached is not None:
                return cached
        rate_limit_waits = 0
        attempt = 0
        while True:
            try:
                response = self.client.get(path, params)
            except RateLimitError as error:
                rate_limit_waits += 1
                if rate_limit_waits > self.config.max_rate_limit_waits:
                    raise
                self.sleep(self._wait_seconds(error))
                continue
            except APIError as error:
                if error.status in RETRYABLE_STATUS and attempt < self.config.max_attempts - 1:
                    self.sleep(self.config.base_delay * (2 ** attempt))
                    attempt += 1
                    continue
                raise
            if self.cache is not None:
                self.cache.set(path, params, response)
            return response

    def _wait_seconds(self, error: RateLimitError) -> float:
        # Mensagem vem de github_client.py: "Rate limit: remaining=.., reset=.., retry_after=..."
        retry_after = re.search(r"retry_after=(\d+)", str(error))
        if retry_after:
            return float(retry_after.group(1))
        reset = re.search(r"reset=(\d+)", str(error))
        if reset:
            return max(0.0, float(reset.group(1)) - self.now())
        return self.config.default_wait_seconds