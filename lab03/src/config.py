"""Parâmetros da seleção; datas oficiais permanecem ausentes até confirmação."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "s01.json"


@dataclass(frozen=True)
class SelectionConfig:
    sample_size: int = 100
    search_queries: tuple[str, ...] = ("stars:>1000",)
    per_page: int = 100
    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self):
        if type(self.sample_size) is not int or self.sample_size < 1:
            raise ValueError("sample_size deve ser um inteiro positivo.")
        if type(self.per_page) is not int or not 1 <= self.per_page <= 100:
            raise ValueError("per_page deve estar entre 1 e 100.")
        if not self.search_queries or any(not isinstance(q, str) or not q.strip() for q in self.search_queries):
            raise ValueError("Informe ao menos uma search_query não vazia.")
        if bool(self.start_date) != bool(self.end_date):
            raise ValueError("Informe start_date e end_date juntas.")
        if self.start_date:
            start, end = date.fromisoformat(self.start_date), date.fromisoformat(self.end_date)
            if end <= start:
                raise ValueError("end_date deve ser posterior a start_date.")
            # Convenção: janela de 12 meses [início, fim), com ajuste para 29/02.
            try:
                anniversary = start.replace(year=start.year + 1)
            except ValueError:
                anniversary = start.replace(year=start.year + 1, day=28)
            if end != anniversary:
                raise ValueError("A janela oficial deve ter 12 meses: [start_date, end_date).")


def load_config(path: Path = DEFAULT_CONFIG, **overrides) -> SelectionConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("A configuração deve ser um objeto JSON.")
    if "search_queries" in data:
        if not isinstance(data["search_queries"], list):
            raise ValueError("search_queries deve ser uma lista.")
        data["search_queries"] = tuple(data["search_queries"])
    config = SelectionConfig(**data)
    return replace(config, **{key: value for key, value in overrides.items() if value is not None})
