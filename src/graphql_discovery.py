"""Descoberta e releases GraphQL com adaptação aos componentes REST S01."""

from urllib.parse import parse_qs, quote, urlencode, urlsplit

from .github_client import APIError, APIResponse
from .graphql_context import graphql

SEARCH = '''query($q:String!,$after:String) { search(query:$q,type:REPOSITORY,first:100,after:$after) {
 repositoryCount pageInfo{hasNextPage endCursor} nodes{...on Repository{
 id databaseId name nameWithOwner url description createdAt stargazerCount isPrivate isFork isArchived
 owner{login} primaryLanguage{name} defaultBranchRef{name}
 }} } }'''
RELEASES = '''query($id:ID!,$after:String) { node(id:$id) { ...on Repository{
 defaultBranchRef{name target{...on Commit{oid authoredDate committedDate message url}}}
 releases(first:100,after:$after,orderBy:{field:CREATED_AT,direction:DESC}){
 totalCount pageInfo{hasNextPage endCursor} nodes{
 id databaseId name description isDraft isPrerelease tagName publishedAt url
 }} } } }'''


class SearchClient:
    def __init__(self, client):
        self.client, self.cache = client, client.cache

    def get(self, path, params=None):
        if '/search/repositories' not in path:
            return self.client.get(path, params)
        supplied = dict(params or {})
        if not supplied:
            supplied = {k: v[0] for k, v in parse_qs(urlsplit(path).query).items()}
        query, after = supplied['q'], supplied.get('after')
        data = graphql(self.cache, SEARCH, {'q': query + ' sort:stars-desc', 'after': after})['data']['search']
        items = []
        for r in data['nodes']:
            if not r:
                raise APIError('Repositório ausente na busca GraphQL.')
            items.append({'id': r['databaseId'], 'node_id': r['id'], 'name': r['name'],
                          'full_name': r['nameWithOwner'], 'html_url': r['url'],
                          'description': r['description'], 'created_at': r['createdAt'],
                          'stargazers_count': r['stargazerCount'], 'private': r['isPrivate'],
                          'fork': r['isFork'], 'archived': r['isArchived'], 'owner': r['owner'],
                          'language': (r['primaryLanguage'] or {}).get('name'),
                          'default_branch': (r['defaultBranchRef'] or {}).get('name', '')})
        headers = {}
        if data['pageInfo']['hasNextPage']:
            cursor = data['pageInfo']['endCursor']
            if not cursor:
                raise APIError('Busca GraphQL sem cursor para próxima página.')
            link = 'https://api.github.com/search/repositories?' + urlencode({'q': query, 'after': cursor})
            headers['Link'] = '<' + link + '>; rel="next"'
        return APIResponse({'total_count': data['repositoryCount'], 'incomplete_results': False, 'items': items}, headers)


class RepositoryReleaseClient:
    def __init__(self, client, candidate):
        self.client, self.cache = client, client.cache
        self.root = '/repos/' + candidate['full_name']
        self.releases, self.branch, self.branch_name = [], None, None
        after, expected, cursors, seen = None, None, set(), set()
        while True:
            repository = graphql(self.cache, RELEASES, {'id': candidate['node_id'], 'after': after})['data']['node']
            if not repository:
                raise APIError('Repositório removido ou inacessível na consulta GraphQL.')
            branch = repository['defaultBranchRef']
            if branch is None:
                raise ValueError('Default branch sem referência válida.')
            if self.branch_name is not None and self.branch_name != branch['name']:
                raise APIError('Nome da default branch mudou durante paginação.')
            # O primeiro SHA é o snapshot. Novos pushes durante a paginação
            # não mudam esse snapshot nem tornam incompletas as releases.
            if self.branch is None:
                self.branch, self.branch_name = branch['target'], branch['name']
            connection = repository['releases']
            if expected is not None and expected != connection['totalCount']:
                raise APIError('Contagem de releases mudou durante paginação.')
            expected = connection['totalCount']
            for r in connection['nodes']:
                if r['databaseId'] in seen:
                    raise APIError('Release repetida na paginação GraphQL.')
                seen.add(r['databaseId'])
                self.releases.append({'id': r['databaseId'], 'node_id': r['id'], 'name': r['name'],
                                      'body': r['description'], 'draft': r['isDraft'],
                                      'prerelease': r['isPrerelease'], 'tag_name': r['tagName'],
                                      'published_at': r['publishedAt'], 'html_url': r['url'],
                                      'target_commitish': ''})
            if not connection['pageInfo']['hasNextPage']:
                break
            after = connection['pageInfo']['endCursor']
            if not after or after in cursors:
                raise APIError('Cursor de releases inválido/repetido.')
            cursors.add(after)
        if len(self.releases) != expected:
            raise APIError('Lista de releases GraphQL incompleta.')

    def get(self, path, params=None):
        if path == self.root + '/releases' and params and params.get('page') == 1:
            return APIResponse(self.releases, {'X-Lab03-Source': 'graphql.Repository.releases'})
        if path == self.root + '/commits/' + quote(self.branch_name, safe='') and params is None:
            c = self.branch
            return APIResponse({'sha': c['oid'], 'html_url': c['url'],
                                'commit': {'author': {'date': c['authoredDate']},
                                           'committer': {'date': c['committedDate']}, 'message': c['message']}},
                               {'X-Lab03-Source': 'graphql.Repository.defaultBranchRef'})
        return self.client.get(path, params)
