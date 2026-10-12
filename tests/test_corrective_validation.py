import gzip
import json
from pathlib import Path

import pytest

from src.corrective_validation import evaluate, main, previous_tags
from src.gold_sample import CONTEXT_FIELDS, HUMAN_FIELDS, LABEL_FIELDS, read_csv, sha256
from src.label_validation import load_sample
from src.pipeline import write_csv
from tests.test_gold_sample import generated, universe


@pytest.fixture
def evaluation_files(generated, tmp_path):
    folder, _, _ = generated
    sample_path = folder / "gold_sample.csv"
    rows = read_csv(sample_path)
    for index, row in enumerate(rows):
        row["tag_name"] = f"2.{index % 5}.0"
        row["commits_context"] = json.dumps([{"message": "fix: crash" if index % 2 else "feat: API"}])
        row["interval_status"] = "complete"
    write_csv(sample_path, CONTEXT_FIELDS, rows)
    human = [{**r, **dict.fromkeys(HUMAN_FIELDS, ""), "project_type": "other",
              "releases_represent_real_delivery": "uncertain", "corrective_release": "yes" if i % 2 else "no"}
             for i, r in enumerate(rows)]
    fernanda, consensus = folder / "gold_sample_fernanda.csv", folder / "gold_sample_consensus.csv"
    write_csv(fernanda, LABEL_FIELDS, human)
    write_csv(consensus, LABEL_FIELDS, list(reversed(human)))
    history = [{"full_name": r["repository"], "release_id": r["release_id"], "tag_name": r["tag_name"],
                "published_at": r["published_at"], "prerelease": "False"} for r in rows]
    release_file, predecessors = tmp_path / "history.csv", tmp_path / "predecessors.csv"
    write_csv(release_file, tuple(history[0]), history)
    write_csv(predecessors, tuple(history[0]), [])
    return sample_path, fernanda, consensus, release_file, predecessors


def test_evaluation_aligned_to_ids_and_records_immutable_sources(evaluation_files, tmp_path):
    before = [sha256(p) for p in evaluation_files]
    output = tmp_path / "v1"
    result = evaluate(*evaluation_files, output)
    assert result["items"] == 300 and result["f1"] == 1 and result["status"] == "accepted"
    assert result["tp"] == result["tn"] == 150
    assert result["predictions_sha256"] == sha256(output / "predictions.csv")
    assert result["implementation_sha256"] == sha256(output / "corrective.py.txt")
    assert [s["sha256"] for s in result["sources"]] == before
    assert [sha256(p) for p in evaluation_files] == before
    assert json.loads((output / "evaluation.json").read_text(encoding="utf-8"))["f1"] == 1
    with pytest.raises(ValueError, match="pasta nova"):
        evaluate(*evaluation_files, output)


def test_gates_do_not_generate_predictions(evaluation_files, tmp_path):
    sample, fernanda, consensus, releases, predecessors = evaluation_files
    output = tmp_path / "blocked"
    rows = read_csv(fernanda)
    rows[0]["corrective_release"] = ""
    write_csv(fernanda, LABEL_FIELDS, rows)
    with pytest.raises(ValueError, match="independente"):
        evaluate(*evaluation_files, output)
    assert not output.exists()
    rows[0]["corrective_release"] = "no"
    write_csv(fernanda, LABEL_FIELDS, rows)
    consensus.unlink()
    with pytest.raises(ValueError, match="Consenso"):
        evaluate(*evaluation_files, output)
    assert not output.exists()
    with pytest.raises(ValueError, match="distintos"):
        evaluate(sample, fernanda, fernanda, releases, predecessors, output)
    with pytest.raises(ValueError, match="Versão"):
        evaluate(*evaluation_files, output, "invented")
    with pytest.raises(ValueError, match="Fernanda"):
        evaluate(sample, consensus, consensus, releases, predecessors, output)


