import csv
import json

import pytest

from src.cli import main as pipeline_main
from src.deliveries import OUTPUT_FIELDS, collect_delivery_data
from src.delivery_cli import load_repositories, main
from src.funnel import load_evidence
from src.github_client import APIError, RateLimitError
from tests.test_commit_collection import comparison
from tests.test_metadata_funnel import contributors, workflows
from tests.test_release_collection import raw_commit, raw_release, response
from tests.test_selection import FakeClient, page


def delivery_responses(*, failure=None, negative=False):
    """Um intervalo conhecido e uma predecessora fora da janela."""
    commits = [raw_commit(f"sha{day}", f"2025-03-{day:02}T00:00:00Z") for day in (2, 10, 14)]
    if negative:
        commits[0] = raw_commit("future", "2025-03-16T00:00:00Z")
    return [response(raw_commit("head")),
            response([raw_release(2, "v1"), raw_release(1, "v0", "2024-12-01T00:00:00Z")]),
            response(raw_commit("head")), response(raw_commit("base", "2024-12-01T00:00:00Z")),
            response({"status": "ahead"}),
            response([{"name": "v0", "commit": {"sha": "base"}}, {"name": "v1", "commit": {"sha": "head"}}]),
            failure if failure is not None else comparison(commits)]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_csvs_and_manifest_preserve_data_and_validation_contract(window, tmp_path):
    rows = collect_delivery_data(FakeClient(delivery_responses()), [{"full_name": "a/b", "default_branch": "main"}], window, tmp_path)
    assert rows[0]["status"] == "complete"
    assert rows[0]["release_count"] == 1
    assert rows[0]["lead_time_release_median_hours"] == 312
    assert rows[0]["lead_time_commit_median_hours"] == 120
    for name, fields in OUTPUT_FIELDS.items():
        with (tmp_path / name).open(encoding="utf-8", newline="") as handle:
            assert tuple(csv.DictReader(handle).fieldnames) == fields
    evidence = load_evidence(tmp_path / "release_validation_s01.csv")["a/b"]
    assert evidence.release_count == 1 and evidence.valid_workflow_runs is None
    releases = read_csv(tmp_path / "releases_s01.csv")
    assert releases[0]["in_window"] == "False" and releases[1]["in_window"] == "True"
    assert len(read_csv(tmp_path / "release_commits_s01.csv")) == 3
    assert len(read_csv(tmp_path / "lead_time_commits_s01.csv")) == 3
    manifest = json.loads((tmp_path / "delivery_manifest_s01.json").read_text(encoding="utf-8"))
    assert manifest["window"] == {"start_date": "2025-01-01", "end_date": "2026-01-01"}
    assert manifest["repositories"][0]["default_branch_sha"] == "head"


def test_100_repositories_offline_are_not_an_empirical_sample(window, tmp_path):
    repos = [{"full_name": f"a/repo{i}", "default_branch": "main"} for i in range(100)]
    responses = [r for _ in repos for r in delivery_responses()]
    rows = collect_delivery_data(FakeClient(responses), repos, window, tmp_path)
    assert len(rows) == 100 and all(row["status"] == "complete" for row in rows)
    assert len(read_csv(tmp_path / "release_commits_s01.csv")) == 300
    assert len(load_evidence(tmp_path / "release_validation_s01.csv")) == 100


@pytest.mark.parametrize("error", [RateLimitError("quota"), APIError("401", status=401)])
def test_interruption_preserves_known_release_count_and_pending_repositories(window, tmp_path, error):
    repos = [{"full_name": "a/b", "default_branch": "main"}, {"full_name": "a/c", "default_branch": "main"}]
    rows = collect_delivery_data(FakeClient(delivery_responses(failure=error)), repos, window, tmp_path)
    assert [r["status"] for r in rows] == ["api_error", "pending_collection"]
    assert rows[0]["release_count"] == 1 and rows[1]["release_count"] is None
    assert all(r["lead_time_commit_median_hours"] is None for r in rows)
    assert read_csv(tmp_path / "release_validation_s01.csv")[1]["release_count"] == ""


def test_comparison_error_preserves_diagnostic_and_suppresses_repository_median(window, tmp_path):
    rows = collect_delivery_data(FakeClient(delivery_responses(failure=APIError("500", status=500))),
                                 [{"full_name": "a/b", "default_branch": "main"}], window, tmp_path)
    assert rows[0]["status"] == "comparison_error"
    assert read_csv(tmp_path / "release_intervals_s01.csv")[0]["commit_count"] == ""
    assert rows[0]["release_count"] == 1
    assert rows[0]["lead_time_release_median_hours"] is None


