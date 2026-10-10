"""Fixtures sintéticas exclusivamente em tmp_path; nunca evidência empírica."""

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from src.gold_sample import (
    CONTEXT_FIELDS, HUMAN_FIELDS, LABEL_FIELDS, RATERS, generate, read_csv,
    review_markdown, sample_rows, validate_sample,
)
from src.label_validation import load_sample, validate_labels
from src.pipeline import write_csv
from src.s02 import main

WINDOW = {"start_date": "2025-10-01", "end_date": "2026-10-01"}


@pytest.fixture
def universe():
    repos, releases = [], []
    for index in range(305):
        name = f"fixture/project{index:02d}"
        repos.append({"full_name": name, "status": "selected", "metadata_complete": "True",
                      "has_github_actions": "True", "default_branch": "main", "private": "False",
                      "stargazers_count": "2000", "default_branch_sha": "snapshot", "repository_id": str(index + 1), "valid_workflow_runs": "50",
                      "release_count": "7", "description": "Descrição factual", "language": "Python",
                      "corrective_score": "DO_NOT_EXPOSE"})
        for release in range(7):
            releases.append({"full_name": name, "release_id": str(index * 10 + release + 1),
                             "tag_name": f"v{release}", "published_at": f"2026-01-{release + 1:02d}T00:00:00Z",
                             "prerelease": "False", "in_window": "True", "body": "Notas\ncom vírgula, aspas: \"oi\"",
                             "corrective_release": "DO_NOT_EXPOSE", "score": "DO_NOT_EXPOSE"})
    return repos, releases


@pytest.fixture
def generated(tmp_path, universe):
    repos, releases = universe
    rp, lp = tmp_path / "repositories.csv", tmp_path / "releases.csv"
    write_csv(rp, tuple(repos[0]), repos)
    write_csv(lp, tuple(releases[0]), releases)
    out, report = tmp_path / "gold", tmp_path / "review.md"
    manifest = generate(rp, lp, out, report, **WINDOW)
    return out, report, manifest


def test_sample_exact_deterministic_order_independent(universe):
    repos, releases = universe
    rows, manifest = sample_rows(repos, releases, **WINDOW)
    reordered, _ = sample_rows(list(reversed(repos)), list(reversed(releases)), **WINDOW)
    assert rows == reordered
    assert len(rows) == 300
    assert len({r["repository"] for r in rows}) == 60
    assert set(Counter(r["repository"] for r in rows).values()) == {5}
    assert manifest["eligible_repositories"] == 305
    assert sample_rows(repos, releases, seed=43, **WINDOW)[0] != rows


def test_excludes_short_repositories_without_invention(universe):
    repos, releases = universe
    releases = [r for r in releases if r["full_name"] != repos[0]["full_name"] or r["tag_name"] == "v0"]
    rows, audit = sample_rows(repos, releases, **WINDOW)
    assert audit["eligible_repositories"] == 304
    assert audit["excluded_repositories"][0]["eligible_releases"] == 1
    assert repos[0]["full_name"] not in {row["repository"] for row in rows}


def test_insufficient_universe_rejected(universe):
    repos, releases = universe
    for repo in repos[299:]:
        repo["status"] = "pending_validation"
    with pytest.raises(ValueError, match="299 elegíveis"):
        sample_rows(repos, releases, **WINDOW)


@pytest.mark.parametrize("field,value", [("prerelease", "???"), ("in_window", "False"),
    ("published_at", "2026-01-01"), ("release_id", ""), ("draft", "True"), ("on_default_branch", "False")])
def test_bad_release_evidence_rejected(universe, field, value):
    repos, releases = universe
    releases[0][field] = value
    with pytest.raises(ValueError):
        sample_rows(repos, releases, **WINDOW)


@pytest.mark.parametrize("field,value", [("release_count", "99"), ("valid_workflow_runs", "49"),
    ("metadata_complete", "False"), ("has_github_actions", "False"), ("default_branch", ""),
    ('private', 'True'), ('stargazers_count', '1000'), ('default_branch_sha', ''), ('repository_id', '0')])
def test_selected_contradiction_rejected(universe, field, value):
    repos, releases = universe
    repos[0][field] = value
    with pytest.raises(ValueError):
        sample_rows(repos, releases, **WINDOW)


def test_duplicate_sources_rejected(universe):
    repos, releases = universe
    with pytest.raises(ValueError, match="duplicado"):
        sample_rows(repos + [repos[0]], releases, **WINDOW)
    with pytest.raises(ValueError, match="duplicada"):
        sample_rows(repos, releases + [releases[0]], **WINDOW)


