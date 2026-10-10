"""Coleta real retomável até >=300 elegíveis, reutilizando componentes da S01."""

from __future__ import annotations

import argparse
import json
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from .cache import CacheStore, ResilientClient
from .config import load_config
from .funnel import TemporalEvidence, classify
from .github_client import APIError, GitHubClient, RateLimitError, header, iter_pages
from .graphql_context import ReleaseCommitClient
from .graphql_discovery import RepositoryReleaseClient, SearchClient
from .metadata import parse_metadata
from .pipeline import REPOSITORY_FIELDS, collect_metadata, write_csv
from .releases import collect_releases_and_tags
from .temporal import ObservationWindow
from .workflow_adaptive import collect_runs


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


class PacedClient:
    """Limita a taxa agregada, compartilhando quota entre threads; nunca loga requests."""
    def __init__(self, client):
        self.client, self.lock = client, threading.Lock()
        self.next_call = 0.0
        self.remaining, self.reset = None, 0
        self.calls = 0

    def get(self, path, params=None):
        with self.lock:
            wait = max(0, self.next_call - time.monotonic())
            self.next_call = max(self.next_call, time.monotonic()) + 0.12
            if self.remaining is not None and self.remaining <= 8 and time.time() < self.reset:
                wait = max(wait, self.reset - time.time() + 2)
        if wait:
            safe_sleep(wait)
        response = self.client.get(path, params)
        with self.lock:
            self.calls += 1
            if header(response.headers, 'X-RateLimit-Resource') == 'core':
                remaining = header(response.headers, 'X-RateLimit-Remaining')
                reset = header(response.headers, 'X-RateLimit-Reset')
                if remaining.isdigit() and reset.isdigit():
                    if int(reset) != self.reset:
                        self.remaining = int(remaining)
                    else:
                        self.remaining = min(self.remaining if self.remaining is not None else int(remaining), int(remaining))
                    self.reset = int(reset)
        return response


def safe_sleep(seconds):
    if seconds > 5:
        print(f'Espera de quota/backoff: {int(seconds)} segundos; checkpoints preservados.', flush=True)
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        time.sleep(max(0, min(30, until - time.monotonic())))


def candidate_stream(client, queries, low=1001, high=2000, *, bands=None, pushed_since=None):
    """Fatias inclusivas de estrelas; subdivide até eliminar o teto de 1000."""
    def slice_candidates(lo, hi):
        query = f'stars:{lo}..{hi} is:public'
        if pushed_since:
            query += f' pushed:>={pushed_since}'
        params = {'q': query, 'sort': 'stars', 'order': 'desc', 'per_page': 100, 'page': 1}
        pages = iter_pages(client, '/search/repositories', params, max_pages=10)
        first = next(pages)
        data = first.data
        if not isinstance(data, dict) or not isinstance(data.get('items'), list) or type(data.get('total_count')) is not int:
            raise APIError('Busca sem items/total_count válidos.')
        count = data['total_count']
        queries.append({'query': query, 'total_count': count, 'incomplete_results': bool(data.get('incomplete_results'))})
        if count > 1000 or data.get('incomplete_results'):
            if lo == hi:
                raise APIError(f'Fatia {query} ainda supera o teto/retorna incomplete_results; subdivisão por criação necessária.')
            middle = (lo + hi) // 2
            yield from slice_candidates(lo, middle)
            yield from slice_candidates(middle + 1, hi)
            return
        import itertools
        for response in itertools.chain([first], pages):
            if response.data.get('incomplete_results'):
                raise APIError('Busca incompleta, não prosseguir silenciosamente.')
            yield from response.data['items']
    if bands is not None:
        for low, high in bands:
            yield from slice_candidates(low, high)
        return
    while low <= 2147483647:
        yield from slice_candidates(low, min(high, 2147483647))
        low, high = high + 1, high * 2


