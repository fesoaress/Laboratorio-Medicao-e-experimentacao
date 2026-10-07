from datetime import date

import pytest

from src.workflow_runs import (
    MonthReport, WorkflowRunError, classify_conclusion, collect_workflow_runs,
    month_windows, parse_workflow_run,
)
from tests.test_selection import FakeClient
from src.github_client import APIResponse


def runs_page(runs, link="", total=None):
    return APIResponse({"total_count": total if total is not None else len(runs), "workflow_runs": runs}, {"Link": link})


def run(identifier=1, conclusion="success", branch="main", event="push",
        created="2025-03-01T10:00:00Z", started="2025-03-01T10:00:00Z", updated="2025-03-01T10:05:00Z"):
    return {"id": identifier, "workflow_id": 7, "head_branch": branch, "event": event,
            "conclusion": conclusion, "created_at": created, "run_started_at": started, "updated_at": updated}


@pytest.mark.parametrize("conclusion,expected", [
    ("success", "success"), ("failure", "failure"), ("timed_out", "failure"), ("startup_failure", "failure"),
    ("cancelled", None), ("skipped", None), ("neutral", None), ("action_required", None),
    ("stale", None), ("", None), (None, None),
])
def test_classify_conclusion(conclusion, expected):
    assert classify_conclusion(conclusion) == expected


def test_classify_unknown_conclusion_is_explicit():
    with pytest.raises(WorkflowRunError):
        classify_conclusion("unexpected_value")


def test_month_windows_clips_at_both_ends():
    windows = month_windows(date(2025, 1, 15), date(2025, 4, 10))
    assert windows == [
        (date(2025, 1, 15), date(2025, 2, 1)),
        (date(2025, 2, 1), date(2025, 3, 1)),
        (date(2025, 3, 1), date(2025, 4, 1)),
        (date(2025, 4, 1), date(2025, 4, 10)),
    ]


def test_month_windows_single_month():
    assert month_windows(date(2025, 6, 1), date(2025, 6, 15)) == [(date(2025, 6, 1), date(2025, 6, 15))]


def test_month_windows_invalid_range():
    with pytest.raises(WorkflowRunError):
        month_windows(date(2025, 6, 1), date(2025, 6, 1))


def test_parse_workflow_run_filters_other_branch_and_event():
    assert parse_workflow_run(run(branch="dev"), "main") is None
    assert parse_workflow_run(run(event="schedule"), "main") is None
    parsed = parse_workflow_run(run(), "main")
    assert parsed["status_class"] == "success"
    assert parsed["id"] == 1


@pytest.mark.parametrize("field", ["id", "workflow_id", "head_branch", "event", "created_at", "run_started_at", "updated_at"])
def test_parse_workflow_run_missing_field_is_explicit(field):
    data = run()
    del data[field]
    with pytest.raises(WorkflowRunError):
        parse_workflow_run(data, "main")


def test_collect_workflow_runs_single_month(monkeypatch):
    client = FakeClient([runs_page([run(1, created="2025-03-05T00:00:00Z"), run(2, conclusion="failure", created="2025-03-06T00:00:00Z")])])
    runs, reports = collect_workflow_runs(client, "org/repo", "main", "2025-03-01", "2025-04-01")
    assert len(runs) == 2
    assert reports == [MonthReport("2025-03-01", "2025-04-01", 2, 2, False)]
    assert client.calls[0][1]["event"] == "push"
    assert client.calls[0][1]["created"] == "2025-03-01..2025-04-01"


def test_collect_workflow_runs_excludes_dates_outside_official_window():
    client = FakeClient([runs_page([run(1, created="2025-02-28T23:59:59Z"), run(2, created="2025-03-02T00:00:00Z")])])
    runs, _ = collect_workflow_runs(client, "org/repo", "main", "2025-03-01", "2025-04-01")
    assert [item["id"] for item in runs] == [2]


def test_collect_workflow_runs_spans_multiple_months():
    client = FakeClient([
        runs_page([run(1, created="2025-01-15T00:00:00Z")]),
        runs_page([run(2, created="2025-02-15T00:00:00Z")]),
    ])
    runs, reports = collect_workflow_runs(client, "org/repo", "main", "2025-01-01", "2025-03-01")
    assert len(runs) == 2
    assert len(reports) == 2
    assert len(client.calls) == 2


def test_collect_workflow_runs_raises_on_capped_month():
    full_page = [run(i, created="2025-03-01T00:00:00Z") for i in range(1000)]
    client = FakeClient([runs_page(full_page, total=1500)])
    with pytest.raises(WorkflowRunError, match="teto de 1.000"):
        collect_workflow_runs(client, "org/repo", "main", "2025-03-01", "2025-04-01")


def test_collect_workflow_runs_unexpected_response_shape():
    client = FakeClient([APIResponse([], {})])
    with pytest.raises(WorkflowRunError):
        collect_workflow_runs(client, "org/repo", "main", "2025-03-01", "2025-04-01")