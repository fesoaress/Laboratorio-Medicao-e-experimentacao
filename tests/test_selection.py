import io
import json
from urllib.error import HTTPError, URLError
from unittest.mock import MagicMock

import pytest

from src.config import SelectionConfig, load_config
from src.github_client import (
    APIError, APIResponse, GitHubClient, RateLimitError, iter_pages, parse_links,
)
from src.repository_selector import select_candidates


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        response = next(self.responses)
        if isinstance(response, BaseException):
            raise response
        return response


def repo(identifier, name=None):
    return {"id": identifier, "full_name": name or f"org/repo{identifier}"}


def page(items, link="", total=1200, incomplete=False):
    return APIResponse({"items": items, "total_count": total, "incomplete_results": incomplete}, {"Link": link})


def test_links_relations_and_pagination():
    value = '<https://api.github.com/search/repositories?page=2>; rel="next", <https://api.github.com/search/repositories?page=10>; rel="last"'
    assert parse_links(value)["last"].endswith("page=10")
    assert parse_links('<https://api.github.com/x?page=2>; rel="next last"')["next"].endswith("2")
    assert parse_links("") == {}
    client = FakeClient([page([repo(1)], value), page([repo(2)])])
    assert len(list(iter_pages(client, "/search/repositories", {"page": 1}))) == 2
    assert client.calls[1] == ("https://api.github.com/search/repositories?page=2", None)


def test_pagination_detects_cycles_and_obeys_limit():
    response = page([], '<https://api.github.com/x>; rel="next"')
    with pytest.raises(APIError, match="circular"):
        list(iter_pages(FakeClient([response, response]), "https://api.github.com/x"))
    assert len(list(iter_pages(FakeClient([response]), "/x", max_pages=1))) == 1


def test_selection_limit_deduplication_and_slices():
    client = FakeClient([page([repo(1), repo(1), repo(2)], total=3), page([repo(3, "ORG/REPO2"), repo(4)])])
    result = select_candidates(client, SelectionConfig(sample_size=3, search_queries=("stars:1001..2000", "stars:2001..5000")))
    assert [r["id"] for r in result.repositories] == [1, 2, 4]
    assert result.duplicates_skipped == 2
    assert len(client.calls) == 2
    assert client.calls[0][1]["sort"] == "stars"


def test_selection_fetches_second_page_and_stops_at_limit():
    client = FakeClient([page([repo(1)], '<https://api.github.com/search/repositories?page=2>; rel="next"'), page([repo(2), repo(3)])])
    result = select_candidates(client, SelectionConfig(sample_size=2))
    assert len(result.repositories) == 2
    assert len(client.calls) == 2


def test_search_never_fetches_more_than_thousand_per_query():
    pages = [page([repo(i) for i in range(n * 100, (n + 1) * 100)],
                  f'<https://api.github.com/search/repositories?page={n + 2}>; rel="next"') for n in range(11)]
    client = FakeClient(pages)
    result = select_candidates(client, SelectionConfig(sample_size=1100))
    assert len(result.repositories) == 1000
    assert len(client.calls) == 10


@pytest.mark.parametrize("response", [APIResponse([], {}), page([{}]), APIError("HTTP 500")])
def test_search_errors_are_explicit(response):
    result = select_candidates(FakeClient([response]), SelectionConfig())
    assert result.errors
    assert not result.repositories


def test_incomplete_search_is_recorded():
    result = select_candidates(FakeClient([page([repo(1)], incomplete=True)]), SelectionConfig(sample_size=1))
    assert result.queries[0]["incomplete_results"] is True


@pytest.mark.parametrize("kwargs", [{"sample_size": 0}, {"per_page": 101}, {"search_queries": ()},
    {"start_date": "2025-01-01"}, {"start_date": "2025-01-01", "end_date": "2025-12-31"}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        SelectionConfig(**kwargs)


def test_config_missing_official_dates_and_cli_overrides(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"sample_size": 100}), encoding="utf-8")
    assert load_config(path, sample_size=5).sample_size == 5
    assert load_config(path).start_date is None
    assert SelectionConfig(start_date="2024-02-29", end_date="2025-02-28").end_date == "2025-02-28"


def test_http_headers_and_environment_token(monkeypatch):
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = b'{"ok": true}'
    response.headers, response.status = {"Link": ""}, 200
    opener = MagicMock(return_value=response)
    monkeypatch.setattr("src.github_client.urlopen", opener)
    monkeypatch.setenv("GITHUB_TOKEN", "fixture-secret")
    assert GitHubClient().get("/x", {"q": "stars:>1000"}).data == {"ok": True}
    request = opener.call_args.args[0]
    assert request.get_header("Authorization") == "Bearer fixture-secret"
    assert request.get_header("Accept") == "application/vnd.github+json"
    monkeypatch.delenv("GITHUB_TOKEN")
    GitHubClient().get("/x")
    assert opener.call_args.args[0].get_header("Authorization") is None


@pytest.mark.parametrize("status,headers,expected", [(429, {}, RateLimitError),
    (403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "123"}, RateLimitError),
    (403, {"Retry-After": "10"}, RateLimitError), (404, {}, APIError)])
def test_http_errors_do_not_expose_response_body(monkeypatch, status, headers, expected):
    def fail(*args, **kwargs):
        raise HTTPError("https://api.github.com/x", status, "error", headers, io.BytesIO(b"secret"))
    monkeypatch.setattr("src.github_client.urlopen", fail)
    with pytest.raises(expected) as captured:
        GitHubClient().get("/x")
    assert "secret" not in str(captured.value)
    assert captured.value.status == status


def test_http_connection_and_invalid_json(monkeypatch):
    def fail(*args, **kwargs):
        raise URLError("network")
    monkeypatch.setattr("src.github_client.urlopen", fail)
    with pytest.raises(APIError, match="conexão"):
        GitHubClient().get("/x")
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = b"not json"
    monkeypatch.setattr("src.github_client.urlopen", lambda *args, **kwargs: response)
    with pytest.raises(APIError, match="JSON"):
        GitHubClient().get("/x")


def test_http_rejects_foreign_pagination_endpoint():
    with pytest.raises(APIError, match="Endpoint"):
        GitHubClient().get("https://example.com/steal")
