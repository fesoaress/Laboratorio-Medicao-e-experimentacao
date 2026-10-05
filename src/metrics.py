"""Issue #42: Lead Time for Changes (a)/(b), em horas, com mediana e IQR."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .commits import ReleaseInterval
from .temporal import utc_datetime


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
