import json
import subprocess
from dataclasses import asdict

import pytest

from src.git_context import GitRepository, GitIntervalClient
from src.github_client import APIError, APIResponse
from src.commits import collect_release_intervals
from src.s02_enrichment import enrich
from src.temporal import Release


@pytest.fixture
def git_history(tmp_path):
    directory = tmp_path / 'objects.git'
    subprocess.run(['git', 'init', '--bare', str(directory)], check=True, capture_output=True)
    def git(*args, body=None):
        return subprocess.run(['git', '--git-dir', str(directory), *args], input=body,
                              check=True, capture_output=True).stdout.decode().strip()
    git('config', 'remote.origin.url', 'https://github.com/fixture/repo.git')
    tree = git('hash-object', '-w', '-t', 'tree', '--stdin', body=b'')
    def commit(epoch, parent=None, message='actual message'):
        headers = f'tree {tree}\n' + (f'parent {parent}\n' if parent else '')
        headers += f'author Example <example@example.test> {epoch} +0000\n'
        headers += f'committer Example <example@example.test> {epoch} +0000\n\n{message}\n'
        return git('hash-object', '-w', '-t', 'commit', '--stdin', body=headers.encode())
    a = commit(1733011200)  # 2024-12-01; real predecessor outside test window.
    b = commit(1740787200, a, 'message B')  # 2025-03-01
    c = commit(1740873600, b, 'mensagem C: ação')
    d = commit(1740960000, a, 'side branch')
    git('update-ref', 'refs/heads/main', c)
    for name, sha in [('old', a), ('v1', b), ('side', d)]:
        git('update-ref', 'refs/tags/' + name, sha)
    annotated = git('hash-object', '-w', '-t', 'tag', '--stdin', body=(
        f'object {c}\ntype commit\ntag v2\ntagger Example <example@example.test> 1740873600 +0000\n\nannotation\n').encode())
    nested = git('hash-object', '-w', '-t', 'tag', '--stdin', body=(
        f'object {annotated}\ntype tag\ntag nested\ntagger Example <example@example.test> 1740873600 +0000\n\nnested\n').encode())
    git('update-ref', 'refs/tags/v2', annotated)
    git('update-ref', 'refs/tags/nested', nested)
    return directory, git, (a, b, c, d), tree


def test_git_peels_nested_tags_checks_snapshot_and_preserves_commits(git_history, window):
    directory, _, (a, b, c, d), _ = git_history
    repository = GitRepository(directory, 'fixture/repo', c)
    tags, scanned = repository.tags(window)
    assert scanned == 5 and len(tags) == 4
    tags = {t.name: t for t in tags}
    assert tags['nested'].commit_sha == tags['v2'].commit_sha == c
    assert tags['v1'].on_default_branch and not tags['side'].on_default_branch
    assert len(repository.tag_snapshot) == 5
    data = repository.compare(a, c).data
    assert data['status'] == 'ahead' and data['total_commits'] == 2
    assert {v['sha'] for v in data['commits']} == {b, c}
    assert 'ação' in data['commits'][0]['commit']['message']
    assert data['commits'][0]['commit']['author']['date'] == '2025-03-02T00:00:00Z'
    assert repository.compare(c, a).data['status'] == 'behind'
    assert repository.compare(c, d).data['status'] == 'diverged'
    assert repository.compare(c, c).data == {'status': 'identical', 'total_commits': 0, 'commits': []}
    assert repository.objects([]) == {}


def test_git_interval_adapter_and_enrichment_use_real_objects(git_history, window, tmp_path):
    directory, _, (a, b, c, _), _ = git_history
    class NoNetwork:
        def get(self, path, params=None):
            return APIResponse({'fallback': True}, {})
    client = NoNetwork()
    history = (Release(1, 'old', '2024-12-01T00:00:00Z', a),
               Release(2, 'v1', '2025-03-03T00:00:00Z', b),
               Release(3, 'v2', '2025-03-04T00:00:00Z', c))
    adapter = GitIntervalClient(client, 'fixture/repo', history, window,
                                GitRepository(directory, 'fixture/repo', c))
    intervals = collect_release_intervals(adapter, 'fixture/repo', history, window)
    assert [len(i.commits) for i in intervals] == [1, 1]
    assert adapter.get('/fallback').data['fallback']
    payload = {'row': {'full_name': 'fixture/repo', 'release_count': 2}, 'workflow_runs': [],
               'collection': {'default_branch': 'main', 'default_branch_sha': c,
                              'history': [asdict(r) for r in history]}}
    result = enrich(client, payload, window, tmp_path / 'result.json', git_repository=directory)
    assert result['status'] == 'complete'
    assert len(result['outputs']['release_commits_s01.csv']) == 2
    assert result['context_source']['transport'] == 'github_git_objects'
    snapshot = json.loads((tmp_path / 'fixture--repo_tags_snapshot.json').read_text())
    assert snapshot['default_branch_sha'] == c and len(snapshot['refs']) == 5


@pytest.mark.parametrize('condition', ['remote', 'shallow', 'missing'])
def test_git_rejects_unverifiable_repository(git_history, condition):
    directory, git, (_, b, c, _), _ = git_history
    if condition == 'remote':
        git('config', 'remote.origin.url', 'https://github.com/wrong/repo.git')
    elif condition == 'shallow':
        (directory / 'shallow').write_text(b + '\n')
    else:
        c = 'f' * 40
    with pytest.raises(APIError):
        GitRepository(directory, 'fixture/repo', c)


def test_git_rejects_noncommit_tag_and_missing_objects(git_history, window):
    directory, git, (_, _, c, _), tree = git_history
    repository = GitRepository(directory, 'fixture/repo', c)
    with pytest.raises(APIError, match='commit'):
        repository.objects(['f' * 40])
    git('update-ref', 'refs/tags/tree', tree)
    with pytest.raises(APIError, match='commit'):
        repository.tags(window)


@pytest.mark.parametrize('body', [b'abc', b'header without separator'])
def test_git_rejects_truncated_or_malformed_object(git_history, monkeypatch, body):
    directory, _, (_, b, c, _), _ = git_history
    repository = GitRepository(directory, 'fixture/repo', c)
    raw = b.encode() + b' commit ' + str(len(body)).encode() + b'\n' + body
    if body != b'abc':
        raw += b'\n'
    monkeypatch.setattr(repository, 'run', lambda *args: raw)
    with pytest.raises(APIError):
        repository.objects([b])


def test_git_empty_tag_snapshot_is_valid(git_history, window):
    directory, git, (_, _, c, _), _ = git_history
    repository = GitRepository(directory, 'fixture/repo', c)
    for line in git('for-each-ref', '--format=%(refname)', 'refs/tags').splitlines():
        git('update-ref', '-d', line)
    assert repository.tags(window) == ([], 0)
