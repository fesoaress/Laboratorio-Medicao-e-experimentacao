import pytest
from src import s03_audit


@pytest.fixture(scope="module")
def real_audit():
    return s03_audit.run()


def test_independent_audit_reconciles_homologated_s02(real_audit):
    assert real_audit["status"] == "valid"
    assert real_audit["dataset"]["repositories"] == 311
    assert real_audit["independent_cfr_statuses"] == dict(failed=20038, not_failed=6406, right_censored=677, unassessable_context=31)
    assert real_audit["consensus_pending"] == 0
    assert real_audit["evaluations"][-1]["f1"] >= .7
    assert real_audit["fleiss_kappa"]["releases_represent_real_delivery"] == pytest.approx(.15401301518438)


def test_audit_sources_use_versioned_compressed_inputs(real_audit):
    sources = {s["path"] for s in real_audit["protected_sources"]}
    for name in ("release_commits_s01.csv", "releases_s01.csv", "workflow_runs_s02.csv"):
        assert f"data/processed/s02/{name}" not in sources
        assert f"data/processed/s02/{name}.gz" in sources


def test_audit_refuses_changed_human_hash(monkeypatch):
    monkeypatch.setattr(s03_audit, "sha256", lambda p: "changed")
    with pytest.raises(ValueError, match="homologada"):
        s03_audit.run()


def test_independent_kappa_constant_and_no_agreement():
    assert s03_audit.independent_kappa([["yes"] * 3] * 4) is None
    assert s03_audit.independent_kappa([["a", "b", "c"]] * 2) == pytest.approx(-.5)


def test_independent_cfr_rejects_changed_classification():
    rows = [dict(full_name="o/r", release_id="1", published_at="2026-01-01T00:00:00Z", classification_usable="True", corrective_release="no")]
    with pytest.raises(ValueError, match="diverge"):
        s03_audit.independent_cfr(rows, [dict(full_name="o/r", release_id="1", status="failed")], 2e9)
    with pytest.raises(ValueError, match="sem previsão"):
        s03_audit.independent_cfr([], [dict(full_name="o/r", release_id="1", status="failed")], 2e9)


