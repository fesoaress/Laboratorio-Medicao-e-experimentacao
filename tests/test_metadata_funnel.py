import csv
import json
from copy import deepcopy

import pytest

from lab03.src.cli import main
from lab03.src.audit import audit, main as audit_main
from lab03.src.config import SelectionConfig
from lab03.src.funnel import TemporalEvidence, build_funnel, classify, load_evidence
from lab03.src.github_client import APIError, APIResponse, RateLimitError
from lab03.src.metadata import MetadataError, check_actions, count_contributors, parse_metadata
from lab03.src.pipeline import REPOSITORY_FIELDS, collect_metadata, save_outputs
from lab03.tests.test_selection import FakeClient, page

COLLECTED = "2026-10-03T20:00:00+00:00"


@pytest.fixture
def repository():
    return {"id": 42, "owner": {"login": "equipe"}, "name": "medição",
            "full_name": "equipe/medição", "html_url": "https://github.com/equipe/medição",
            "stargazers_count": 1500, "language": "Python", "created_at": "2025-10-03T20:00:00Z",
            "default_branch": "trunk"}


def workflows(total):
    return APIResponse({"total_count": total}, {})


def contributors(data=None, link="", status=200):
    return APIResponse(data if data is not None else [{"login": "one"}], {"Link": link}, status)


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_metadata_and_deterministic_age(repository):
    data = parse_metadata(repository, COLLECTED)
    assert data["owner"] == "equipe"
    assert data["name"] == "medição"
    assert data["repo_age_days"] == 365
    assert data["created_at"] == repository["created_at"]
    assert data["default_branch"] == "trunk"
    assert data["collected_at"] == COLLECTED
    assert parse_metadata(repository, "2026-10-03T17:00:00-03:00")["repo_age_days"] == 365
    repository["language"] = None
    assert parse_metadata(repository, COLLECTED)["language"] is None


@pytest.mark.parametrize("field,value", [("created_at", "invalid"), ("created_at", "2027-01-01T00:00:00Z"),
    ("created_at", "2025-01-01T00:00:00"), ("owner", {}), ("stargazers_count", True),
    ("stargazers_count", -1), ("default_branch", None), ("full_name", "other/repo"),
    ("html_url", "https://example.com"), ("language", 5)])
def test_metadata_errors_are_explicit(repository, field, value):
    repository[field] = value
    with pytest.raises(MetadataError):
        parse_metadata(repository, COLLECTED)


@pytest.mark.parametrize("response,expected", [
    (contributors(link='<https://api.github.com/repos/a/b/contributors?anon=true&per_page=1&page=87>; rel="last"'), 87),
    (contributors(), 1), (contributors([]), 0), (contributors(status=204), 0),
])
def test_contributor_count_single_request(response, expected):
    client = FakeClient([response])
    assert count_contributors(client, "a/b") == expected
    assert client.calls == [("/repos/a/b/contributors", {"per_page": 1, "anon": "true"})]


@pytest.mark.parametrize("response", [APIResponse({}, {}), contributors([{}, {}]),
    contributors(link='<https://api.github.com/x?page=x>; rel="last"'),
    contributors(link='<https://api.github.com/x>; rel="last"'),
    contributors(link='<https://api.github.com/x?page=0>; rel="last"'),
    contributors(link='<https://api.github.com/x?page=2>; rel="next"')])
def test_contributors_unexpected_response(response):
    with pytest.raises(MetadataError):
        count_contributors(FakeClient([response]), "a/b")


def test_contributors_api_error_is_not_zero():
    with pytest.raises(APIError):
        count_contributors(FakeClient([APIError("HTTP 404", status=404)]), "a/b")


@pytest.mark.parametrize("count,expected", [(0, False), (1, True), (90, True)])
def test_actions_check(count, expected):
    client = FakeClient([workflows(count)])
    assert check_actions(client, "a/b") is expected
    assert client.calls == [("/repos/a/b/actions/workflows", {"per_page": 1})]


@pytest.mark.parametrize("response", [APIResponse([], {}), workflows(None), workflows(-1), workflows(True)])
def test_actions_unexpected_response(response):
    with pytest.raises(MetadataError):
        check_actions(FakeClient([response]), "a/b")


def test_pending_validations_and_unknown_funnel_counts(repository):
    rows = collect_metadata(FakeClient([workflows(2), contributors()]), [repository], SelectionConfig(), COLLECTED)
    assert rows[0]["reasons"] == "pending_release_validation;pending_workflow_validation"
    assert rows[0]["status"] == "pending_validation"
    funnel = {stage["stage"]: stage for stage in build_funnel(rows)}
    assert funnel["candidates"]["count"] == funnel["processed"]["count"] == 1
    assert funnel["actions_enabled"]["count"] == 1
    assert funnel["release_filter"]["count"] is None
    assert funnel["workflow_filter"]["count"] is None
    assert funnel["final_sample"]["count"] is None


