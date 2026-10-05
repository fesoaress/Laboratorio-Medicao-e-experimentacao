from copy import deepcopy

import pytest

from src.github_client import APIError, APIResponse
from src.releases import collect_releases_and_tags
from src.temporal import ObservationWindow, parse_commit, repository_path, utc_datetime
from tests.test_selection import FakeClient


def raw_commit(sha, date="2025-03-02T00:00:00Z"):
    return {"sha": sha, "commit": {"author": {"date": date}, "committer": {"date": date}, "message": "fix: example"}}


def raw_release(identifier, tag, published="2025-03-15T00:00:00Z", **kwargs):
    return {"id": identifier, "tag_name": tag, "published_at": published, "draft": False,
            "prerelease": False, "target_commitish": "outdated-branch", **kwargs}


def response(data, next_url=None):
    return APIResponse(data, {"Link": f'<{next_url}>; rel="next"'} if next_url else {})


def test_all_release_pages_sorted_by_publication_and_tags_use_author_date(window):
    next_page = "https://api.github.com/repos/a/b/releases?page=2"
    next_tags = "https://api.github.com/repos/a/b/tags?page=2"
    current = raw_release(2, "v1/next")
    old = raw_release(1, "v0", "2024-12-01T00:00:00Z")
    pre = raw_release(3, "v2rc", prerelease=True)
    responses = [response(raw_commit("branch")), response([current], next_page),
                 response(raw_commit("head")), response({"status": "ahead"}),
                 response([old, pre, raw_release(4, "draft", published=None, draft=True),
                           raw_release(5, "future", "2026-01-01T00:00:00Z")]),
                 response(raw_commit("base", "2024-12-01T00:00:00Z")), response({"status": "ahead"}),
                 response(raw_commit("pre")), response({"status": "ahead"}),
                 response([{"name": "v1/next", "commit": {"sha": "head"}}], next_tags),
                 response([{"name": "bare", "commit": {"sha": "bare-sha"}}]),
                 response(raw_commit("bare-sha", "2025-03-03T00:00:00Z")), response({"status": "ahead"})]
    client = FakeClient(responses)
    result = collect_releases_and_tags(client, "a/b", "trunk/dev", window)
    assert [r.release_id for r in result.history] == [1, 2, 3]
    assert [r.release_id for r in result.in_window(window)] == [2]
    assert len(result.in_window(window, include_prereleases=True)) == 2
    assert result.tags[1].author_date == "2025-03-03T00:00:00Z"
    assert result.default_branch_sha == "branch"
    assert [r["reason"] for r in result.excluded_releases] == ["draft", "outside_window_after_end"]
    assert client.calls[0][0].endswith("trunk%2Fdev")
    assert client.calls[2][0].endswith("v1%2Fnext")
    assert (next_page, None) in client.calls and (next_tags, None) in client.calls
    assert client.calls[1][1] == {"per_page": 100, "page": 1}
    assert all(not path.endswith("/commits/head") for path, _ in client.calls)  # reutiliza SHA resolvido


@pytest.mark.parametrize("status", ["behind", "diverged"])
def test_release_from_other_branch_is_excluded_even_if_target_says_main(window, status):
    client = FakeClient([response(raw_commit("main")), response([raw_release(1, "off", target_commitish="main")]),
                         response(raw_commit("off")), response({"status": status}), response([])])
    result = collect_releases_and_tags(client, "a/b", "main", window)
    assert not result.history
    assert result.excluded_releases[0]["reason"] == "not_on_default_branch"


def test_branch_head_tag_needs_no_ancestry_request(window):
    client = FakeClient([response(raw_commit("head")), response([raw_release(1, "v1")]),
                         response(raw_commit("head")), response([{"name": "v1", "commit": {"sha": "head"}}])])
    result = collect_releases_and_tags(client, "a/b", "main", window)
    assert len(result.in_window(window)) == 1
    assert result.tags[0].on_default_branch
    assert len(client.calls) == 4


def test_empty_history_and_tags_are_real_zero(window):
    result = collect_releases_and_tags(FakeClient([response(raw_commit("main")), response([]), response([])]), "a/b", "main", window)
    assert result.history == result.tags == ()


@pytest.mark.parametrize("raw", [{}, raw_release(1, "v1", published=None),
    raw_release(1, "v1", draft="false"), raw_release(1, "v1", prerelease=None),
    raw_release(1, "v1", tag_name="")])
def test_invalid_release_is_error_not_zero(window, raw):
    with pytest.raises(ValueError):
        collect_releases_and_tags(FakeClient([response(raw_commit("main")), response([raw])]), "a/b", "main", window)


@pytest.mark.parametrize("raw", [{}, {"name": "", "commit": {"sha": "x"}}, {"name": "x", "commit": {"sha": None}}])
def test_invalid_tag(window, raw):
    with pytest.raises(ValueError):
        collect_releases_and_tags(FakeClient([response(raw_commit("main")), response([]), response([raw])]), "a/b", "main", window)


def test_missing_reference_is_explicit_api_error(window):
    with pytest.raises(APIError):
        collect_releases_and_tags(FakeClient([response(raw_commit("main")), response([raw_release(1, "deleted")]),
                                             APIError("HTTP 404", status=404)]), "a/b", "main", window)


def test_pagination_duplicates_do_not_inflate_counts(window):
    raw = raw_release(1, "v1")
    client = FakeClient([response(raw_commit("main")), response([raw, deepcopy(raw)]),
                         response(raw_commit("main")), response([{"name": "v1", "commit": {"sha": "main"}}] * 2)])
    result = collect_releases_and_tags(client, "a/b", "main", window)
    assert len(result.history) == len(result.tags) == 1


@pytest.mark.parametrize("branch,page_size", [("", 100), ("main", 0), ("main", True)])
def test_invalid_collection_parameters_before_network(window, branch, page_size):
    client = FakeClient([])
    with pytest.raises(ValueError):
        collect_releases_and_tags(client, "a/b", branch, window, per_page=page_size)
    assert not client.calls


@pytest.mark.parametrize("timestamp", [None, "2025-01-01", "nonsense"])
def test_missing_or_naive_timestamp_rejected(timestamp):
    with pytest.raises(ValueError):
        utc_datetime(timestamp)


def test_window_boundary_and_timezone(window):
    assert window.contains("2024-12-31T21:00:00-03:00")
    assert not window.contains("2025-12-31T21:00:00-03:00")
    assert not window.contains("2024-12-31T23:59:59Z")
    with pytest.raises(ValueError):
        ObservationWindow(None, None)
    with pytest.raises(ValueError):
        repository_path("a/b/c")
    with pytest.raises(ValueError):
        parse_commit({"sha": "x"})
