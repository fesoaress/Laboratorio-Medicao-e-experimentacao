"""Issue #41: comparação completa, sem truncar intervalos em 250 commits."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from .github_client import APIError, Client, RateLimitError, iter_pages
from .temporal import Commit, ObservationWindow, Release, parse_commit, repository_path, utc_datetime


@dataclass(frozen=True)
class ReleaseInterval:
    release: Release
    previous_release: Release | None
    commits: tuple[Commit, ...] = ()
    status: str = "complete"
    error_detail: str = ""
    error_status: int | None = None


def collect_commits_between(client: Client, full_name: str, base: str, head: str,
                            *, per_page: int = 100) -> tuple[Commit, ...]:
    root = repository_path(full_name)
    if not all(isinstance(ref, str) and ref for ref in (base, head)):
        raise ValueError("Comparação exige base e head.")
    if type(per_page) is not int or not 1 <= per_page <= 100:
        raise ValueError("per_page deve estar entre 1 e 100.")
    if base == head:
        return ()
    path = root + "/compare/" + quote(base, safe="") + "..." + quote(head, safe="")
    commits, expected, comparison_status = {}, None, None
    for page in iter_pages(client, path, {"per_page": per_page, "page": 1}):
        data = page.data
        if not isinstance(data, dict) or not isinstance(data.get("commits"), list):
            raise ValueError("Comparação sem lista de commits.")
        total, status = data.get("total_commits"), data.get("status")
        if type(total) is not int or total < 0 or status not in ("ahead", "identical"):
            raise ValueError("Releases não formam intervalo ancestral válido (ahead/identical).")
        if expected is not None and (expected != total or comparison_status != status):
            raise APIError("Comparação mudou durante a paginação; repita a coleta.")
        expected, comparison_status = total, status
        for raw in data["commits"]:
            commit = parse_commit(raw)
            if commit.sha in commits and commits[commit.sha] != commit:
                raise APIError("Commit inconsistente durante a paginação.")
            commits[commit.sha] = commit
    if len(commits) != expected:
        raise APIError(f"Comparação incompleta: {len(commits)} commits únicos de {expected} anunciados.")
    return tuple(commits.values())


def collect_release_intervals(client: Client, full_name: str, history: tuple[Release, ...],
                              window: ObservationWindow, *, include_prereleases: bool = False,
                              per_page: int = 100) -> tuple[ReleaseInterval, ...]:
    """A primeira release real é ignorada; predecessora pode preceder a janela.

    HTTP 404 na comparação registra a release como ignorada, conforme a FAQ.
    A próxima release continua usando sua predecessora real; não se cria um
    intervalo artificial com uma release mais antiga.
    """
    ordered = sorted((r for r in history if include_prereleases or not r.prerelease),
                     key=lambda r: (utc_datetime(r.published_at), r.release_id))
    intervals, previous = [], None
    for release in ordered:
        if window.contains(release.published_at):
            if previous is None:
                intervals.append(ReleaseInterval(release, None, status="no_previous_release"))
            else:
                try:
                    commits = collect_commits_between(client, full_name, previous.commit_sha,
                                                      release.commit_sha, per_page=per_page)
                    intervals.append(ReleaseInterval(release, previous, commits))
                except RateLimitError:
                    raise
                except APIError as error:
                    if error.status == 401:
                        raise
                    intervals.append(ReleaseInterval(
                        release, previous, status="ignored_compare_404" if error.status == 404 else "error",
                        error_detail=str(error), error_status=error.status))
                except ValueError as error:
                    intervals.append(ReleaseInterval(release, previous, status="error", error_detail=str(error)))
        previous = release
    return tuple(intervals)
