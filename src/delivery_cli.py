"""Execução independente da contribuição de Fernanda, sem nova busca."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .config import DEFAULT_CONFIG, load_config
from .deliveries import collect_delivery_data
from .github_client import APIError, GitHubClient
from .temporal import ObservationWindow, repository_path


def load_repositories(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"full_name", "default_branch"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV precisa de full_name e default_branch.")
        return [dict(row) for row in reader if row.get("metadata_complete", "True") == "True"
                and row.get("has_github_actions", "True") == "True"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Lab03 S01 — releases, tags, commits e Lead Time")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repositories-csv", type=Path)
    source.add_argument("--repository", action="append", help="owner/repo; pode repetir")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date", help="Fim exclusivo")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/fernanda"))
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config, start_date=args.start_date, end_date=args.end_date)
        window = ObservationWindow(config.start_date, config.end_date)
        client = GitHubClient()
        if args.repositories_csv:
            repositories = load_repositories(args.repositories_csv)
        else:
            repositories = []
            for name in args.repository:
                data = client.get(repository_path(name)).data
                if not isinstance(data, dict):
                    raise ValueError("Resposta de metadados inválida.")
                repositories.append({"full_name": name, "default_branch": data.get("default_branch")})
        rows = collect_delivery_data(client, repositories, window, args.output_dir, per_page=config.per_page)
    except (OSError, ValueError, TypeError) as error:
        parser.error(str(error))
    except APIError as error:
        print(f"Coleta interrompida: {error}")
        return 1
    print(f"Coleta temporal: {sum(row['status'] == 'complete' for row in rows)}/{len(rows)} concluídos.")
    print(f"Artefatos: {args.output_dir}")
    return 0 if rows and all(row["status"] == "complete" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
