"""Contexto factual e métricas S02; não executa classificação corretiva."""

from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

from .cache import CacheStore, ResilientClient
from .commits import collect_release_intervals
from .deliveries import OUTPUT_FIELDS, SUMMARY_FIELDS
from .github_client import APIError, APIResponse, GitHubClient
from .graphql_context import graphql, ReleaseCommitClient
from .metrics import (calculate_lead_time, change_failure_rate_a, recovery_episodes,
                      repository_recovery_time)
from .pipeline import write_csv
from .s02_collection import PacedClient, safe_sleep, save_json
from .temporal import ObservationWindow, Release, Tag, utc_datetime, parse_commit

COMMIT_FIELDS = 'oid authoredDate committedDate message url'
TARGET = '... on Commit { ' + COMMIT_FIELDS + ' }'
for _ in range(4):
    TARGET = '... on Commit { ' + COMMIT_FIELDS + ' } ... on Tag { target { ' + TARGET + ' } }'
TAGS_QUERY = '''query($owner:String!,$name:String!,$after:String) {
 repository(owner:$owner,name:$name) { refs(refPrefix:"refs/tags/",first:100,after:$after) {
 totalCount pageInfo {hasNextPage endCursor} nodes {id name target {''' + TARGET + '''}} } } }'''
MEMBERSHIP_QUERY = '''query($ids:[ID!]!,$head:String!) { nodes(ids:$ids) { ... on Ref {
 id compare(headRef:$head) {status baseTarget{oid} headTarget{oid}} } } }'''


def rest_commit(commit):
    return {'sha': commit['oid'], 'html_url': commit['url'],
            'commit': {'author': {'date': commit['authoredDate']},
                       'committer': {'date': commit['committedDate']}, 'message': commit['message']}}


def with_predecessor(client, payload, window):
    collection = payload['collection']
    history = tuple(Release(**r) for r in collection['history'])
    if any(not r.prerelease and utc_datetime(r.published_at) < window.start for r in history):
        return history
    older = sorted((r for r in payload.get('raw_releases', []) if not r['draft'] and not r['prerelease']
                    and utc_datetime(r['published_at']) < window.start),
                   key=lambda r: (utc_datetime(r['published_at']), r['id']), reverse=True)
    name, head = payload['row']['full_name'], collection['default_branch_sha']
    for start in range(0, len(older), 25):
        batch = older[start:start + 25]
        adapter = ReleaseCommitClient(client, name, batch, head)
        for raw in batch:
            commit = parse_commit(adapter.get(f'/repos/{name}/commits/' + quote(raw['tag_name'], safe='')).data)
            comparison = adapter.get(f'/repos/{name}/compare/{commit.sha}...{head}', {'per_page': 1, 'page': 2}).data
            if comparison.get('status') not in ('ahead', 'identical', 'behind', 'diverged'):
                raise APIError('Ancestralidade da predecessora não comprovada.')
            if comparison['status'] in ('ahead', 'identical'):
                return (Release(raw['id'], raw['tag_name'], raw['published_at'], commit.sha, False,
                                raw.get('html_url', ''), raw.get('target_commitish', '')), *history)
    return history  # Primeira release real: sem predecessora, nunca inventada.


def predecessor_rows(history, payload, window):
    originals = {r['id']: r for r in payload.get('raw_releases', [])}
    return [{'full_name': payload['row']['full_name'], **asdict(r),
             'release_body': (originals.get(r.release_id) or {}).get('body') or ''}
            for r in history if not r.prerelease and utc_datetime(r.published_at) < window.start]


