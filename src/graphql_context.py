"""Resolução factual em lote de tagCommit, preservando coletores REST existentes."""

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .github_client import APIError, APIResponse, header

QUERY = '''query($ids: [ID!]!, $head: String!) {
  nodes(ids: $ids) { ... on Release { id tagName tagCommit {
    oid authoredDate committedDate message url
  } tag { compare(headRef: $head) { status baseTarget { oid } headTarget { oid } } } } }
}'''


def graphql(cache, query, variables):
    params = {'query': query, 'variables': variables}
    cached = cache.get('/graphql', params) if cache else None
    if cached is not None:
        return cached.data
    # Só o corpo query/variables é serializado; Authorization permanece em memória.
    headers = {'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'].strip(),
               'Content-Type': 'application/json', 'User-Agent': 'lab03-s02-context'}
    request = Request('https://api.github.com/graphql', data=json.dumps(params).encode(), headers=headers, method='POST')
    for attempt in range(5):
        delay = 2 ** attempt
        try:
            with urlopen(request, timeout=90) as response:
                data = json.loads(response.read())
                stored = APIResponse(data, dict(response.headers), response.status)
        except HTTPError as error:
            if error.code == 403 and error.headers.get('X-RateLimit-Remaining') == '0':
                delay = max(2, float(error.headers.get('X-RateLimit-Reset', time.time() + 60)) - time.time() + 2)
            elif error.code in (403, 429) and (error.headers.get('Retry-After') or '').isdigit():
                delay = max(1, int(error.headers['Retry-After']))
            elif error.code == 403 and 'secondary rate limit' in error.read(4096).decode('utf-8', errors='replace').lower():
                delay = 60
            elif error.code not in (429, 500, 502, 503, 504):
                raise APIError(f'GraphQL retornou HTTP {error.code}.', status=error.code) from None
        except (URLError, OSError, ValueError):
            pass
        else:
            if not data.get('errors') and isinstance(data.get('data'), dict):
                break
            if header(stored.headers, 'X-RateLimit-Remaining') == '0':
                delay = max(2, float(header(stored.headers, 'X-RateLimit-Reset') or time.time() + 60) - time.time() + 2)
            elif header(stored.headers, 'Retry-After').isdigit():
                delay = max(1, int(header(stored.headers, 'Retry-After')))
            elif any(e.get('type') == 'RATE_LIMITED' for e in data.get('errors', [])):
                delay = 60
        if attempt == 4:
            raise APIError('GraphQL indisponível ou retornou erros; detalhes não registrados.')
        if delay > 60:
            print(f'Espera de quota GraphQL: {int(delay)} segundos; checkpoints preservados.', flush=True)
        # A espera não serializa request, headers ou segredo.
        while delay > 0:
            interval = min(30, delay)
            time.sleep(interval)
            delay -= interval
    if cache:
        cache.set('/graphql', params, stored)
    return data


def query_nodes(cache, identifiers, head):
    data = graphql(cache, QUERY, {'ids': identifiers, 'head': head})
    if not isinstance(data['data'].get('nodes'), list):
        raise APIError('GraphQL sem nodes.')
    return data


class ReleaseCommitClient:
    def __init__(self, client, name, releases, head):
        self.client, self.resolved = client, {}
        identifiers = sorted({r['node_id'] for r in releases if r.get('node_id') and not r.get('draft')})
        for start in range(0, len(identifiers), 25):
            data = query_nodes(getattr(client, 'cache', None), identifiers[start:start + 25], head)
            for node in data['data']['nodes']:
                if node is None or not node.get('tagCommit'):
                    continue  # O coletor REST fará a resolução e registrará erro se necessário.
                commit = node['tagCommit']
                rest_shape = {'sha': commit['oid'], 'html_url': commit['url'],
                              'commit': {'author': {'date': commit['authoredDate']},
                                         'committer': {'date': commit['committedDate']}, 'message': commit['message']}}
                root = f'/repos/{name}/commits/'
                response = APIResponse(rest_shape, {'X-Lab03-Source': 'graphql.Release.tagCommit'})
                self.resolved[root + quote(node['tagName'], safe='')] = response
                self.resolved[root + quote(commit['oid'], safe='')] = response
                comparison = (node.get('tag') or {}).get('compare') or {}
                if (comparison.get('baseTarget', {}).get('oid') == commit['oid']
                        and comparison.get('headTarget', {}).get('oid') == head
                        and comparison.get('status') in ('AHEAD', 'IDENTICAL', 'BEHIND', 'DIVERGED')):
                    path = f"/repos/{name}/compare/{commit['oid']}...{head}"
                    self.resolved[path] = APIResponse({'status': comparison['status'].lower()},
                                                     {'X-Lab03-Source': 'graphql.Ref.compare'})

    def get(self, path, params=None):
        if path in self.resolved and (params is None or (params.get('per_page') == 1 and params.get('page') == 2)):
            return self.resolved[path]
        return self.client.get(path, params)
