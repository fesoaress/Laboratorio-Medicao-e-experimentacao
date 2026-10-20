from types import SimpleNamespace
from pathlib import Path
import gzip
import json

import pytest

from src import s03_collect as m
from src.github_client import APIError


def comparison(nodes=(), next_page=False, cursor=None, total=0):
    return {"baseTarget": {"oid": "base"}, "headTarget": {"oid": "head"}, "status": "AHEAD",
            "commits": {"nodes": list(nodes), "totalCount": total,
                        "pageInfo": {"hasNextPage": next_page, "endCursor": cursor}}}


def test_graphql_checks_oids_and_variables(monkeypatch):
    pair = {"base_tag": "v1", "head_tag": "v2", "base_date": "2026-01-01T00:00:00Z",
            "head_date": "2026-02-01T00:00:00Z", "base": "base", "head": "head"}
    def query(cache, text, variables):
        assert variables["owner"] == "owner" and variables["name"] == "repo"
        assert "repo" not in variables
        return {"data": {"repository": {"a0": {"compare": comparison()}}}}
    monkeypatch.setattr(m, "graphql", query)
    actual = m.graph_batch(SimpleNamespace(cache=None), "owner/repo", [("key", pair)])
    assert actual["key"]["commits"] == []


def test_graphql_pagination_rejects_status_change(monkeypatch):
    pair = {"base_tag": "v1", "head_tag": "v2", "base_date": "2026-01-01T00:00:00Z",
            "head_date": "2026-02-01T00:00:00Z", "base": "base", "head": "head"}
    first = comparison(next_page=True, cursor="next", total=1)
    second = comparison(total=1)
    second["status"] = "DIVERGED"
    values = iter([first, second])
    monkeypatch.setattr(m, "graphql", lambda *a: {"data": {"repository": {"a0": {"compare": next(values)}}}})
    with pytest.raises(APIError, match="mudou"):
        m.graph_batch(SimpleNamespace(cache=None), "o/r", [("key", pair)])


def test_pair_identity_and_atomic_save(tmp_path):
    assert m.pair_key("O/R", "a", "b") == m.pair_key("o/r", "a", "b")
    assert m.pair_key("o/r", "a", "b") != m.pair_key("o/r", "b", "a")
    m.save(tmp_path / "out.json", {"value": "ação"})
    assert "ação" in (tmp_path / "out.json").read_text(encoding="utf-8")
    assert not (tmp_path / "out.tmp").exists()


def test_plan_real_snapshot_keeps_distinct_units():
    p = m.plan(Path("data/processed/s02"))
    assert p["window"] == dict(start_date="2025-10-01", end_date="2026-10-01")
    assert len(p["repositories"]) == 311
    assert sum(e["variant"] == "C2" for e in p["events"]) == 29007
    assert sum(e["variant"] == "C3" for e in p["events"]) == 37051
    assert sum(v["source"] == "complementary" for v in p["pairs"].values()) == 9980
    for event in p["events"]:
        if event["pair_key"]:
            assert p["pairs"][event["pair_key"]]["head"] == event["sha"]


def test_layered_cache_preserves_original(tmp_path):
    from src.github_client import APIResponse
    old = tmp_path / "old"
    original = m.CacheStore(old / "cache")
    original.set("/a", None, APIResponse({"value": 1}, {}))
    cache = m.LayeredCache(tmp_path / "new", old)
    assert cache.get("/a", None).data == {"value": 1}
    assert cache.get("/absent", None) is None
    cache.set("/a", None, APIResponse({"value": 2}, {}))
    assert cache.get("/a", None).data == {"value": 2}
    assert original.get("/a", None).data == {"value": 1}


def specification():
    pair = dict(full_name="o/r", base="a", head="b", base_tag="v1", head_tag="v2", base_date="2026-01-01T00:00:00Z", head_date="2026-01-02T00:00:00Z", source="complementary", source_release_id="", expected_commits=None)
    return dict(window={}, repositories=[], events=[], pairs={"k": pair})