def collect_tags(cache, name, head, window, client=None):
    owner, repo = name.split('/')
    after, expected, refs, seen_cursors = None, None, {}, set()
    while True:
        data = graphql(cache, TAGS_QUERY, {'owner': owner, 'name': repo, 'after': after})
        connection = data['data']['repository']['refs']
        if expected is not None and expected != connection['totalCount']:
            raise APIError('Contagem de tags mudou durante paginação.')
        expected = connection['totalCount']
        for ref in connection['nodes']:
            if ref['id'] in refs and refs[ref['id']] != ref:
                raise APIError('Tag mudou durante paginação.')
            refs[ref['id']] = ref
        if not connection['pageInfo']['hasNextPage']:
            break
        after = connection['pageInfo']['endCursor']
        if not after or after in seen_cursors:
            raise APIError('Cursor de tags inválido/repetido.')
        seen_cursors.add(after)
    if len(refs) != expected:
        raise APIError('Lista de tags incompleta.')
    eligible = {}
    for identifier, ref in refs.items():
        target = ref['target']
        while isinstance(target, dict) and 'target' in target:
            target = target['target']
        if not isinstance(target, dict) or not target.get('authoredDate'):
            raise APIError('Tag sem commit resolvido; contexto requer nova coleta.')
        if window.contains(target['authoredDate']):
            eligible[identifier] = (ref, target)
    tags = []
    identifiers = sorted(eligible)
    for start in range(0, len(identifiers), 25):
        data = graphql(cache, MEMBERSHIP_QUERY, {'ids': identifiers[start:start + 25], 'head': head})
        nodes = data['data']['nodes']
        if len(nodes) != len(identifiers[start:start + 25]):
            raise APIError('Verificação de tags incompleta.')
        for identifier, node in zip(identifiers[start:start + 25], nodes):
            if (not node and client is None) or (node and node['id'] != identifier):
                raise APIError('Ref ausente ao verificar ancestralidade.')
            ref, commit = eligible[identifier]
            comparison = (node or {}).get('compare') or {}
            if (comparison.get('baseTarget', {}).get('oid') != commit['oid']
                    or comparison.get('headTarget', {}).get('oid') != head
                    or comparison.get('status') not in ('AHEAD', 'IDENTICAL', 'BEHIND', 'DIVERGED')):
                if client is None:
                    raise APIError('Comparação de tag não corresponde ao snapshot.')
                # A ref pode ter mudado. Verifica os SHAs já observados, sem
                # substituir o commit da tag nem inferir ancestralidade.
                path = f"/repos/{name}/compare/{commit['oid']}...{head}"
                actual = client.get(path, {'per_page': 1, 'page': 2}).data
                if not isinstance(actual, dict) or actual.get('status') not in ('ahead', 'identical', 'behind', 'diverged'):
                    raise APIError('REST não comprova ancestralidade dos SHAs do snapshot.')
                comparison = {'status': actual['status'].upper()}
            tags.append(Tag(ref['name'], commit['oid'], commit['authoredDate'],
                            comparison['status'] in ('AHEAD', 'IDENTICAL'), True))
    if len(tags) != len(eligible):
        raise APIError('Verificação de tags incompleta.')
    return sorted(tags, key=lambda t: (utc_datetime(t.author_date), t.name)), len(refs)


def comparison_query(pairs, cursors=None):
    definitions, aliases, variables = ['$owner:String!', '$name:String!'], [], {}
    cursors = cursors or {}
    for i, (previous, release) in enumerate(pairs):
        definitions.extend([f'$base{i}:String!', f'$head{i}:String!', f'$after{i}:String'])
        variables.update({f'base{i}': 'refs/tags/' + previous.tag_name,
                          f'head{i}': release.commit_sha, f'after{i}': cursors.get(i)})
        aliases.append(f'''a{i}:ref(qualifiedName:$base{i}) {{ compare(headRef:$head{i}) {{
 status baseTarget{{oid}} headTarget{{oid}} commits(first:100,after:$after{i}) {{
 totalCount pageInfo{{hasNextPage endCursor}} nodes{{{COMMIT_FIELDS}}} }} }} }}''')
    return ('query(' + ','.join(definitions) + '){repository(owner:$owner,name:$name){'
            + ' '.join(aliases) + '}}'), variables


class IntervalClient:
    """Adapta comparações GraphQL completas ao coletor de intervalos existente."""
    def __init__(self, client, name, history, window):
        self.client, self.responses = client, {}
        stable = sorted((r for r in history if not r.prerelease),
                        key=lambda r: (utc_datetime(r.published_at), r.release_id))
        pairs = [(a, b) for a, b in zip(stable, stable[1:])
                 if window.contains(b.published_at) and a.commit_sha != b.commit_sha]
        owner, repo = name.split('/')
        for offset in range(0, len(pairs), 8):
            batch = pairs[offset:offset + 8]
            query, variables = comparison_query(batch)
            variables.update(owner=owner, name=repo)
            data = graphql(client.cache, query, variables)['data']['repository']
            for i, (previous, release) in enumerate(batch):
                comparison = (data.get(f'a{i}') or {}).get('compare')
                if comparison is None:
                    continue  # Ref removida: usa REST por SHA, sem inferir ausência.
                if (comparison['baseTarget']['oid'] != previous.commit_sha
                        or comparison['headTarget']['oid'] != release.commit_sha):
                    continue  # Tag movida: o snapshot por SHA continua sendo a fonte.
                connection = comparison['commits']
                total, status = connection['totalCount'], comparison['status'].lower()
                if total > 1000:
                    # A API pode encerrar pageInfo em 1000 apesar de totalCount maior.
                    # O coletor REST existente verifica o total real por SHA.
                    continue
                commits = {c['oid']: rest_commit(c) for c in connection['nodes']}
                cursors = set()
                while connection['pageInfo']['hasNextPage']:
                    cursor = connection['pageInfo']['endCursor']
                    if not cursor or cursor in cursors:
                        raise APIError('Cursor de commits inválido/repetido.')
                    cursors.add(cursor)
                    query, variables = comparison_query([(previous, release)], {0: cursor})
                    variables.update(owner=owner, name=repo)
                    continuation = graphql(client.cache, query, variables)['data']['repository']['a0']['compare']
                    connection = continuation['commits']
                    if continuation['status'].lower() != status or connection['totalCount'] != total:
                        raise APIError('Comparação mudou durante paginação.')
                    for c in connection['nodes']:
                        normalized = rest_commit(c)
                        if c['oid'] in commits and commits[c['oid']] != normalized:
                            raise APIError('Commit inconsistente entre páginas.')
                        commits[c['oid']] = normalized
                if len(commits) != total:
                    continue  # Nunca adapta uma lista truncada como completa.
                path = f'/repos/{name}/compare/{previous.commit_sha}...{release.commit_sha}'
                self.responses[path] = APIResponse({'status': status, 'total_commits': total,
                                                    'commits': list(commits.values())},
                                                   {'X-Lab03-Source': 'graphql.Ref.compare.commits'})

    def get(self, path, params=None):
        if path in self.responses and params == {'per_page': 100, 'page': 1}:
            return self.responses[path]
        return self.client.get(path, params)


