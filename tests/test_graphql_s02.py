import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from src.cache import CacheStore
from src.github_client import APIError, APIResponse
from src import graphql_context as context
from src import graphql_discovery as discovery


class Response(BytesIO):
    status = 200
    headers = {'X-RateLimit-Remaining': '4900'}


def commit(oid='head'):
    return dict(oid=oid, authoredDate='2025-03-01T00:00:00Z',
                committedDate='2025-03-02T00:00:00Z', message='factual message', url='https://github.com/a/b/commit/' + oid)


def test_graphql_auth_only_in_memory_cache_and_retry(monkeypatch, tmp_path):
    cache = CacheStore(tmp_path)
    monkeypatch.setenv('GITHUB_TOKEN', 'temporary-fixture-credential')
    calls, sleeps = [], []
    def request(req, timeout):
        calls.append(req)
        if len(calls) == 1:
            raise HTTPError(req.full_url, 503, '', {}, None)
        assert req.get_header('Authorization') == 'Bearer temporary-fixture-credential'
        return Response(json.dumps({'data': {'nodes': []}}).encode())
    monkeypatch.setattr(context, 'urlopen', request)
    monkeypatch.setattr(context.time, 'sleep', sleeps.append)
    assert context.query_nodes(cache, ['id'], 'head') == {'data': {'nodes': []}}
    assert sleeps == [1]
    assert context.query_nodes(cache, ['id'], 'head') == {'data': {'nodes': []}}
    assert len(calls) == 2
    stored = next(tmp_path.glob('*.json')).read_text()
    assert 'temporary-fixture-credential' not in stored and 'Authorization' not in stored


@pytest.mark.parametrize('error', [URLError('unavailable'), ValueError('bad json'),
                                  HTTPError('https://api.github.com/graphql', 429, '', {}, None)])
def test_graphql_retries_and_returns_sanitized_failure(monkeypatch, error):
    monkeypatch.setenv('GITHUB_TOKEN', 'fixture')
    monkeypatch.setattr(context.time, 'sleep', lambda delay: None)
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(context, 'urlopen', fail)
    with pytest.raises(APIError, match='detalhes não registrados'):
        context.graphql(None, 'query{x}', {})


def test_graphql_waits_for_quota_and_rejects_unauthorized(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'fixture')
    monkeypatch.setattr(context.time, 'time', lambda: 100)
    sleeps, calls = [], []
    monkeypatch.setattr(context.time, 'sleep', sleeps.append)
    def response(req, **kwargs):
        calls.append(req)
        if len(calls) == 1:
            raise HTTPError(req.full_url, 403, '', {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '110'}, None)
        return Response(b'{"data":{"nodes":[]}}')
    monkeypatch.setattr(context, 'urlopen', response)
    context.query_nodes(None, [], 'head')
    assert sleeps == [12]
    monkeypatch.setattr(context, 'urlopen', lambda *a, **k: (_ for _ in ()).throw(HTTPError('url', 401, '', {}, None)))
    with pytest.raises(APIError, match='HTTP 401'):
        context.graphql(None, 'query{x}', {})


def test_graphql_errors_or_missing_nodes_are_not_accepted(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'fixture')
    monkeypatch.setattr(context.time, 'sleep', lambda _: None)
    monkeypatch.setattr(context, 'urlopen', lambda *a, **k: Response(b'{"errors":[{"message":"not logged"}]}'))
    with pytest.raises(APIError):
        context.graphql(None, 'query{x}', {})
    monkeypatch.setattr(context, 'graphql', lambda *a: {'data': {}})
    with pytest.raises(APIError, match='sem nodes'):
        context.query_nodes(None, [], 'head')


class Client:
    cache = None
    def __init__(self):
        self.calls = []
    def get(self, path, params=None):
        self.calls.append((path, params))
        return APIResponse({'fallback': True}, {})


def test_release_adapter_checks_base_and_head_before_reusing_comparison(monkeypatch):
    good = {'id': '1', 'tagName': 'v1/a', 'tagCommit': commit('base'),
            'tag': {'compare': {'status': 'AHEAD', 'baseTarget': {'oid': 'base'}, 'headTarget': {'oid': 'head'}}}}
    moved = {'id': '2', 'tagName': 'v2', 'tagCommit': commit('base2'),
             'tag': {'compare': {'status': 'AHEAD', 'baseTarget': {'oid': 'moved'}, 'headTarget': {'oid': 'head'}}}}
    monkeypatch.setattr(context, 'query_nodes', lambda *a: {'data': {'nodes': [None, {'tagCommit': None}, good, moved]}})
    client = Client()
    adapter = context.ReleaseCommitClient(client, 'a/b', [{'node_id': '1'}], 'head')
    assert adapter.get('/repos/a/b/commits/v1%2Fa').data['sha'] == 'base'
    assert adapter.get('/repos/a/b/compare/base...head', {'per_page': 1, 'page': 2}).data['status'] == 'ahead'
    assert adapter.get('/repos/a/b/compare/base2...head', {'per_page': 1, 'page': 2}).data['fallback']
    assert adapter.get('/repos/a/b/compare/base...head', {'per_page': 100, 'page': 1}).data['fallback']


