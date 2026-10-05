"""Verificação pequena da API real; não usa nem define a janela do estudo.

Executar da raiz: python -m scripts.smoke_fernanda
Não produz dataset ou métricas do estudo; testa contratos REST com poucas
chamadas públicas. Os testes automatizados continuam totalmente offline.
"""

import json
from urllib.parse import quote

from src.commits import ReleaseInterval, collect_commits_between
from src.github_client import GitHubClient
from src.metrics import calculate_lead_time
from src.temporal import Release, parse_commit, utc_datetime


def main():
    client = GitHubClient()
    root = "/repos/pallets/itsdangerous"
    metadata = client.get(root).data
    branch = parse_commit(client.get(root + "/commits/" + quote(metadata["default_branch"], safe="")).data)
    raw = client.get(root + "/releases", {"per_page": 2, "page": 1}).data
    releases = []
    for item in raw:
        if item["draft"] or item["prerelease"]:
            continue
        commit = parse_commit(client.get(root + "/commits/" + quote(item["tag_name"], safe="")).data)
        ancestry = client.get(root + "/compare/" + commit.sha + "..." + branch.sha,
                              {"per_page": 1, "page": 1}).data["status"]
        if ancestry not in ("ahead", "identical"):
            raise ValueError("Release do smoke fora da default branch.")
        releases.append(Release(item["id"], item["tag_name"], item["published_at"], commit.sha))
    releases.sort(key=lambda r: utc_datetime(r.published_at))
    if len(releases) != 2:
        raise ValueError("Smoke exige duas releases públicas estáveis.")
    commits = collect_commits_between(client, "pallets/itsdangerous", releases[0].commit_sha, releases[1].commit_sha)
    lead_time = calculate_lead_time((ReleaseInterval(releases[1], releases[0], commits),))
    tags = client.get(root + "/tags", {"per_page": 2, "page": 1}).data
    tag_commit = parse_commit(client.get(root + "/commits/" + tags[0]["commit"]["sha"]).data)
    print(json.dumps({"kind": "API_contract_smoke_not_study_results", "repository": metadata["full_name"],
                      "default_branch": metadata["default_branch"], "base": releases[0].tag_name,
                      "head": releases[1].tag_name, "commits_collected": len(commits),
                      "lead_time_calculation": "ok" if lead_time.by_commit.count else "empty",
                      "tag_author_date_resolved": bool(tag_commit.author_date)}, indent=2))


if __name__ == "__main__":
    main()
