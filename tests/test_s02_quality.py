import json

import pytest

from src import s02_dataset as dataset
from src import s02_quality as quality
from tests.test_s02_dataset import save


@pytest.fixture
def quality_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "PROCESSED", tmp_path)
    monkeypatch.setattr(dataset, "OUT", tmp_path / "dataset_final_s02.csv")
    save(tmp_path / "repositories_final_s02.csv", [{"full_name": "group/repo", "release_count": "5"}])
    save(tmp_path / "deployment_frequency_s02.csv", [dict(full_name="group/repo", releases="5",
         window_days="365", per_week=str(35 / 365), per_month=str(150 / 365))])
    lead = dict.fromkeys(dataset.LEAD_TIME_FIELDS, "")
    lead.update(full_name="group/repo", status="complete", lead_time_release_count="2", lead_time_commit_count="3")
    for variant in ("release", "commit"):
        for field, value in [("q1", "1"), ("median", "2"), ("q3", "3"), ("iqr", "2")]:
            lead[f"lead_time_{variant}_{field}_hours"] = value
    save(tmp_path / "lead_time_s01.csv", [lead])
    save(tmp_path / "workflow_metrics_s02.csv", [dict(full_name="group/repo", successes="9", failures="1",
         ignored="0", cfr="0.1", n_episodes="2", n_censored="1", median_hours="3", censored_proportion="0.5")])
    dataset.main()
    return tmp_path


def change(folder, filename, **updates):
    path = folder / filename
    rows = dataset.read_csv(path)
    rows[0].update(updates)
    save(path, rows)


def test_valid_partial_audit_preserves_sources_and_counts_missing_cfr(quality_sources):
    folder = quality_sources
    before = {p.name: p.read_bytes() for p in folder.glob("*.csv")}
    result = quality.audit(folder)
    assert result["repositories"] == 1 and result["errors"] == []
    assert result["status"] == "valid_with_pending_cfr_delivery"
    assert result["metrics"]["cfr_ci"] == dict(valid=1, missing=0, invalid=0)
    assert result["metrics"]["cfr_delivery"] == dict(valid=0, missing=1, invalid=0)
    assert len(result["sources"]) == 5
    assert all(len(s["sha256"]) == 64 for s in result["sources"])
    assert {p.name: p.read_bytes() for p in folder.glob("*.csv")} == before


def test_delivery_audit_and_cli_output_and_source_protection(quality_sources, tmp_path):
    folder = quality_sources
    save(folder / "cfr_delivery_s02.csv", [{"full_name": "group/repo", "cfr_delivery": "0", "source": "v1:sha256",
         "failed_releases": "0", "evaluable_releases": "5", "right_censored": "0", "unassessable_context": "0"}])
    dataset.main()
    result = quality.audit(folder)
    assert result["status"] == "valid" and result["errors"] == []
    output = folder / "audit" / "result.json"
    assert quality.main(["--folder", str(folder), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == result
    with pytest.raises(ValueError, match="sobrescrever"):
        quality.main(["--folder", str(folder), "--output", str(dataset.OUT)])
    change(folder, "dataset_final_s02.csv", cfr_delivery_source="")
    assert any("sem proveniência" in e for e in quality.audit(folder)["errors"])
    assert quality.main(["--folder", str(folder), "--output", str(output)]) == 1


def test_delivery_partition_formula_and_release_details_must_agree(quality_sources):
    folder = quality_sources
    save(folder / "cfr_delivery_s02.csv", [{"full_name": "group/repo", "cfr_delivery": "0.5", "source": "v5:sha256",
         "failed_releases": "1", "evaluable_releases": "2", "right_censored": "2", "unassessable_context": "1"}])
    save(folder / "cfr_delivery_releases_s02.csv", [{"full_name": "group/repo", "release_id": "1", "status": "failed"}] * 2)
    (folder / "cfr_delivery_manifest_s02.json").write_text("{}")
    dataset.main()
    result = quality.audit(folder)
    assert any("duplicadas no detalhamento" in e for e in result["errors"])
    assert any("agregação difere" in e for e in result["errors"])
    change(folder, "cfr_delivery_s02.csv", failed_releases="3", evaluable_releases="2", unassessable_context="2")
    dataset.main()
    assert any("partição/denominador inválido" in e for e in quality.audit(folder)["errors"])


@pytest.mark.parametrize("field,value", [("cfr_ci", "NaN"), ("cfr_ci", "bad"), ("cfr_ci", "1.2"),
                                         ("lead_time_commit_count", "1.5"), ("lead_time_commit_median_hours", "-1")])
def test_invalid_numeric_domains_are_not_valid_values(quality_sources, field, value):
    change(quality_sources, "dataset_final_s02.csv", **{field: value})
    result = quality.audit(quality_sources)
    assert result["status"] == "invalid"
    assert result["metrics"][field]["invalid"] == 1
    assert any("tipo/domínio" in e for e in result["errors"])


def test_cross_field_formula_quartile_censor_and_join_mismatches(quality_sources):
    change(quality_sources, "dataset_final_s02.csv", cfr_ci="0.9", deployment_frequency_per_week="0",
           release_count="6", lead_time_release_q1_hours="4", lead_time_commit_count="0",
           recovery_time_n_censored="3", recovery_time_median_hours="", cfr_delivery="0.2")
    errors = quality.audit(quality_sources)["errors"]
    for fragment in ("fonte ausente ou valor divergente", "denominador", "quartis desordenados", "observações/ausência",
                     "contagem de releases", "censuras excedem", "sem proveniência"):
        assert any(fragment in e for e in errors), fragment
    change(quality_sources, "dataset_final_s02.csv", recovery_time_n_censored="2", recovery_time_median_hours="1")
    assert any("ausência de recovery" in e for e in quality.audit(quality_sources)["errors"])


@pytest.mark.parametrize("episodes,censored,reason", [("0", "0", "recovery:no_episodes"), ("2", "2", "recovery:all_censored")])
def test_valid_absence_zero_denominators_and_failed_enrichment(quality_sources, episodes, censored, reason):
    folder = quality_sources
    fields = dict.fromkeys(dataset.LEAD_TIME_FIELDS, "")
    change(folder, "lead_time_s01.csv", **fields, status="comparison_error")
    change(folder, "workflow_metrics_s02.csv", successes="0", failures="0", cfr="", n_episodes=episodes,
           n_censored=censored, median_hours="", censored_proportion="" if episodes == "0" else "1")
    change(folder, "deployment_frequency_s02.csv", window_days="0", per_week="", per_month="")
    dataset.main()
    result = quality.audit(folder)
    assert result["errors"] == []
    assert result["missing_reasons"][reason] == 1
    assert result["missing_reasons"]["lead_time:comparison_error"] == 1
    assert result["metrics"]["cfr_ci"]["missing"] == 1


def test_empty_incomplete_duplicate_and_wrong_population(quality_sources):
    folder = quality_sources
    row = dataset.read_csv(dataset.OUT)[0]
    save(dataset.OUT, [row, row])
    assert quality.audit(folder)["duplicate_keys"] == 1
    row["full_name"] = ""
    save(dataset.OUT, [row])
    assert any("População difere" in e for e in quality.audit(folder)["errors"])
    save(dataset.OUT, [{"full_name": "group/repo"}])
    with pytest.raises(ValueError, match="schema"):
        quality.audit(folder)
    save(dataset.OUT, [], ["full_name"])
    with pytest.raises(ValueError, match="vazio"):
        quality.audit(folder)
