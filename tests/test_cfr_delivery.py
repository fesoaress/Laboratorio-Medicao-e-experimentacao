import json
from pathlib import Path

import pytest

from src.cfr_delivery import calculate, main, run
from src.corrective_population import classify
from src.gold_sample import read_csv, sha256
from src.temporal import ObservationWindow
from tests.test_corrective_population import population_files


WINDOW = ObservationWindow("2025-10-01", "2026-10-01")


def release(identifier, date, corrective="no", usable="True", previous=""):
    return dict(full_name="group/repo", release_id=str(identifier), tag_name=f"r{identifier}",
                published_at=date, corrective_release=corrective, classification_usable=usable, previous_release_id=previous)


def test_any_corrective_with_intermediates_counts_each_original_once_and_includes_seven_days():
    rows = [release(1, "2025-10-01T00:00:00Z"), release(2, "2025-10-02T00:00:00Z"),
            release(3, "2025-10-08T00:00:00Z", "yes"), release(4, "2025-10-08T01:00:00Z", "yes")]
    summaries, details = calculate(list(reversed(rows)), WINDOW)
    assert [r["failed"] for r in details] == ["True", "True", "True", "False"]
    assert details[0]["evidence_release_id"] == "3"
    assert not details[0]["has_predecessor"]  # Não exclui a primeira release.
    assert summaries[0]["failed_releases"] == 3
    assert summaries[0]["evaluable_releases"] == 4
    assert summaries[0]["cfr_delivery"] == .75


def test_unconditional_cutoff_even_with_positive_evidence_and_censored_can_be_evidence():
    rows = [release(1, "2026-09-23T23:59:59Z"), release(2, "2026-09-24T00:00:00Z", "yes"),
            release(3, "2026-09-25T00:00:00Z", "yes")]
    summaries, details = calculate(rows, WINDOW)
    assert [r["status"] for r in details] == ["failed", "right_censored", "right_censored"]
    assert details[1]["evidence_release_id"] == "3" and details[1]["failed"] == ""
    assert summaries[0]["cfr_delivery"] == 1 and summaries[0]["right_censored"] == 2


def test_unavailable_is_not_negative_but_known_positive_proves_existential_failure():
    rows = [release(1, "2025-10-01T00:00:00Z"), release(2, "2025-10-02T00:00:00Z", usable="False"),
            release(3, "2025-10-03T00:00:00Z", "yes")]
    summaries, details = calculate(rows, WINDOW)
    assert details[0]["status"] == "failed" and details[0]["unavailable_posterior_classifications"] == 1
    # A própria classificação indisponível de R não exclui R: usa evidência posterior.
    assert details[1]["status"] == "failed"
    rows[-1]["corrective_release"] = "no"
    summaries, details = calculate(rows, WINDOW)
    assert details[0]["status"] == "unassessable_context" and details[0]["failed"] == ""
    assert summaries[0]["evaluable_releases"] == 2 and summaries[0]["cfr_delivery"] == 0


def test_later_than_seven_days_or_same_instant_is_not_evidence():
    rows = [release(1, "2025-10-01T00:00:00Z"), release(2, "2025-10-01T00:00:00Z", "yes"),
            release(3, "2025-10-08T00:00:01Z", "yes")]
    _, details = calculate(rows, WINDOW)
    assert details[0]["status"] == "not_failed" and details[1]["status"] == "not_failed"


def test_all_censored_denominator_zero_stays_missing():
    summaries, details = calculate([release(1, "2026-09-30T00:00:00Z", "yes")], WINDOW)
    assert summaries[0]["cfr_delivery"] == ""
    assert summaries[0]["evaluable_releases"] == 0
    assert summaries[0]["status"] == "not_calculable_zero_evaluable_releases"
    assert details[0]["failed"] == ""


@pytest.mark.parametrize("rows", [
    [release(1, "2025-10-01T00:00:00Z")] * 2,
    [release(1, "2026-10-01T00:00:00Z")],
    [release(1, "2025-10-01T00:00:00Z", "maybe")],
    [release(1, "2025-10-01T00:00:00Z", usable="invalid")],
])
def test_invalid_population_rejected(rows):
    with pytest.raises(ValueError):
        calculate(rows, WINDOW)


def test_full_run_and_provenance_and_cli(population_files):
    folder, evaluation, output = population_files
    classify(folder, evaluation, output)
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    assert main(["--folder", str(folder), "--population-dir", str(output)]) == 0
    manifest = json.loads((folder / "cfr_delivery_manifest_s02.json").read_text(encoding="utf-8"))
    assert manifest["valid_repositories"] == 1 and manifest["missing_repositories"] == 0
    assert manifest["release_statuses"] == {"failed": 1, "unassessable_context": 1, "not_failed": 1}
    row = read_csv(folder / "cfr_delivery_s02.csv")[0]
    assert float(row["cfr_delivery"]) == .5 and "heuristic=v5" in row["source"]
    for item in manifest["outputs"]:
        assert sha256(Path(item["path"])) == item["sha256"]
    assert {name: (folder / name).read_bytes() for name in before} == before
    with pytest.raises(ValueError, match="já existe"):
        run(folder, output)


@pytest.mark.parametrize("kind,match", [("predictions", "Previsões"), ("evaluation", "Avaliação aceita"),
                                        ("source", "Fonte da população"), ("population", "população esperada")])
def test_corrupted_or_incomplete_provenance_does_not_write_cfr(population_files, kind, match):
    folder, evaluation, output = population_files
    classify(folder, evaluation, output)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if kind == "predictions":
        manifest["predictions_sha256"] = "changed"
    elif kind == "evaluation":
        manifest["evaluation_sha256"] = "changed"
    elif kind == "source":
        manifest["sources"][0]["sha256"] = "changed"
    else:
        manifest["releases"] = 99
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        run(folder, output)
    assert not (folder / "cfr_delivery_s02.csv").exists()