def test_history_uses_unsampled_predecessor_excludes_prereleases_and_accepts_gzip(evaluation_files, tmp_path):
    sample_path, _, _, release_file, predecessors = evaluation_files
    sample = load_sample(sample_path)
    item = next(iter(sample.values()))
    rows = read_csv(release_file)
    older = {"full_name": item["repository"], "release_id": "999001", "tag_name": "2.3.0",
             "published_at": "2025-12-31T00:00:00Z", "prerelease": "False"}
    pre = {**older, "release_id": "999002", "tag_name": "2.3.1-beta", "published_at": "2026-01-01T00:00:01Z", "prerelease": "True"}
    write_csv(predecessors, tuple(older), [older, pre, {**older, "full_name": "outside/sample"}])
    compressed = release_file.with_suffix(".csv.gz")
    with gzip.open(compressed, "wb") as out:
        out.write(release_file.read_bytes())
    result = previous_tags(compressed, predecessors, sample)
    first = min((r for r in sample.values() if r["repository"] == item["repository"]), key=lambda r: r["published_at"])
    assert result[first["item_id"]] == "2.3.0"
    write_csv(predecessors, tuple(rows[0]), [rows[0]])
    assert len(previous_tags(release_file, predecessors, sample)) == 300
    write_csv(predecessors, tuple(rows[0]), [{**rows[0], "tag_name": "rewritten"}])
    with pytest.raises(ValueError, match="conflitante"):
        previous_tags(release_file, predecessors, sample)
    write_csv(predecessors, ("wrong",), [])
    with pytest.raises(ValueError, match="Histórico"):
        previous_tags(release_file, predecessors, sample)


def test_history_missing_or_misaligned_release_rejected(evaluation_files):
    sample_path, _, _, history, predecessors = evaluation_files
    sample, rows = load_sample(sample_path), read_csv(history)
    write_csv(history, tuple(rows[0]), rows[1:])
    with pytest.raises(ValueError, match="todas"):
        previous_tags(history, predecessors, sample)
    rows[0]["tag_name"] = "different"
    write_csv(history, tuple(rows[0]), rows)
    with pytest.raises(ValueError, match="desalinhado"):
        previous_tags(history, predecessors, sample)


def test_bad_commit_context_and_source_mutation_refused(evaluation_files, tmp_path, monkeypatch):
    sample_path, fernanda, consensus, *_ = evaluation_files
    for path, fields in [(sample_path, CONTEXT_FIELDS), (fernanda, LABEL_FIELDS), (consensus, LABEL_FIELDS)]:
        rows = read_csv(path)
        for row in rows:
            row["commits_context"] = '{"bad":true}'
        write_csv(path, fields, rows)
    with pytest.raises(ValueError, match="commits"):
        evaluate(*evaluation_files, tmp_path / "invalid")
    import src.corrective_validation as module
    original = module.sha256
    calls = 0
    def changing_hash(path):
        nonlocal calls
        calls += 1
        return original(path) if calls <= 5 else "changed"
    for path, fields in [(sample_path, CONTEXT_FIELDS), (fernanda, LABEL_FIELDS), (consensus, LABEL_FIELDS)]:
        rows = read_csv(path)
        for row in rows:
            row["commits_context"] = "[]"
        write_csv(path, fields, rows)
    monkeypatch.setattr(module, "sha256", changing_hash)
    with pytest.raises(ValueError, match="mudou"):
        evaluate(*evaluation_files, tmp_path / "changed")
    assert not (tmp_path / "changed").exists()


def test_cli_success_rejection_and_refinement(evaluation_files, tmp_path, capsys):
    names = ("--sample", "--fernanda", "--consensus", "--releases", "--predecessors")
    argv = [v for pair in zip(names, map(str, evaluation_files)) for v in pair]
    assert main([*argv, "--output-dir", str(tmp_path / "cli")]) == 0
    assert "F1=1.0000" in capsys.readouterr().out
    assert main([*argv, "--output-dir", str(tmp_path / "cli")]) == 1
    rows = read_csv(evaluation_files[2])
    for row in rows:
        row["corrective_release"] = "yes"
    write_csv(evaluation_files[2], LABEL_FIELDS, rows)
    assert main([*argv, "--version", "v2", "--output-dir", str(tmp_path / "cli-refine")]) == 2
    assert "needs_refinement" in capsys.readouterr().out
