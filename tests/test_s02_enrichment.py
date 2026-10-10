import json
from dataclasses import asdict, replace

import pytest

from src import s02_enrichment as enrichment
from src.cache import CacheStore
from src.commits import ReleaseInterval
from src.github_client import APIError, APIResponse
from src.temporal import Release
from tests.test_graphql_s02 import commit
from tests.test_selection import FakeClient
from tests.test_workflow_runs import run
from tests.test_release_collection import raw_release, raw_commit
from src.workflow_runs import parse_workflow_run


def tags_page(nodes, total, next_page=False, cursor='next'):
    return {'data': {'repository': {'refs': {'nodes': nodes, 'totalCount': total,
                                            'pageInfo': {'hasNextPage': next_page, 'endCursor': cursor}}}}}


def test_tags_peel_annotations_filter_dates_and_preserve_ancestry(monkeypatch, window):
    old = {**commit('old'), 'authoredDate': '2024-01-01T00:00:00Z'}
    pages = iter([
        tags_page([{'id': '1', 'name': 'v1', 'target': {'target': {'target': commit('base')}}}], 2, True),
        tags_page([{'id': '2', 'name': 'old', 'target': old}], 2),
        {'data': {'nodes': [{'id': '1', 'compare': {'status': 'DIVERGED',
                                                 'baseTarget': {'oid': 'base'}, 'headTarget': {'oid': 'head'}}}]}},
    ])
    monkeypatch.setattr(enrichment, 'graphql', lambda *a: next(pages))
    tags, scanned = enrichment.collect_tags(None, 'a/b', 'head', window)
    assert scanned == 2 and len(tags) == 1
    assert tags[0].name == 'v1' and not tags[0].on_default_branch and tags[0].in_window


@pytest.mark.parametrize('pages,message', [
    ([tags_page([], 1)], 'incompleta'),
    ([tags_page([], 2, True), tags_page([], 3)], 'Contagem'),
    ([tags_page([{'id': '1', 'name': 'a'}], 1, True),
      tags_page([{'id': '1', 'name': 'b'}], 1)], 'Tag mudou'),
    ([tags_page([], 1, True, None)], 'Cursor'),
    ([tags_page([{'id': '1', 'name': 'v1', 'target': {}}], 1)], 'sem commit'),
    ([tags_page([{'id': '1', 'name': 'v1', 'target': commit()}], 1), {'data': {'nodes': [None]}}], 'Ref ausente'),
    ([tags_page([{'id': '1', 'name': 'v1', 'target': commit()}], 1), {'data': {'nodes': []}}], 'incompleta'),
    ([tags_page([{'id': '1', 'name': 'v1', 'target': commit()}], 1), {'data': {'nodes': [{'id': '1', 'compare': {}}]}}], 'snapshot'),
])
def test_tags_reject_missing_or_mutating_evidence(monkeypatch, window, pages, message):
    responses = iter(pages)
    monkeypatch.setattr(enrichment, 'graphql', lambda *a: next(responses))
    with pytest.raises(APIError, match=message):
        enrichment.collect_tags(None, 'a/b', 'head', window)


def comparison(nodes, total=1, next_page=False, cursor='next', base='base', head='head', status='AHEAD'):
    return {'status': status, 'baseTarget': {'oid': base}, 'headTarget': {'oid': head},
            'commits': {'nodes': nodes, 'totalCount': total,
                        'pageInfo': {'hasNextPage': next_page, 'endCursor': cursor}}}


def history():
    return (Release(1, 'v0', '2024-12-01T00:00:00Z', 'base'),
            Release(2, 'v1', '2025-03-05T00:00:00Z', 'head'))


def cached_client(tmp_path):
    client = FakeClient([APIResponse({'fallback': True}, {})])
    client.cache = CacheStore(tmp_path)
    return client


def test_interval_adapter_collects_all_pages_and_preserves_real_sha(monkeypatch, tmp_path, window):
    responses = iter([comparison([commit('a')], 2, True), comparison([commit('b')], 2)])
    monkeypatch.setattr(enrichment, 'graphql', lambda *a: {'data': {'repository': {'a0': {'compare': next(responses)}}}})
    client = cached_client(tmp_path)
    adapter = enrichment.IntervalClient(client, 'a/b', history(), window)
    result = adapter.get('/repos/a/b/compare/base...head', {'per_page': 100, 'page': 1})
    assert result.data['total_commits'] == 2 and len(result.data['commits']) == 2
    assert result.data['commits'][1]['sha'] == 'b'
    assert adapter.get('/other').data['fallback']