def test_window_and_prereleases_are_filtered(universe):
    repos, releases = universe
    releases[0]["published_at"] = "2026-10-01T00:00:00Z"
    releases[0]["in_window"] = "False"
    releases[1]["prerelease"] = "True"
    repos[0]["release_count"] = "5"
    rows, _ = sample_rows(repos, releases, **WINDOW)
    assert not {"1", "2"}.intersection(row["release_id"] for row in rows)


def test_blind_independent_files_and_review(generated):
    out, report, manifest = generated
    files = [out / f"gold_sample_{r}.csv" for r in RATERS]
    assert len({p.read_bytes() for p in files}) == 1
    for path in files:
        rows = read_csv(path, LABEL_FIELDS, exact=True)
        assert len(rows) == 300
        assert all(all(row[field] == "" for field in HUMAN_FIELDS) for row in rows)
        assert "DO_NOT_EXPOSE" not in path.read_text(encoding="utf-8")
    text = report.read_text(encoding="utf-8")
    assert text.count("\n## ") == 60
    assert text.count("corrective_release: [VAZIO]") == 300
    assert "DO_NOT_EXPOSE" not in text
    assert "Notas" in text and "com vírgula" in text
    assert manifest["seed"] == 42 and len(manifest["sources"]) == 2
    first = read_csv(files[0])
    first[0]["notes"] = "human note"
    write_csv(files[0], LABEL_FIELDS, first)
    assert "human note" not in files[1].read_text(encoding="utf-8")


def test_refuses_overwrite_human_work(generated):
    out, report, manifest = generated
    before = (out / "gold_sample_islayder.csv").read_bytes()
    paths = [Path(source["path"]) for source in manifest["sources"]]
    with pytest.raises(ValueError, match="nunca são sobrescritos"):
        generate(*paths, out, report, **WINDOW)
    assert (out / "gold_sample_islayder.csv").read_bytes() == before


def test_incomplete_counts_and_cli_failure(generated, tmp_path):
    out, _, _ = generated
    path = out / "gold_sample_islayder.csv"
    sample_path = out / "gold_sample.csv"
    result = validate_labels(path, load_sample(sample_path))
    assert result["repositories_evaluated"] == result["releases_evaluated"] == 0
    assert result["repositories_missing"] == 60 and result["releases_missing"] == 300
    assert len(result["errors"]) == 900
    assert main(["validate", str(path), "--sample", str(sample_path), "--json", str(tmp_path / "status.json")]) == 1


def completed_rows(path):
    rows = read_csv(path)
    for row in rows:
        row.update(project_type="library_framework", releases_represent_real_delivery="yes", corrective_release="no")
    return rows


@pytest.mark.parametrize("dimension,value", [("project_type", "library"),
    ("releases_represent_real_delivery", "maybe"), ("corrective_release", "uncertain"), ("corrective_release", "")])
def test_invalid_categories(generated, dimension, value):
    out, _, _ = generated
    path = out / "gold_sample_islayder.csv"
    rows = completed_rows(path)
    rows[0][dimension] = value
    write_csv(path, LABEL_FIELDS, rows)
    result = validate_labels(path, load_sample(out / "gold_sample.csv"))
    assert not result["complete"] and any(dimension in e for e in result["errors"])


def test_alignment_duplicates_missing_and_conflicting_project(generated):
    out, _, _ = generated
    path = out / "gold_sample_islayder.csv"
    rows = completed_rows(path)
    sample = load_sample(out / "gold_sample.csv")
    write_csv(path, LABEL_FIELDS, list(reversed(rows)))
    assert validate_labels(path, sample)["complete"]
    corrupted = deepcopy(rows)
    corrupted[1]["project_type"] = "other"
    corrupted[0]["release_id"] = "99999"
    corrupted[-1] = corrupted[0]
    write_csv(path, LABEL_FIELDS, corrupted)
    errors = " ".join(validate_labels(path, sample)["errors"])
    assert "duplicado" in errors and "ausentes" in errors and "inconsistente" in errors and "alterado" in errors


def test_csv_schema_errors(generated):
    out, _, _ = generated
    path = out / "gold_sample_islayder.csv"
    rows = completed_rows(path)
    write_csv(path, (*LABEL_FIELDS, "heuristic"), [{**r, "heuristic": "yes"} for r in rows])
    assert not validate_labels(path, load_sample(out / "gold_sample.csv"))["complete"]
    path.write_text("item_id,item_id\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cabeçalhos"):
        read_csv(path, LABEL_FIELDS)


