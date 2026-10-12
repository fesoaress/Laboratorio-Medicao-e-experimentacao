import copy
import http.client
import json
import re
from pathlib import Path
from threading import Thread

import pytest

from src.fernanda_review import ReviewStore, main, make_server
from src.gold_sample import CONTEXT_FIELDS, LABEL_FIELDS, read_csv, sha256
from src.pipeline import write_csv
from tests.test_gold_sample import generated, universe


@pytest.fixture
def review(generated, tmp_path):
    folder, _, _ = generated
    return ReviewStore(folder / "gold_sample.csv", folder / "gold_sample_fernanda.csv", tmp_path / "backups")


def update_payload(store):
    item = store.repository(0)
    return {"repository": item["repository"], "revision": item["revision"],
            "fields": {"project_type": "cli_tool", "releases_represent_real_delivery": "yes"},
            "releases": {r["item_id"]: {"corrective_release": "no", "notes": "Decisão humana\ncom vírgula, e aspas: \"texto\""}
                         for r in item["releases"]}}


def test_blind_store_partial_save_preserves_all_context_and_backup(review):
    before, digest = review.labels_path.read_bytes(), review.revision
    assert review.progress()["decisions"] == 0 and review.progress()["total"] == 420
    payload = update_payload(review)
    one = next(iter(payload["releases"]))
    payload["releases"][one]["corrective_release"] = ""
    result = review.update(payload)
    assert result["decisions"] == 6 and result["revision"] != digest
    assert (review.backup_dir / f"fernanda_{digest}.csv").read_bytes() == before
    saved = read_csv(review.labels_path)
    for row in saved:
        assert all(row[key] == review.sample[row["item_id"]][key] for key in CONTEXT_FIELDS)
    assert sum(r["project_type"] == "cli_tool" for r in saved) == 5
    assert sum(r["corrective_release"] == "no" for r in saved) == 4
    assert not review.validation()["complete"]
    assert review.validation()["repositories_evaluated"] == 1
    assert review.repository(0)["fields"]["project_type"] == "cli_tool"
    restarted = ReviewStore(review.sample_path, review.labels_path, review.backup_dir)
    assert restarted.progress()["decisions"] == 6
    assert restarted.repository(0)["releases"][0]["notes"].endswith('"texto"')


@pytest.mark.parametrize("case", ["revision", "repository", "unknown_field", "fields", "releases", "extra_release_field", "category", "nonstring"])
def test_invalid_changes_are_rejected_without_writing(review, case):
    payload = update_payload(review)
    first = next(iter(payload["releases"]))
    if case == "revision":
        payload["revision"] = "stale"
    elif case == "repository":
        payload["repository"] = ["not a string"]
    elif case == "unknown_field":
        payload["release_body"] = "forged"
    elif case == "fields":
        payload["fields"] = []
    elif case == "releases":
        payload["releases"].pop(first)
    elif case == "extra_release_field":
        payload["releases"][first]["release_id"] = "forged"
    elif case == "category":
        payload["fields"]["project_type"] = "invalid"
    else:
        payload["releases"][first]["notes"] = 3
    digest = sha256(review.labels_path)
    with pytest.raises(ValueError):
        review.update(payload)
    assert sha256(review.labels_path) == digest and review.progress()["decisions"] == 0
    assert not review.backup_dir.exists()


def test_external_edit_and_changed_canonical_sample_are_protected(review):
    payload = update_payload(review)
    review.labels_path.write_bytes(review.labels_path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="mudou"):
        review.update(payload)
    review.revision = sha256(review.labels_path)
    payload["revision"] = review.revision
    review.sample_path.write_bytes(review.sample_path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="mudou"):
        review.update(payload)


def test_failed_atomic_replace_does_not_change_labels_or_memory(review, monkeypatch):
    import src.fernanda_review as module
    digest = review.revision
    def fail(*_):
        raise OSError("simulated replace failure")
    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError):
        review.update(update_payload(review))
    assert sha256(review.labels_path) == digest and review.progress()["decisions"] == 0
    assert not list(review.labels_path.parent.glob(".fernanda-*.csv"))