def test_collection_resume_and_plan_guard(tmp_path, monkeypatch):
    p = specification()
    monkeypatch.setattr(m, "plan", lambda *a: p)
    monkeypatch.setattr(m, "graph_batch", lambda *a: {"k": dict(status="complete", transport="mock", commits=[])})
    m.collect(tmp_path, tmp_path / "raw", tmp_path / "old", 1)
    target = tmp_path / "raw/intervals/k.json"
    original = target.read_bytes()
    m.collect(tmp_path, tmp_path / "raw", tmp_path / "old", 1)
    assert target.read_bytes() == original
    saved = json.loads(original)
    saved["head"] = "wrong"
    m.save(target, saved)
    with pytest.raises(ValueError, match="Checkpoint"):
        m.collect(tmp_path, tmp_path / "raw", tmp_path / "old", 1)
    p["window"] = {"changed": True}
    with pytest.raises(ValueError, match="Plano mudou"):
        m.collect(tmp_path, tmp_path / "raw", tmp_path / "old", 1)


@pytest.mark.parametrize("status,expected", [(404, "ignored_compare_404"), (422, "complete"), (500, "error"), (401, "raises")])
def test_collection_rest_failure_is_explicit(tmp_path, monkeypatch, status, expected):
    monkeypatch.setattr(m, "plan", lambda *a: specification())
    def fail(*a):
        raise APIError("HTTP error", status=status)
    monkeypatch.setattr(m, "graph_batch", fail)
    monkeypatch.setattr(m, "collect_commits_between", fail)
    if expected == "raises":
        with pytest.raises(APIError):
            m.collect(tmp_path, tmp_path / "raw", tmp_path / "old", 1)
    else:
        m.collect(tmp_path, tmp_path / "raw", tmp_path / "old", 1)
        row = json.loads((tmp_path / "raw/intervals/k.json").read_text())
        assert row["status"] == expected and not row["commits"]
        if expected == "error":
            assert "HTTP error" in row["error"]
        else:
            assert row["error"] == ""

def test_export_reuses_exact_s02_pair_and_counts(tmp_path):
    from src.pipeline import write_csv
    p = specification()
    p["pairs"]["k"].update(source="s02_export", source_release_id="2", expected_commits=1)
    p["pairs"]["identical"] = {**p["pairs"]["k"], "source": "identical", "expected_commits": 0}
    p["pairs"]["new"] = {**p["pairs"]["k"], "source": "complementary", "expected_commits": None}
    m.save(tmp_path / "raw/plan.json", p)
    m.save(tmp_path / "raw/intervals/new.json", {**p["pairs"]["new"], "status": "error", "commits": []})
    fields = ("full_name", "release_id", "sha", "author_date", "committer_date", "message", "html_url")
    row = dict(zip(fields, ["o/r", "2", "sha", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "fix: x", "url"]))
    csv_path = tmp_path / "commits.csv"
    write_csv(csv_path, fields, [row])
    with gzip.open(tmp_path / "release_commits_s01.csv.gz", "wb") as handle:
        handle.write(csv_path.read_bytes())
    output = tmp_path / "out/context.jsonl.gz"
    _, contexts = m.export_context(tmp_path, tmp_path / "raw", output)
    assert contexts["k"]["commits"][0]["message"] == "fix: x"
    assert contexts["new"]["status"] == "error"
    shard = output.parent / "variant_context/part-000.jsonl.gz"
    original = shard.read_bytes()
    m.export_context(tmp_path, tmp_path / "raw", output)
    assert shard.read_bytes() == original
    p["pairs"]["k"]["expected_commits"] = 2
    m.save(tmp_path / "raw/plan.json", p)
    with pytest.raises(ValueError, match="incompleto"):
        m.export_context(tmp_path, tmp_path / "raw", output)
