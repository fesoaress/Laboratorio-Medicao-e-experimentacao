import json
from dataclasses import asdict
from pathlib import Path

import pytest

from src.config import SelectionConfig
from src.github_client import APIError, APIResponse
from src.releases import collect_releases_and_tags
from src.s02_collection import candidate_stream, export_outputs, process_candidate, save_json
from src.temporal import ObservationWindow
from src.workflow_adaptive import collect_runs
from tests.test_release_collection import raw_commit, raw_release
from tests.test_selection import FakeClient
from tests.test_workflow_runs import run, runs_page
from src import s02_collection as collection
from src.pipeline import REPOSITORY_FIELDS
from src.releases import ReleaseCollection
from src.temporal import Release


def metadata():
    return {'id': 1, 'node_id': 'R1', 'owner': {'login': 'a'}, 'name': 'b', 'full_name': 'a/b',
            'html_url': 'https://github.com/a/b', 'created_at': '2020-01-01T00:00:00Z',
            'default_branch': 'main', 'stargazers_count': 2000, 'language': 'Python'}


def test_window_only_retains_valid_predecessor_without_all_old_tags(window):
    old = raw_release(1, 'old', '2024-12-01T00:00:00Z')
    older = raw_release(2, 'older', '2024-11-01T00:00:00Z')
    current = raw_release(3, 'new')
    client = FakeClient([APIResponse(raw_commit('branch'), {}), APIResponse([older, current, old], {}),
                         APIResponse(raw_commit('head'), {}), APIResponse({'status': 'ahead'}, {}),
                         APIResponse(raw_commit('base'), {}), APIResponse({'status': 'ahead'}, {})])
    result = collect_releases_and_tags(client, 'a/b', 'main', window, collect_tags=False, window_only=True)
    assert [r.release_id for r in result.history] == [1, 3]
    assert not result.tags
    assert not any('older' in path or path.endswith('/tags') for path, _ in client.calls)


def test_eligibility_does_not_resolve_predecessor_before_repo_is_selected(window):
    client = FakeClient([APIResponse(raw_commit('branch'), {}),
                         APIResponse([raw_release(1, 'old', '2024-12-01T00:00:00Z')], {})])
    result = collect_releases_and_tags(client, 'a/b', 'main', window, collect_tags=False,
                                       window_only=True, include_predecessor=False)
    assert not result.history and len(client.calls) == 2


def test_adaptive_runs_split_and_deduplicate(window):
    left = run(1, created='2025-03-01T00:00:00Z')
    right = run(2, created='2025-10-01T00:00:00Z')
    client = FakeClient([runs_page([], total=1001), runs_page([left]), runs_page([right])])
    rows, reports = collect_runs(client, 'a/b', 'main', window.start_date, window.end_date)
    assert [r['id'] for r in rows] == [1, 2]
    assert len(reports) == 2
    assert client.calls[1][1]['created'] == '2025-01-01..2025-07-01'
    assert client.calls[2][1]['created'] == '2025-07-02..2025-12-31'


def test_adaptive_runs_rejects_truncated_page(window):
    with pytest.raises(APIError, match='incompleta'):
        collect_runs(FakeClient([runs_page([run(1)], total=2)]), 'a/b', 'main', window.start_date, window.end_date)


def test_valid_run_count_excludes_ignored_conclusions(window):
    rows, _ = collect_runs(FakeClient([runs_page([run(1), run(2, conclusion='cancelled')])]), 'a/b', 'main', window.start_date, window.end_date)
    assert len(rows) == 2
    assert sum(r['status_class'] is not None for r in rows) == 1


def test_candidate_slices_split_before_yielding_truncated_search():
    truncated = {'total_count': 1001, 'items': [{'id': 0}], 'incomplete_results': False}
    left = {'total_count': 1, 'items': [{'id': 1}], 'incomplete_results': False}
    right = {'total_count': 1, 'items': [{'id': 2}], 'incomplete_results': False}
    client = FakeClient([APIResponse(d, {}) for d in (truncated, left, right)])
    queries = []
    stream = candidate_stream(client, queries, 1001, 1002)
    assert next(stream)['id'] == 1 and next(stream)['id'] == 2
    assert len(queries) == 3