def test_constructor_rejects_other_raters_and_corruption(review):
    with pytest.raises(ValueError, match="só abre"):
        ReviewStore(review.sample_path, review.labels_path.with_name("gold_sample_vinicius.csv"), review.backup_dir)
    rows = read_csv(review.labels_path)
    rows[0]["release_body"] = "modified"
    write_csv(review.labels_path, LABEL_FIELDS, rows)
    with pytest.raises(ValueError, match="canônico"):
        ReviewStore(review.sample_path, review.labels_path, review.backup_dir)
    rows[0]["release_body"] = review.sample[rows[0]["item_id"]]["release_body"]
    rows[0]["corrective_release"] = "uncertain"
    write_csv(review.labels_path, LABEL_FIELDS, rows)
    with pytest.raises(ValueError, match="Categoria"):
        ReviewStore(review.sample_path, review.labels_path, review.backup_dir)
    rows[0]["corrective_release"] = ""
    write_csv(review.labels_path, LABEL_FIELDS, rows[:-1])
    with pytest.raises(ValueError, match="IDs"):
        ReviewStore(review.sample_path, review.labels_path, review.backup_dir)
    for index in (-1, 60):
        with pytest.raises(ValueError):
            review.repository(index)


def test_existing_inconsistent_repository_decision_is_not_hidden(review):
    rows = read_csv(review.labels_path)
    rows[0]["project_type"] = "other"
    write_csv(review.labels_path, LABEL_FIELDS, rows)
    restarted = ReviewStore(review.sample_path, review.labels_path, review.backup_dir)
    assert restarted.repository(0)["fields"]["project_type"] == ""
    assert restarted.progress()["decisions"] == 0


def test_http_local_routes_token_and_malformed_requests(review):
    with make_server(review, 0) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def request(method, path, body=None, headers=None):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            conn.request(method, path, body, headers or {})
            response = conn.getresponse()
            content = response.read().decode("utf-8")
            status = response.status
            conn.close()
            return status, content
        try:
            status, page = request("GET", "/")
            assert status == 200 and "Rotulagem independente" in page
            token = re.search(r'const token="([^"]+)"', page).group(1)
            for route in ("/api/progress", "/api/repository?index=0", "/api/validate"):
                assert request("GET", route)[0] == 200
            assert request("GET", "/api/repository?index=wrong")[0] == 400
            assert request("GET", "/missing")[0] == 404
            assert request("GET", "/", headers={"Host": "evil.example"})[0] == 403
            payload = json.dumps(update_payload(review))
            assert request("POST", "/api/save", payload)[0] == 403
            headers = {"X-Review-Token": token, "Content-Type": "application/json"}
            assert request("POST", "/api/save", payload, {**headers, "Origin": "https://evil.example"})[0] == 403
            assert request("POST", "/missing", payload, headers)[0] == 404
            assert request("POST", "/api/save", "", headers)[0] == 400
            assert request("POST", "/api/save", "not json", headers)[0] == 400
            assert request("POST", "/api/save", "[]", headers)[0] == 400
            status, saved = request("POST", "/api/save", payload, headers)
            assert status == 200 and json.loads(saved)["decisions"] == 7
            assert request("POST", "/api/save", payload, headers)[0] == 400
        finally:
            server.shutdown()
            thread.join(3)


def test_main_uses_only_configured_blind_and_own_files(review, monkeypatch, capsys):
    import src.fernanda_review as module
    class FakeServer:
        server_port = 8765
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def serve_forever(self): raise KeyboardInterrupt
    monkeypatch.setattr(module, "make_server", lambda *_: FakeServer())
    assert main(["--sample", str(review.sample_path), "--labels", str(review.labels_path),
                 "--backups", str(review.backup_dir)]) == 0
    assert "http://127.0.0.1:8765" in capsys.readouterr().out