def process_candidate(client, candidate, config, window, collected_at, checkpoint, *, graphql_discovery=False):
    if checkpoint.exists():
        old = json.loads(checkpoint.read_text(encoding='utf-8'))
        if old['row']['status'] in ('selected', 'discarded'):
            return old
    row = dict.fromkeys(REPOSITORY_FIELDS)
    row.update(full_name=candidate.get('full_name'), collected_at=collected_at, processed=True,
               metadata_complete=False, status='pending_validation', reasons='', error_detail='')
    payload = {'row': row, 'candidate': {key: candidate.get(key) for key in
               ('id', 'full_name', 'description', 'language', 'html_url', 'default_branch', 'private', 'fork', 'archived')},
               'collection': None, 'raw_releases': [], 'workflow_runs': [], 'workflow_queries': []}
    try:
        if not graphql_discovery:
            row.update(collect_metadata(client, [candidate], config, collected_at, raise_unauthorized=True)[0])
        if graphql_discovery:
            row.update(parse_metadata(candidate, collected_at))
            client = RepositoryReleaseClient(client, candidate)
            candidate = {**candidate, 'default_branch': client.branch_name}
            row['default_branch'] = client.branch_name
        if candidate.get('private') is not False:
            raise ValueError('Candidato sem comprovação de acesso público.')
        if row['stargazers_count'] is not None and row['stargazers_count'] <= 1000:
            row.update(status='discarded', reasons='insufficient_stars')
            save_json(checkpoint, payload)
            return payload
        if row['status'] not in ('discarded', 'api_error', 'metadata_error'):
            root = f"/repos/{row['full_name']}"
            # Pré-filtro barato. É apenas reprovação por contagem; não declara ancestralidade.
            raw_releases = []
            for page in iter_pages(client, root + '/releases', {'per_page': 100, 'page': 1}):
                if not isinstance(page.data, list):
                    raise ValueError('Resposta de releases inválida.')
                raw_releases.extend(page.data)
            payload['raw_releases'] = raw_releases
            for release in raw_releases:
                if (not isinstance(release, dict) or type(release.get('id')) is not int
                        or type(release.get('draft')) is not bool or type(release.get('prerelease')) is not bool):
                    raise ValueError('Release sem ID/flags válidos; contagem não medida.')
                if not release['draft']:
                    # Valida timestamp também fora da janela, sem ignorar registros incompletos.
                    window.contains(release.get('published_at'))
            payload['release_prefilter_measured'] = True
            possible = [r for r in raw_releases if r.get('draft') is False and r.get('prerelease') is False
                        and r.get('published_at') and window.contains(r['published_at'])]
            if len({r['id'] for r in possible}) < 5:
                # Zero aqui é contagem real de publicadas estáveis, suficiente para reprovar;
                # não rotula as releases restantes como ancestrais da branch.
                row.update(status='discarded', reasons='insufficient_releases', release_count=len({r['id'] for r in possible}))
                payload['release_count_definition'] = 'published_stable_upper_bound_before_ancestry'
            else:
                if graphql_discovery:
                    row.update(collect_metadata(client, [candidate], config, collected_at, raise_unauthorized=True)[0])
                    if row['status'] in ('discarded', 'api_error', 'metadata_error'):
                        save_json(checkpoint, payload)
                        return payload
                runs, reports = collect_runs(client, row['full_name'], row['default_branch'], config.start_date, config.end_date)
                payload.update(workflow_runs=runs, workflow_queries=reports)
                valid = sum(r['status_class'] is not None for r in runs)
                row['valid_workflow_runs'] = valid
                if valid < 50:
                    row.update(status='discarded', reasons='insufficient_workflow_runs')
                else:
                    window_releases = [r for r in raw_releases if not r['draft']
                                       and window.contains(r['published_at'])]
                    snapshot = client.get(root + '/commits/' + quote(row['default_branch'], safe='')).data['sha']
                    context_client = ReleaseCommitClient(client, row['full_name'], window_releases, snapshot)
                    collection = collect_releases_and_tags(context_client, row['full_name'], row['default_branch'], window,
                                                          collect_tags=False, window_only=True, include_predecessor=False)
                    payload['collection'] = asdict(collection)
                    classify(row, config, TemporalEvidence(row['full_name'], config.start_date, config.end_date,
                                                          len(collection.in_window(window)), valid))
    except APIError as error:
        row.update(status='api_error', reasons='api_error', error_detail=str(error))
        if error.status == 401:
            save_json(checkpoint, payload)
            raise
    except (ValueError, KeyError, TypeError) as error:
        row.update(status='metadata_error', reasons='metadata_error', error_detail=str(error))
    save_json(checkpoint, payload)
    return payload