def test_checkpoint_resume_skips_completed_repository(tmp_path, window):
    path = tmp_path / 'checkpoint.json'
    payload = {'row': {'status': 'selected'}}
    save_json(path, payload)
    client = FakeClient([])
    assert process_candidate(client, {}, SelectionConfig(), window, 'unused', path) == payload
    assert not client.calls


def test_export_records_lower_bound_and_keeps_missing_values(tmp_path, window):
    from src.pipeline import REPOSITORY_FIELDS
    row = dict.fromkeys(REPOSITORY_FIELDS)
    row.update(full_name='a/b', status='pending_validation', reasons='pending_release_validation;pending_workflow_validation',
               processed=True, metadata_complete=True, has_github_actions=True, default_branch='main')
    checkpoints = tmp_path / 'checkpoints'
    save_json(checkpoints / '1.json', {'row': row, 'candidate': {}, 'collection': None,
                                     'raw_releases': [], 'workflow_runs': []})
    manifest = {'target': 300, 'window': asdict(window)}
    result = export_outputs(tmp_path / 'output', checkpoints, manifest)
    assert result['final_sample'] == 0 and not result['target_met']
    assert result['candidates_processed'] == 1
    assert json.loads((tmp_path / 'output/collection_manifest_s02.json').read_text())['target'] == 300


def row(name='a/b'):
    result = dict.fromkeys(REPOSITORY_FIELDS)
    result.update(full_name=name, status='pending_validation', reasons='', processed=True,
                  metadata_complete=True, has_github_actions=True, default_branch='main')
    return result


def test_pacing_shares_core_quota_and_preserves_other_resource(monkeypatch):
    sleeps = []
    monkeypatch.setattr(collection, 'safe_sleep', sleeps.append)
    monkeypatch.setattr(collection.time, 'monotonic', lambda: 0)
    monkeypatch.setattr(collection.time, 'time', lambda: 100)
    headers = {'X-RateLimit-Resource': 'core', 'X-RateLimit-Remaining': '8', 'X-RateLimit-Reset': '110'}
    client = collection.PacedClient(FakeClient([APIResponse({}, headers), APIResponse({}, {}),
                                              APIResponse({}, {**headers, 'X-RateLimit-Remaining': '7'}),
                                              APIResponse({}, {**headers, 'X-RateLimit-Reset': '200', 'X-RateLimit-Remaining': '4000'})]))
    for _ in range(4):
        client.get('/x')
    assert sleeps == [12, 12, 12]
    assert client.remaining == 4000 and client.reset == 200 and client.calls == 4


def test_safe_sleep_uses_bounded_segments(monkeypatch, capsys):
    now = [0]
    monkeypatch.setattr(collection.time, 'monotonic', lambda: now[0])
    segments = []
    def advance(delay):
        segments.append(delay)
        now[0] += delay
    monkeypatch.setattr(collection.time, 'sleep', advance)
    collection.safe_sleep(65)
    assert segments == [30, 30, 5]
    assert 'checkpoints preservados' in capsys.readouterr().out


@pytest.mark.parametrize('data', [[], {'total_count': -1}, {'items': [], 'total_count': '1'}])
def test_candidate_invalid_search_rejected(data):
    with pytest.raises(APIError):
        next(candidate_stream(FakeClient([APIResponse(data, {})]), [], bands=[(1, 1)]))


def test_candidate_unsplittable_search_is_explicit():
    data = {'total_count': 1001, 'items': [], 'incomplete_results': False}
    with pytest.raises(APIError, match='subdivisão'):
        next(candidate_stream(FakeClient([APIResponse(data, {})]), [], bands=[(1001, 1001)]))