def test_discard_no_actions_and_missing_branch(repository):
    repository["default_branch"] = ""
    rows = collect_metadata(FakeClient([workflows(0), contributors([])]), [repository], SelectionConfig(), COLLECTED)
    assert rows[0]["reasons"] == "missing_default_branch;no_github_actions"
    assert rows[0]["contributors_count"] == 0
    assert rows[0]["status"] == "discarded"
    funnel = {stage["stage"]: stage for stage in build_funnel(rows)}
    assert funnel["actions_enabled"]["discarded"] == 1
    assert funnel["final_sample"]["count"] == 0


@pytest.mark.parametrize("releases,runs,status,reason", [(4, 50, "discarded", "insufficient_releases"),
    (5, 49, "discarded", "insufficient_workflow_runs"), (5, 50, "selected", ""),
    (None, 50, "pending_validation", "pending_release_validation"),
    (5, None, "pending_validation", "pending_workflow_validation")])
def test_temporal_integration_only_uses_supplied_counts(repository, releases, runs, status, reason):
    config = SelectionConfig(start_date="2025-10-03", end_date="2026-10-03")
    evidence = TemporalEvidence(repository["full_name"], config.start_date, config.end_date, releases, runs)
    rows = collect_metadata(FakeClient([workflows(1), contributors()]), [repository], config, COLLECTED,
                            {repository["full_name"].casefold(): evidence})
    assert rows[0]["status"] == status
    assert rows[0]["reasons"] == reason
    assert rows[0]["release_count"] == releases
    if status == "selected":
        assert build_funnel(rows)[-1]["count"] == 1


def test_temporal_evidence_cannot_use_unofficial_or_different_window(repository):
    row = {**parse_metadata(repository, COLLECTED), "has_github_actions": True}
    item = TemporalEvidence(repository["full_name"], "2025-10-03", "2026-10-03", 5, 50)
    with pytest.raises(ValueError, match="janela"):
        classify(row, SelectionConfig(), item)
    with pytest.raises(ValueError, match="janela"):
        classify(row, SelectionConfig(start_date="2025-01-01", end_date="2026-01-01"), item)


def test_pipeline_errors_and_rate_limit_preserve_pending_records(repository):
    repositories = [repository, {**repository, "id": 43, "name": "second", "full_name": "equipe/second",
                               "html_url": "https://github.com/equipe/second"}]
    client = FakeClient([RateLimitError("remaining=0 reset=123")])
    rows = collect_metadata(client, repositories, SelectionConfig(), COLLECTED)
    assert rows[0]["status"] == rows[0]["reasons"] == "api_error"
    assert rows[0]["has_github_actions"] is None
    assert rows[1]["status"] == "pending_metadata"
    assert rows[1]["processed"] is False
    assert len(client.calls) == 1
    assert build_funnel(rows)[1]["count"] == 1


def test_regular_api_error_continues_and_metadata_errors_are_distinct(repository):
    rows = collect_metadata(FakeClient([APIError("HTTP 404"), workflows(1), contributors()]),
                            [repository, repository], SelectionConfig(), COLLECTED)
    assert rows[0]["status"] == "api_error"
    assert rows[1]["status"] == "pending_validation"
    bad = deepcopy(repository)
    del bad["created_at"]
    assert collect_metadata(FakeClient([]), [bad], SelectionConfig(), COLLECTED)[0]["status"] == "metadata_error"


def test_csv_output_encoding_order_and_absence_of_fabricated_counts(repository, tmp_path):
    rows = collect_metadata(FakeClient([workflows(1), contributors()]), [repository], SelectionConfig(), COLLECTED)
    save_outputs(tmp_path, rows, build_funnel(rows))
    actual = read_csv(tmp_path / "repositories_s01.csv")
    assert tuple(actual[0]) == REPOSITORY_FIELDS
    assert actual[0]["name"] == "medição"
    assert actual[0]["release_count"] == actual[0]["valid_workflow_runs"] == ""
    assert actual[0]["repo_age_days"] == "365"
    assert read_csv(tmp_path / "selection_funnel_s01.csv")[-1]["count"] == ""


def test_cli_integration_with_mock_api(repository, tmp_path, monkeypatch, capsys):
    client = FakeClient([page([repository], total=1), workflows(1), contributors()])
    monkeypatch.setattr("lab03.src.cli.GitHubClient", lambda: client)
    assert main(["--limit", "1", "--output-dir", str(tmp_path)]) == 0
    assert read_csv(tmp_path / "repositories_s01.csv")[0]["default_branch"] == "trunk"
    manifest = json.loads((tmp_path / "selection_manifest_s01.json").read_text(encoding="utf-8"))
    assert manifest["processed"] == manifest["actions_enabled"] == 1
    assert "N/D" in capsys.readouterr().out
    assert all("/releases" not in path and "/runs" not in path for path, _ in client.calls)


def test_cli_search_error_saves_honest_empty_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr("lab03.src.cli.GitHubClient", lambda: FakeClient([APIError("HTTP 500")]))
    assert main(["--limit", "5", "--output-dir", str(tmp_path)]) == 1
    assert read_csv(tmp_path / "repositories_s01.csv") == []
    assert read_csv(tmp_path / "selection_funnel_s01.csv")[0]["count"] == "0"


