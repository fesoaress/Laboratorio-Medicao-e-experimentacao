"""Entrada reproduzível da seleção Lab03 S01."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .config import DEFAULT_CONFIG, load_config
from .github_client import GitHubClient
from .repository_selector import select_candidates


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Lab03 S01 — seleção de candidatos públicos")
    result.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    result.add_argument("--limit", type=int, help="Número máximo de candidatos, não de aprovados finais")
    result.add_argument("--query", action="append", help="Consulta ou fatia de busca; pode repetir")
    result.add_argument("--start-date", help="Início oficial ISO (YYYY-MM-DD)")
    result.add_argument("--end-date", help="Fim oficial exclusivo ISO (YYYY-MM-DD)")
    result.add_argument("--output-dir", type=Path, default=Path("lab03/data/processed"))
    return result


def main(argv: list[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    try:
        config = load_config(args.config, sample_size=args.limit,
            search_queries=tuple(args.query) if args.query else None,
            start_date=args.start_date, end_date=args.end_date)
    except (OSError, ValueError, TypeError) as error:
        argument_parser.error(str(error))
    result = select_candidates(GitHubClient(), config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"collected_at": datetime.now(timezone.utc).isoformat(), "config": asdict(config),
                "queries": result.queries, "duplicates_skipped": result.duplicates_skipped,
                "errors": result.errors, "candidates_found": len(result.repositories)}
    (args.output_dir / "selection_manifest_s01.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "candidates_s01.json").write_text(
        json.dumps(result.repositories, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Candidatos únicos: {len(result.repositories)} / {config.sample_size}")
    for error in result.errors:
        print(f"Erro: {error}")
    if not config.start_date:
        print("Janela oficial ausente; validação temporal permanece pendente.")
    if len(result.repositories) < config.sample_size:
        print("Seleção incompleta: verifique erros, limite de 1.000 e fatias de busca.")
    return 1 if result.errors or len(result.repositories) < config.sample_size else 0
