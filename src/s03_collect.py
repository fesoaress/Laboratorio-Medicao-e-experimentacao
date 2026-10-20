"""Coleta pontual offline/cache/Git/API dos intervalos C2/C3 autorizados (#66)."""

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from threading import Lock

from .cache import CacheStore, ResilientClient
from .commits import collect_commits_between
from .git_context import GitRepository
from .github_client import APIError, GitHubClient
from .gold_sample import read_csv, timestamp
from .graphql_context import graphql
from .s02_enrichment import comparison_query, rest_commit
from .temporal import ObservationWindow, Release, parse_commit


def save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
    temporary.replace(path)


def pair_key(name, base, head):
    return hashlib.sha256(f"{name.casefold()}:{base}:{head}".encode()).hexdigest()


def plan(folder):
    window = ObservationWindow(**json.loads((folder / "collection_manifest_s02.json").read_text(encoding="utf-8"))["window"])
    repos = {r["full_name"].casefold(): r for r in read_csv(folder / "repositories_final_s02.csv")}
    releases = read_csv(folder / "releases_s01.csv.gz") + read_csv(folder / "release_predecessors_s02.csv")
    tags = read_csv(folder / "tags_s01.csv")
    existing = {(r["full_name"].casefold(), r["base_sha"], r["head_sha"]): r
                for r in read_csv(folder / "release_intervals_s01.csv") if r["status"] == "complete"}
    events, pairs = [], {}
    for variant, pool in (("C2", releases), ("C3", tags)):
        grouped = defaultdict(dict)
        for r in pool:
            name = r["full_name"].casefold()
            if name not in repos or (variant == "C3" and r["on_default_branch"] != "True"):
                continue
            identifier = r["release_id"] if variant == "C2" else r["name"]
            grouped[name][identifier] = {"full_name": repos[name]["full_name"], "identifier": identifier,
                "tag_name": r["tag_name"] if variant == "C2" else r["name"],
                "date": r["published_at"] if variant == "C2" else r["author_date"],
                "sha": r["commit_sha"], "body": r.get("release_body", ""),
                "prerelease": r.get("prerelease", "False")}
        for name in sorted(repos):
            ordered = sorted(grouped[name].values(), key=lambda r: (timestamp(r["date"]), int(r["identifier"]) if variant == "C2" else r["identifier"]))
            for i, event in enumerate(ordered):
                if not window.contains(event["date"]):
                    continue
                previous = ordered[i - 1] if i else None
                key = pair_key(name, previous["sha"], event["sha"]) if previous else ""
                events.append({**event, "variant": variant, "pair_key": key,
                               "previous_identifier": previous["identifier"] if previous else ""})
                if not previous or key in pairs:
                    continue
                old = existing.get((name, previous["sha"], event["sha"]))
                pairs[key] = {"full_name": repos[name]["full_name"], "base": previous["sha"], "head": event["sha"],
                    "base_tag": previous["tag_name"], "head_tag": event["tag_name"],
                    "base_date": previous["date"], "head_date": event["date"],
                    "source_release_id": old["release_id"] if old else "",
                    "expected_commits": int(old["commit_count"]) if old else 0 if previous["sha"] == event["sha"] else None,
                    "source": "identical" if previous["sha"] == event["sha"] else "s02_export" if old else "complementary"}
    return {"window": {"start_date": window.start_date, "end_date": window.end_date},
            "repositories": list(repos.values()), "events": events, "pairs": pairs}


class LayeredCache:
    def __init__(self, output, old_root):
        self.output = CacheStore(output)
        self.lock = Lock()
        directories = [old_root / "cache", *(old_root / "retry_cache").glob("*")]
        self.old = [CacheStore(p) for p in directories if p.is_dir()]

    def get(self, path, params):
        for cache in [self.output, *self.old]:
            result = cache.get(path, params)
            if result is not None:
                return result
        return None

    def set(self, path, params, response):
        with self.lock:
            self.output.set(path, params, response)