def test_compare_404_only_repository_has_missing_metric_and_explicit_counter(window, tmp_path):
    rows = collect_delivery_data(FakeClient(delivery_responses(failure=APIError("404", status=404))),
                                 [{"full_name": "a/b", "default_branch": "main"}], window, tmp_path)
    row = rows[0]
    assert row["status"] == "complete"
    assert row["release_count"] == 1  # permanece release publicada na definição principal
    assert row["releases_ignored_compare_404"] == 1
    assert row["lead_time_commit_count"] == row["lead_time_release_count"] == 0
    assert row["lead_time_release_median_hours"] is None
    interval = read_csv(tmp_path / "release_intervals_s01.csv")[0]
    assert interval["status"] == "ignored_compare_404" and interval["error_status"] == "404"
    manifest = json.loads((tmp_path / "delivery_manifest_s01.json").read_text(encoding="utf-8"))
    assert manifest["releases_ignored_compare_404"] == 1


def test_compare_404_preserves_metrics_of_other_releases_end_to_end(window, tmp_path):
    responses = delivery_responses(failure=APIError("404", status=404))
    # Insere uma nova release na resposta /releases e resolve sua referência.
    responses[1] = response([raw_release(3, "v2", "2025-03-16T00:00:00Z"),
                             raw_release(2, "v1"), raw_release(1, "v0", "2024-12-01T00:00:00Z")])
    responses[0] = response(raw_commit("last"))
    responses[2:2] = [response(raw_commit("last"))]
    responses[4:4] = [response({"status": "ahead"})]
    responses.append(comparison([raw_commit("new", "2025-03-15T00:00:00Z")]))
    client = FakeClient(responses)
    rows = collect_delivery_data(client, [{"full_name": "a/b", "default_branch": "main"}], window, tmp_path)
    assert rows[0]["status"] == "complete"
    assert rows[0]["releases_ignored_compare_404"] == 1
    assert rows[0]["release_count"] == 2
    assert rows[0]["lead_time_release_median_hours"] == 24
    assert rows[0]["lead_time_commit_median_hours"] == 24
    assert client.calls[-1][0].endswith("head...last")
    assert len(read_csv(tmp_path / "lead_time_releases_s01.csv")) == 1
    assert len(read_csv(tmp_path / "lead_time_commits_s01.csv")) == 1


def test_tags_without_releases_are_discarded_in_principal_selection(tmp_path, monkeypatch):
    repo = {"id": 42, "owner": {"login": "a"}, "name": "b", "full_name": "a/b",
            "html_url": "https://github.com/a/b", "stargazers_count": 1500, "language": "Python",
            "created_at": "2024-01-01T00:00:00Z", "default_branch": "main"}
    client = FakeClient([page([repo], total=1), workflows(1), contributors(), response(raw_commit("head")),
                         response([]), response([{"name": "v1", "commit": {"sha": "head"}}]),
                         response(raw_commit("head"))])
    monkeypatch.setattr("src.cli.GitHubClient", lambda: client)
    assert pipeline_main(["--limit", "1", "--collect-lead-time", "--start-date", "2025-01-01",
                          "--end-date", "2026-01-01", "--output-dir", str(tmp_path)]) == 0
    row = read_csv(tmp_path / "repositories_s01.csv")[0]
    assert row["release_count"] == "0" and row["status"] == "discarded"
    assert row["reasons"] == "insufficient_releases"
    assert len(read_csv(tmp_path / "tags_s01.csv")) == 1
    funnel = {r["stage"]: r for r in read_csv(tmp_path / "selection_funnel_s01.csv")}
    assert funnel["release_filter"]["discarded"] == "1"


def test_negative_lead_time_preserves_raw_data_for_audit(window, tmp_path):
    rows = collect_delivery_data(FakeClient(delivery_responses(negative=True)),
                                 [{"full_name": "a/b", "default_branch": "main"}], window, tmp_path)
    assert rows[0]["status"] == "metric_error"
    assert "negativo" in rows[0]["error_detail"]
    assert len(read_csv(tmp_path / "release_commits_s01.csv")) == 3
    assert not read_csv(tmp_path / "lead_time_commits_s01.csv")


def test_data_error_is_not_a_zero_and_next_repository_still_runs(window, tmp_path):
    client = FakeClient([response({}), *delivery_responses()])
    repos = [{"full_name": "a/b", "default_branch": "main"}, {"full_name": "a/c", "default_branch": "main"}]
    rows = collect_delivery_data(client, repos, window, tmp_path)
    assert rows[0]["status"] == "data_error" and rows[0]["release_count"] is None
    assert rows[1]["status"] == "complete"