@pytest.mark.parametrize('value', [None, comparison([], base='moved'), comparison([], head='moved'),
                                  comparison([commit()], 2), comparison([commit()], 1001, True)])
def test_interval_adapter_falls_back_to_verified_rest_for_missing_or_truncated_data(monkeypatch, tmp_path, window, value):
    monkeypatch.setattr(enrichment, 'graphql', lambda *a: {'data': {'repository': {'a0': {'compare': value}}}})
    adapter = enrichment.IntervalClient(cached_client(tmp_path), 'a/b', history(), window)
    assert adapter.get('/repos/a/b/compare/base...head', {'per_page': 100, 'page': 1}).data['fallback']


@pytest.mark.parametrize('continuation,message', [
    (comparison([commit('b')], 3), 'Comparação mudou'),
    (comparison([{**commit('a'), 'message': 'mutated'}], 2), 'Commit inconsistente'),
])
def test_interval_adapter_rejects_mutation_across_pages(monkeypatch, tmp_path, window, continuation, message):
    responses = iter([comparison([commit('a')], 2, True), continuation])
    monkeypatch.setattr(enrichment, 'graphql', lambda *a: {'data': {'repository': {'a0': {'compare': next(responses)}}}})
    with pytest.raises(APIError, match=message):
        enrichment.IntervalClient(cached_client(tmp_path), 'a/b', history(), window)


def test_interval_adapter_rejects_repeated_cursor(monkeypatch, tmp_path, window):
    monkeypatch.setattr(enrichment, 'graphql', lambda *a: {'data': {'repository': {'a0': {'compare': comparison([commit()], 2, True)}}}})
    with pytest.raises(APIError, match='Cursor'):
        enrichment.IntervalClient(cached_client(tmp_path), 'a/b', history(), window)


def payload(interval):
    return {'row': {'full_name': 'a/b', 'repository_id': 1, 'status': 'selected', 'release_count': 1},
            'collection': {'default_branch': 'main', 'default_branch_sha': 'snapshot',
                           'history': [asdict(interval.previous_release), asdict(interval.release)],
                           'excluded_releases': []},
            'workflow_runs': [parse_workflow_run(run(), 'main')]}


@pytest.mark.parametrize('kind,expected', [('complete', 'complete'), ('comparison', 'comparison_error'),
                                         ('negative', 'metric_error'), ('api', 'api_error'), ('data', 'data_error')])
def test_enrich_preserves_facts_and_missing_metrics_on_errors(monkeypatch, tmp_path, window, lead_time_example, kind, expected):
    interval = lead_time_example
    if kind == 'comparison':
        interval = replace(interval, status='error', error_detail='not ancestral')
    if kind == 'negative':
        interval = replace(interval, commits=(replace(interval.commits[0], author_date='2026-03-01T00:00:00Z'),))
    def tags(*args):
        if kind == 'api':
            raise APIError('unavailable')
        if kind == 'data':
            raise ValueError('bad evidence')
        return [], 0
    monkeypatch.setattr(enrichment, 'collect_tags', tags)
    monkeypatch.setattr(enrichment, 'IntervalClient', lambda *a: None)
    monkeypatch.setattr(enrichment, 'collect_release_intervals', lambda *a: (interval,))
    destination = tmp_path / 'result.json'
    result = enrichment.enrich(cached_client(tmp_path / 'cache'), payload(interval), window, destination)
    assert result['status'] == expected
    assert result['workflow_metrics']['successes'] == 1
    if kind in ('negative', 'comparison'):
        assert result['outputs']['lead_time_s01.csv'][0]['lead_time_release_median_hours'] is None
        assert result['outputs']['release_intervals_s01.csv']
    if kind == 'complete':
        assert result['outputs']['lead_time_s01.csv'][0]['lead_time_release_median_hours'] == 312
        assert len(result['outputs']['release_commits_s01.csv']) == 3
        assert enrichment.enrich(None, None, None, destination) == result