def graph_batch(client, name, pairs):
    """Usa o comparador próprio existente, confere OIDs e pagina até o total."""
    releases = [(Release(i * 2, p["base_tag"], p["base_date"], p["base"]),
                 Release(i * 2 + 1, p["head_tag"], p["head_date"], p["head"])) for i, (_, p) in enumerate(pairs)]
    query, variables = comparison_query(releases)
    variables.update(zip(("owner", "name"), name.split("/")))
    data = graphql(client.cache, query, variables)["data"]["repository"]
    results = {}
    for i, (key, pair) in enumerate(pairs):
        comparison = (data.get(f"a{i}") or {}).get("compare")
        if not comparison or comparison["baseTarget"]["oid"] != pair["base"] or comparison["headTarget"]["oid"] != pair["head"]:
            continue
        connection = comparison["commits"]
        total = connection["totalCount"]
        if comparison["status"].lower() not in ("ahead", "identical") or total > 1000:
            continue
        commits, cursors = {}, set()
        while True:
            for c in connection["nodes"]:
                value = rest_commit(c)
                if c["oid"] in commits and commits[c["oid"]] != value:
                    raise APIError("Commit mudou entre páginas da coleta complementar.")
                commits[c["oid"]] = value
            if not connection["pageInfo"]["hasNextPage"]:
                break
            cursor = connection["pageInfo"]["endCursor"]
            if not cursor or cursor in cursors:
                raise APIError("Cursor inválido na coleta complementar.")
            cursors.add(cursor)
            query, variables = comparison_query([releases[i]], {0: cursor})
            variables.update(zip(("owner", "name"), name.split("/")))
            continuation = graphql(client.cache, query, variables)["data"]["repository"]["a0"]["compare"]
            if (not continuation or continuation["baseTarget"]["oid"] != pair["base"] or continuation["headTarget"]["oid"] != pair["head"]
                    or continuation["commits"]["totalCount"] != total or continuation["status"] != comparison["status"]):
                raise APIError("Comparação mudou entre páginas.")
            connection = continuation["commits"]
        if len(commits) == total:
            results[key] = {"status": "complete", "transport": "graphql_verified_oids",
                            "commits": [asdict(parse_commit(c)) for c in commits.values()]}
    return results


def collect(folder, raw, old_root, workers=4):
    specification = plan(folder)
    previous_plan = raw / "plan.json"
    if previous_plan.exists() and json.loads(previous_plan.read_text(encoding="utf-8")) != specification:
        raise ValueError("Plano mudou: preserve a coleta anterior em diretório próprio.")
    save(raw / "plan.json", specification)
    cache = LayeredCache(raw / "cache", old_root)
    client = ResilientClient(GitHubClient(), cache)
    pending = defaultdict(list)
    completed = 0
    for key, pair in specification["pairs"].items():
        if pair["source"] != "complementary":
            continue
        path = raw / "intervals" / (key + ".json")
        if path.exists():
            saved = json.loads(path.read_text(encoding="utf-8"))
            if any(saved.get(field) != pair[field] for field in ("full_name", "base", "head")):
                raise ValueError("Checkpoint não corresponde ao par de SHAs planejado.")
            completed += 1
        else:
            pending[pair["full_name"]].append((key, pair))
    total = completed + sum(map(len, pending.values()))
    print(f"COMPLEMENTARY total={total} resumed={completed}", flush=True)
    git_repos = {}
    git_dir = old_root / "git" / "web-platform-tests--wpt.git"
    if git_dir.exists() and "web-platform-tests/wpt" in pending:
        repo = next(r for r in specification["repositories"] if r["full_name"].casefold() == "web-platform-tests/wpt")
        git_repos[repo["full_name"]] = GitRepository(git_dir, repo["full_name"], repo["default_branch_sha"])

    def work(name, batch):
        values = {}
        if name not in git_repos:
            try:
                values = graph_batch(client, name, batch)
            except APIError:
                pass  # REST por SHA preservado é o fallback, não aprovação fictícia.
        for key, pair in batch:
            value = values.get(key)
            if value is None:
                try:
                    adapter = git_repos.get(name)
                    if adapter:
                        data = adapter.compare(pair["base"], pair["head"]).data
                        if data["status"] not in ("ahead", "identical"):
                            raise ValueError("Referências não formam intervalo ancestral.")
                        commits = [asdict(parse_commit(c)) for c in data["commits"]]
                    else:
                        commits = [asdict(c) for c in collect_commits_between(client, name, pair["base"], pair["head"])]
                    value = {"status": "complete", "commits": commits, "transport": "git_objects" if adapter else "rest_complete"}
                except (APIError, ValueError) as error:
                    if getattr(error, "status", None) == 401:
                        raise
                    value = {"status": "ignored_compare_404" if getattr(error, "status", None) == 404 else "error",
                             "commits": [], "error": str(error), "error_status": getattr(error, "status", None)}
            save(raw / "intervals" / (key + ".json"), {**pair, **value,
                 "url": f"https://api.github.com/repos/{name}/compare/{pair['base']}...{pair['head']}"})
        return len(batch)

    batches = [(name, rows[i:i + 8]) for name, rows in pending.items() for i in range(0, len(rows), 8)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(work, name, batch) for name, batch in batches]
        for future in as_completed(futures):
            completed += future.result()
            if completed % 64 < 8 or completed == total:
                print(f"COMPLEMENTARY completed={completed}/{total}", flush=True)
    print("COMPLEMENTARY finished; raw intervals and errors preserved", flush=True)
    return specification


