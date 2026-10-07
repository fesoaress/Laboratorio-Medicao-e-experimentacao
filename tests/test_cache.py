from pathlib import Path

import pytest

from src.cache import CacheStore, ResilientClient, RetryConfig, cache_key
from src.github_client import APIError, APIResponse, RateLimitError
from tests.test_selection import FakeClient


def test_cache_key_is_order_independent():
    assert cache_key("/x", {"a": 1, "b": 2}) == cache_key("/x", {"b": 2, "a": 1})
    assert cache_key("/x", {"a": 1}) != cache_key("/x", {"a": 2})


def test_cache_store_roundtrip(tmp_path):
    store = CacheStore(tmp_path)
    assert store.get("/x", {"a": 1}) is None
    response = APIResponse({"ok": True}, {"Link": "<next>"}, 200)
    store.set("/x", {"a": 1}, response)
    cached = store.get("/x", {"a": 1})
    assert cached.data == {"ok": True}
    assert cached.headers == {"Link": "<next>"}
    assert cached.status == 200


def test_cache_store_write_is_atomic_no_leftover_tmp(tmp_path):
    store = CacheStore(tmp_path)
    store.set("/x", None, APIResponse({}, {}, 200))
    assert list(tmp_path.glob("*.tmp")) == []
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_resilient_client_uses_cache_without_hitting_underlying_client(tmp_path):
    store = CacheStore(tmp_path)
    client = FakeClient([APIResponse({"n": 1}, {}, 200)])
    resilient = ResilientClient(client, store)
    first = resilient.get("/x", {"a": 1})
    second = resilient.get("/x", {"a": 1})  # não deve consumir a segunda resposta da fila
    assert first.data == second.data == {"n": 1}
    assert len(client.calls) == 1


def test_resilient_client_waits_for_rate_limit_reset_then_succeeds():
    error = RateLimitError("Rate limit: remaining=0, reset=1000, retry_after=unknown.", status=403)
    client = FakeClient([error, APIResponse({"ok": True}, {}, 200)])
    sleeps = []
    resilient = ResilientClient(client, sleep=sleeps.append, now=lambda: 940.0)
    response = resilient.get("/x")
    assert response.data == {"ok": True}
    assert sleeps == [60.0]  # reset(1000) - now(940)


def test_resilient_client_prefers_retry_after_over_reset():
    error = RateLimitError("Rate limit: remaining=0, reset=9999999, retry_after=5.", status=403)
    client = FakeClient([error, APIResponse({"ok": True}, {}, 200)])
    sleeps = []
    resilient = ResilientClient(client, sleep=sleeps.append, now=lambda: 0.0)
    resilient.get("/x")
    assert sleeps == [5.0]


def test_resilient_client_gives_up_after_too_many_rate_limit_waits():
    error = RateLimitError("Rate limit: remaining=0, reset=unknown, retry_after=unknown.", status=403)
    client = FakeClient([error] * 25)
    resilient = ResilientClient(client, config=RetryConfig(max_rate_limit_waits=2), sleep=lambda s: None)
    with pytest.raises(RateLimitError):
        resilient.get("/x")


def test_resilient_client_backs_off_exponentially_on_5xx_then_succeeds():
    client = FakeClient([APIError("HTTP 503", status=503), APIError("HTTP 503", status=503),
                          APIResponse({"ok": True}, {}, 200)])
    sleeps = []
    resilient = ResilientClient(client, sleep=sleeps.append)
    response = resilient.get("/x")
    assert response.data == {"ok": True}
    assert sleeps == [1.0, 2.0]


def test_resilient_client_gives_up_after_max_attempts_on_5xx():
    client = FakeClient([APIError("HTTP 500", status=500)] * 10)
    resilient = ResilientClient(client, config=RetryConfig(max_attempts=3), sleep=lambda s: None)
    with pytest.raises(APIError):
        resilient.get("/x")
    assert len(client.calls) == 3


def test_resilient_client_does_not_retry_on_4xx():
    client = FakeClient([APIError("HTTP 404", status=404)])
    resilient = ResilientClient(client, sleep=lambda s: pytest.fail("não deveria esperar em 404"))
    with pytest.raises(APIError):
        resilient.get("/x")
    assert len(client.calls) == 1


def test_resilient_client_caches_only_after_success(tmp_path):
    store = CacheStore(tmp_path)
    client = FakeClient([APIError("HTTP 503", status=503), APIResponse({"ok": True}, {}, 200)])
    ResilientClient(client, store, sleep=lambda s: None).get("/x")
    assert store.get("/x", None).data == {"ok": True}