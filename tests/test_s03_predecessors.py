import json
from types import SimpleNamespace

import pytest

from src import s03_predecessors as m
from src.github_client import APIResponse, APIError
from src.gold_sample import timestamp
from src.s03_collect import save


def tags_page(after=None):
    return APIResponse({"data": {"repository": {"refs": {"nodes": [dict(name="old", target=dict(target=dict(oid="oldsha", authoredDate="2025-09-28T00:00:00Z")))],
        "pageInfo": {"hasNextPage": after is not None, "endCursor": after}}}}}, {})


def test_cached_catalog_never_calls_api_and_rejects_cursor_cycle():
    start = timestamp("2025-10-01T00:00:00Z")
    assert m.cached_tags(SimpleNamespace(get=lambda *a: None), "o/r", start) is None
    rows = m.cached_tags(SimpleNamespace(get=lambda *a: tags_page()), "o/r", start)
    assert rows[0]["sha"] == "oldsha"
    with pytest.raises(ValueError, match="circular"):
        m.cached_tags(SimpleNamespace(get=lambda *a: tags_page("repeated")), "o/r", start)


def test_choose_filters_ancestry_and_resolves_commit():
    candidate = dict(tag_name="pre", date="2025-09-01T00:00:00Z", identifier="1", sha="")
    def get(path, params=None):
        if "/commits/" in path:
            return APIResponse(dict(sha="x", commit=dict(author=dict(date="2025-09-01T00:00:00Z"), committer=dict(date="2025-09-01T00:00:00Z"), message="fix")), {})
        return APIResponse(dict(status="ahead"), {})
    
    repo = dict(full_name="o/r", default_branch_sha="head")
    assert m.choose(SimpleNamespace(get=get), repo, [candidate])["sha"] == "x"
    assert m.choose(None, repo, [{**candidate, "sha": "x"}], SimpleNamespace(ancestors=set())) is None
    assert m.choose(None, repo, [{**candidate, "sha": "x"}], SimpleNamespace(ancestors={"x"}))["sha"] == "x"
    
    with pytest.raises(APIError):
        m.choose(SimpleNamespace(get=lambda *a: APIResponse(dict(status="bad"), {})), repo, [{**candidate, "sha": "x"}])
        
    # --- NOVO TESTE: Diverged status skips candidate ---
    def get_diverged(path, params=None):
        if "/commits/" in path:
            return APIResponse(dict(sha="x", commit=dict(author=dict(date="2025-09-01T00:00:00Z"), committer=dict(date="2025-09-01T00:00:00Z"), message="fix")), {})
        return APIResponse(dict(status="diverged"), {})
        
    assert m.choose(SimpleNamespace(get=get_diverged), repo, [{**candidate, "sha": "x"}]) is None


def test_boundary_patch_preserves_initial_plan_and_resumes(tmp_path, monkeypatch):
    raw, old = tmp_path / "new", tmp_path / "old"
    repo = dict(full_name="o/r", repository_id="1", default_branch_sha="snapshot")
    event = dict(full_name="o/r", identifier="2", date="2025-10-02T00:00:00Z", sha="head", tag_name="new", pair_key="old", previous_identifier="0", body="")
    plan = dict(window=dict(start_date="2025-10-01", end_date="2026-10-01"), repositories=[repo],
                events=[{**event, "variant": "C2"}, {**event, "variant": "C3", "pair_key": ""}], pairs={"old": dict(base_date="2025-09-01T00:00:00Z")})
    save(raw / "plan.json", plan)
    save(old / "checkpoints/1.json", dict(raw_releases=[dict(prerelease=True, draft=False, tag_name="old", published_at="2025-09-28T00:00:00Z", id=1)]))
    monkeypatch.setattr(m, "cached_tags", lambda *a: [dict(tag_name="old", date="2025-09-28T00:00:00Z", sha="oldsha", identifier="old")])
    monkeypatch.setattr(m, "choose", lambda client, repo, candidates, git: {**candidates[0], "sha": "oldsha"})
    monkeypatch.setattr(m, "graph_batch", lambda *a: {})
    monkeypatch.setattr(m, "collect_commits_between", lambda *a: [])
    original = (raw / "plan.json").read_bytes()
    patch = m.run(raw, old, workers=1)
    assert len(patch["events"]) == 2 and len(patch["pairs"]) == 1
    assert (raw / "plan.json").read_bytes() == original
    assert m.run(raw, old, workers=1) == patch
    assert all(r["status"] == "predecessor_verified" for r in patch["audit"])


def test_boundary_failure_does_not_keep_wrong_stable_predecessor(tmp_path, monkeypatch):
    raw, old = tmp_path / "new", tmp_path / "old"
    event = dict(full_name="o/r", variant="C2", identifier="2", pair_key="stable", previous_identifier="0")
    save(raw / "plan.json", dict(window=dict(start_date="2025-10-01"), repositories=[dict(full_name="o/r", repository_id="1")], events=[event], pairs={"stable": dict(base_date="2025-09-01T00:00:00Z")}))
    save(old / "checkpoints/1.json", dict(raw_releases=[]))
    def fail(*a):
        raise APIError("Reference missing", status=404)
    monkeypatch.setattr(m, "choose", fail)
    patch = m.run(raw, old, workers=1)
    assert patch["events"][0]["pair_key"] == ""
    assert patch["audit"][0]["status"] == "predecessor_unavailable_first_interval_excluded"


# --- NOVO TESTE: Não cacheia falhas temporárias (5xx) ---
def test_transient_error_does_not_cache_patch(tmp_path, monkeypatch):
    raw, old = tmp_path / "new", tmp_path / "old"
    event = dict(full_name="o/r", variant="C2", identifier="2", pair_key="stable", previous_identifier="0")
    save(raw / "plan.json", dict(window=dict(start_date="2025-10-01"), repositories=[dict(full_name="o/r", repository_id="1")], events=[event], pairs={"stable": dict(base_date="2025-09-01T00:00:00Z")}))
    save(old / "checkpoints/1.json", dict(raw_releases=[]))
    def fail(*a):
        raise APIError("Service Unavailable", status=503)
    monkeypatch.setattr(m, "choose", fail)
    with pytest.raises(RuntimeError, match="Transient API errors"):
        m.run(raw, old, workers=1)
    assert not (raw / "predecessors/patch.json").exists()