def export_context(folder, raw, output):
    """Snapshot comprimido reproduzível dos pares reutilizados e complementares."""
    specification = json.loads((raw / "plan.json").read_text(encoding="utf-8"))
    correction = raw / "predecessors/patch.json"
    if correction.exists():
        patch = json.loads(correction.read_text(encoding="utf-8"))
        specification["pairs"].update(patch["pairs"])
        changes = {(e["variant"], e["full_name"], e["identifier"]): e for e in patch["events"]}
        specification["events"] = [changes.get((e["variant"], e["full_name"], e["identifier"]), e) for e in specification["events"]]
        specification["predecessor_audit"] = patch["audit"]
    needed = defaultdict(list)
    contexts = {}
    for key, pair in specification["pairs"].items():
        if pair["source"] == "identical":
            contexts[key] = {**pair, "status": "complete", "commits": []}
        elif pair["source"] == "s02_export":
            contexts[key] = {**pair, "status": "complete", "commits": []}
            needed[pair["full_name"].casefold(), pair["source_release_id"]].append(key)
        else:
            path = raw / "intervals" / (key + ".json")
            if not path.exists():
                path = raw / "predecessors/intervals" / (key + ".json")
            contexts[key] = json.loads(path.read_text(encoding="utf-8"))
    with gzip.open(folder / "release_commits_s01.csv.gz", "rt", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            for key in needed.get((row["full_name"].casefold(), row["release_id"]), []):
                contexts[key]["commits"].append({k: row[k] for k in ("sha", "author_date", "committer_date", "message", "html_url")})
    output.parent.mkdir(parents=True, exist_ok=True)
    for context in contexts.values():
        expected = context.get("expected_commits")
        if context["status"] == "complete" and expected is not None and len(context["commits"]) != expected:
            raise ValueError("Export de commits incompleto; não reutilizar como comparação válida.")
    def compressed(path, records):
        with path.open("wb") as handle:
            with gzip.GzipFile(filename="", fileobj=handle, mode="wb", mtime=0) as zipped:
                for record in records:
                    zipped.write((json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8"))
    compressed(output.parent / "variant_plan.json.gz", [specification])
    directory = output.parent / "variant_context"
    directory.mkdir(parents=True, exist_ok=True)
    keys = sorted(contexts)
    for part, offset in enumerate(range(0, len(keys), 1000)):
        compressed(directory / f"part-{part:03}.jsonl.gz", [{"pair_key": key, **contexts[key]} for key in keys[offset:offset+1000]])
    return specification, contexts


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--folder", type=Path, default=Path("data/processed/s02"))
    p.add_argument("--raw", type=Path, default=Path("data/raw/s03"))
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--export-only", action="store_true")
    args = p.parse_args(argv)
    if not args.export_only:
        collect(args.folder, args.raw, Path("data/raw/s02"), args.workers)
    export_context(args.folder, args.raw, Path("data/processed/s03/variant_context.jsonl.gz"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
