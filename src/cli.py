"""Entrada reproduzível da seleção Lab03 S01."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .cache import CacheStore, ResilientClient
from .config import DEFAULT_CONFIG, load_config
from .deliveries import collect_delivery_data
from .funnel import TemporalEvidence, build_funnel, classify, load_evidence, print_funnel
from .github_client import GitHubClient
from .pipeline import collect_metadata, save_outputs
from .repository_selector import select_candidates
from .temporal import ObservationWindow


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Lab03 S01 — seleção de candidatos públicos")
    result.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    result.add_argument("--limit", type=int, help="Número máximo de candidatos, não de aprovados finais")
    result.add_argument("--query", action="append", help="Consulta ou fatia de busca; pode repetir")
    result.add_argument("--start-date", help="Início oficial ISO (YYYY-MM-DD)")
    result.add_argument("--end-date", help="Fim oficial exclusivo ISO (YYYY-MM-DD)")
    result.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    result.add_argument("--candidates-only", action="store_true", help="Executa somente a busca de #38")
    result.add_argument("--validation-csv", type=Path, help="Contagens temporais fornecidas por #40/#43")
    result.add_argument("--collect-lead-time", action="store_true", help="Coleta #40/#41/#42 na janela oficial")
    return result


def main(argv: list[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    try:
        config = load_config(args.config, sample_size=args.limit,
            search_queries=tuple(args.query) if args.query else None,
            start_date=args.start_date, end_date=args.end_date)
        if args.collect_lead_time:
            if args.candidates_only:
                raise ValueError("--collect-lead-time não combina com --candidates-only.")
            ObservationWindow(config.start_date, config.end_date)
        evidence = load_evidence(args.validation_csv)
        for item in evidence.values():
            if not config.start_date or (item.start_date, item.end_date) != (config.start_date, config.end_date):
                raise ValueError("CSV temporal não corresponde à janela oficial configurada.")
    except (OSError, ValueError, TypeError) as error:
        argument_parser.error(str(error))
    cache = CacheStore(args.output_dir / "cache")
    client = ResilientClient(GitHubClient(), cache)
    result = select_candidates(client, config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(timezone.utc).isoformat()
    manifest = {"collected_at": collected_at, "config": asdict(config),
                "queries": result.queries, "duplicates_skipped": result.duplicates_skipped,
                "errors": result.errors, "candidates_found": len(result.repositories),
                "validation_csv": str(args.validation_csv) if args.validation_csv else None}
    metadata_errors = False
    if args.candidates_only:
        # Persistência compacta, sem respostas cruas ou milhares de campos.
        fields = ("id", "full_name", "name", "html_url", "stargazers_count", "language", "created_at", "default_branch")
        candidates = [{**{key: repository.get(key) for key in fields},
                       "owner": {"login": repository.get("owner", {}).get("login")}}
                      for repository in result.repositories]
        (args.output_dir / "candidates_s01.json").write_text(
            json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        rows = collect_metadata(client, result.repositories, config, collected_at, evidence,
                                stop_before_collection=bool(result.errors))
        if args.collect_lead_time:
            eligible = [row for row in rows if row["metadata_complete"] and row["has_github_actions"]
                        and row["default_branch"].strip()]
            deliveries = collect_delivery_data(client, eligible, ObservationWindow(config.start_date, config.end_date),
                                               args.output_dir, per_page=config.per_page)
            by_name = {row["full_name"].casefold(): row for row in deliveries}
            for row in eligible:
                delivery = by_name[row["full_name"].casefold()]
                classify(row, config, TemporalEvidence(row["full_name"], config.start_date, config.end_date,
                                                      delivery["release_count"], row["valid_workflow_runs"]))
            manifest["delivery_errors"] = sum(row["status"] != "complete" for row in deliveries)
        funnel = build_funnel(rows)
        save_outputs(args.output_dir, rows, funnel)
        print_funnel(funnel)
        manifest["processed"] = sum(row["processed"] for row in rows)
        manifest["actions_enabled"] = sum(row["has_github_actions"] is True for row in rows)
        manifest["metadata_errors"] = sum(row["status"] in ("api_error", "metadata_error") for row in rows)
        metadata_errors = (any(row["status"] in ("api_error", "metadata_error", "pending_metadata") for row in rows)
                           or bool(manifest.get("delivery_errors")))
    (args.output_dir / "selection_manifest_s01.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Candidatos únicos: {len(result.repositories)} / {config.sample_size}")
    for error in result.errors:
        print(f"Erro: {error}")
    if not config.start_date:
        print("Janela oficial ausente; validação temporal permanece pendente.")
    if len(result.repositories) < config.sample_size:
        print("Seleção incompleta: verifique erros, limite de 1.000 e fatias de busca.")
    incomplete = any(query["incomplete_results"] for query in result.queries)
    if incomplete:
        print("A API indicou incomplete_results; consulte o manifesto e refine a busca.")
    return 1 if result.errors or metadata_errors or incomplete or len(result.repositories) < config.sample_size else 0


if __name__ == "__main__":
    raise SystemExit(main())