def test_canonical_size_and_ids(generated):
    out, _, _ = generated
    rows = read_csv(out / "gold_sample.csv")
    with pytest.raises(ValueError, match="60 repositórios"):
        validate_sample(rows[:-1])
    rows[0]["item_id"] = "wrong"
    with pytest.raises(ValueError, match="Identificador"):
        validate_sample(rows)


def test_cli_missing_real_input(tmp_path):
    assert main(["generate", "--repositories", str(tmp_path / "absent.csv"), "--releases", str(tmp_path / "absent2.csv"),
                 "--start-date", WINDOW["start_date"], "--end-date", WINDOW["end_date"]]) == 1


def test_factual_commit_context(universe):
    repos, releases = universe
    commits = [{"full_name": r["full_name"], "release_id": r["release_id"], "sha": "abc", "message": "Original commit",
                "html_url": "https://github.com/fixture/commit/abc", "score": "DO_NOT_EXPOSE"} for r in releases]
    intervals = [{"full_name": r["full_name"], "release_id": r["release_id"], "base_sha": "base", "head_sha": "head"} for r in releases]
    rows, _ = sample_rows(repos, releases, commits=commits, intervals=intervals, **WINDOW)
    assert all(row["compare_url"].endswith("/compare/base...head") for row in rows)
    assert all(json.loads(row["commits_context"])[0]["message"] == "Original commit" for row in rows)
    assert "DO_NOT_EXPOSE" not in review_markdown(rows)


def test_missing_window_or_invalid_repository(universe):
    repos, releases = universe
    with pytest.raises(ValueError, match="janela oficial"):
        sample_rows(repos, releases, start_date="", end_date="")
    repos[0]["full_name"] = "invalid"
    with pytest.raises(ValueError, match="Identidade"):
        sample_rows(repos, releases, **WINDOW)


def test_unknown_repository_and_duplicate_interval(universe):
    repos, releases = universe
    unknown = deepcopy(releases)
    unknown[0]["full_name"] = "unknown/repo"
    with pytest.raises(ValueError, match="sem repositório"):
        sample_rows(repos, unknown, **WINDOW)
    interval = {"full_name": repos[0]["full_name"], "release_id": "1"}
    with pytest.raises(ValueError, match="Intervalo duplicado"):
        sample_rows(repos, releases, intervals=[interval, interval], **WINDOW)


