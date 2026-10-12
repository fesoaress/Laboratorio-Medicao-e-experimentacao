"""Consolida o dataset final da Sprint 02 (issue #51).

Merge por `full_name` a partir de repositories_final_s02.csv, juntando:
- deployment_frequency_s02.csv  (RQ01)
- lead_time_s01.csv             (RQ02)
- workflow_metrics_s02.csv      (RQ03(a) + RQ04)
- cfr_delivery_s02.csv          (RQ03(b), quando existir)

Colunas ambíguas são renomeadas para variantes explícitas. Colunas
ausentes (ex.: cfr_delivery) são criadas vazias para permitir o merge
incremental quando o consenso sair.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

csv.field_size_limit(sys.maxsize)

PROCESSED = Path("data/processed/s02")
OUT = PROCESSED / "dataset_final_s02.csv"

# Metadados que preservamos (subset legível do repositories_final_s02.csv)
METADATA_FIELDS = [
    "repository_id", "full_name", "owner", "name", "html_url",
    "stargazers_count", "language", "created_at", "repo_age_days",
    "default_branch", "contributors_count", "has_github_actions",
    "collected_at", "release_count", "valid_workflow_runs",
    "metadata_complete", "status", "reasons", "description",
]

# Colunas de cada fonte a serem juntadas (renomeadas para evitar ambiguidade)
DEPLOYMENT_FIELDS = {
    "releases": "deployment_frequency_releases",
    "window_days": "deployment_frequency_window_days",
    "per_week": "deployment_frequency_per_week",
    "per_month": "deployment_frequency_per_month",
}

LEAD_TIME_FIELDS = {
    "start_date": "lead_time_window_start",
    "end_date": "lead_time_window_end",
    "lead_time_release_count": "lead_time_release_count",
    "lead_time_release_median_hours": "lead_time_release_median_hours",
    "lead_time_release_q1_hours": "lead_time_release_q1_hours",
    "lead_time_release_q3_hours": "lead_time_release_q3_hours",
    "lead_time_release_iqr_hours": "lead_time_release_iqr_hours",
    "lead_time_commit_count": "lead_time_commit_count",
    "lead_time_commit_median_hours": "lead_time_commit_median_hours",
    "lead_time_commit_q1_hours": "lead_time_commit_q1_hours",
    "lead_time_commit_q3_hours": "lead_time_commit_q3_hours",
    "lead_time_commit_iqr_hours": "lead_time_commit_iqr_hours",
    "releases_without_predecessor": "lead_time_releases_without_predecessor",
    "releases_without_new_commits": "lead_time_releases_without_new_commits",
    "releases_ignored_compare_404": "lead_time_releases_ignored_compare_404",
}

WORKFLOW_FIELDS = {
    "successes": "cfr_ci_successes",
    "failures": "cfr_ci_failures",
    "ignored": "cfr_ci_ignored",
    "cfr": "cfr_ci",
    "n_episodes": "recovery_time_n_episodes",
    "n_censored": "recovery_time_n_censored",
    "median_hours": "recovery_time_median_hours",
    "censored_proportion": "recovery_time_censored_proportion",
}

# Colunas futuras (criadas vazias agora)
FUTURE_FIELDS = [
    "cfr_delivery",          # RQ03(b) — depende do consenso
    "cfr_delivery_source",   # referência ao gold_sample_consensus.csv
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def index_by_full_name(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["full_name"]: row for row in rows}


def main() -> int:
    repos_path = PROCESSED / "repositories_final_s02.csv"
    df_path = PROCESSED / "deployment_frequency_s02.csv"
    lt_path = PROCESSED / "lead_time_s01.csv"
    wf_path = PROCESSED / "workflow_metrics_s02.csv"
    cfr_b_path = PROCESSED / "cfr_delivery_s02.csv"

    for required in (repos_path, df_path, lt_path, wf_path):
        if not required.exists():
            print(f"ERRO: não encontrei {required}")
            return 1

    repos = read_csv(repos_path)
    df = index_by_full_name(read_csv(df_path))
    lt = index_by_full_name(read_csv(lt_path))
    wf = index_by_full_name(read_csv(wf_path))
    cfr_b = index_by_full_name(read_csv(cfr_b_path)) if cfr_b_path.exists() else {}

    print(f"repos: {len(repos)}")
    print(f"deployment_frequency: {len(df)}")
    print(f"lead_time: {len(lt)}")
    print(f"workflow_metrics: {len(wf)}")
    print(f"cfr_delivery: {len(cfr_b)} (0 = ainda não existe)")

    out_fields = list(METADATA_FIELDS) + list(DEPLOYMENT_FIELDS.values()) + \
                 list(LEAD_TIME_FIELDS.values()) + list(WORKFLOW_FIELDS.values()) + \
                 FUTURE_FIELDS

    out_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    missing_df, missing_lt, missing_wf = [], [], []

    for repo in repos:
        name = repo["full_name"]
        if name in seen:
            raise ValueError(f"Duplicata em repositories_final_s02.csv: {name}")
        seen.add(name)

        row: dict[str, Any] = {field: repo.get(field, "") for field in METADATA_FIELDS}

        d = df.get(name)
        if d is None:
            missing_df.append(name)
        for src, dst in DEPLOYMENT_FIELDS.items():
            row[dst] = (d or {}).get(src, "")

        l = lt.get(name)
        if l is None:
            missing_lt.append(name)
        for src, dst in LEAD_TIME_FIELDS.items():
            row[dst] = (l or {}).get(src, "")

        w = wf.get(name)
        if w is None:
            missing_wf.append(name)
        for src, dst in WORKFLOW_FIELDS.items():
            row[dst] = (w or {}).get(src, "")

        # CFR de entrega (futuro)
        cb = cfr_b.get(name)
        row["cfr_delivery"] = (cb or {}).get("cfr_delivery", "")
        row["cfr_delivery_source"] = (cb or {}).get("source", "")

        out_rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=out_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"\nArquivo gravado: {OUT}")
    print(f"Linhas: {len(out_rows)}")
    print(f"Colunas: {len(out_fields)}")

    # Diagnóstico
    if missing_df:
        print(f"\nRepos sem deployment_frequency: {len(missing_df)} (ex: {missing_df[:3]})")
    if missing_lt:
        print(f"Repos sem lead_time: {len(missing_lt)} (ex: {missing_lt[:3]})")
    if missing_wf:
        print(f"Repos sem workflow_metrics: {len(missing_wf)} (ex: {missing_wf[:3]})")

    # Validação de duplicatas
    if len(seen) != len(repos):
        raise ValueError("Duplicatas detectadas no merge.")

    # Validação de tipos (contagens conhecidas)
    if len(missing_df) == 0 and len(missing_lt) == 0 and len(missing_wf) == 0:
        print("\nMERGE COMPLETO: todas as fontes cobrem os 311 repos")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())