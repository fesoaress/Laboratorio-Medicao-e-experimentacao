"""Contrato do left join S02; fontes sintéticas, sem tocar nos CSVs reais."""

import csv

import pytest

from src import s02_dataset as dataset


def save(path, rows, fields=None):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def sources(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "PROCESSED", tmp_path)
    monkeypatch.setattr(dataset, "OUT", tmp_path / "result" / "dataset.csv")
    repos = [{"full_name": "team/alpha", "release_count": "5", "description": 'Ação, "API"\nsegunda linha'},
             {"full_name": "team/beta", "release_count": "9", "description": ""}]
    save(tmp_path / "repositories_final_s02.csv", repos)
    for filename, mapping in [
        ("deployment_frequency_s02.csv", dataset.DEPLOYMENT_FIELDS),
        ("lead_time_s01.csv", dataset.LEAD_TIME_FIELDS),
        ("workflow_metrics_s02.csv", dataset.WORKFLOW_FIELDS),
    ]:
        # Ordem deliberadamente inversa: alinhamento é por identidade.
        save(tmp_path / filename, [dict(full_name=r["full_name"],
             **{key: f"{r['full_name']}:{key}" for key in mapping}) for r in reversed(repos)])
    return tmp_path, repos


def test_consolidation_preserves_grain_all_variants_context_and_sources(sources, capsys):
    folder, repos = sources
    before = {p.name: p.read_bytes() for p in folder.glob("*.csv")}
    assert dataset.main() == 0
    result = dataset.read_csv(dataset.OUT)
    assert [r["full_name"] for r in result] == [r["full_name"] for r in repos]
    assert len(result) == 2
    assert list(result[0]) == (dataset.METADATA_FIELDS + list(dataset.DEPLOYMENT_FIELDS.values())
                             + list(dataset.LEAD_TIME_FIELDS.values())
                             + list(dataset.WORKFLOW_FIELDS.values()) + dataset.FUTURE_FIELDS)
    for row, source in zip(result, repos):
        assert row["description"] == source["description"]
        assert row["repository_id"] == ""
        for mapping in (dataset.DEPLOYMENT_FIELDS, dataset.LEAD_TIME_FIELDS, dataset.WORKFLOW_FIELDS):
            for old, new in mapping.items():
                assert row[new] == f"{source['full_name']}:{old}"
        assert row["cfr_delivery"] == row["cfr_delivery_source"] == ""
    assert {p.name: p.read_bytes() for p in folder.glob("*.csv")} == before
    assert "MERGE COMPLETO" in capsys.readouterr().out


def test_optional_delivery_retains_zero_provenance_and_missingness(sources):
    folder, _ = sources
    save(folder / "cfr_delivery_s02.csv", [
        {"full_name": "team/alpha", "cfr_delivery": "0", "source": "policy-v1:sha256"}])
    assert dataset.main() == 0
    first, second = dataset.read_csv(dataset.OUT)
    assert first["cfr_delivery"] == "0"
    assert first["cfr_delivery_source"] == "policy-v1:sha256"
    assert second["cfr_delivery"] == second["cfr_delivery_source"] == ""


@pytest.mark.parametrize("filename", ["repositories_final_s02.csv", "deployment_frequency_s02.csv",
                                     "lead_time_s01.csv", "workflow_metrics_s02.csv"])
def test_required_source_missing_does_not_replace_existing_result(sources, filename, capsys):
    folder, _ = sources
    dataset.OUT.parent.mkdir()
    dataset.OUT.write_bytes(b"previous result")
    (folder / filename).unlink()
    assert dataset.main() == 1
    assert dataset.OUT.read_bytes() == b"previous result"
    assert filename in capsys.readouterr().out


def test_missing_metric_rows_preserve_left_join_and_explicit_blanks(sources, capsys):
    folder, _ = sources
    for filename in ("deployment_frequency_s02.csv", "lead_time_s01.csv", "workflow_metrics_s02.csv"):
        save(folder / filename, [], ["full_name"])
    assert dataset.main() == 0
    rows = dataset.read_csv(dataset.OUT)
    assert len(rows) == 2
    for row in rows:
        assert row["deployment_frequency_per_week"] == ""
        assert row["lead_time_commit_count"] == ""
        assert row["recovery_time_median_hours"] == ""
    output = capsys.readouterr().out
    assert "sem deployment_frequency: 2" in output
    assert "sem lead_time: 2" in output
    assert "sem workflow_metrics: 2" in output
    assert "MERGE COMPLETO" not in output


def test_duplicate_repositories_fail_before_writing(sources):
    folder, repos = sources
    save(folder / "repositories_final_s02.csv", [repos[0], repos[0]])
    with pytest.raises(ValueError, match="Duplicata em repositories"):
        dataset.main()
    assert not dataset.OUT.exists()


@pytest.mark.parametrize("filename", ["deployment_frequency_s02.csv", "lead_time_s01.csv",
                                     "workflow_metrics_s02.csv", "cfr_delivery_s02.csv"])
def test_duplicate_join_keys_cannot_silently_overwrite_metrics(sources, filename):
    folder, _ = sources
    save(folder / filename, [{"full_name": "team/alpha"}] * 2)
    with pytest.raises(ValueError, match="Duplicata na fonte"):
        dataset.main()
    assert not dataset.OUT.exists()


def test_empty_metric_identity_rejected():
    with pytest.raises(ValueError, match="full_name vazio"):
        dataset.index_by_full_name([{"full_name": "  "}])


def test_large_csv_field_survives_round_trip(tmp_path):
    path = tmp_path / "large.csv"
    original = {"full_name": "team/large", "description": "á" * 150000 + "\nnotas"}
    save(path, [original])
    assert dataset.read_csv(path) == [original]