def test_candidate_rejects_later_incomplete_page():
    first = APIResponse({'total_count': 2, 'items': [{'id': 1}]},
                        {'Link': '<https://api.github.com/search/repositories?page=2>; rel="next"'})
    second = APIResponse({'total_count': 2, 'items': [], 'incomplete_results': True}, {})
    with pytest.raises(APIError, match='incompleta'):
        list(candidate_stream(FakeClient([first, second]), [], bands=[(1001, 1002)]))


@pytest.mark.parametrize('kind,expected', [('private', 'metadata_error'), ('few_releases', 'discarded'),
                                         ('few_runs', 'discarded'), ('valid', 'selected'),
                                         ('api', 'api_error'), ('malformed', 'metadata_error')])
def test_candidate_filters_preserve_measured_counts(monkeypatch, tmp_path, window, kind, expected):
    candidate = {**metadata(), 'full_name': 'a/b', 'private': kind != 'private'}
    # O indicador private da API deve ser False para comprovar acesso público.
    candidate['private'] = kind == 'private'
    monkeypatch.setattr(collection, 'collect_metadata', lambda *a, **k: [row()])
    releases = [raw_release(i, f'v{i}', node_id=str(i)) for i in range(5 if kind != 'few_releases' else 4)]
    if kind == 'malformed':
        response = APIResponse({}, {})
    elif kind == 'api':
        response = APIError('temporarily unavailable', status=503)
    else:
        response = APIResponse(releases, {})
    client = FakeClient([response, APIResponse({'sha': 'snapshot'}, {})])
    count = 49 if kind == 'few_runs' else 50
    monkeypatch.setattr(collection, 'collect_runs', lambda *a: ([{'status_class': 'success'} for _ in range(count)], []))
    monkeypatch.setattr(collection, 'ReleaseCommitClient', lambda *a: client)
    history = tuple(Release(i, f'v{i}', '2025-03-15T00:00:00Z', str(i)) for i in range(5))
    monkeypatch.setattr(collection, 'collect_releases_and_tags', lambda *a, **k: ReleaseCollection('main', 'snapshot', history, (), ()))
    result = process_candidate(client, candidate, SelectionConfig(start_date=window.start_date, end_date=window.end_date),
                               window, '2026-01-01T00:00:00Z', tmp_path / 'checkpoint.json')
    assert result['row']['status'] == expected
    if kind == 'few_runs':
        assert result['row']['valid_workflow_runs'] == 49 and result['row']['release_count'] is None
    if kind == 'valid':
        assert result['row']['release_count'] == 5 and result['row']['valid_workflow_runs'] == 50
    if kind == 'few_releases':
        assert result['row']['release_count'] == 4 and result['row']['valid_workflow_runs'] is None


def test_candidate_graphql_prefilter_avoids_rest_metadata_for_rejection(monkeypatch, tmp_path, window):
    candidate = metadata()
    candidate.update(private=False)
    client = FakeClient([APIResponse([], {})])
    client.branch_name = 'main'
    monkeypatch.setattr(collection, 'RepositoryReleaseClient', lambda *a: client)
    monkeypatch.setattr(collection, 'collect_metadata', lambda *a, **k: pytest.fail('pré-filtro não deve consumir quota REST'))
    result = process_candidate(client, candidate, SelectionConfig(), window, '2026-01-01T00:00:00Z',
                               tmp_path / 'checkpoint.json', graphql_discovery=True)
    assert result['row']['reasons'] == 'insufficient_releases'
    assert result['row']['has_github_actions'] is None


