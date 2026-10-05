import pytest

from src.commits import collect_commits_between, collect_release_intervals
from src.github_client import APIError, RateLimitError
from src.temporal import Release
from tests.test_release_collection import raw_commit, response
from tests.test_selection import FakeClient


def comparison(commits, total=None, status="ahead", next_url=None):
    return response({"commits": commits, "total_commits": len(commits) if total is None else total,
                     "status": status}, next_url)


def test_pagination_beyond_250_commits_with_unique_complete_count():
    commits = [raw_commit(f"sha{i}") for i in range(301)]
    pages = [comparison(commits[i:i+100], 301, next_url=f"https://api.github.com/repos/a/b/compare/base...head?page={i//100+2}"
                        if i < 300 else None) for i in range(0, 301, 100)]
    client = FakeClient(pages)
    result = collect_commits_between(client, "a/b", "base", "head")
    assert len(result) == 301
    assert len(client.calls) == 4
    assert client.calls[0][1] == {"per_page": 100, "page": 1}
    assert client.calls[-1][1] is None


def test_same_sha_and_identical_empty_comparisons():
    assert collect_commits_between(FakeClient([]), "a/b", "same", "same") == ()
    assert collect_commits_between(FakeClient([comparison([], status="identical")]), "a/b", "v1", "v2") == ()


def test_compare_refs_are_url_encoded():
    client = FakeClient([comparison([])])
    collect_commits_between(client, "a/b", "releases/v1", "releases/v2")
    assert client.calls[0][0].endswith("releases%2Fv1...releases%2Fv2")


@pytest.mark.parametrize("data", [comparison([raw_commit("x")], total=251),
    comparison([], status="diverged"), comparison([], status="behind"),
    comparison([], total=True), response({}), response([])])
def test_truncated_or_invalid_interval_cannot_be_success(data):
    with pytest.raises((ValueError, APIError)):
        collect_commits_between(FakeClient([data]), "a/b", "base", "head")


def test_duplicate_sha_is_counted_once_but_inconsistent_data_rejected():
    assert len(collect_commits_between(FakeClient([comparison([raw_commit("x")] * 2, total=1)]), "a/b", "base", "head")) == 1
    with pytest.raises(APIError, match="inconsistente"):
        collect_commits_between(FakeClient([comparison([raw_commit("x"), raw_commit("x", "2025-03-03T00:00:00Z")], total=1)]),
                               "a/b", "base", "head")


def test_changed_compare_total_between_pages_rejected():
    client = FakeClient([comparison([raw_commit("x")], 2, next_url="https://api.github.com/next"),
                         comparison([raw_commit("y")], 3)])
    with pytest.raises(APIError, match="mudou"):
        collect_commits_between(client, "a/b", "base", "head")


def test_predecessor_outside_window_and_prerelease_does_not_replace_it(window):
    old = Release(1, "v1", "2024-12-01T00:00:00Z", "base")
    pre = Release(2, "rc", "2025-02-01T00:00:00Z", "pre", True)
    current = Release(3, "v2", "2025-03-01T00:00:00Z", "head")
    client = FakeClient([comparison([raw_commit("x", "2024-12-15T00:00:00Z")])])
    intervals = collect_release_intervals(client, "a/b", (current, pre, old), window)
    assert len(intervals) == 1
    assert intervals[0].previous_release == old
    assert client.calls[0][0].endswith("base...head")


def test_first_release_ignored_but_next_empty_release_kept(window):
    first = Release(1, "v1", "2025-02-01T00:00:00Z", "same")
    second = Release(2, "v2", "2025-03-01T00:00:00Z", "same")
    intervals = collect_release_intervals(FakeClient([]), "a/b", (second, first), window)
    assert [i.status for i in intervals] == ["no_previous_release", "complete"]
    assert intervals[1].commits == ()


def test_prerelease_variant_has_its_own_predecessor_chain(window):
    first = Release(1, "v1", "2024-12-01T00:00:00Z", "base")
    pre = Release(2, "rc", "2025-02-01T00:00:00Z", "pre", True)
    second = Release(3, "v2", "2025-03-01T00:00:00Z", "head")
    client = FakeClient([comparison([]), comparison([])])
    result = collect_release_intervals(client, "a/b", (first, pre, second), window, include_prereleases=True)
    assert len(result) == 2
    assert result[1].previous_release == pre


@pytest.mark.parametrize("error", [APIError("500", status=500), ValueError("invalid")])
def test_comparison_error_is_recorded_instead_of_empty_commit_list(window, error):
    old = Release(1, "v1", "2024-12-01T00:00:00Z", "base")
    new = Release(2, "v2", "2025-03-01T00:00:00Z", "head")
    result = collect_release_intervals(FakeClient([error]), "a/b", (old, new), window)
    assert result[0].status == "error"
    assert result[0].error_detail


def test_compare_404_is_counted_without_changing_next_predecessor(window):
    old = Release(1, "v1", "2024-12-01T00:00:00Z", "base")
    missing = Release(2, "v2", "2025-03-01T00:00:00Z", "middle")
    last = Release(3, "v3", "2025-03-15T00:00:00Z", "head")
    client = FakeClient([APIError("deleted reference", status=404), comparison([raw_commit("new")])])
    result = collect_release_intervals(client, "a/b", (old, missing, last), window)
    assert result[0].status == "ignored_compare_404"
    assert result[0].error_status == 404
    assert result[0].error_detail == "deleted reference"
    assert result[1].status == "complete"
    assert result[1].previous_release == missing
    assert client.calls[1][0].endswith("middle...head")


@pytest.mark.parametrize("error", [RateLimitError("quota"), APIError("unauthorized", status=401)])
def test_rate_limit_or_authentication_error_propagates(window, error):
    old = Release(1, "v1", "2024-12-01T00:00:00Z", "base")
    new = Release(2, "v2", "2025-03-01T00:00:00Z", "head")
    with pytest.raises(APIError):
        collect_release_intervals(FakeClient([error]), "a/b", (old, new), window)


@pytest.mark.parametrize("base,head,page_size", [("", "head", 100), ("base", None, 100), ("base", "head", 101)])
def test_invalid_comparison_parameters(base, head, page_size):
    with pytest.raises(ValueError):
        collect_commits_between(FakeClient([]), "a/b", base, head, per_page=page_size)
