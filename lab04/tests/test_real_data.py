"""Regression tests for real CI-run data and its denominator rules."""

import csv

import pytest

from lab04.src.real_data import load_ci_runs, summarize_ci_runs

FIELDS = (
    "run_id", "created_at", "run_url", "repository", "workflow_id",
    "workflow_name", "branch", "conclusion", "failed",
)


def sample(run_id, conclusion):
    return {
        "run_id": str(run_id),
        "created_at": "2026-08-15T12:00:00Z",
        "run_url": f"https://github.com/fastapi/fastapi/actions/runs/{run_id}",
        "repository": "fastapi/fastapi",
        "workflow_id": "1929523",
        "workflow_name": "Test",
        "branch": "master",
        "conclusion": conclusion,
        "failed": "1" if conclusion == "failure" else "0",
    }


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_load_and_summarize(tmp_path):
    path = tmp_path / "ci.csv"
    write_csv(path, [sample(1, "success"), sample(2, "failure"), sample(3, "success")])
    data = load_ci_runs(path)
    assert summarize_ci_runs(data) == {"n": 3, "k": 1, "p_hat": 1 / 3}
    assert data["run_id"].tolist() == [1, 2, 3]


@pytest.mark.parametrize("change,match", [
    ({"run_id": "1", "run_url": "https://github.com/fastapi/fastapi/actions/runs/1"}, "Duplicate run_id"),
    ({"conclusion": "cancelled"}, "Only completed"),
    ({"failed": "1"}, "disagrees"),
    ({"workflow_id": "999"}, "one workflow_id"),
    ({"run_url": "https://example.org/fastapi/fastapi/actions/runs/2"}, "Invalid run_url"),
    ({"created_at": "not-a-date"}, "created_at"),
])
def test_reject_invalid_rows(tmp_path, change, match):
    path = tmp_path / "ci.csv"
    bad = sample(2, "success")
    bad.update(change)
    write_csv(path, [sample(1, "success"), bad])
    with pytest.raises(ValueError, match=match):
        load_ci_runs(path)


def test_missing_column_is_rejected(tmp_path):
    path = tmp_path / "ci.csv"
    path.write_text("run_id,conclusion\n1,success\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing columns"):
        load_ci_runs(path)


def test_versioned_sample_matches_documented_counts():
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "data" / "ci_runs.csv"
    data = load_ci_runs(path)
    assert summarize_ci_runs(data) == {"n": 169, "k": 7, "p_hat": 7 / 169}
    assert set(data["repository"]) == {"fastapi/fastapi"}
    assert set(data["branch"]) == {"master"}
