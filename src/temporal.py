"""Contratos temporais compartilhados pelos coletores da Sprint 01."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote

from .config import SelectionConfig


def utc_datetime(value: str) -> datetime:
    """Recusa datas sem fuso; nunca assume o horário da máquina."""
    if not isinstance(value, str):
        raise ValueError("Timestamp ausente ou inválido.")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp precisa de fuso horário explícito.")
    return parsed.astimezone(timezone.utc)


def repository_path(full_name: str) -> str:
    if not isinstance(full_name, str) or not re.fullmatch(r"[\w.-]+/[\w.-]+", full_name):
        raise ValueError("Repositório deve ter formato owner/repo.")
    return "/repos/" + "/".join(quote(part, safe="") for part in full_name.split("/"))


@dataclass(frozen=True)
class ObservationWindow:
    start_date: str
    end_date: str

    def __post_init__(self):
        SelectionConfig(start_date=self.start_date, end_date=self.end_date)
        if not self.start_date or not self.end_date:
            raise ValueError("A coleta temporal exige a janela oficial.")

    @property
    def start(self) -> datetime:
        return utc_datetime(self.start_date + "T00:00:00Z")

    @property
    def end(self) -> datetime:
        return utc_datetime(self.end_date + "T00:00:00Z")

    def contains(self, timestamp: str) -> bool:
        return self.start <= utc_datetime(timestamp) < self.end


@dataclass(frozen=True)
class Release:
    release_id: int
    tag_name: str
    published_at: str
    commit_sha: str
    prerelease: bool = False
    html_url: str = ""
    target_commitish: str = ""


@dataclass(frozen=True)
class Tag:
    name: str
    commit_sha: str
    author_date: str
    on_default_branch: bool
    in_window: bool


@dataclass(frozen=True)
class Commit:
    sha: str
    author_date: str
    committer_date: str
    message: str
    html_url: str = ""


def parse_commit(data: dict) -> Commit:
    try:
        sha = data["sha"]
        details = data["commit"]
        author_date = details["author"]["date"]
        committer_date = details["committer"]["date"]
        message = details["message"]
    except (KeyError, TypeError) as error:
        raise ValueError("Commit sem SHA, datas ou mensagem.") from error
    if not isinstance(sha, str) or not sha or not isinstance(message, str):
        raise ValueError("Commit com SHA ou mensagem inválida.")
    utc_datetime(author_date)
    utc_datetime(committer_date)
    return Commit(sha, author_date, committer_date, message, data.get("html_url", ""))