def build_s02_funnel(payloads, window):
    """Funil de aprovações comprovadas; testes pulados permanecem não medidos.

    O pré-filtro GraphQL pode reprovar releases antes de Actions. Portanto,
    pending em Actions inclui esses descartes já definitivos, sem assumir
    que ausência de medição equivale a ausência de Actions.
    """
    remaining, stages = list(payloads), []
    def stage(name, predicate, reason):
        nonlocal remaining
        flags = [(p, predicate(p)) for p in remaining]
        passed = [p for p, flag in flags if flag is True]
        stages.append({'stage': name, 'count': len(passed),
                       'discarded': sum(flag is False for _, flag in flags),
                       'pending': sum(flag is None for _, flag in flags), 'reason': reason})
        remaining = passed
    stage('candidates', lambda p: True, 'unique_completed_attempts_not_search_hit_count')
    stage('public_verified', lambda p: None if type(p['candidate'].get('private')) is not bool
          else p['candidate']['private'] is False,
          'public_api_metadata')
    stage('default_branch_identified', lambda p: None if p['row']['default_branch'] is None
          else bool(p['row']['default_branch'].strip()),
          'valid_reference_is_additionally_checked_before_final_eligibility')
    stage('actions_enabled', lambda p: p['row']['has_github_actions'],
          'unmeasured_includes_early_release_rejections;not_assumed_false')
    def release_prefilter(p):
        measured = (p.get('release_prefilter_measured') or p.get('release_count_definition')
                    or p['raw_releases'] or p.get('workflow_queries') or p['collection'])
        if not measured:
            return None
        count = len({r['id'] for r in p['raw_releases'] if r.get('draft') is False
                     and r.get('prerelease') is False and r.get('published_at') and window.contains(r['published_at'])})
        return count >= 5
    stage('published_stable_release_prefilter', release_prefilter, 'minimum_5_before_ancestry')
    stage('workflow_filter', lambda p: None if p['row']['valid_workflow_runs'] is None
          else p['row']['valid_workflow_runs'] >= 50, 'minimum_50_success_or_failure_push_runs_on_default_branch')
    stage('release_ancestry_filter', lambda p: None if p['collection'] is None else
          sum(not r['prerelease'] and window.contains(r['published_at']) for r in p['collection']['history']) >= 5,
          'minimum_5_published_stable_releases_ancestral_to_recorded_default_branch_snapshot')
    stages.append({'stage': 'final_sample', 'count': sum(p['row']['status'] == 'selected' for p in payloads),
                   'discarded': sum(p['row']['status'] == 'discarded' for p in payloads),
                   'pending': sum(p['row']['status'] not in ('selected', 'discarded') for p in payloads),
                   'reason': 'confirmed_eligible_lower_bound;unresolved_candidates_are_pending'})
    return stages


