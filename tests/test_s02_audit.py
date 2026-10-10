"""Dados sintéticos somente em tmp_path; não são usados na coleta real."""

import json

import pytest

from src.pipeline import write_csv
from src.s02_audit import audit_collection, main, read_rows


def dataset(path, n=1):
    repositories, releases, runs = [], [], []
    for i in range(n):
        name = f'fixture/project{i}'
        repositories.append({'repository_id': str(i + 1), 'full_name': name, 'status': 'selected',
            'metadata_complete': 'True', 'has_github_actions': 'True', 'private': 'False',
            'default_branch': 'main', 'default_branch_sha': 'snapshot', 'stargazers_count': '2000',
            'release_count': '5', 'valid_workflow_runs': '50'})
        releases.extend({'full_name': name, 'release_id': str(i * 10 + j + 1),
                         'published_at': '2026-01-01T00:00:00Z', 'prerelease': 'False', 'in_window': 'True'} for j in range(5))
        runs.extend({'full_name': name, 'id': str(i * 100 + j + 1), 'conclusion': 'success',
                     'status_class': 'success', 'created_at': '2026-01-01T00:00:00Z',
                     'event': 'push', 'head_branch': 'main'} for j in range(50))
    path.mkdir(exist_ok=True)
    (path / 'collection_manifest_s02.json').write_text(json.dumps({
        'window': {'start_date': '2025-10-01', 'end_date': '2026-10-01'},
        'target': 300, 'target_met': n >= 300, 'final_sample': n}), encoding='utf-8')
    for filename, rows in zip(('repositories_final_s02.csv', 'releases_s01.csv', 'workflow_runs_s02.csv'),
                              (repositories, releases, runs)):
        write_csv(path / filename, tuple(rows[0]), rows)
    return repositories, releases, runs


def test_final_collection_gate_requires_300_verified_repositories(tmp_path):
    dataset(tmp_path, 300)
    result = audit_collection(tmp_path)
    assert result['ready_for_gold_sample'] and not result['errors']
    assert result['eligible_repositories'] == 300 and result['stable_releases_in_window'] == 1500
    assert result['valid_workflow_runs'] == result['workflow_runs'] == 15000
    assert len(result['sources']) == 4 and all(len(s['sha256']) == 64 for s in result['sources'])
    assert main([str(tmp_path)]) == 0


def test_partial_audit_never_releases_gold_sample(tmp_path):
    dataset(tmp_path)
    assert main([str(tmp_path)]) == 1
    assert main([str(tmp_path), '--allow-partial']) == 0
    result = json.loads((tmp_path / 'collection_audit_s02.json').read_text())
    assert result['status'] == 'verified_partial_collection' and not result['ready_for_gold_sample']


@pytest.mark.parametrize('dimension,key,value,expected', [
    (0, 'private', 'True', 'contradictory_eligibility'),
    (0, 'default_branch_sha', '', 'contradictory_eligibility'),
    (0, 'stargazers_count', '1000', 'contradictory_eligibility'),
    (0, 'repository_id', '', 'duplicate_or_missing_repository_id'),
    (1, 'in_window', 'False', 'contradictory_release_window'),
    (1, 'prerelease', 'invalid', 'invalid_prerelease_flag'),
    (1, 'full_name', 'unknown/repo', 'unaligned_or_duplicate_release'),
    (1, 'published_at', '2026-10-01T00:00:00Z', 'count_mismatch'),
    (2, 'event', 'pull_request', 'unaligned_duplicate_or_invalid_run'),
    (2, 'head_branch', 'develop', 'unaligned_duplicate_or_invalid_run'),
    (2, 'conclusion', 'cancelled', 'count_mismatch'),
    (2, 'status_class', '', 'unaligned_duplicate_or_invalid_run'),
])
def test_collection_audit_rejects_contradictory_evidence(tmp_path, dimension, key, value, expected):
    rows = dataset(tmp_path)
    rows[dimension][0][key] = value
    filename = ('repositories_final_s02.csv', 'releases_s01.csv', 'workflow_runs_s02.csv')[dimension]
    write_csv(tmp_path / filename, tuple(rows[dimension][0]), rows[dimension])
    result = audit_collection(tmp_path)
    assert not result['ready_for_gold_sample']
    assert any(expected in error for error in result['errors'])


def test_collection_audit_rejects_duplicate_repository_and_manifest_contradiction(tmp_path):
    rows, _, _ = dataset(tmp_path)
    write_csv(tmp_path / 'repositories_final_s02.csv', tuple(rows[0]), rows * 2)
    result = audit_collection(tmp_path)
    assert any('duplicate_repository' in e for e in result['errors'])
    assert 'contradictory_manifest_target_or_sample' in result['errors']


@pytest.mark.parametrize('contents', ['', 'a,a\n1,2\n', 'a,b\n1\n'])
def test_audit_csv_shape_errors_are_explicit(tmp_path, contents):
    path = tmp_path / 'bad.csv'
    path.write_text(contents)
    with pytest.raises(ValueError):
        read_rows(path)


def test_audit_cli_missing_sources_is_failure(tmp_path):
    assert main([str(tmp_path)]) == 1


def test_compressed_snapshots_are_verified_and_work_after_clone(tmp_path):
    import gzip
    dataset(tmp_path, 300)
    for name in ('releases_s01.csv', 'workflow_runs_s02.csv'):
        source = tmp_path / name
        with gzip.open(source.with_suffix('.csv.gz'), 'wb') as output:
            output.write(source.read_bytes())
    result = audit_collection(tmp_path)
    assert result['ready_for_gold_sample']
    assert all(r['path'].endswith('.csv.gz') for r in result['sources'][2:])
    (tmp_path / 'releases_s01.csv').write_text('stale source', encoding='utf-8')
    with pytest.raises(ValueError, match='desatualizado'):
        audit_collection(tmp_path)
    assert main([str(tmp_path)]) == 1
    (tmp_path / 'releases_s01.csv').unlink()
    (tmp_path / 'workflow_runs_s02.csv').unlink()
    assert audit_collection(tmp_path)['ready_for_gold_sample']
