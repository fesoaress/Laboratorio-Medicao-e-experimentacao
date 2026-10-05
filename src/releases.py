"""Issue #40: releases/tags paginadas e pertencimento à branch principal."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from .github_client import APIError, Client, iter_pages
from .temporal import ObservationWindow, Release, Tag, parse_commit, repository_path, utc_datetime


@dataclass(frozen=True)
class ReleaseCollection:
    default_branch: str
    default_branch_sha: str
    history: tuple[Release, ...]
    tags: tuple[Tag, ...]
    excluded_releases: tuple[dict, ...]

    def in_window(self, window: ObservationWindow, *, include_prereleases: bool = False) -> tuple[Release, ...]:
        return tuple(r for r in self.history if window.contains(r.published_at)
                     and (include_prereleases or not r.prerelease))


def collect_releases_and_tags(
    client: Client, full_name: str, default_branch: str, window: ObservationWindow,
    *, per_page: int = 100,
) -> ReleaseCollection:
    """Preserva histórico anterior; filtra por published_at e ancestralidade.

    target_commitish é apenas metadado: pode estar desatualizado se a tag já
    existia. Compara o SHA real da tag com um snapshot da default branch.
    """
    root = repository_path(full_name)
    if not isinstance(default_branch, str) or not default_branch.strip():
        raise ValueError("default_branch ausente.")
    if type(per_page) is not int or not 1 <= per_page <= 100:
        raise ValueError("per_page deve estar entre 1 e 100.")
    branch = parse_commit(client.get(root + "/commits/" + quote(default_branch, safe="")).data)
    resolved = {}
    membership = {branch.sha: True}

    def resolve(ref):
        if not isinstance(ref, str) or not ref:
            raise ValueError("Referência de tag ausente.")
        if ref not in resolved:
            resolved[ref] = parse_commit(client.get(root + "/commits/" + quote(ref, safe="")).data)
            resolved[resolved[ref].sha] = resolved[ref]
        return resolved[ref]

    def on_branch(sha):
        if sha not in membership:
            data = client.get(root + "/compare/" + quote(sha, safe="") + "..." + branch.sha,
                              {"per_page": 1, "page": 1}).data
            if not isinstance(data, dict) or data.get("status") not in ("ahead", "identical", "behind", "diverged"):
                raise ValueError("Resposta inválida ao verificar ancestralidade da tag.")
            membership[sha] = data["status"] in ("ahead", "identical")
        return membership[sha]

    releases, excluded, seen = [], [], {}
    for page in iter_pages(client, root + "/releases", {"per_page": per_page, "page": 1}):
        if not isinstance(page.data, list):
            raise ValueError("Resposta de releases deve ser uma lista.")
        for raw in page.data:
            if not isinstance(raw, dict) or type(raw.get("id")) is not int:
                raise ValueError("Release sem identificador válido.")
            identifier = raw["id"]
            if identifier in seen:
                if seen[identifier] != raw:
                    raise APIError("Release mudou durante a paginação; repita a coleta.")
                continue
            seen[identifier] = raw
            if type(raw.get("draft")) is not bool or type(raw.get("prerelease")) is not bool:
                raise ValueError("Release sem flags draft/prerelease válidas.")
            reason = None
            if raw["draft"]:
                reason = "draft"
            elif utc_datetime(raw.get("published_at")) >= window.end:
                reason = "outside_window_after_end"
            if reason:
                excluded.append({"release_id": identifier, "tag_name": raw.get("tag_name", ""), "reason": reason})
                continue
            commit = resolve(raw.get("tag_name"))
            if not on_branch(commit.sha):
                excluded.append({"release_id": identifier, "tag_name": raw["tag_name"], "reason": "not_on_default_branch"})
                continue
            releases.append(Release(identifier, raw["tag_name"], raw["published_at"], commit.sha,
                                    raw["prerelease"], raw.get("html_url", ""), raw.get("target_commitish", "")))

    tags, seen_tags = [], {}
    for page in iter_pages(client, root + "/tags", {"per_page": per_page, "page": 1}):
        if not isinstance(page.data, list):
            raise ValueError("Resposta de tags deve ser uma lista.")
        for raw in page.data:
            try:
                name, sha = raw["name"], raw["commit"]["sha"]
            except (KeyError, TypeError) as error:
                raise ValueError("Tag sem nome ou SHA.") from error
            if not isinstance(name, str) or not name or not isinstance(sha, str) or not sha:
                raise ValueError("Tag sem nome ou SHA.")
            if name in seen_tags:
                if seen_tags[name] != sha:
                    raise APIError("Tag mudou durante a paginação; repita a coleta.")
                continue
            seen_tags[name] = sha
            commit = resolve(sha)
            # O endpoint /tags já fornece o SHA do commit, inclusive em tags anotadas.
            if commit.sha != sha:
                raise ValueError("SHA da tag não corresponde ao commit resolvido.")
            tags.append(Tag(name, sha, commit.author_date, on_branch(sha), window.contains(commit.author_date)))
    releases.sort(key=lambda r: (utc_datetime(r.published_at), r.release_id))
    tags.sort(key=lambda t: (utc_datetime(t.author_date), t.name))
    return ReleaseCollection(default_branch, branch.sha, tuple(releases), tuple(tags), tuple(excluded))
