"""Paginação adaptativa dos mesmos runs da S01, sem truncar consultas >1000."""

from datetime import date, datetime, timedelta, timezone

from .github_client import APIError, iter_pages
from .temporal import utc_datetime
from .workflow_runs import WorkflowRunError, parse_workflow_run


def collect_runs(client, name, branch, start_date, end_date):
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if end <= start:
        raise ValueError('Janela inválida.')
    indexed, reports = {}, []

    def collect(lo, hi):
        precise = isinstance(lo, datetime)
        created = (f'{lo:%Y-%m-%dT%H:%M:%SZ}..{hi - timedelta(seconds=1):%Y-%m-%dT%H:%M:%SZ}'
                   if precise else f'{lo}..{hi - timedelta(days=1)}')
        params = {'branch': branch, 'event': 'push', 'created': created, 'per_page': 100}
        pages = iter_pages(client, f'/repos/{name}/actions/runs', params)
        first = next(pages)
        data = first.data
        if not isinstance(data, dict) or type(data.get('total_count')) is not int or data['total_count'] < 0:
            raise WorkflowRunError('total_count inválido.')
        total = data['total_count']
        if total > 1000:
            if not precise and (hi - lo).days <= 1:
                lo = datetime.combine(lo, datetime.min.time(), timezone.utc)
                hi = datetime.combine(hi, datetime.min.time(), timezone.utc)
                precise = True
            if precise:
                seconds = int((hi - lo).total_seconds())
                if seconds <= 1:
                    raise WorkflowRunError(f'{name}: mais de 1000 runs no mesmo segundo; consulta não é completa.')
                middle = lo + timedelta(seconds=seconds // 2)
            else:
                middle = lo + timedelta(days=(hi - lo).days // 2)
            collect(lo, middle)
            collect(middle, hi)
            return
        local = {}
        import itertools
        for response in itertools.chain([first], pages):
            if not isinstance(response.data, dict) or response.data.get('total_count') != total:
                raise APIError('Contagem mudou durante paginação dos runs.')
            if not isinstance(response.data.get('workflow_runs'), list):
                raise WorkflowRunError('Resposta sem workflow_runs.')
            for raw in response.data['workflow_runs']:
                parsed = parse_workflow_run(raw, branch)
                if raw['id'] in local and local[raw['id']] != raw:
                    raise APIError('Run mudou durante paginação.')
                local[raw['id']] = raw
                if parsed is not None and lo <= (utc_datetime(parsed['created_at']) if precise
                                                else utc_datetime(parsed['created_at']).date()) < hi:
                    indexed[parsed['id']] = parsed
        if len(local) != total:
            raise APIError(f'Coleta de runs incompleta: {len(local)}/{total}.')
        reports.append({'start': str(lo), 'end': str(hi), 'total_count': total})
    collect(start, end)
    return sorted(indexed.values(), key=lambda r: (r['created_at'], r['id'])), reports