def repository(identifier=1):
    return dict(id='R'+str(identifier), databaseId=identifier, name='b', nameWithOwner='a/b',
                url='https://github.com/a/b', description='description', createdAt='2020-01-01T00:00:00Z',
                stargazerCount=5000, isPrivate=False, isFork=False, isArchived=False,
                owner={'login': 'a'}, primaryLanguage={'name': 'Python'}, defaultBranchRef={'name': 'main'})


def test_search_adapter_follows_cursor_with_original_query(monkeypatch):
    calls = []
    def graphql(cache, query, variables):
        calls.append(variables)
        return {'data': {'search': {'repositoryCount': 200, 'nodes': [repository()],
                                   'pageInfo': {'hasNextPage': not variables['after'], 'endCursor': 'cursor'}}}}
    monkeypatch.setattr(discovery, 'graphql', graphql)
    client = Client()
    adapter = discovery.SearchClient(client)
    first = adapter.get('/search/repositories', {'q': 'stars:>1000 is:public'})
    assert first.data['items'][0]['private'] is False
    assert first.data['items'][0]['node_id'] == 'R1'
    link = first.headers['Link'].split('<')[1].split('>')[0]
    second = adapter.get(link)
    assert not second.headers
    assert calls[-1] == {'q': 'stars:>1000 is:public sort:stars-desc', 'after': 'cursor'}
    assert adapter.get('/repos/a/b').data['fallback']


@pytest.mark.parametrize('nodes,cursor', [([None], 'cursor'), ([repository()], None)])
def test_search_missing_repository_or_cursor_rejected(monkeypatch, nodes, cursor):
    monkeypatch.setattr(discovery, 'graphql', lambda *a: {'data': {'search': {
        'repositoryCount': 200, 'nodes': nodes, 'pageInfo': {'hasNextPage': True, 'endCursor': cursor}}}})
    with pytest.raises(APIError):
        discovery.SearchClient(Client()).get('/search/repositories', {'q': 'stars:>1000'})


def release(identifier=1):
    return dict(id='RE'+str(identifier), databaseId=identifier, name='v1', description='notes',
                isDraft=False, isPrerelease=False, tagName='v1', publishedAt='2025-03-03T00:00:00Z',
                url='https://github.com/a/b/releases/tag/v1')


def repository_page(nodes, total=1, next_page=False, cursor='cursor', branch='head'):
    return {'data': {'node': {'defaultBranchRef': {'name': 'main', 'target': commit(branch)},
                             'releases': {'nodes': nodes, 'totalCount': total,
                                          'pageInfo': {'hasNextPage': next_page, 'endCursor': cursor}}}}}


def test_repository_adapter_preserves_notes_and_snapshot_across_pages(monkeypatch):
    responses = iter([repository_page([release(1)], 2, True), repository_page([release(2)], 2)])
    monkeypatch.setattr(discovery, 'graphql', lambda *a: next(responses))
    adapter = discovery.RepositoryReleaseClient(Client(), {'node_id': 'R1', 'full_name': 'a/b'})
    data = adapter.get('/repos/a/b/releases', {'per_page': 100, 'page': 1}).data
    assert len(data) == 2 and data[0]['body'] == 'notes'
    assert adapter.get('/repos/a/b/commits/main').data['sha'] == 'head'
    assert adapter.get('/other').data['fallback']


@pytest.mark.parametrize('pages,message', [
    ([{'data': {'node': None}}], 'inacessível'),
    ([{'data': {'node': {'defaultBranchRef': None}}}], 'Default branch'),
    ([repository_page([], 1)], 'incompleta'),
    ([repository_page([release()], 2, True), repository_page([release()], 2)], 'repetida'),
    ([repository_page([release()], 2, True), repository_page([release(2)], 3)], 'Contagem'),
    ([repository_page([], 3, True, None)], 'Cursor'),
])
def test_repository_adapter_rejects_inconsistent_collection(monkeypatch, pages, message):
    responses = iter(pages)
    monkeypatch.setattr(discovery, 'graphql', lambda *a: next(responses))
    with pytest.raises((APIError, ValueError), match=message):
        discovery.RepositoryReleaseClient(Client(), {'node_id': 'R1', 'full_name': 'a/b'})
