"""Contexto factual em lote de um cache Git completo, sem árvores de arquivos."""

import io
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .github_client import APIError, APIResponse
from .temporal import Tag, utc_datetime


class GitRepository:
    def __init__(self, directory, name, snapshot):
        self.directory, self.name, self.snapshot = directory, name, snapshot
        self.remote_url = f'https://github.com/{name}.git'
        if self.run(['config', '--get', 'remote.origin.url']).decode().strip() != self.remote_url:
            raise APIError('Cache Git não corresponde ao repositório público esperado.')
        if self.run(['rev-parse', '--is-shallow-repository']).strip() != b'false':
            raise APIError('Cache Git raso: ancestralidade não comprovada.')
        self.run(['cat-file', '-e', snapshot + '^{commit}'])
        self.ancestors = set(self.run(['rev-list', snapshot]).decode().splitlines())

    def command(self, args, incoming=None, allowed=(0,)):
        environment = {k: v for k, v in os.environ.items() if k not in ('GITHUB_TOKEN', 'GH_TOKEN')}
        environment['GIT_TERMINAL_PROMPT'] = '0'
        result = subprocess.run(['git', '--git-dir', str(self.directory), *args], input=incoming,
                                capture_output=True, env=environment)
        if result.returncode not in allowed:
            raise APIError(f'Comando de objetos Git falhou (código {result.returncode}); contexto incompleto.')
        return result

    def run(self, args, incoming=None):
        return self.command(args, incoming).stdout

    def objects(self, identifiers):
        identifiers = list(dict.fromkeys(identifiers))
        if not identifiers:
            return {}
        stream = io.BytesIO(self.run(['cat-file', '--batch'], ('\n'.join(identifiers) + '\n').encode()))
        result = {}
        for identifier in identifiers:
            fields = stream.readline().split()
            if len(fields) != 3 or fields[0].decode() != identifier or fields[1] != b'commit':
                raise APIError('Tag/intervalo sem objeto commit Git completo.')
            body = stream.read(int(fields[2]))
            if stream.read(1) != b'\n':
                raise APIError('Objeto Git truncado.')
            headers, separator, message = body.partition(b'\n\n')
            if not separator:
                raise APIError('Cabeçalho de commit Git inválido.')
            parsed = dict(line.split(b' ', 1) for line in headers.splitlines()
                          if line.startswith((b'author ', b'committer ', b'encoding ')))
            def date(field):
                epoch = int(parsed[field].rsplit(b' ', 2)[1])
                return datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace('+00:00', 'Z')
            result[identifier] = {'sha': identifier, 'html_url': f'https://github.com/{self.name}/commit/{identifier}',
                'commit': {'author': {'date': date(b'author')}, 'committer': {'date': date(b'committer')},
                           'message': message.decode(parsed.get(b'encoding', b'utf-8').decode('ascii'), errors='replace')}}
        return result

    def tags(self, window):
        output = self.command(['show-ref', '--tags', '--dereference'], allowed=(0, 1)).stdout
        refs, peeled = {}, {}
        for line in output.decode().splitlines():
            sha, ref = line.split(' ', 1)
            if ref.endswith('^{}'):
                peeled[ref[:-3]] = sha
            else:
                refs[ref] = sha
        targets = {ref: peeled.get(ref, sha) for ref, sha in refs.items()}
        commits = self.objects(targets.values())
        tags, snapshot = [], []
        for ref, target in sorted(targets.items()):
            date = commits[target]['commit']['author']['date']
            on_branch = target in self.ancestors
            snapshot.append({'ref': ref, 'object_sha': refs[ref], 'commit_sha': target,
                             'author_date': date, 'on_default_branch': on_branch})
            if window.contains(date):
                tags.append(Tag(ref[len('refs/tags/'):], target, date, on_branch, True))
        self.tag_snapshot = snapshot
        return tags, len(refs)

    def is_ancestor(self, base, head):
        return self.command(['merge-base', '--is-ancestor', base, head], allowed=(0, 1)).returncode == 0

    def compare(self, base, head):
        status = ('identical' if base == head else 'ahead' if self.is_ancestor(base, head)
                  else 'behind' if self.is_ancestor(head, base) else 'diverged')
        identifiers = self.run(['rev-list', base + '..' + head]).decode().splitlines()
        commits = list(self.objects(identifiers).values())
        return APIResponse({'status': status, 'total_commits': len(commits), 'commits': commits},
                           {'X-Lab03-Source': 'github_git_objects'})


class GitIntervalClient:
    def __init__(self, client, name, history, window, repository):
        self.client, self.responses = client, {}
        stable = sorted((r for r in history if not r.prerelease),
                        key=lambda r: (utc_datetime(r.published_at), r.release_id))
        pairs = {(a.commit_sha, b.commit_sha) for a, b in zip(stable, stable[1:])
                 if window.contains(b.published_at) and a.commit_sha != b.commit_sha}
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(repository.compare, a, b): (a, b) for a, b in sorted(pairs)}
            for number, future in enumerate(as_completed(futures), 1):
                a, b = futures[future]
                self.responses[f'/repos/{name}/compare/{a}...{b}'] = future.result()
                if number % 500 == 0:
                    print(f'GIT_CONTEXT intervals {number}/{len(pairs)}', flush=True)

    def get(self, path, params=None):
        if path in self.responses and params == {'per_page': 100, 'page': 1}:
            return self.responses[path]
        return self.client.get(path, params)