def export_outputs(output, checkpoints, manifest):
    payloads = [json.loads(path.read_text(encoding='utf-8')) for path in sorted(checkpoints.glob('*.json'))]
    rows = [payload['row'] for payload in payloads]
    write_csv(output / 'repositories_s01.csv', REPOSITORY_FIELDS, rows)
    write_csv(output / 'repositories_final_s02.csv', (*REPOSITORY_FIELDS, 'description', 'private', 'default_branch_sha'),
              [{**row, 'description': payload['candidate'].get('description') or '',
                'private': payload['candidate'].get('private'),
                'default_branch_sha': (payload['collection'] or {}).get('default_branch_sha', '')}
               for row, payload in zip(rows, payloads) if row['status'] == 'selected'])
    # Funil S02 registra filtros na ordem realmente executada: pré-filtro de releases,
    # runs, ancestralidade das releases. Não converte ausência de medição em zero.
    window = ObservationWindow(**manifest['window'])
    funnel = build_s02_funnel(payloads, window)
    selected = sum(row['status'] == 'selected' for row in rows)
    write_csv(output / 'selection_funnel_s02.csv', tuple(funnel[0]), funnel)
    fields = ('full_name', 'release_id', 'tag_name', 'published_at', 'commit_sha', 'prerelease',
              'html_url', 'target_commitish', 'in_window', 'release_name', 'release_body')
    releases = []
    for payload in payloads:
        if payload['row']['status'] != 'selected':
            continue
        raw_map = {r['id']: r for r in payload['raw_releases']}
        for release in payload['collection']['history']:
            original = raw_map[release['release_id']]
            releases.append({'full_name': payload['row']['full_name'], **release,
                             'in_window': window.contains(release['published_at']),
                             'release_name': original.get('name') or '', 'release_body': original.get('body') or ''})
    write_csv(output / 'releases_s01.csv', fields, releases)
    run_fields = ('full_name', 'id', 'workflow_id', 'head_branch', 'event', 'conclusion', 'status_class', 'created_at', 'run_started_at', 'updated_at')
    write_csv(output / 'workflow_runs_s02.csv', run_fields,
              ({'full_name': p['row']['full_name'], **run} for p in payloads if p['row']['status'] == 'selected' for run in p['workflow_runs']))
    manifest.update(candidates_processed=len(rows), final_sample=selected, target_met=selected >= manifest['target'],
                    errors=sum(r['status'] in ('api_error', 'metadata_error') for r in rows),
                    statuses={status: sum(r['status'] == status for r in rows) for status in sorted({r['status'] for r in rows})})
    save_json(output / 'collection_manifest_s02.json', manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=int, default=300)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--output-dir', type=Path, default=Path('data/processed/s02'))
    parser.add_argument('--raw-dir', type=Path, default=Path('data/raw/s02'))
    args = parser.parse_args(argv)
    if args.target < 300 or not 1 <= args.workers <= 8:
        parser.error('target deve ser >=300 e workers entre 1 e 8.')
    config = load_config()
    window = ObservationWindow(config.start_date, config.end_date)
    output, raw = args.output_dir, args.raw_dir
    if output.resolve() == Path('data/processed/smoke').resolve():
        parser.error('Nunca sobrescrever o smoke.')
    checkpoints = raw / 'checkpoints'
    checkpoints.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / 'collection_manifest_s02.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['window'] != asdict(window):
            parser.error('Checkpoint usa outra janela.')
        manifest['target'] = args.target
    else:
        manifest = {'collected_at': datetime.now(timezone.utc).isoformat(), 'window': asdict(window),
                    'window_source': 'group_defined_on_2026-10-10', 'target': args.target,
                    'queries': [], 'selection_order': 'ascending_star_slices_then_descending_stars_within_slice',
                    'workflow_valid_definition': 'push_default_branch_success_or_failure',
                    'enrichment_status': 'pending_tags_and_release_commits'}
    paced = PacedClient(GitHubClient())
    client = ResilientClient(paced, CacheStore(raw / 'cache'), sleep=safe_sleep)
    queries = list(manifest.get('queries', []))
    seen_ids, seen_names = set(), set()
    try:
        if export_outputs(output, checkpoints, manifest)['target_met']:
            return 0
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            # Prioriza a faixa intermediária para não gastar toda a quota em
            # um único monorepo. Nenhuma faixa >1000 estrelas é excluída.
            bands = [(5001, 10000), (10001, 20000), (20001, 50000),
                     (50001, 2147483647), (2001, 5000), (1001, 2000)]
            manifest['search_bands'] = bands
            manifest['selection_order'] = 'documented_star_bands;descending_stars_within_leaf_slice'
            manifest['search_necessary_prefilter'] = 'pushed_at>=window_start (50 push runs require a push)'
            manifest['discovery_api'] = 'graphql;release_prefilter_before_actions_and_contributors'
            candidates = candidate_stream(SearchClient(client), queries, bands=bands, pushed_since=config.start_date)
            pending = set()
            stopping = False
            completed = 0

            def submit_next():
                for candidate in candidates:
                    key, identifier = candidate['full_name'].casefold(), candidate['id']
                    if identifier in seen_ids or key in seen_names:
                        continue
                    seen_ids.add(identifier)
                    seen_names.add(key)
                    checkpoint = checkpoints / f'{identifier}.json'
                    if checkpoint.exists() and json.loads(checkpoint.read_text(encoding='utf-8'))['row']['status'] in ('selected', 'discarded'):
                        continue
                    pending.add(pool.submit(process_candidate, client, candidate, config, window,
                                            manifest['collected_at'], checkpoint, graphql_discovery=True))
                    return

            for _ in range(args.workers * 2):
                submit_next()
            while pending:
                done, _ = wait(pending, return_when=FIRST_COMPLETED)
                pending.difference_update(done)
                for future in done:
                    p = future.result()
                    completed += 1
                    print(f"{p['row']['status']}: {p['row']['full_name']} releases={p['row']['release_count']} valid_runs={p['row']['valid_workflow_runs']}", flush=True)
                    if completed % 8 == 0 or p['row']['status'] == 'selected':
                        manifest['queries'] = queries
                        result = export_outputs(output, checkpoints, manifest)
                        print(f"PROGRESS candidates={result['candidates_processed']} eligible={result['final_sample']} target={args.target} calls={paced.calls}", flush=True)
                        stopping = stopping or result['target_met']
                    if not stopping:
                        submit_next()
            return 0 if manifest.get('target_met') else 1
    except (APIError, ValueError, KeyboardInterrupt) as error:
        manifest['interruption'] = type(error).__name__ + ': ' + str(error)
        print('Coleta interrompida: ' + manifest['interruption'], flush=True)
    finally:
        manifest['queries'] = queries
        export_outputs(output, checkpoints, manifest)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
