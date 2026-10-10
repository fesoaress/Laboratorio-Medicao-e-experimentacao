from dataclasses import asdict

import pytest

from src.config import SelectionConfig
from src import pipeline_workflow_metrics as integration
from src.workflow_runs import MonthReport, parse_workflow_run
from tests.test_workflow_runs import run


def test_workflow_integration_excludes_ignored_runs_from_eligibility(monkeypatch):
    rows = [parse_workflow_run(run(i, conclusion=conclusion), 'main')
            for i, conclusion in enumerate(('success', 'failure', 'cancelled'), 1)]
    report = MonthReport('2025-01-01', '2026-01-01', 3, 3, False)
    monkeypatch.setattr(integration, 'collect_workflow_runs', lambda *a: (rows, [report]))
    config = SelectionConfig(start_date='2025-01-01', end_date='2026-01-01')
    result = integration.collect_workflow_metrics(None, {'full_name': 'a/b', 'default_branch': 'main'}, config)
    assert result['valid_workflow_runs'] == 2
    assert result['cfr_a'] == 0.5 and result['cfr_a_ignored'] == 1
    assert result['recovery_time_n_episodes'] == 1 and result['recovery_time_censored_proportion'] == 1
    assert result['workflow_runs_months'] == [asdict(report)]


def test_workflow_integration_requires_defined_window_before_api():
    with pytest.raises(ValueError, match='Janela oficial ausente'):
        integration.collect_workflow_metrics(None, {}, SelectionConfig())
