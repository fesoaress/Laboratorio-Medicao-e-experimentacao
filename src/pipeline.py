"""Coleta de metadados e persistência do funil da issue #39."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping

from .config import SelectionConfig
from .funnel import FUNNEL_FIELDS, TemporalEvidence, classify
from .github_client import APIError, Client, RateLimitError
from .metadata import MetadataError, check_actions, count_contributors, parse_metadata

REPOSITORY_FIELDS = (
    "repository_id", "owner", "name", "full_name", "html_url", "stargazers_count",
    "language", "created_at", "repo_age_days", "default_branch", "contributors_count",
    "has_github_actions", "collected_at", "release_count", "valid_workflow_runs",
    "processed", "metadata_complete", "status", "reasons", "error_detail",
)


def collect_metadata(
    client: Client, candidates: list[dict[str, Any]], config: SelectionConfig,
    collected_at: str, evidence: Mapping[str, TemporalEvidence] | None = None,
    *, stop_before_collection: bool = False,
) -> list[dict[str, Any]]:
    rows = []
    stopped = stop_before_collection
    for candidate in candidates:
        row = dict.fromkeys(REPOSITORY_FIELDS)
        row.update(full_name=candidate.get("full_name"), collected_at=collected_at,
                   processed=False, metadata_complete=False, status="pending_metadata",
                   reasons="pending_metadata_collection", error_detail="")
        rows.append(row)
        if stopped:
            continue
        row["processed"] = True
        try:
            row.update(parse_metadata(candidate, collected_at))
            row["has_github_actions"] = check_actions(client, row["full_name"])
            row["contributors_count"] = count_contributors(client, row["full_name"])
            row["metadata_complete"] = True
            classify(row, config, (evidence or {}).get(row["full_name"].casefold()))
        except APIError as error:
            row.update(status="api_error", reasons="api_error", error_detail=str(error))
            stopped = isinstance(error, RateLimitError) or error.status == 401
        except MetadataError as error:
            row.update(status="metadata_error", reasons="metadata_error", error_detail=str(error))
    return rows


def write_csv(path: Path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def save_outputs(output_dir: Path, rows, funnel) -> None:
    write_csv(output_dir / "repositories_s01.csv", REPOSITORY_FIELDS, rows)
    write_csv(output_dir / "selection_funnel_s01.csv", FUNNEL_FIELDS, funnel)
