"""Auditoria offline de CSVs já coletados; não acessa o GitHub."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from .funnel import FUNNEL_FIELDS, build_funnel
from .metadata import parse_metadata
from .pipeline import REPOSITORY_FIELDS


def read_rows(path: Path, fields) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(fields):
            raise ValueError(f"Cabeçalho inconsistente: {path.name}.")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Linha CSV com quantidade incorreta de colunas: {path.name}.")
    return rows


def audit(output_dir: Path) -> dict:
    raw = read_rows(output_dir / "repositories_s01.csv", REPOSITORY_FIELDS)
    rows, names, identifiers = [], set(), set()
    integer_fields = ("repository_id", "stargazers_count", "repo_age_days", "contributors_count", "release_count", "valid_workflow_runs")
    for raw_row in raw:
        row = dict(raw_row)
        name = row["full_name"].casefold()
        if not name or name in names or (row["repository_id"] and row["repository_id"] in identifiers):
            raise ValueError("Repositório duplicado ou sem identificação.")
        names.add(name)
        if row["repository_id"]:
            identifiers.add(row["repository_id"])
        for key in integer_fields:
            row[key] = int(row[key]) if row[key] else None
            if row[key] is not None and row[key] < 0:
                raise ValueError(f"Contagem negativa: {key}.")
        for key in ("processed", "metadata_complete", "has_github_actions"):
            if row[key] not in ("True", "False", ""):
                raise ValueError(f"Booleano inválido: {key}.")
            row[key] = {"True": True, "False": False, "": None}[row[key]]
        if row["metadata_complete"]:
            parsed = parse_metadata({"id": row["repository_id"], "owner": {"login": row["owner"]},
                "name": row["name"], "full_name": row["full_name"], "html_url": row["html_url"],
                "created_at": row["created_at"], "default_branch": row["default_branch"],
                "stargazers_count": row["stargazers_count"], "language": row["language"] or None}, row["collected_at"])
            if parsed["repo_age_days"] != row["repo_age_days"]:
                raise ValueError("Idade não corresponde ao timestamp da coleta.")
            if row["contributors_count"] is None or row["has_github_actions"] is None:
                raise ValueError("Metadados completos sem contributors/Actions medidos.")
        rows.append(row)
    expected = [{key: "" if value is None else str(value) for key, value in row.items()} for row in build_funnel(rows)]
    if read_rows(output_dir / "selection_funnel_s01.csv", FUNNEL_FIELDS) != expected:
        raise ValueError("Funil não corresponde aos registros dos repositórios.")
    manifest = json.loads((output_dir / "selection_manifest_s01.json").read_text(encoding="utf-8"))
    summary = {"candidates": len(rows), "processed": sum(bool(row["processed"]) for row in rows),
               "actions_enabled": sum(row["has_github_actions"] is True for row in rows),
               "statuses": dict(Counter(row["status"] for row in rows)), "duplicates": 0}
    for key, value in (("candidates_found", summary["candidates"]), ("processed", summary["processed"]),
                       ("actions_enabled", summary["actions_enabled"])):
        if manifest[key] != value:
            raise ValueError("Manifesto não corresponde aos CSVs.")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Audita CSVs e manifesto Lab03 sem rede")
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        summary = audit(args.output_dir)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Auditoria falhou: {error}\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
