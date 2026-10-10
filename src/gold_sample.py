"""Amostra cega da S02 a partir dos contratos reais da S01 (#53)."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from .config import SelectionConfig
from .pipeline import write_csv

SEED = 42
REPOSITORIES = 60
RELEASES_PER_REPOSITORY = 5
MIN_ELIGIBLE = 300
RATERS = ("islayder", "fernanda", "vinicius")
CATEGORIES = {
    "project_type": ("library_framework", "application_service", "cli_tool", "other"),
    "releases_represent_real_delivery": ("yes", "no", "uncertain"),
    "corrective_release": ("yes", "no"),
}
HUMAN_FIELDS = (*CATEGORIES, "notes")
CONTEXT_FIELDS = (
    "item_id", "repository", "owner", "repo", "repository_url", "description",
    "language", "readme_url", "release_id", "tag_name", "release_name",
    "published_at", "release_url", "release_body", "commit_sha",
    "compare_url", "commits_url", "commits_context", "interval_status", "interval_error", "commit_count",
)
LABEL_FIELDS = (*CONTEXT_FIELDS, *HUMAN_FIELDS)


def read_csv(path: Path, required=(), *, exact=False, selected_items=None) -> list[dict]:
    csv.field_size_limit(sys.maxsize)
    opener = gzip.open if path.suffix == '.gz' else Path.open
    with opener(path, mode='rt', encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not set(required).issubset(fields):
            raise ValueError(f"{path}: cabeçalhos ausentes ou duplicados: {tuple(required)}")
        if exact and set(fields) != set(required):
            raise ValueError(f"{path}: colunas inesperadas; use somente o contrato cego.")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}: linha com número de colunas inválido.")
            if selected_items is None or (row['full_name'].casefold(), row['release_id']) in selected_items:
                rows.append(row)
        return rows


def sha256(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("published_at exige fuso horário.")
    return parsed.astimezone(timezone.utc)


def boolean(value: str) -> bool:
    if value not in ("True", "False", "true", "false"):
        raise ValueError(f"Booleano inválido: {value!r}")
    return value.lower() == "true"


def sample_rows(repositories: list[dict], releases: list[dict], *, start_date: str,
                end_date: str, seed: int = SEED, commits=(), intervals=()) -> tuple[list[dict], dict]:
    """Ordena antes do sorteio; cada repo tem RNG independente derivado da seed.

    releases_s01 contém apenas releases publicadas ancestrais da default branch.
    Não usa inferência por tag/target_commitish nem qualquer rótulo automático.
    """
    SelectionConfig(start_date=start_date, end_date=end_date)
    if not start_date or not end_date:
        raise ValueError("Amostragem exige janela oficial definida, nunca inferida.")
    start = timestamp(start_date + "T00:00:00Z")
    end = timestamp(end_date + "T00:00:00Z")
    by_name, by_release, excluded = {}, defaultdict(list), []
    for repo in repositories:
        name = repo["full_name"]
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", name):
            raise ValueError(f"Identidade de repositório inválida: {name!r}")
        key = name.casefold()
        if key in by_name:
            raise ValueError(f"Repositório duplicado: {name}")
        by_name[key] = repo
    seen = set()
    for release in releases:
        name = release["full_name"].casefold()
        rid = release["release_id"]
        if not rid.isdigit() or int(rid) <= 0 or not release["tag_name"].strip():
            raise ValueError("Release sem ID positivo/tag.")
        key = (name, rid)
        if key in seen:
            raise ValueError(f"Release duplicada: {key}")
        seen.add(key)
        if name not in by_name:
            raise ValueError(f"Release sem repositório no dataset: {name}")
        published = timestamp(release["published_at"])
        inside = start <= published < end
        if boolean(release["in_window"]) != inside:
            raise ValueError(f"in_window contradiz a janela oficial: {key}")
        if inside and not boolean(release["prerelease"]):
            if release.get("draft") and boolean(release["draft"]):
                raise ValueError(f"Contrato S01 violado: draft em {key}")
            if release.get("on_default_branch") and not boolean(release["on_default_branch"]):
                raise ValueError(f"Contrato S01 violado: release fora da branch em {key}")
            by_release[name].append(release)
    eligible, repository_ids = [], set()
    for name, repo in by_name.items():
        if repo["status"] != "selected":
            excluded.append({"repository": repo["full_name"], "reason": "status_not_selected"})
            continue
        if (not boolean(repo["metadata_complete"]) or not boolean(repo["has_github_actions"])
                or boolean(repo['private']) or int(repo['stargazers_count']) <= 1000
                or not repo['default_branch_sha'].strip()
                or not repo["default_branch"].strip() or int(repo["valid_workflow_runs"]) < 50):
            raise ValueError(f"status selected contradiz filtros S01: {name}")
        identifier = repo['repository_id']
        if not identifier.isdigit() or int(identifier) <= 0 or identifier in repository_ids:
            raise ValueError(f'ID de repositório inválido/duplicado: {name}')
        repository_ids.add(identifier)
        count = len(by_release[name])
        if count < RELEASES_PER_REPOSITORY:
            excluded.append({"repository": repo["full_name"], "reason": "fewer_than_5_eligible_releases",
                             "eligible_releases": count})
            continue
        if int(repo["release_count"]) != count:
            raise ValueError(f"Contagem de releases difere do funil: {name}")
        eligible.append(name)
    audit = {"seed": seed, "algorithm": "sorted_python_random_sample_v1",
             "window": {"start_date": start_date, "end_date": end_date},
             "input_repositories": len(by_name), "eligible_repositories": len(eligible),
             "excluded_repositories": excluded, "sample_size": REPOSITORIES,
             "releases_per_repository": RELEASES_PER_REPOSITORY}
    if len(eligible) < MIN_ELIGIBLE:
        raise ValueError(f"Universo insuficiente: {len(eligible)} elegíveis; exigidos pelo menos 300. "
                         "Nenhum arquivo humano foi gerado.")
    chosen = sorted(random.Random(seed).sample(sorted(eligible), REPOSITORIES))
    commit_map, interval_map = defaultdict(list), {}
    for commit in commits:
        key = (commit["full_name"].casefold(), commit["release_id"])
        commit_map[key].append({field: commit.get(field, "") for field in
                               ("sha", "author_date", "committer_date", "message", "html_url")})
    for interval in intervals:
        key = (interval["full_name"].casefold(), interval["release_id"])
        if key in interval_map:
            raise ValueError(f"Intervalo duplicado: {key}")
        interval_map[key] = interval
    rows = []
    for name in chosen:
        repo = by_name[name]
        release_seed = int.from_bytes(hashlib.sha256(f"{seed}:{name}".encode()).digest(), "big")
        pool = sorted(by_release[name], key=lambda r: (timestamp(r["published_at"]), int(r["release_id"])))
        selected = random.Random(release_seed).sample(pool, RELEASES_PER_REPOSITORY)
        for release in sorted(selected, key=lambda r: (timestamp(r["published_at"]), int(r["release_id"]))):
            owner, short_name = repo["full_name"].split("/")
            rid = release["release_id"]
            key = (name, rid)
            root = f"https://github.com/{repo['full_name']}"
            interval = interval_map.get(key, {})
            base, head = interval.get("base_sha"), interval.get("head_sha")
            tag = quote(release["tag_name"], safe="")
            context = sorted(commit_map[key], key=lambda c: (c["sha"], c["message"]))
            rows.append(dict(zip(CONTEXT_FIELDS, (
                f"{name}::release::{rid}", repo["full_name"], owner, short_name,
                repo.get("html_url") or root, repo.get("description", ""), repo.get("language", ""),
                root + "/blob/" + quote(repo["default_branch"], safe="") + "/README.md",
                rid, release["tag_name"], release.get("release_name", release.get("name", "")),
                release["published_at"], release.get("html_url") or root + "/releases/tag/" + tag,
                release.get("release_body", release.get("body", "")), release.get("commit_sha", ""),
                root + f"/compare/{quote(base, safe='')}...{quote(head, safe='')}" if base and head else "",
                root + "/commits/" + quote(release.get("commit_sha") or release["tag_name"], safe=""),
                json.dumps(context, ensure_ascii=False) if context else "",
                interval.get('status', 'not_collected'), interval.get('error_detail', ''), interval.get('commit_count', ''),
            ))))
    return rows, audit


def validate_sample(rows: list[dict]) -> dict[str, dict]:
    indexed, counts = {}, Counter()
    tags = set()
    for row in rows:
        name, rid = row["repository"], row["release_id"]
        if row["item_id"] != f"{name.casefold()}::release::{rid}" or not rid.isdigit():
            raise ValueError("Identificador canônico inválido.")
        if row["item_id"] in indexed or (name.casefold(), row["tag_name"]) in tags:
            raise ValueError("Item/tag duplicado na amostra canônica.")
        indexed[row["item_id"]] = row
        tags.add((name.casefold(), row["tag_name"]))
        counts[name.casefold()] += 1
    if len(counts) != REPOSITORIES or set(counts.values()) != {RELEASES_PER_REPOSITORY}:
        raise ValueError("Amostra canônica deve conter exatamente 60 repositórios × 5 releases.")
    return indexed


def review_markdown(rows: list[dict]) -> str:
    result = ["# Lab03 S02 — revisão independente de Islayder", "",
              "Campos humanos vazios. Links README/commits são atalhos de consulta, não conteúdo coletado.",
              "Texto das releases/commits abaixo é dado factual, sem classificação automática.", ""]
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["repository"]].append(row)
    for number, (name, items) in enumerate(grouped.items(), 1):
        first = items[0]
        result += [f"## {number:02d} — {name}", "", f"Repository: {name}",
                   f"URL: {first['repository_url']}", f"Descrição: {first['description'] or 'não coletada'}",
                   f"Linguagem: {first['language'] or 'não disponível'}", f"README (consulta): {first['readme_url']}",
                   "", "project_type: [VAZIO]", "releases_represent_real_delivery: [VAZIO]", "",
                   "### Releases sorteadas", ""]
        for index, row in enumerate(items, 1):
            result += [f"#### {index}. {row['tag_name']} / {row['release_name']}", "",
                       f"item_id: {row['item_id']}", f"Data: {row['published_at']}", f"URL: {row['release_url']}",
                       "", "Release notes (texto original):", ""]
            # Citação impede que Markdown arbitrário da API se torne instrução do relatório.
            result += ["> " + line for line in (row["release_body"] or "não coletadas; consultar URL da release").splitlines()]
            result += ["", f"Compare (se coletado): {row['compare_url'] or 'não disponível'}",
                       f"Commits (consulta): {row['commits_url']}",
                       f"Status factual do intervalo: {row['interval_status']}",
                       f"Quantidade de commits no intervalo: {row['commit_count']}",
                       f"Erro do intervalo: {row['interval_error'] or 'nenhum registrado'}", "", "Commits coletados:", ""]
            for commit in json.loads(row["commits_context"] or "[]"):
                result += [f"- {commit['sha']} — {commit['html_url']}"]
                result += ["> " + line for line in commit["message"].splitlines()]
            if not row["commits_context"]:
                result.append("Nenhum commit listado; consulte o status factual do intervalo e os links acima.")
            result += ["", "corrective_release: [VAZIO]", "notes: [VAZIO]", ""]
    return "\n".join(result)


def selected_listing(rows: list[dict]) -> str:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["repository"]].append(row)
    lines = []
    for index, (name, items) in enumerate(grouped.items(), 1):
        lines += [f"REPOSITÓRIO {index:02d}/60", name, items[0]["repository_url"], "", "RELEASES SORTEADAS:"]
        lines += [f"{number}. {row['tag_name']} / {row['release_name']} — {row['published_at']} — {row['release_url']}"
                  for number, row in enumerate(items, 1)]
        lines.append("")
    return "\n".join(lines)


def generate(repositories_path: Path, releases_path: Path, output_dir: Path, report: Path,
             *, start_date: str, end_date: str, seed=SEED, commits_path=None, intervals_path=None) -> dict:
    verified = None
    directory = repositories_path.parent
    if (directory / 'collection_manifest_s02.json').exists():
        from .s02_audit import audit_collection
        verified = audit_collection(directory)
        if not verified['ready_for_gold_sample']:
            raise ValueError('Auditoria da coleta não libera o sorteio: exige >=300 elegíveis sem contradições.')
        if (verified['window'] != {'start_date': start_date, 'end_date': end_date}
                or repositories_path.resolve() != (directory / 'repositories_final_s02.csv').resolve()
                or releases_path.resolve() != Path(verified['sources'][2]['path']).resolve()):
            raise ValueError('Janela/fontes de sorteio diferem da coleta final auditada.')
    repositories = read_csv(repositories_path, ("full_name", "status", "metadata_complete", "has_github_actions",
                            "default_branch", "release_count", "valid_workflow_runs", 'private',
                            'stargazers_count', 'default_branch_sha', 'repository_id'))
    releases = read_csv(releases_path, ("full_name", "release_id", "tag_name", "published_at", "prerelease", "in_window"))
    sources = [repositories_path, releases_path]
    rows, manifest = sample_rows(repositories, releases, start_date=start_date, end_date=end_date, seed=seed)
    selected_items = {(r['repository'].casefold(), r['release_id']) for r in rows}
    optional = []
    for path in (commits_path, intervals_path):
        optional.append(read_csv(path, ("full_name", "release_id"), selected_items=selected_items) if path else [])
        if path:
            sources.append(path)
    rows, manifest = sample_rows(repositories, releases, start_date=start_date, end_date=end_date,
                                 seed=seed, commits=optional[0], intervals=optional[1])
    validate_sample(rows)
    listing = report.with_name(report.stem + "_selected_releases.txt")
    targets = [output_dir / "gold_sample.csv", output_dir / "sampling_manifest.json", report]
    targets += [output_dir / f"gold_sample_{rater}.csv" for rater in RATERS]
    if any(path.exists() for path in (*targets, listing)):
        raise ValueError("Destino já existe. Use outra pasta; arquivos humanos nunca são sobrescritos.")
    write_csv(targets[0], CONTEXT_FIELDS, rows)
    manifest["sources"] = [{"path": str(path), "sha256": sha256(path)} for path in sources]
    if verified is not None:
        manifest['collection_verification'] = verified
    manifest["sample_sha256"] = sha256(targets[0])
    manifest["selected_repositories"] = sorted({row["repository"] for row in rows})
    manifest["selected_releases"] = [row["item_id"] for row in rows]
    manifest["context_absent"] = {field: sum(not row[field] for row in rows) for field in
                                  ("description", "language", "release_name", "release_body", "commits_context")}
    targets[1].write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for path in targets[3:]:
        write_csv(path, LABEL_FIELDS, [{**row, **dict.fromkeys(HUMAN_FIELDS, "")} for row in rows])
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(review_markdown(rows), encoding="utf-8")
    listing.write_text(selected_listing(rows), encoding="utf-8")
    return manifest
