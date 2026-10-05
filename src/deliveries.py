"""Persistência e integração dos componentes #40, #41 e #42."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .commits import collect_release_intervals
from .github_client import APIError, Client, RateLimitError
from .metrics import calculate_lead_time
from .pipeline import write_csv
from .releases import collect_releases_and_tags
from .temporal import ObservationWindow, repository_path

SUMMARY_FIELDS = (
    "full_name", "start_date", "end_date", "default_branch", "default_branch_sha",
    "release_count", "prerelease_count", "tag_count", "status", "error_detail",
    "releases_without_predecessor", "releases_without_new_commits",
    "releases_ignored_compare_404",
    "lead_time_release_count", "lead_time_release_median_hours", "lead_time_release_q1_hours",
    "lead_time_release_q3_hours", "lead_time_release_iqr_hours", "lead_time_commit_count",
    "lead_time_commit_median_hours", "lead_time_commit_q1_hours", "lead_time_commit_q3_hours",
    "lead_time_commit_iqr_hours",
)

OUTPUT_FIELDS = {
    "releases_s01.csv": ("full_name", "release_id", "tag_name", "published_at", "commit_sha",
                          "prerelease", "html_url", "target_commitish", "in_window"),
    "tags_s01.csv": ("full_name", "name", "commit_sha", "author_date", "on_default_branch", "in_window"),
    "excluded_releases_s01.csv": ("full_name", "release_id", "tag_name", "reason"),
    "release_intervals_s01.csv": ("full_name", "release_id", "tag_name", "previous_release_id",
                                  "previous_tag_name", "base_sha", "head_sha", "commit_count", "status", "error_detail", "error_status"),
    "release_commits_s01.csv": ("full_name", "release_id", "tag_name", "sha", "author_date",
                                "committer_date", "message", "html_url"),
    "lead_time_releases_s01.csv": ("full_name", "release_id", "tag_name", "commit_count", "lead_time_hours"),
    "lead_time_commits_s01.csv": ("full_name", "release_id", "tag_name", "commit_sha", "lead_time_hours"),
    "lead_time_s01.csv": SUMMARY_FIELDS,
    "release_validation_s01.csv": ("full_name", "start_date", "end_date", "release_count", "valid_workflow_runs"),
}


def collect_delivery_data(client: Client, repositories: list[dict], window: ObservationWindow,
                          output_dir: Path, *, per_page: int = 100) -> list[dict]:
    """Persiste progresso por repositório e aceita o Client da futura issue #44.

    Não conta erro como ausência de releases. Na interrupção por quota/401,
    os repositórios ainda não tentados permanecem pending_collection.
    """
    seen = set()
    for repo in repositories:
        name = repo.get("full_name")
        repository_path(name)
        if name.casefold() in seen:
            raise ValueError("Repositório duplicado na coleta temporal.")
        seen.add(name.casefold())
        if not isinstance(repo.get("default_branch"), str) or not repo["default_branch"].strip():
            raise ValueError("Repositório sem default_branch.")
    rows = []
    for repo in repositories:
        row = dict.fromkeys(SUMMARY_FIELDS)
        row.update(full_name=repo["full_name"], default_branch=repo["default_branch"],
                   start_date=window.start_date, end_date=window.end_date,
                   status="pending_collection", error_detail="")
        rows.append(row)
    outputs = {name: [] for name in OUTPUT_FIELDS}
    outputs["lead_time_s01.csv"] = rows
    collected_at = datetime.now(timezone.utc).isoformat()

    def save():
        outputs["release_validation_s01.csv"] = [
            {"full_name": row["full_name"], "start_date": window.start_date, "end_date": window.end_date,
             "release_count": row["release_count"], "valid_workflow_runs": None} for row in rows]
        for name, fields in OUTPUT_FIELDS.items():
            write_csv(output_dir / name, fields, outputs[name])
        manifest = {"collected_at": collected_at, "window": asdict(window), "per_page": per_page,
                    "definition": "published_non_draft_non_prerelease_on_default_branch",
                    "tag_date_source": "commit.author.date", "unit": "hours",
                    "quartiles": "linear_interpolation_type_7",
                    "releases_ignored_compare_404": sum(row["releases_ignored_compare_404"] or 0 for row in rows),
                    "repositories": rows}
        (output_dir / "delivery_manifest_s01.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    save()
    try:
        for row in rows:
            name = row["full_name"]
            try:
                collection = collect_releases_and_tags(client, name, row["default_branch"], window, per_page=per_page)
                row.update(default_branch_sha=collection.default_branch_sha,
                           release_count=len(collection.in_window(window)),
                           prerelease_count=sum(r.prerelease and window.contains(r.published_at) for r in collection.history),
                           tag_count=sum(t.on_default_branch and t.in_window for t in collection.tags))
                outputs["releases_s01.csv"].extend({"full_name": name, **asdict(r), "in_window": window.contains(r.published_at)}
                                                   for r in collection.history)
                outputs["tags_s01.csv"].extend({"full_name": name, **asdict(t)} for t in collection.tags)
                outputs["excluded_releases_s01.csv"].extend({"full_name": name, **r} for r in collection.excluded_releases)
                intervals = collect_release_intervals(client, name, collection.history, window, per_page=per_page)
                for interval in intervals:
                    release, previous = interval.release, interval.previous_release
                    outputs["release_intervals_s01.csv"].append({
                        "full_name": name, "release_id": release.release_id, "tag_name": release.tag_name,
                        "previous_release_id": previous.release_id if previous else None,
                        "previous_tag_name": previous.tag_name if previous else None,
                        "base_sha": previous.commit_sha if previous else None, "head_sha": release.commit_sha,
                        "commit_count": len(interval.commits) if interval.status == "complete" else None,
                        "status": interval.status, "error_detail": interval.error_detail,
                        "error_status": interval.error_status})
                    outputs["release_commits_s01.csv"].extend({"full_name": name, "release_id": release.release_id,
                                                              "tag_name": release.tag_name, **asdict(c)} for c in interval.commits)
                row["releases_ignored_compare_404"] = sum(i.status == "ignored_compare_404" for i in intervals)
                errors = [i.error_detail for i in intervals if i.status == "error"]
                if errors:
                    row.update(status="comparison_error", error_detail="; ".join(errors))
                else:
                    try:
                        result = calculate_lead_time(intervals)
                    except ValueError as error:
                        row.update(status="metric_error", error_detail=str(error))
                    else:
                        row.update(status="complete", releases_without_predecessor=result.releases_without_predecessor,
                                   releases_without_new_commits=result.releases_without_new_commits,
                                   releases_ignored_compare_404=result.releases_ignored_compare_404)
                        for variant, distribution in (("release", result.by_release), ("commit", result.by_commit)):
                            for field, value in asdict(distribution).items():
                                row[f"lead_time_{variant}_{field}"] = value
                        outputs["lead_time_releases_s01.csv"].extend({"full_name": name, **v} for v in result.release_values)
                        outputs["lead_time_commits_s01.csv"].extend({"full_name": name, **v} for v in result.commit_values)
            except APIError as error:
                row.update(status="api_error", error_detail=str(error))
                if isinstance(error, RateLimitError) or error.status == 401:
                    save()
                    break
            except ValueError as error:
                row.update(status="data_error", error_detail=str(error))
            save()
    except KeyboardInterrupt:
        # A linha em andamento fica pendente; não declara sucesso em Ctrl+C.
        save()
        raise
    return rows
