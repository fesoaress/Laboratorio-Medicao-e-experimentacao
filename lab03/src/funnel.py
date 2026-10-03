"""Critérios e funil; medições temporais são fornecidas pelos colegas."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import SelectionConfig


@dataclass(frozen=True)
class TemporalEvidence:
    full_name: str
    start_date: str
    end_date: str
    release_count: int | None = None
    valid_workflow_runs: int | None = None

    def __post_init__(self):
        for value in (self.release_count, self.valid_workflow_runs):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("Contagens temporais devem ser inteiros não negativos ou ausentes.")
        if not self.full_name or not self.start_date or not self.end_date:
            raise ValueError("Evidência temporal precisa de full_name e janela.")


def load_evidence(path: Path | None) -> dict[str, TemporalEvidence]:
    if path is None:
        return {}
    evidence = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"full_name", "start_date", "end_date", "release_count", "valid_workflow_runs"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV temporal sem as colunas obrigatórias.")
        for row in reader:
            item = TemporalEvidence(row["full_name"], row["start_date"], row["end_date"],
                int(row["release_count"]) if row["release_count"] else None,
                int(row["valid_workflow_runs"]) if row["valid_workflow_runs"] else None)
            key = item.full_name.casefold()
            if key in evidence:
                raise ValueError("Evidência temporal duplicada por repositório.")
            evidence[key] = item
    return evidence


def classify(row: dict[str, Any], config: SelectionConfig, evidence: TemporalEvidence | None = None) -> None:
    """Atualiza uma linha já validada, sem consultar endpoints temporais."""
    reasons = []
    if not row["default_branch"].strip():
        reasons.append("missing_default_branch")
    if row["has_github_actions"] is False:
        reasons.append("no_github_actions")
    if reasons:
        row.update(status="discarded", reasons=";".join(reasons))
        return
    if evidence:
        if not config.start_date or (evidence.start_date, evidence.end_date) != (config.start_date, config.end_date):
            raise ValueError("Evidência temporal não corresponde à janela oficial configurada.")
        if evidence.full_name.casefold() != row["full_name"].casefold():
            raise ValueError("Evidência temporal pertence a outro repositório.")
        row["release_count"] = evidence.release_count
        row["valid_workflow_runs"] = evidence.valid_workflow_runs
    releases, runs = row["release_count"], row["valid_workflow_runs"]
    if releases is not None and releases < 5:
        reasons.append("insufficient_releases")
    if runs is not None and runs < 50:
        reasons.append("insufficient_workflow_runs")
    if reasons:
        row.update(status="discarded", reasons=";".join(reasons))
        return
    if releases is None:
        reasons.append("pending_release_validation")
    if runs is None:
        reasons.append("pending_workflow_validation")
    row.update(status="pending_validation" if reasons else "selected", reasons=";".join(reasons))


FUNNEL_FIELDS = ("stage", "count", "discarded", "pending", "reason")


def build_funnel(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Contagens não medidas ficam vazias no CSV; 0 é contagem conhecida."""
    def count(reason):
        return sum(reason in row["reasons"].split(";") for row in rows)

    eligible = [row for row in rows if row["metadata_complete"] and row["has_github_actions"]
                and row["default_branch"].strip()]
    measured_releases = [row for row in eligible if row["release_count"] is not None]
    release_pass = [row for row in measured_releases if row["release_count"] >= 5]
    measured_runs = [row for row in release_pass if row["valid_workflow_runs"] is not None]
    workflow_count_known = bool(measured_runs) or not any(
        row["release_count"] is None or row["release_count"] >= 5 for row in eligible)
    pending = sum(row["status"] == "pending_validation" for row in rows)
    unresolved = sum(row["status"] in ("pending_validation", "pending_metadata", "api_error", "metadata_error") for row in rows)

    def stage(name, total, discarded=0, pending=0, reason=""):
        return dict(zip(FUNNEL_FIELDS, (name, total, discarded, pending, reason)))

    return [
        stage("candidates", len(rows), reason="unique_candidates_selected"),
        stage("processed", sum(row["processed"] for row in rows), pending=count("pending_metadata_collection")),
        stage("metadata_complete", sum(row["metadata_complete"] for row in rows),
              pending=sum(row["status"] in ("api_error", "metadata_error", "pending_metadata") for row in rows), reason="errors_are_not_insufficient_counts"),
        stage("actions_enabled", sum(row["has_github_actions"] is True for row in rows),
              discarded=sum(row["has_github_actions"] is False for row in rows),
              pending=sum(row["has_github_actions"] is None for row in rows), reason="no_github_actions"),
        stage("pending_validation", pending, reason="pending_release_validation;pending_workflow_validation"),
        stage("release_filter", len(release_pass) if measured_releases or not eligible else None,
              discarded=sum(row["release_count"] < 5 for row in measured_releases) if measured_releases or not eligible else None,
              pending=len(eligible) - len(measured_releases), reason="minimum_5_releases_in_official_window"),
        stage("workflow_filter", sum(row["valid_workflow_runs"] >= 50 for row in measured_runs) if workflow_count_known else None,
              discarded=sum(row["valid_workflow_runs"] < 50 for row in measured_runs) if workflow_count_known else None,
              pending=sum(row["release_count"] is None or (row["release_count"] >= 5 and row["valid_workflow_runs"] is None) for row in eligible),
              reason="minimum_50_valid_runs_in_official_window"),
        stage("final_sample", sum(row["status"] == "selected" for row in rows) if not unresolved else None,
              discarded=sum(row["status"] == "discarded" for row in rows), pending=unresolved,
              reason="provisional_until_all_validations_complete"),
    ]


def print_funnel(funnel: list[dict[str, Any]]) -> None:
    print(f"{'stage':<22} {'count':>8} {'discarded':>10} {'pending':>8}")
    for row in funnel:
        values = ["N/D" if row[key] is None else str(row[key]) for key in ("count", "discarded", "pending")]
        print(f"{row['stage']:<22} {values[0]:>8} {values[1]:>10} {values[2]:>8}")
