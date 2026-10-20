"""Recupera apenas predecessoras de fronteira, preservando o plano inicial (#66)."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

from .cache import ResilientClient
from .commits import collect_commits_between
from .git_context import GitRepository
from .github_client import APIError, GitHubClient
from .gold_sample import timestamp
from .s02_enrichment import TAGS_QUERY
from .s03_collect import LayeredCache, graph_batch, pair_key, save
from .temporal import parse_commit


def cached_tags(cache, name, start):
    """Somente páginas do snapshot S02; não consulta novamente o catálogo de tags."""
    owner, repo = name.split("/")
    after, refs, cursors = None, {}, set()
    while True:
        cached = cache.get("/graphql", {"query": TAGS_QUERY, "variables": {"owner": owner, "name": repo, "after": after}})
        if cached is None:
            return None
        connection = cached.data["data"]["repository"]["refs"]
        for ref in connection["nodes"]:
            target = ref["target"]
            while "target" in target:
                target = target["target"]
            if target.get("authoredDate") and timestamp(target["authoredDate"]) < start:
                refs[ref["name"]] = dict(tag_name=ref["name"], date=target["authoredDate"], sha=target["oid"], identifier=ref["name"])
        if not connection["pageInfo"]["hasNextPage"]:
            return list(refs.values())
        after = connection["pageInfo"]["endCursor"]
        if not after or after in cursors:
            raise ValueError("Snapshot de tags com paginação circular/incompleta.")
        cursors.add(after)


def choose(client, repository, candidates, git=None):
    name, head = repository["full_name"], repository["default_branch_sha"]
    for row in sorted(candidates, key=lambda r: (timestamp(r["date"]), r["identifier"]), reverse=True):
        row = dict(row)
        if not row.get("sha"):
            row["sha"] = parse_commit(client.get(f"/repos/{name}/commits/" + quote(row["tag_name"], safe="")).data).sha
        if git:
            on_branch = row["sha"] in git.ancestors
        else:
            data = client.get(f"/repos/{name}/compare/{row['sha']}...{head}", {"per_page": 1, "page": 2}).data
            if data.get("status") not in ("ahead", "identical", "behind", "diverged"):
                raise APIError("Ancestralidade de predecessora não comprovada.")
            on_branch = data["status"] in ("ahead", "identical")
        if on_branch:
            return row
    return None


def run(raw=Path("data/raw/s03"), old=Path("data/raw/s02"), workers=4):
    patch_path = raw / "predecessors/patch.json"
    if patch_path.exists():
        return json.loads(patch_path.read_text(encoding="utf-8"))
    plan = json.loads((raw / "plan.json").read_text(encoding="utf-8"))
    cache = LayeredCache(raw / "predecessors/cache", old)
    client = ResilientClient(GitHubClient(), cache)
    start = timestamp(plan["window"]["start_date"] + "T00:00:00Z")
    repositories = {r["full_name"]: r for r in plan["repositories"]}
    first = {}
    for event in plan["events"]:
        key = event["variant"], event["full_name"]
        if key not in first:
            first[key] = event
    git_repos = {}
    git_path = old / "git/web-platform-tests--wpt.git"
    if git_path.exists():
        name = "web-platform-tests/wpt"
        git_repos[name] = GitRepository(git_path, name, repositories[name]["default_branch_sha"])

    def work(item):
        (variant, name), event = item
        repo = repositories[name]
        previous = plan["pairs"].get(event["pair_key"], {})
        entry = {"variant": variant, "full_name": name, "first_identifier": event["identifier"], "status": "unchanged"}
        try:
            if variant == "C2":
                payload = json.loads((old / "checkpoints" / (repo["repository_id"] + ".json")).read_text(encoding="utf-8"))
                minimum = timestamp(previous["base_date"]) if previous else timestamp("1970-01-01T00:00:00Z")
                candidates = [dict(tag_name=r["tag_name"], date=r["published_at"], sha="", identifier=str(r["id"]))
                    for r in payload["raw_releases"] if r["prerelease"] and not r["draft"] and r["published_at"]
                    and minimum < timestamp(r["published_at"]) < start]
            elif name in git_repos:
                snapshot = json.loads((old / "git/web-platform-tests--wpt_tags_snapshot.json").read_text(encoding="utf-8"))
                candidates = [dict(tag_name=r["ref"][len("refs/tags/"):], date=r["author_date"], sha=r["commit_sha"], identifier=r["ref"])
                              for r in snapshot["refs"] if timestamp(r["author_date"]) < start and r["on_default_branch"]]
            else:
                candidates = cached_tags(cache, name, start)
            if candidates is None:
                return None, None, {**entry, "status": "history_unavailable_first_interval_excluded"}
            predecessor = choose(client, repo, candidates, git_repos.get(name))
            if predecessor is None:
                return None, None, {**entry, "status": "no_earlier_eligible_candidate"}
            key = pair_key(name, predecessor["sha"], event["sha"])
            updated = {**event, "pair_key": key, "previous_identifier": predecessor["identifier"]}
            entry.update(status="predecessor_verified", previous_identifier=predecessor["identifier"], base_sha=predecessor["sha"], pair_key=key)
            if key in plan["pairs"]:
                return updated, None, entry
            pair = dict(full_name=name, base=predecessor["sha"], head=event["sha"], base_tag=predecessor["tag_name"], head_tag=event["tag_name"],
                        base_date=predecessor["date"], head_date=event["date"], source_release_id="", expected_commits=None,
                        source="identical" if predecessor["sha"] == event["sha"] else "complementary")
            if pair["source"] != "identical":
                path = raw / "predecessors/intervals" / (key + ".json")
                if not path.exists():
                    try:
                        try:
                            value = graph_batch(client, name, [(key, pair)]).get(key)
                        except APIError:
                            value = None
                        if value is None:
                            commits = collect_commits_between(client, name, pair["base"], pair["head"])
                            value = dict(status="complete", transport="rest_complete", commits=[asdict(c) for c in commits])
                    except (APIError, ValueError) as error:
                        status = getattr(error, "status", None)
                        value = dict(status="ignored_compare_404" if status == 404 else "error",
                                     commits=[], error=str(error), error_status=status)
                    save(path, {**pair, **value, "url": f"https://api.github.com/repos/{name}/compare/{pair['base']}...{pair['head']}"})
            return updated, (key, pair), entry
        except (APIError, ValueError) as error:
            # --- ALTERAÇÃO: Não salva erros transientes (5xx) no patch, permitindo retentativa ---
            status = getattr(error, "status", None)
            if status is not None and status >= 500:
                return None, None, {**entry, "status": "transient_error", "error": str(error)}
            
            # Não usar uma predecessora estável possivelmente errada no C2.
            updated = {**event, "pair_key": "", "previous_identifier": "", "predecessor_unavailable": True}
            return updated, None, {**entry, "status": "predecessor_unavailable_first_interval_excluded", "error": str(error)}

    events, pairs, audit = [], {}, []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for updated, pair, entry in pool.map(work, first.items()):
            if updated:
                events.append(updated)
            if pair:
                pairs[pair[0]] = pair[1]
            audit.append(entry)
            
    # --- ALTERAÇÃO: Aborta a gravação do patch se houve erro transiente de API ---
    if any(e.get("status") == "transient_error" for e in audit):
        raise RuntimeError("Transient API errors during predecessor collection: " + str([e.get("error") for e in audit if e.get("status") == "transient_error"]))

    patch = dict(events=events, pairs=pairs, audit=audit)
    save(patch_path, patch)
    print(f"PREDECESSORS checked={len(audit)} updated={len(events)} new_pairs={len(pairs)}", flush=True)
    return patch


if __name__ == "__main__":
    run()