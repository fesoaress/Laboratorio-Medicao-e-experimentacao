"""Métricas do Lab03: Lead Time (RQ02), CFR (RQ03) e Recovery Time (RQ04)."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from typing import Any

from .commits import ReleaseInterval
from .temporal import utc_datetime


# =====================================================================
# Lead Time for Changes (Issue #42 / RQ02)
# =====================================================================


@dataclass(frozen=True)
class Distribution:
    count: int
    median_hours: float | None
    q1_hours: float | None
    q3_hours: float | None
    iqr_hours: float | None


def summarize_hours(values) -> Distribution:
    """Quartis com interpolação linear: posição (n - 1) * p (tipo 7)."""
    ordered = sorted(values)
    if not ordered:
        return Distribution(0, None, None, None, None)

    def quantile(p):
        position = (len(ordered) - 1) * p
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    q1, q3 = quantile(0.25), quantile(0.75)
    return Distribution(len(ordered), median(ordered), q1, q3, q3 - q1)


@dataclass(frozen=True)
class LeadTimeResult:
    by_release: Distribution
    by_commit: Distribution
    releases_without_predecessor: int
    releases_without_new_commits: int
    releases_ignored_compare_404: int
    release_values: tuple[dict, ...]
    commit_values: tuple[dict, ...]


def calculate_lead_time(intervals: tuple[ReleaseInterval, ...]) -> LeadTimeResult:
    """(a) maior duração por release; (b) todas as durações commit/release.

    Não recorta commits pela janela: um commit antigo entregue na janela
    continua pertencendo à release. Comparações HTTP 404 são ignoradas e
    contabilizadas conforme a FAQ. Outras falhas de coleta ou durações negativas
    invalidam o resultado, em vez de produzir uma mediana artificialmente baixa.
    SHAs duplicados dentro de um intervalo contam uma vez; cada observação em
    releases distintas é mantida conforme a definição de RQ02(b).
    """
    release_values, commit_values = [], []
    without_previous = without_commits = 0
    ignored_compare_404 = 0
    seen_releases = set()
    for interval in intervals:
        release = interval.release
        if release.release_id in seen_releases:
            raise ValueError("Release duplicada nos intervalos de Lead Time.")
        seen_releases.add(release.release_id)
        if interval.status == "ignored_compare_404" and interval.error_status == 404:
            ignored_compare_404 += 1
            continue
        if interval.status == "no_previous_release" and interval.previous_release is None:
            without_previous += 1
            continue
        if interval.status != "complete" or interval.previous_release is None:
            raise ValueError("Lead Time indisponível: intervalo não coletado completamente.")
        if utc_datetime(interval.previous_release.published_at) > utc_datetime(release.published_at):
            raise ValueError("Predecessora publicada depois da release atual.")
        unique = {}
        for commit in interval.commits:
            if commit.sha in unique and unique[commit.sha] != commit:
                raise ValueError("SHA duplicado com dados de commit inconsistentes.")
            unique[commit.sha] = commit
        if not unique:
            without_commits += 1
            continue
        values = []
        for commit in unique.values():
            hours = (utc_datetime(release.published_at) - utc_datetime(commit.author_date)).total_seconds() / 3600
            if hours < 0:
                raise ValueError(f"Lead Time negativo: release {release.release_id}, commit {commit.sha}.")
            values.append(hours)
            commit_values.append({"release_id": release.release_id, "tag_name": release.tag_name,
                                  "commit_sha": commit.sha, "lead_time_hours": hours})
        release_values.append({"release_id": release.release_id, "tag_name": release.tag_name,
                               "commit_count": len(unique), "lead_time_hours": max(values)})
    return LeadTimeResult(summarize_hours(v["lead_time_hours"] for v in release_values),
                          summarize_hours(v["lead_time_hours"] for v in commit_values),
                          without_previous, without_commits, ignored_compare_404,
                          tuple(release_values), tuple(commit_values))


# =====================================================================
# CFR (RQ03) e Recovery Time (RQ04) — Issues #44 / #45
# =====================================================================


def _parse_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass(frozen=True)
class ChangeFailureRateA:
    successes: int
    failures: int
    ignored: int
    cfr: float | None  # None quando não há successes+failures para formar a base


def change_failure_rate_a(runs: list[dict[str, Any]]) -> ChangeFailureRateA:
    """RQ03(a): falhas / (falhas + sucessos) entre todos os workflow runs do repo."""
    successes = sum(run["status_class"] == "success" for run in runs)
    failures = sum(run["status_class"] == "failure" for run in runs)
    ignored = sum(run["status_class"] is None for run in runs)
    total = successes + failures
    return ChangeFailureRateA(successes, failures, ignored, failures / total if total else None)


@dataclass(frozen=True)
class RecoveryEpisode:
    workflow_id: int
    failure_started_at: str
    recovered_at: str | None  # None quando censurado (nunca voltou a 'success' na janela)
    hours: float | None


def recovery_episodes(runs: list[dict[str, Any]]) -> list[RecoveryEpisode]:
    """RQ04: episódios de falha por workflow, ordenados cronologicamente.

    Runs com status_class None são ignorados antes de montar a sequência,
    conforme a seção 3 ("não entra em nenhum cálculo"). Uma sequência de
    falhas no início dos dados, sem nenhum 'success' anterior observado, não
    tem início definido pela fórmula do enunciado ("começa na primeira falha
    após um sucesso") e é descartada — registrar como censura à esquerda da
    janela na seção de ameaças à validade do artigo.
    """
    by_workflow: dict[int, list[dict[str, Any]]] = {}
    for run in runs:
        if run["status_class"] is None:
            continue
        by_workflow.setdefault(run["workflow_id"], []).append(run)

    episodes: list[RecoveryEpisode] = []
    for workflow_id, workflow_runs in by_workflow.items():
        ordered = sorted(workflow_runs, key=lambda run: _parse_instant(run["run_started_at"]))
        seen_success = False
        episode_start: str | None = None
        for run in ordered:
            if run["status_class"] == "success":
                if episode_start is not None:
                    hours = (_parse_instant(run["updated_at"]) - _parse_instant(episode_start)).total_seconds() / 3600
                    episodes.append(RecoveryEpisode(workflow_id, episode_start, run["updated_at"], hours))
                    episode_start = None
                seen_success = True
            elif run["status_class"] == "failure" and seen_success and episode_start is None:
                episode_start = run["run_started_at"]
        if episode_start is not None:
            episodes.append(RecoveryEpisode(workflow_id, episode_start, None, None))
    return episodes


@dataclass(frozen=True)
class RecoveryTimeSummary:
    n_episodes: int
    n_censored: int
    median_hours: float | None
    censored_proportion: float | None


def repository_recovery_time(episodes: list[RecoveryEpisode]) -> RecoveryTimeSummary:
    """Valor do repositório = mediana dos episódios resolvidos; censurados só entram na proporção."""
    resolved = [episode.hours for episode in episodes if episode.hours is not None]
    n = len(episodes)
    n_censored = sum(episode.hours is None for episode in episodes)
    return RecoveryTimeSummary(
        n_episodes=n, n_censored=n_censored,
        median_hours=statistics.median(resolved) if resolved else None,
        censored_proportion=(n_censored / n) if n else None,
    )