def test_ctrl_c_leaves_pending_row_and_preserves_files(window, tmp_path):
    with pytest.raises(KeyboardInterrupt):
        collect_delivery_data(FakeClient([KeyboardInterrupt()]), [{"full_name": "a/b", "default_branch": "main"}], window, tmp_path)
    assert read_csv(tmp_path / "lead_time_s01.csv")[0]["status"] == "pending_collection"


@pytest.mark.parametrize("repos", [[{"full_name": "a/b", "default_branch": ""}],
    [{"full_name": "a/b", "default_branch": "main"}, {"full_name": "A/B", "default_branch": "main"}]])
def test_invalid_repository_input_before_network(window, tmp_path, repos):
    client = FakeClient([])
    with pytest.raises(ValueError):
        collect_delivery_data(client, repos, window, tmp_path)
    assert client.calls == []


def test_independent_cli_uses_repository_default_branch_from_api(tmp_path, monkeypatch):
    client = FakeClient([response({"default_branch": "trunk"}), *delivery_responses()])
    monkeypatch.setattr("src.delivery_cli.GitHubClient", lambda: client)
    assert main(["--repository", "a/b", "--start-date", "2025-01-01", "--end-date", "2026-01-01", "--output-dir", str(tmp_path)]) == 0
    assert client.calls[1][0].endswith("/commits/trunk")


def test_csv_source_skips_incomplete_metadata_and_repos_without_actions(tmp_path):
    path = tmp_path / "input.csv"
    path.write_text("full_name,default_branch,metadata_complete,has_github_actions\na/b,main,True,True\na/c,main,False,True\na/d,main,True,False\n", encoding="utf-8")
    assert [r["full_name"] for r in load_repositories(path)] == ["a/b"]
    path.write_text("full_name\na/b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="default_branch"):
        load_repositories(path)


@pytest.mark.parametrize("function,args", [(main, ["--repository", "a/b"]),
    (pipeline_main, ["--collect-lead-time"]),
    (pipeline_main, ["--collect-lead-time", "--candidates-only", "--start-date", "2025-01-01", "--end-date", "2026-01-01"])])
def test_missing_window_or_incompatible_options_rejected_before_network(function, args, monkeypatch):
    monkeypatch.setattr("src.delivery_cli.GitHubClient", lambda: pytest.fail("Network must not run"))
    monkeypatch.setattr("src.cli.GitHubClient", lambda: pytest.fail("Network must not run"))
    with pytest.raises(SystemExit) as captured:
        function(args)
    assert captured.value.code == 2


def test_single_command_integrates_release_count_into_selection_funnel(tmp_path, monkeypatch):
    repo = {"id": 42, "owner": {"login": "a"}, "name": "b", "full_name": "a/b",
            "html_url": "https://github.com/a/b", "stargazers_count": 1500, "language": "Python",
            "created_at": "2024-01-01T00:00:00Z", "default_branch": "main"}
    client = FakeClient([page([repo], total=1), workflows(1), contributors(), *delivery_responses()])
    monkeypatch.setattr("src.cli.GitHubClient", lambda: client)
    assert pipeline_main(["--limit", "1", "--collect-lead-time", "--start-date", "2025-01-01", "--end-date", "2026-01-01", "--output-dir", str(tmp_path)]) == 0
    row = read_csv(tmp_path / "repositories_s01.csv")[0]
    assert row["release_count"] == "1"
    assert row["status"] == "discarded" and row["reasons"] == "insufficient_releases"
    assert row["valid_workflow_runs"] == ""


def test_main_cli_reports_temporal_failure_and_retains_missing_count(tmp_path, monkeypatch):
    repo = {"id": 42, "owner": {"login": "a"}, "name": "b", "full_name": "a/b",
            "html_url": "https://github.com/a/b", "stargazers_count": 1500, "language": "Python",
            "created_at": "2024-01-01T00:00:00Z", "default_branch": "main"}
    client = FakeClient([page([repo], total=1), workflows(1), contributors(), APIError("404", status=404)])
    monkeypatch.setattr("src.cli.GitHubClient", lambda: client)
    assert pipeline_main(["--limit", "1", "--collect-lead-time", "--start-date", "2025-01-01", "--end-date", "2026-01-01", "--output-dir", str(tmp_path)]) == 1
    assert read_csv(tmp_path / "repositories_s01.csv")[0]["release_count"] == ""
    assert json.loads((tmp_path / "selection_manifest_s01.json").read_text(encoding="utf-8"))["delivery_errors"] == 1