def test_csv_malformed_row_and_duplicate_canonical(generated, tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text("a,b\n1,2,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="número de colunas"):
        read_csv(path, ("a", "b"))
    rows = read_csv(generated[0] / "gold_sample.csv")
    with pytest.raises(ValueError, match="duplicado"):
        validate_sample(rows + [rows[0]])


def test_cli_generate_with_optional_context_and_listing(generated, tmp_path):
    out, _, manifest = generated
    sources = [source["path"] for source in manifest["sources"]]
    releases = read_csv(Path(sources[1]))
    commits = [{"full_name": r["full_name"], "release_id": r["release_id"], "sha": "abc", "message": "original"} for r in releases]
    intervals = [{"full_name": r["full_name"], "release_id": r["release_id"], "base_sha": "base", "head_sha": "head"} for r in releases]
    cp, ip = tmp_path / "commits.csv", tmp_path / "intervals.csv"
    write_csv(cp, tuple(commits[0]), commits)
    write_csv(ip, tuple(intervals[0]), intervals)
    dest, report = tmp_path / "cli", tmp_path / "cli.md"
    assert main(["generate", "--repositories", sources[0], "--releases", sources[1],
                 "--commits", str(cp), "--intervals", str(ip), "--start-date", WINDOW["start_date"],
                 "--end-date", WINDOW["end_date"], "--output-dir", str(dest), "--report", str(report)]) == 0
    text = report.with_name("cli_selected_releases.txt").read_text(encoding="utf-8")
    assert text.count("REPOSITÓRIO ") == 60
    assert "REPOSITÓRIO 01/60" in text and "REPOSITÓRIO 60/60" in text
    assert len(read_csv(dest / "gold_sample.csv")) == 300
    assert len(json.loads((dest / "sampling_manifest.json").read_text(encoding="utf-8"))["sources"]) == 4


def test_cli_validate_success_and_input_protection(generated):
    out, _, _ = generated
    path, sample = out / "gold_sample_islayder.csv", out / "gold_sample.csv"
    write_csv(path, LABEL_FIELDS, completed_rows(path))
    assert main(["validate", str(path), "--sample", str(sample)]) == 0
    before = path.read_bytes()
    assert main(["validate", str(path), "--sample", str(sample), "--json", str(path)]) == 1
    assert path.read_bytes() == before


def test_gzip_context_accepts_large_fields_and_filters_selected_items(tmp_path):
    import gzip
    from src.gold_sample import sha256
    import hashlib
    path = tmp_path / 'commits.csv'
    rows = [{'full_name': 'fixture/a', 'release_id': '1', 'message': 'x' * 150000},
            {'full_name': 'fixture/b', 'release_id': '2', 'message': 'unselected factual context'}]
    write_csv(path, tuple(rows[0]), rows)
    compressed = path.with_suffix('.csv.gz')
    with gzip.open(compressed, 'wb') as output:
        output.write(path.read_bytes())
    selected = read_csv(compressed, ('full_name', 'release_id'), selected_items={('fixture/a', '1')})
    assert selected == rows[:1]
    assert sha256(compressed) == hashlib.sha256(compressed.read_bytes()).hexdigest()
    path.write_text('full_name,release_id,message\nfixture/a,1,ok\nfixture/b,2\n', encoding='utf-8')
    with pytest.raises(ValueError, match='número de colunas'):
        read_csv(path, selected_items={('fixture/a', '1')})


def test_duplicate_repository_ids_and_partial_collection_block_generation(universe, tmp_path):
    repos, releases = universe
    repos[1]['repository_id'] = repos[0]['repository_id']
    with pytest.raises(ValueError, match='ID de repositório'):
        sample_rows(repos, releases, **WINDOW)
    repos[1]['repository_id'] = '2'
    for repo in repos[299:]:
        repo['status'] = 'pending_validation'
    rp, lp = tmp_path / 'repositories.csv', tmp_path / 'releases.csv'
    write_csv(rp, tuple(repos[0]), repos)
    write_csv(lp, tuple(releases[0]), releases)
    with pytest.raises(ValueError, match='299 elegíveis'):
        generate(rp, lp, tmp_path / 'gold', tmp_path / 'review.md', **WINDOW)
    assert not (tmp_path / 'gold').exists() and not (tmp_path / 'review.md').exists()


def test_generate_reaudits_real_collection_manifest_before_writing(tmp_path):
    from tests.test_s02_audit import dataset
    dataset(tmp_path)
    rp, lp = tmp_path / 'repositories_final_s02.csv', tmp_path / 'releases_s01.csv'
    with pytest.raises(ValueError, match='Auditoria da coleta'):
        generate(rp, lp, tmp_path / 'gold', tmp_path / 'review.md', **WINDOW)
    assert not (tmp_path / 'gold').exists()


def test_generate_checks_audited_window_and_canonical_sources(universe, tmp_path):
    from tests.test_s02_audit import dataset
    dataset(tmp_path, 300)
    rp, lp = tmp_path / 'repositories_final_s02.csv', tmp_path / 'releases_s01.csv'
    with pytest.raises(ValueError, match='Janela/fontes'):
        generate(rp, lp, tmp_path / 'gold', tmp_path / 'review.md', start_date='2024-10-01', end_date='2025-10-01')
    with pytest.raises(ValueError, match='Janela/fontes'):
        generate(tmp_path / 'wrong.csv', lp, tmp_path / 'gold', tmp_path / 'review.md', **WINDOW)
    # Mantem os runs reais da fixture de auditoria, enriquecendo as duas fontes
    # sinteticas com contexto completo para provar a integracao bem sucedida.
    repos, releases = universe
    repos = repos[:300]
    releases = [r for r in releases if r['full_name'] in {p['full_name'] for p in repos}]
    from src.s02_audit import read_rows
    runs_path = tmp_path / 'workflow_runs_s02.csv'
    runs = read_rows(runs_path)
    mapping = {f'fixture/project{i}': repos[i]['full_name'] for i in range(300)}
    for run in runs:
        run['full_name'] = mapping[run['full_name']]
    write_csv(runs_path, tuple(runs[0]), runs)
    write_csv(rp, tuple(repos[0]), repos)
    write_csv(lp, tuple(releases[0]), releases)
    result = generate(rp, lp, tmp_path / 'gold', tmp_path / 'review.md', **WINDOW)
    assert result['collection_verification']['ready_for_gold_sample']