def enrich(client, payload, window, destination, *, git_repository=None):
    if destination.exists():
        old = json.loads(destination.read_text(encoding='utf-8'))
        if old['status'] in ('complete', 'metric_error', 'comparison_error'):
            if 'predecessors' not in old and payload is not None:
                old['predecessors'] = predecessor_rows(tuple(Release(**r) for r in payload['collection']['history']), payload, window)
                save_json(destination, old)
            return old
    name, collection = payload['row']['full_name'], payload['collection']
    result = {'full_name': name, 'status': 'pending_collection', 'error_detail': '', 'outputs': {}}
    try:
        history = with_predecessor(client, payload, window)
        result['predecessors'] = predecessor_rows(history, payload, window)
        if git_repository is None:
            tags, scanned = collect_tags(client.cache, name, collection['default_branch_sha'], window, client)
            adapter = None
        else:
            from .git_context import GitRepository, GitIntervalClient
            repository = GitRepository(git_repository, name, collection['default_branch_sha'])
            tags, scanned = repository.tags(window)
            snapshot_path = git_repository.parent / (name.replace('/', '--') + '_tags_snapshot.json')
            save_json(snapshot_path, {'remote_url': repository.remote_url,
                                      'default_branch_sha': collection['default_branch_sha'],
                                      'refs': repository.tag_snapshot})
            result['context_source'] = {'transport': 'github_git_objects', 'remote_url': repository.remote_url,
                                        'tag_snapshot': str(snapshot_path), 'git_directory': str(git_repository)}
            adapter = GitIntervalClient(client, name, history, window, repository)
        result['tags_scanned'] = scanned
        result['outputs']['tags_s01.csv'] = [{'full_name': name, **asdict(t)} for t in tags]
        if adapter is None:
            adapter = IntervalClient(client, name, history, window)
        intervals = collect_release_intervals(adapter, name, history, window)
        result['outputs']['release_intervals_s01.csv'] = [
            {'full_name': name, 'release_id': i.release.release_id, 'tag_name': i.release.tag_name,
             'previous_release_id': i.previous_release.release_id if i.previous_release else None,
             'previous_tag_name': i.previous_release.tag_name if i.previous_release else None,
             'base_sha': i.previous_release.commit_sha if i.previous_release else None,
             'head_sha': i.release.commit_sha, 'commit_count': len(i.commits) if i.status == 'complete' else None,
             'status': i.status, 'error_detail': i.error_detail, 'error_status': i.error_status} for i in intervals]
        result['outputs']['release_commits_s01.csv'] = [
            {'full_name': name, 'release_id': i.release.release_id, 'tag_name': i.release.tag_name, **asdict(c)}
            for i in intervals for c in i.commits]
        summary = dict.fromkeys(SUMMARY_FIELDS)
        summary.update(full_name=name, start_date=window.start_date, end_date=window.end_date,
                       default_branch=collection['default_branch'], default_branch_sha=collection['default_branch_sha'],
                       release_count=payload['row']['release_count'],
                       prerelease_count=sum(r.prerelease and window.contains(r.published_at) for r in history),
                       tag_count=sum(t.on_default_branch for t in tags),
                       releases_ignored_compare_404=sum(i.status == 'ignored_compare_404' for i in intervals))
        if any(i.status == 'error' for i in intervals):
            result.update(status='comparison_error', error_detail='; '.join(i.error_detail for i in intervals if i.status == 'error'))
        else:
            try:
                metrics = calculate_lead_time(intervals)
            except ValueError as error:
                result.update(status='metric_error', error_detail=str(error))
            else:
                result['status'] = 'complete'
                summary.update(releases_without_predecessor=metrics.releases_without_predecessor,
                               releases_without_new_commits=metrics.releases_without_new_commits)
                for variant, distribution in (('release', metrics.by_release), ('commit', metrics.by_commit)):
                    for field, value in asdict(distribution).items():
                        summary[f'lead_time_{variant}_{field}'] = value
                result['outputs']['lead_time_releases_s01.csv'] = [{'full_name': name, **r} for r in metrics.release_values]
                result['outputs']['lead_time_commits_s01.csv'] = [{'full_name': name, **r} for r in metrics.commit_values]
        summary.update(status=result['status'], error_detail=result['error_detail'])
        result['outputs']['lead_time_s01.csv'] = [summary]
    except (APIError, ValueError, KeyError, TypeError) as error:
        result.update(status='api_error' if isinstance(error, APIError) else 'data_error', error_detail=str(error))
    runs = payload['workflow_runs']
    episodes = recovery_episodes(runs)
    result['workflow_metrics'] = {'full_name': name, **asdict(change_failure_rate_a(runs)),
                                  **asdict(repository_recovery_time(episodes))}
    result['recovery_episodes'] = [{'full_name': name, **asdict(e)} for e in episodes]
    save_json(destination, result)
    return result