def test_candidate_graphql_metadata_failure_remains_explicit(monkeypatch, tmp_path, window):
    candidate = metadata()
    candidate.update(private=False)
    client = FakeClient([APIResponse([raw_release(i, str(i)) for i in range(5)], {})])
    client.branch_name = 'main'
    monkeypatch.setattr(collection, 'RepositoryReleaseClient', lambda *a: client)
    failed = {**row(), 'status': 'api_error', 'reasons': 'api_error'}
    monkeypatch.setattr(collection, 'collect_metadata', lambda *a, **k: [failed])
    result = process_candidate(client, candidate, SelectionConfig(), window, '2026-01-01T00:00:00Z',
                               tmp_path / 'checkpoint.json', graphql_discovery=True)
    assert result['row']['status'] == 'api_error'


def test_candidate_unauthorized_saves_checkpoint_and_stops(monkeypatch, tmp_path, window):
    monkeypatch.setattr(collection, 'collect_metadata', lambda *a, **k: [row()])
    path = tmp_path / 'checkpoint.json'
    with pytest.raises(APIError):
        process_candidate(FakeClient([APIError('unauthorized', status=401)]), {'private': False},
                          SelectionConfig(), window, '2026-01-01T00:00:00Z', path)
    assert json.loads(path.read_text())['row']['status'] == 'api_error'


def test_export_selected_data_preserves_notes_and_all_runs(tmp_path, window):
    selected = {**row(), 'status': 'selected', 'release_count': 5, 'valid_workflow_runs': 50}
    p = {'row': selected, 'candidate': {'description': 'actual description'},
         'raw_releases': [raw_release(1, 'v1', body='Actual release notes')],
         'collection': {'history': [asdict(Release(1, 'v1', '2025-03-15T00:00:00Z', 'head'))]},
         'workflow_runs': []}
    save_json(tmp_path / 'checkpoints/1.json', p)
    result = export_outputs(tmp_path / 'output', tmp_path / 'checkpoints', {'target': 300, 'window': asdict(window)})
    assert result['final_sample'] == 1 and not result['target_met']
    assert 'Actual release notes' in (tmp_path / 'output/releases_s01.csv').read_text()


@pytest.mark.parametrize('args', [['--target', '299'], ['--workers', '9'], ['--output-dir', 'data/processed/smoke']])
def test_main_rejects_invalid_collection_before_network(args):
    with pytest.raises(SystemExit) as error:
        collection.main(args)
    assert error.value.code == 2


def test_main_collects_beyond_300_candidates_until_300_eligible_and_resumes(monkeypatch, tmp_path, window):
    output, raw = tmp_path / 'output', tmp_path / 'raw'
    monkeypatch.setattr(collection, 'load_config', lambda: SelectionConfig(start_date=window.start_date, end_date=window.end_date))
    source = [{'id': i, 'full_name': f'a/r{i}'} for i in range(500)]
    source.insert(2, source[0])
    monkeypatch.setattr(collection, 'candidate_stream', lambda *a, **k: iter(source))
    finished = []
    def process(client, candidate, *args, **kwargs):
        status = 'discarded' if candidate['id'] < 50 else 'selected'
        finished.append(status)
        return {'row': {'status': status, 'full_name': candidate['full_name'], 'release_count': 5, 'valid_workflow_runs': 50}}
    monkeypatch.setattr(collection, 'process_candidate', process)
    def export(output, checkpoints, manifest):
        manifest.update(final_sample=finished.count('selected'), candidates_processed=len(finished),
                        target_met=finished.count('selected') >= 300)
        save_json(output / 'collection_manifest_s02.json', manifest)
        return manifest
    monkeypatch.setattr(collection, 'export_outputs', export)
    args = ['--workers', '1', '--output-dir', str(output), '--raw-dir', str(raw)]
    assert collection.main(args) == 0
    manifest = json.loads((output / 'collection_manifest_s02.json').read_text())
    assert manifest['candidates_processed'] >= 350 and 300 <= manifest['final_sample'] <= 301
    assert collection.main(args) == 0
    manifest['window']['end_date'] = '2024-01-01'
    save_json(output / 'collection_manifest_s02.json', manifest)
    with pytest.raises(SystemExit):
        collection.main(args)