def test_export_context_does_not_overwrite_original_release_notes(monkeypatch, tmp_path, window, lead_time_example):
    monkeypatch.setattr(enrichment, 'collect_tags', lambda *a: ([], 0))
    monkeypatch.setattr(enrichment, 'IntervalClient', lambda *a: None)
    monkeypatch.setattr(enrichment, 'collect_release_intervals', lambda *a: (lead_time_example,))
    p = payload(lead_time_example)
    result = enrichment.enrich(cached_client(tmp_path / 'cache'), p, window, tmp_path / 'result.json')
    releases = tmp_path / 'releases_s01.csv'
    releases.write_text('original release notes', encoding='utf-8')
    enrichment.export_enrichment(tmp_path, [p], [result])
    assert releases.read_text() == 'original release notes'
    manifest = json.loads((tmp_path / 'enrichment_manifest_s02.json').read_text())
    assert manifest['statuses'] == {'complete': 1}
    assert not manifest['corrective_heuristic_executed']


def test_enrichment_cli_uses_only_selected_checkpoints(monkeypatch, tmp_path, window, lead_time_example):
    raw, output = tmp_path / 'raw', tmp_path / 'output'
    raw.joinpath('checkpoints').mkdir(parents=True)
    output.mkdir()
    p = payload(lead_time_example)
    (raw / 'checkpoints/1.json').write_text(json.dumps(p))
    (raw / 'checkpoints/2.json').write_text(json.dumps({'row': {'status': 'discarded'}}))
    (output / 'collection_manifest_s02.json').write_text(json.dumps({'window': asdict(window)}))
    monkeypatch.setattr(enrichment, 'enrich', lambda *a: {'full_name': 'a/b', 'status': 'complete'})
    exported = []
    monkeypatch.setattr(enrichment, 'export_enrichment', lambda *a: exported.append(a))
    assert enrichment.main(['--workers', '1', '--raw-dir', str(raw), '--output-dir', str(output)]) == 0
    assert len(exported[0][1]) == 1 and exported[0][2][0]['full_name'] == 'a/b'


def test_predecessor_uses_latest_stable_ancestral_release_not_tag_name(monkeypatch, window):
    p = {'row': {'full_name': 'a/b'}, 'collection': {'default_branch_sha': 'head',
          'history': [asdict(Release(3, 'v3', '2025-03-15T00:00:00Z', 'current'))]},
         'raw_releases': [raw_release(1, 'v1', '2024-12-01T00:00:00Z'),
                          raw_release(2, 'v2', '2024-12-02T00:00:00Z')]}
    adapter = FakeClient([APIResponse(raw_commit('offbranch'), {}), APIResponse({'status': 'diverged'}, {}),
                          APIResponse(raw_commit('base'), {}), APIResponse({'status': 'ahead'}, {})])
    monkeypatch.setattr(enrichment, 'ReleaseCommitClient', lambda *a: adapter)
    h = enrichment.with_predecessor(None, p, window)
    assert [r.release_id for r in h] == [1, 3]
    assert h[0].commit_sha == 'base'
    p['collection']['history'] = [asdict(r) for r in h]
    assert enrichment.with_predecessor(None, p, window) == h


def test_predecessor_does_not_accept_unknown_comparison(monkeypatch, window):
    p = {'row': {'full_name': 'a/b'}, 'collection': {'default_branch_sha': 'head', 'history': []},
         'raw_releases': [raw_release(1, 'v1', '2024-12-01T00:00:00Z')]}
    monkeypatch.setattr(enrichment, 'ReleaseCommitClient', lambda *a: FakeClient([
        APIResponse(raw_commit('base'), {}), APIResponse({'status': 'unknown'}, {})]))
    with pytest.raises(APIError, match='não comprovada'):
        enrichment.with_predecessor(None, p, window)
def test_export_snapshots_do_not_depend_on_worker_completion_order(tmp_path):
    from src.s02_enrichment import export_enrichment
    results = [{'full_name': name, 'status': 'complete', 'error_detail': '', 'outputs': {},
                'workflow_metrics': {'full_name': name, 'successes': 1, 'failures': 0},
                'recovery_episodes': [], 'predecessors': []}
               for name in ('fixture/b', 'fixture/A')]
    first, second = tmp_path / 'first', tmp_path / 'second'
    export_enrichment(first, [], results)
    export_enrichment(second, [], list(reversed(results)))
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()}