def export_enrichment(output, payloads, results):
    results = sorted(results, key=lambda r: r['full_name'].casefold())
    for filename, fields in OUTPUT_FIELDS.items():
        if filename in ('releases_s01.csv', 'release_validation_s01.csv'):
            continue  # Coleta elegível conserva notas e contagens completas de runs.
        rows = [r for result in results for r in result['outputs'].get(filename, [])]
        if filename == 'excluded_releases_s01.csv':
            rows = [{'full_name': p['row']['full_name'], **r} for p in payloads for r in p['collection']['excluded_releases']]
        write_csv(output / filename, fields, rows)
    write_csv(output / 'workflow_metrics_s02.csv',
              ('full_name', 'successes', 'failures', 'ignored', 'cfr', 'n_episodes', 'n_censored', 'median_hours', 'censored_proportion'),
              (r['workflow_metrics'] for r in results))
    write_csv(output / 'recovery_episodes_s02.csv',
              ('full_name', 'workflow_id', 'failure_started_at', 'recovered_at', 'hours'),
              (e for r in results for e in r['recovery_episodes']))
    write_csv(output / 'release_predecessors_s02.csv',
              ('full_name', 'release_id', 'tag_name', 'published_at', 'commit_sha', 'prerelease',
               'html_url', 'target_commitish', 'release_body'),
              (p for r in results for p in r.get('predecessors', [])))
    save_json(output / 'enrichment_manifest_s02.json', {
        'repositories_attempted': len(results),
        'statuses': {s: sum(r['status'] == s for r in results) for s in sorted({r['status'] for r in results})},
        'tags_date_source': 'commit.authoredDate', 'tags_scope': 'in_window_only;all_refs_scanned_in_raw_cache',
        'corrective_heuristic_executed': False,
        'repositories': [{k: v for k, v in r.items() if k not in ('outputs', 'workflow_metrics', 'recovery_episodes', 'predecessors')} for r in results]})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--raw-dir', type=Path, default=Path('data/raw/s02'))
    parser.add_argument('--output-dir', type=Path, default=Path('data/processed/s02'))
    args = parser.parse_args(argv)
    manifest = json.loads((args.output_dir / 'collection_manifest_s02.json').read_text(encoding='utf-8'))
    window = ObservationWindow(**manifest['window'])
    payloads = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((args.raw_dir / 'checkpoints').glob('*.json'))]
    payloads = [p for p in payloads if p['row']['status'] == 'selected']
    client = ResilientClient(PacedClient(GitHubClient()), CacheStore(args.raw_dir / 'cache'), sleep=safe_sleep)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(enrich, client, p, window, args.raw_dir / 'enrichment' / f"{p['row']['repository_id']}.json") for p in payloads]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if len(results) % 8 == 0 or len(results) == len(payloads):
                export_enrichment(args.output_dir, payloads, results)
            print(f"CONTEXT {len(results)}/{len(payloads)} {result['full_name']} {result['status']}", flush=True)
    return int(any(r['status'] not in ('complete', 'metric_error', 'comparison_error') for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