def test_cli_candidate_only_is_compact(repository, tmp_path, monkeypatch):
    monkeypatch.setattr("lab03.src.cli.GitHubClient", lambda: FakeClient([page([repository], total=1)]))
    assert main(["--limit", "1", "--candidates-only", "--output-dir", str(tmp_path)]) == 0
    assert not (tmp_path / "repositories_s01.csv").exists()
    assert json.loads((tmp_path / "candidates_s01.json").read_text(encoding="utf-8"))[0]["id"] == 42


def test_cli_invalid_config_exits_before_network(tmp_path):
    with pytest.raises(SystemExit) as captured:
        main(["--limit", "0", "--output-dir", str(tmp_path)])
    assert captured.value.code == 2


def test_validation_csv_duplicate_missing_and_invalid_counts(tmp_path):
    path = tmp_path / "validation.csv"
    path.write_text("full_name,start_date,end_date,release_count,valid_workflow_runs\na/b,2025-01-01,2026-01-01,5,50\n", encoding="utf-8")
    assert load_evidence(path)["a/b"].release_count == 5
    assert load_evidence(None) == {}
    with path.open("a", encoding="utf-8") as handle:
        handle.write("A/B,2025-01-01,2026-01-01,,\n")
    with pytest.raises(ValueError, match="duplicada"):
        load_evidence(path)
    path.write_text("full_name\na/b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="colunas"):
        load_evidence(path)
    with pytest.raises(ValueError, match="Contagens"):
        TemporalEvidence("a/b", "2025-01-01", "2026-01-01", -1)


def test_cli_hundred_candidates_with_mocked_api(repository, tmp_path, monkeypatch):
    """Teste de volume; estes dados sintéticos nunca são resultados do estudo."""
    candidates = [{**repository, "id": identifier, "name": f"repo{identifier}",
                   "full_name": f"equipe/repo{identifier}",
                   "html_url": f"https://github.com/equipe/repo{identifier}"} for identifier in range(100)]
    responses = [page(candidates, total=100)]
    for identifier in range(100):
        responses.extend([workflows(1 if identifier % 2 else 0), contributors()])
    client = FakeClient(responses)
    monkeypatch.setattr("lab03.src.cli.GitHubClient", lambda: client)
    assert main(["--limit", "100", "--output-dir", str(tmp_path)]) == 0
    summary = audit(tmp_path)
    assert summary == {"candidates": 100, "processed": 100, "actions_enabled": 50,
                       "statuses": {"discarded": 50, "pending_validation": 50}, "duplicates": 0}
    assert len(client.calls) == 201
    assert all("/runs" not in path and "/releases" not in path for path, _ in client.calls)


def test_audit_rejects_duplicate_records_and_wrong_totals(repository, tmp_path, monkeypatch):
    monkeypatch.setattr("lab03.src.cli.GitHubClient", lambda: FakeClient([page([repository]), workflows(1), contributors()]))
    assert main(["--limit", "1", "--output-dir", str(tmp_path)]) == 0
    assert audit_main([str(tmp_path)]) == 0
    path = tmp_path / "repositories_s01.csv"
    original = path.read_text(encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(original.splitlines()[1] + "\n")
    with pytest.raises(ValueError, match="duplicado"):
        audit(tmp_path)
    path.write_text(original, encoding="utf-8")
    funnel_path = tmp_path / "selection_funnel_s01.csv"
    funnel_path.write_text(funnel_path.read_text(encoding="utf-8").replace("candidates,1,", "candidates,99,"), encoding="utf-8")
    with pytest.raises(ValueError, match="Funil"):
        audit(tmp_path)


def test_incomplete_search_and_invalid_validation_window_are_not_success(repository, tmp_path, monkeypatch):
    monkeypatch.setattr("lab03.src.cli.GitHubClient", lambda: FakeClient([page([repository], incomplete=True), workflows(1), contributors()]))
    assert main(["--limit", "1", "--output-dir", str(tmp_path)]) == 1
    path = tmp_path / "validation.csv"
    path.write_text("full_name,start_date,end_date,release_count,valid_workflow_runs\na/b,2025-01-01,2026-01-01,5,50\n", encoding="utf-8")
    with pytest.raises(SystemExit) as captured:
        main(["--validation-csv", str(path)])
    assert captured.value.code == 2


def test_secondary_rate_limit_without_retry_header_stops(monkeypatch):
    import io
    from urllib.error import HTTPError
    from lab03.src.github_client import GitHubClient

    def fail(*args, **kwargs):
        raise HTTPError("https://api.github.com/x", 403, "forbidden", {},
                        io.BytesIO(b'{"message":"You have exceeded a secondary rate limit."}'))
    monkeypatch.setattr("lab03.src.github_client.urlopen", fail)
    with pytest.raises(RateLimitError):
        GitHubClient().get("/x")
