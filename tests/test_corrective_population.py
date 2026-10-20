import gzip
import json
from pathlib import Path

import pytest

from src import corrective, corrective_population as population
from src.gold_sample import read_csv, sha256
from tests.test_s02_dataset import save


@pytest.fixture
def population_files(tmp_path):
    folder = tmp_path / "sources"
    folder.mkdir()
    (folder / "collection_manifest_s02.json").write_text(json.dumps({"window": {"start_date": "2025-10-01", "end_date": "2026-10-01"}}))
    save(folder / "repositories_final_s02.csv", [{"full_name": "group/repo", "release_count": "3"}])
    history = [dict(full_name="group/repo", release_id=str(i), tag_name=f"v1.0.{i}",
        published_at=f"2025-10-0{i}T00:00:00Z", commit_sha=f"sha{i}", prerelease="False", release_body="") for i in range(1, 4)]
    history[0]["release_body"] = "- Fix crash"
    save(folder / "history.csv", history)
    with gzip.open(folder / "releases_s01.csv.gz", "wb") as handle:
        handle.write((folder / "history.csv").read_bytes())
    save(folder / "release_predecessors_s02.csv", [history[0], {**history[0], "release_id": "0",
         "published_at": "2025-09-30T00:00:00Z"}, {**history[0], "release_id": "10", "prerelease": "True"},
         {**history[0], "full_name": "outside/population"}])
    save(folder / "release_intervals_s01.csv", [dict(full_name="group/repo", release_id=str(i), status="complete" if i == 2 else "comparison_error") for i in (1, 2)])
    save(folder / "commits.csv", [dict(full_name="group/repo", release_id="2", message="fix: crash\nbody"),
         dict(full_name="group/repo", release_id="2", message=""), dict(full_name="outside/population", release_id="99", message="fix: ignored")])
    with gzip.open(folder / "release_commits_s01.csv.gz", "wb") as handle:
        handle.write((folder / "commits.csv").read_bytes())
    # Contrato sintético da avaliação; não representa desempenho empírico.
    evaluation = tmp_path / "fixture_evaluation.json"
    evaluation.write_text(json.dumps({"status": "accepted", "f1": .9, "implementation_sha256": sha256(Path(corrective.__file__)),
                                      "version": "v5", "policy": corrective.POLICIES["v5"], "sources": []}))
    return folder, evaluation, tmp_path / "output"


def test_population_uses_full_history_and_marks_missing_context_without_changing_inputs(population_files):
    folder, evaluation, output = population_files
    before = {p.name: sha256(p) for p in folder.iterdir()}
    result = population.classify(folder, evaluation, output)
    rows = read_csv(output / "release_predictions.csv")
    assert result["repositories"] == 1 and result["releases"] == 3
    assert result["classification_usable"] == {"True": 2, "False": 1}
    assert [r["previous_release_id"] for r in rows] == ["0", "1", "2"]
    assert [r["classification_source"] for r in rows] == ["notes", "complete_commits", "incomplete_context"]
    assert [r["corrective_release"] for r in rows] == ["yes", "yes", "no"]
    assert {p.name: sha256(p) for p in folder.iterdir()} == before
    assert result["predictions_sha256"] == sha256(output / "release_predictions.csv")
    with pytest.raises(ValueError, match="execução existente"):
        population.classify(folder, evaluation, output)


@pytest.mark.parametrize("field,value,match", [("status", "needs_refinement", "avaliação aceita"),
    ("f1", .69, "avaliação aceita"), ("implementation_sha256", "changed", "Implementação")])
def test_population_requires_accepted_identical_implementation(population_files, field, value, match):
    folder, evaluation, output = population_files
    payload = json.loads(evaluation.read_text())
    payload[field] = value
    evaluation.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match=match):
        population.classify(folder, evaluation, output)
    assert not output.exists()


def test_changed_evaluation_source_rejected(population_files):
    folder, evaluation, output = population_files
    payload = json.loads(evaluation.read_text())
    payload["sources"] = [{"path": str(folder / "history.csv"), "sha256": "changed"}]
    evaluation.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="Fonte da avaliação"):
        population.classify(folder, evaluation, output)


def test_windows_paths_and_only_line_ending_changes_are_portable(population_files, monkeypatch):
    folder, evaluation, output = population_files
    raw = Path(corrective.__file__).read_bytes().replace(b"\r\n", b"\n")
    snapshot = evaluation.parent / "corrective.py.txt"
    snapshot.write_bytes(raw.replace(b"\n", b"\r\n"))
    current = evaluation.parent / "current.py"
    current.write_bytes(raw)
    payload = json.loads(evaluation.read_text())
    payload["implementation_sha256"] = sha256(snapshot)
    payload["sources"] = [{"path": str(folder / "history.csv").replace("/", "\\"), "sha256": sha256(folder / "history.csv")}]
    evaluation.write_text(json.dumps(payload))
    monkeypatch.setattr(corrective, "__file__", str(current))
    assert population.classify(folder, evaluation, output)["releases"] == 3


def test_population_conflicting_history_duplicate_intervals_and_count_mismatch(population_files):
    folder, evaluation, output = population_files
    path = folder / "release_predecessors_s02.csv"
    rows = read_csv(path)
    original = path.read_bytes()
    rows[0]["commit_sha"] = "changed"
    save(path, rows)
    with pytest.raises(ValueError, match="conflitante"):
        population.classify(folder, evaluation, output)
    path.write_bytes(original)
    intervals = folder / "release_intervals_s01.csv"
    original_intervals = intervals.read_bytes()
    save(intervals, read_csv(intervals) * 2)
    with pytest.raises(ValueError, match="Intervalo duplicado"):
        population.classify(folder, evaluation, output)
    intervals.write_bytes(original_intervals)
    save(folder / "repositories_final_s02.csv", [{"full_name": "group/repo", "release_count": "4"}])
    with pytest.raises(ValueError, match="Contagem de releases"):
        population.classify(folder, evaluation, output)


def test_source_mutation_during_classification_refused(population_files, monkeypatch):
    folder, evaluation, output = population_files
    original_predict = corrective.predict
    def mutate(**kwargs):
        with (folder / "repositories_final_s02.csv").open("ab") as handle:
            handle.write(b"\n")
        return original_predict(**kwargs)
    monkeypatch.setattr(corrective, "predict", mutate)
    with pytest.raises(ValueError, match="Fontes mudaram"):
        population.classify(folder, evaluation, output)
    assert not output.exists()


def test_cli(population_files):
    folder, evaluation, output = population_files
    assert population.main(["--folder", str(folder), "--evaluation", str(evaluation), "--output-dir", str(output)]) == 0
