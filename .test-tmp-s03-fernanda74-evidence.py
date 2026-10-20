"""Extract factual evidence from completed runs; never touch empirical inputs."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

folder = Path('.test-tmp-s03-fernanda74-linux-02')
root = ET.parse(folder / 'junit.xml').getroot()
suites = list(root.iter('testsuite'))
counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in ('tests', 'failures', 'errors', 'skipped')}
coverage = json.loads((folder / 'coverage.json').read_text())
assert counts['tests'] == 630
assert not any(counts[key] for key in ('failures', 'errors', 'skipped'))
assert coverage['totals']['percent_covered'] >= 96
new_cases = [t for t in root.iter('testcase') if t.get('classname', '').endswith('test_s03_inference_edge_cases')]
assert len(new_cases) == 43
digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
manifest_path = Path('reports/s03/manifest.json')
manifest = json.loads(manifest_path.read_text())
verified = {}
for category in ('sources', 'outputs', 'figures'):
    for entry in manifest[category]:
        assert digest(entry['path']) == entry['sha256'], entry['path']
    verified[category] = len(manifest[category])
packages = {p['name']: p['version'] for p in json.loads((folder / 'packages.json').read_text())}
evidence = dict(issue=74, date='2026-10-20', branch='Laboratorio-3',
    base_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    status='passed_local_linux_not_remote_ci',
    execution=dict(platform='Linux container; project mounted read-only', python='3.12.15',
        image='python:3.12-slim', image_digest='sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1',
        requirements='requirements-dev.txt', versions={p: packages[p] for p in ('pytest', 'pytest-cov', 'numpy', 'scipy', 'pandas', 'statsmodels', 'scikit-learn', 'matplotlib')},
        command='python -m pytest -q --basetemp=/tmp/pytest-lab03 -o cache_dir=/tmp/pytest-cache --cov=src --cov-report=term-missing --cov-report=json:/results/coverage.json --cov-fail-under=96 --junitxml=/results/junit.xml'),
    **counts, new_regression_cases=len(new_cases),
    coverage_percent=coverage['totals']['percent_covered'], coverage_threshold=96,
    statements=coverage['totals']['num_statements'], covered_lines=coverage['totals']['covered_lines'],
    modified_module_coverage={p: coverage['files'][p]['summary']['percent_covered'] for p in ('src/s03_inference.py', 'src/s03_bootstrap.py')},
    published_artifacts=dict(manifest_sha256=digest(manifest_path), verified_counts=verified,
        all_hashes_unchanged=True, inference_recomputed_in_memory=True,
        empirical_comparison_tolerance=dict(rtol=1e-12, atol=1e-14),
        compared_tables=['spearman', 'factor_tests', 'factor_groups', 'factor_cutpoints', 'bootstrap']),
    implementation=[dict(path=p, sha256_normalized_lf=hashlib.sha256(Path(p).read_bytes().replace(b'\r\n', b'\n')).hexdigest()) for p in ('src/s03_inference.py','src/s03_bootstrap.py','tests/test_s03_inference_edge_cases.py')],
    pending=['member_code_review', 'commit_referencing_74', 'remote_ci_for_new_commit'],
    remote_ci_confirmed=False, commit_created=False, push_performed=False)
Path('reports/s03/fernanda_74_validation.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: evidence[k] for k in ('tests','failures','errors','skipped','new_regression_cases','coverage_percent','modified_module_coverage','published_artifacts')}, ensure_ascii=False))