def test_main_search_failure_preserves_outputs_and_returns_failure(monkeypatch, tmp_path, window):
    monkeypatch.setattr(collection, 'load_config', lambda: SelectionConfig(start_date=window.start_date, end_date=window.end_date))
    def fail(*args, **kwargs):
        raise APIError('search unavailable')
    monkeypatch.setattr(collection, 'candidate_stream', fail)
    output = tmp_path / 'output'
    assert collection.main(['--output-dir', str(output), '--raw-dir', str(tmp_path / 'raw')]) == 1
    manifest = json.loads((output / 'collection_manifest_s02.json').read_text())
    assert manifest['final_sample'] == 0 and manifest['interruption'] == 'APIError: search unavailable'


def test_funnel_does_not_confuse_release_upper_bound_with_ancestry(window):
    releases = [raw_release(i, str(i)) for i in range(5)]
    history = [asdict(Release(i, str(i), '2025-03-15T00:00:00Z', str(i))) for i in range(4)]
    p = {'row': {**row(), 'valid_workflow_runs': 50}, 'candidate': {'private': False},
         'raw_releases': releases, 'release_prefilter_measured': True,
         'collection': {'history': history}}
    missing = {'row': {**row(), 'has_github_actions': None}, 'candidate': {'private': False},
               'raw_releases': [], 'collection': None}
    result = {r['stage']: r for r in collection.build_s02_funnel([p, missing], window)}
    assert result['actions_enabled']['count'] == 1 and result['actions_enabled']['pending'] == 1
    assert result['published_stable_release_prefilter']['count'] == 1
    assert result['workflow_filter']['count'] == 1
    assert result['release_ancestry_filter']['count'] == 0
    assert result['final_sample']['count'] == 0


def test_missing_release_count_stays_pending_in_funnel(window):
    p = {'row': row(), 'candidate': {'private': False}, 'raw_releases': [], 'collection': None}
    result = {r['stage']: r for r in collection.build_s02_funnel([p], window)}
    assert result['published_stable_release_prefilter']['pending'] == 1


def test_candidate_revalidates_star_threshold(monkeypatch, tmp_path, window):
    monkeypatch.setattr(collection, 'collect_metadata', lambda *a, **k: [{**row(), 'stargazers_count': 1000}])
    client = FakeClient([])
    result = process_candidate(client, {'private': False}, SelectionConfig(), window,
                               '2026-01-01T00:00:00Z', tmp_path / 'checkpoint.json')
    assert result['row']['reasons'] == 'insufficient_stars' and not client.calls


def test_adaptive_runs_can_subdivide_a_busy_day_to_seconds(window):
    from datetime import datetime, timezone
    from src.workflow_runs import WorkflowRunError
    class BusyClient:
        def get(self, path, params=None):
            created = params['created']
            if 'T' not in created:
                return runs_page([], total=1001 if created.startswith('2025-01-01') else 0)
            start = datetime.fromisoformat(created.split('..')[0].replace('Z', '+00:00'))
            identifier, hour = (1, 1) if start.hour < 12 else (2, 13)
            return runs_page([run(identifier, created=f'2025-01-01T{hour:02}:00:00Z')])
    rows, reports = collect_runs(BusyClient(), 'a/b', 'main', window.start_date, window.end_date)
    assert [r['id'] for r in rows] == [1, 2]
    assert any('12:00:00' in report['start'] for report in reports)


@pytest.mark.parametrize('responses,message', [
    ([runs_page([], total=-1)], 'total_count'),
    ([APIResponse({'total_count': 0}, {})], 'workflow_runs'),
    ([runs_page([], total=1001)] * 40, 'mesmo segundo'),
])
def test_adaptive_run_invalid_or_unsplittable_results_are_explicit(window, responses, message):
    from src.workflow_runs import WorkflowRunError
    with pytest.raises(WorkflowRunError, match=message):
        collect_runs(FakeClient(responses), 'a/b', 'main', window.start_date, window.end_date)
