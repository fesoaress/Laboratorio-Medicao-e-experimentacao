"""Auditoria offline dos dados reais S02, antes de liberar a amostra-ouro."""

import argparse
import csv
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from .s02_collection import save_json
from .temporal import ObservationWindow
from .workflow_runs import classify_conclusion


def read_rows(path):
    # C long é de 32 bits no Windows, mesmo em Python de 64 bits.
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    opener = gzip.open if path.suffix == '.gz' else Path.open
    with opener(path, mode='rt', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('CSV sem cabeçalho válido/único.')
        rows = list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError('CSV com linha de tamanho inválido.')
        return rows


def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def csv_source(directory, name):
    plain = directory / name
    compressed = plain.with_suffix('.csv.gz')
    if not compressed.exists():
        return plain
    if plain.exists():
        with gzip.open(compressed, 'rb') as handle:
            restored = hashlib.file_digest(handle, 'sha256').hexdigest()
        if restored != digest(plain):
            raise ValueError(f'Snapshot gzip desatualizado: {compressed}; recrie-o após a coleta.')
    return compressed


def audit_collection(directory):
    manifest_path = directory / 'collection_manifest_s02.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    window = ObservationWindow(**manifest['window'])
    rp, lp, wp = [csv_source(directory, name) for name in
                  ('repositories_final_s02.csv', 'releases_s01.csv', 'workflow_runs_s02.csv')]
    repositories, releases, runs = map(read_rows, (rp, lp, wp))
    errors, indexed, repository_ids = [], {}, set()
    for row in repositories:
        name = row['full_name'].casefold()
        if name in indexed:
            errors.append('duplicate_repository:' + name)
        indexed[name] = row
        identifier = row['repository_id']
        if not identifier.isdigit() or int(identifier) <= 0 or identifier in repository_ids:
            errors.append('duplicate_or_missing_repository_id:' + name)
        repository_ids.add(identifier)
        if (row['status'] != 'selected' or row['metadata_complete'] != 'True'
                or row['has_github_actions'] != 'True' or row['private'] != 'False'
                or not row['default_branch'].strip() or not row['default_branch_sha'].strip()
                or int(row['stargazers_count']) <= 1000 or int(row['release_count']) < 5
                or int(row['valid_workflow_runs']) < 50):
            errors.append('contradictory_eligibility:' + name)
    seen_releases, stable = set(), Counter()
    for release in releases:
        name = release['full_name'].casefold()
        identifier = (name, release['release_id'])
        if name not in indexed or identifier in seen_releases:
            errors.append('unaligned_or_duplicate_release:' + name)
        seen_releases.add(identifier)
        inside = window.contains(release['published_at'])
        if release['in_window'] not in ('True', 'False') or (release['in_window'] == 'True') != inside:
            errors.append('contradictory_release_window:' + name)
        if release['prerelease'] not in ('True', 'False'):
            errors.append('invalid_prerelease_flag:' + name)
        if inside and release['prerelease'] == 'False':
            stable[name] += 1
    seen_runs, valid = set(), Counter()
    for run in runs:
        name = run['full_name'].casefold()
        identifier = (name, run['id'])
        expected = classify_conclusion(run['conclusion'] or None)
        if (name not in indexed or identifier in seen_runs or not window.contains(run['created_at'])
                or run['event'] != 'push' or run['head_branch'] != indexed.get(name, {}).get('default_branch')
                or run['status_class'] != (expected or '')):
            errors.append('unaligned_duplicate_or_invalid_run:' + name)
        seen_runs.add(identifier)
        if expected is not None:
            valid[name] += 1
    for name, row in indexed.items():
        if stable[name] != int(row['release_count']) or valid[name] != int(row['valid_workflow_runs']):
            errors.append('count_mismatch:' + name)
    target = manifest['target']
    if (target < 300 or manifest['final_sample'] != len(repositories)
            or manifest['target_met'] != (len(repositories) >= target)):
        errors.append('contradictory_manifest_target_or_sample')
    ready = not errors and len(indexed) >= 300 and manifest['target_met']
    return {'status': 'verified_final_collection' if ready else 'invalid_collection' if errors else 'verified_partial_collection',
            'window': manifest['window'], 'eligible_repositories': len(indexed),
            'stable_releases_in_window': sum(stable.values()), 'workflow_runs': len(runs),
            'valid_workflow_runs': sum(valid.values()), 'ready_for_gold_sample': ready, 'errors': errors,
            'sources': [{'path': str(p), 'sha256': digest(p)} for p in (manifest_path, rp, lp, wp)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, nargs='?', default=Path('data/processed/s02'))
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = audit_collection(args.directory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Auditoria não concluída: ' + str(error))
        return 1
    save_json(args.directory / 'collection_audit_s02.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'sources'}, ensure_ascii=False))
    return 0 if result['ready_for_gold_sample'] or (args.allow_partial and not result['errors']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
