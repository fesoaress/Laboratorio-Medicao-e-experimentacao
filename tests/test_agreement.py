from pathlib import Path

import pytest

from src.agreement import (
    RESOLUTION_FIELDS, analyze, apply_resolutions, interpretation, kappa_result, vote_consensus,
)
from src.gold_sample import LABEL_FIELDS, RATERS, read_csv
from src.pipeline import write_csv
from src.s02 import main
from tests.test_gold_sample import completed_rows, generated, universe


@pytest.mark.parametrize("votes,expected", [
    (["yes", "yes", "yes"], ("yes", False)),
    (["yes", "no", "yes"], ("yes", False)),
    (["library_framework", "cli_tool", "other"], ("", True)),
    (["yes", "no", "uncertain"], ("", True)),
])
def test_consensus_protocol(votes, expected):
    assert vote_consensus(votes) == expected


def test_consensus_requires_filled_votes():
    with pytest.raises(ValueError):
        vote_consensus(["yes", "", "no"])


def test_known_kappa_fixture():
    # Pbar=(1+1+1/3+1/3)/4=2/3, Pe=1/2 => kappa=1/3.
    votes = [["yes"] * 3, ["no"] * 3, ["yes", "yes", "no"], ["no", "no", "yes"]]
    result = kappa_result(votes, "corrective_release")
    assert result["kappa"] == pytest.approx(1 / 3)
    assert result["interpretation"] == "razoável"


def test_kappa_perfect_and_constant():
    assert kappa_result([["yes"] * 3, ["no"] * 3], "corrective_release")["kappa"] == pytest.approx(1)
    result = kappa_result([["yes"] * 3] * 10, "corrective_release")
    assert result["kappa"] == "" and result["status"] == "undefined_constant_category"


@pytest.mark.parametrize("votes", [[], [["yes", "no"]], [["yes", "maybe", "no"]]])
def test_kappa_rejects_bad_votes(votes):
    with pytest.raises(ValueError):
        kappa_result(votes, "corrective_release")


@pytest.mark.parametrize("value,label", [(-0.1, "pobre"), (0, "leve"), (0.2, "leve"),
    (0.2001, "razoável"), (0.4, "razoável"), (0.4001, "moderada"), (0.6, "moderada"),
    (0.6001, "substancial"), (0.8, "substancial"), (0.8001, "quase perfeita"), (1, "quase perfeita")])
def test_continuous_interpretation_boundaries(value, label):
    assert interpretation(value) == label


def paths(out):
    return {rater: out / f"gold_sample_{rater}.csv" for rater in RATERS}


def fill_test_files(out):
    for index, (rater, path) in enumerate(paths(out).items()):
        rows = completed_rows(path)
        for row in rows:
            number = int(row["repo"].replace("project", ""))
            row["project_type"] = "library_framework" if number % 2 else "application_service"
            row["releases_represent_real_delivery"] = "yes" if number % 2 else "no"
            row["corrective_release"] = "yes" if int(row["release_id"]) % 2 else "no"
        write_csv(path, LABEL_FIELDS, list(reversed(rows)) if index == 1 else rows)


def test_waits_for_labels_without_fiction(generated, tmp_path):
    out, _, _ = generated
    dest = tmp_path / "validation"
    assert analyze(out / "gold_sample.csv", paths(out), dest, tmp_path / "validation.md") == 1
    assert not (dest / "fleiss_kappa.csv").exists()
    assert not (dest / "disagreements.csv").exists()
    assert not (dest / "gold_sample_consensus.csv").exists()
    assert "Aguardando" in (tmp_path / "validation.md").read_text(encoding="utf-8")


def test_aligns_by_id_and_separates_repository_dimensions(generated, tmp_path):
    out, _, _ = generated
    fill_test_files(out)
    dest = tmp_path / "validation"
    original = {r: path.read_bytes() for r, path in paths(out).items()}
    assert analyze(out / "gold_sample.csv", paths(out), dest, tmp_path / "validation.md") == 0
    results = read_csv(dest / "fleiss_kappa.csv")
    assert [r["items"] for r in results] == ["60", "60", "300"]
    assert all(float(r["kappa"]) == pytest.approx(1) for r in results)
    assert read_csv(dest / "disagreements.csv") == []
    assert len(read_csv(dest / "gold_sample_consensus.csv")) == 300
    assert original == {r: path.read_bytes() for r, path in paths(out).items()}


def test_misalignment_stops_kappa(generated, tmp_path):
    out, _, _ = generated
    fill_test_files(out)
    path = paths(out)["vinicius"]
    rows = read_csv(path)
    rows[0]["item_id"] = "other/project::release::1"
    write_csv(path, LABEL_FIELDS, rows)
    dest = tmp_path / "bad"
    assert analyze(out / "gold_sample.csv", paths(out), dest, tmp_path / "validation.md") == 1
    assert not (dest / "fleiss_kappa.csv").exists()


def test_manual_consensus_roundtrip(generated, tmp_path):
    out, _, _ = generated
    fill_test_files(out)
    target_repo = read_csv(paths(out)["islayder"])[0]["repository"]
    for rater, label in zip(RATERS, ("library_framework", "application_service", "other")):
        path = paths(out)[rater]
        rows = read_csv(path)
        for row in rows:
            if row["repository"] == target_repo:
                row["project_type"] = label
        write_csv(path, LABEL_FIELDS, rows)
    # Binary 2×1 must be settled by majority independently of manual project review.
    path = paths(out)["vinicius"]
    rows = read_csv(path)
    rows[0]["corrective_release"] = "no" if rows[0]["corrective_release"] == "yes" else "yes"
    write_csv(path, LABEL_FIELDS, rows)
    dest = tmp_path / "first"
    assert analyze(out / "gold_sample.csv", paths(out), dest, tmp_path / "validation.md") == 2
    assert not (dest / "gold_sample_consensus.csv").exists()
    disagreements = read_csv(dest / "disagreements.csv")
    assert len(disagreements) == 2
    assert sum(row["needs_manual_review"] == "True" for row in disagreements) == 1
    resolutions = read_csv(dest / "manual_resolutions_template.csv")
    assert len(resolutions) == 1 and resolutions[0]["consensus"] == ""
    resolutions[0].update(consensus="other", reviewer="test human fixture", notes="Fixture de revisão, não dado real")
    resolution_path = tmp_path / "resolutions.csv"
    write_csv(resolution_path, RESOLUTION_FIELDS, resolutions)
    final = tmp_path / "final"
    assert analyze(out / "gold_sample.csv", paths(out), final, tmp_path / "validation.md", resolution_path) == 0
    assert [r["project_type"] for r in read_csv(final / "gold_sample_consensus.csv")
            if r["repository"] == target_repo] == ["other"] * 5
    assert (dest / "fleiss_kappa.csv").read_bytes() == (final / "fleiss_kappa.csv").read_bytes()


@pytest.mark.parametrize("kind", ["invalid", "unknown", "duplicate", "blank_reviewer", "blank_notes"])
def test_bad_manual_resolution_rejected(tmp_path, kind):
    vote = {"item_id": "fixture/repo", "dimension": "project_type", "consensus": "", "needs_manual_review": True}
    resolution = {"item_id": "fixture/repo", "dimension": "project_type", "consensus": "other",
                  "reviewer": "test fixture", "notes": "test only"}
    rows = [resolution]
    if kind == "invalid":
        resolution["consensus"] = "maybe"
    if kind == "unknown":
        resolution["item_id"] = "unknown"
    if kind == "duplicate":
        rows.append(resolution)
    if kind == "blank_reviewer":
        resolution["reviewer"] = ""
    if kind == "blank_notes":
        resolution["notes"] = ""
    path = tmp_path / "resolutions.csv"
    write_csv(path, RESOLUTION_FIELDS, rows)
    with pytest.raises(ValueError):
        apply_resolutions([vote], path)


def test_independent_paths_required(generated, tmp_path):
    out, _, _ = generated
    same = {r: paths(out)["islayder"] for r in RATERS}
    with pytest.raises(ValueError, match="independentes"):
        analyze(out / "gold_sample.csv", same, tmp_path / "out", tmp_path / "report.md")


def test_does_not_overwrite_existing_result_or_input(generated, tmp_path):
    out, _, _ = generated
    dest = tmp_path / "existing"
    analyze(out / "gold_sample.csv", paths(out), dest, tmp_path / "report.md")
    with pytest.raises(ValueError, match="Execução já existente"):
        analyze(out / "gold_sample.csv", paths(out), dest, tmp_path / "report.md")
    with pytest.raises(ValueError, match="sobrescrever entradas"):
        analyze(out / "gold_sample.csv", paths(out), tmp_path / "new", paths(out)["islayder"])


def test_cli_analysis_waiting_and_complete(generated, tmp_path):
    out, _, _ = generated
    arguments = ["analyze", "--sample", str(out / "gold_sample.csv")]
    for rater, path in paths(out).items():
        arguments += [f"--{rater}", str(path)]
    assert main(arguments + ["--output-dir", str(tmp_path / "pending"), "--consensus-dir", str(tmp_path / "pending-gold"),
                            "--report", str(tmp_path / "pending.md")]) == 1
    fill_test_files(out)
    assert main(arguments + ["--output-dir", str(tmp_path / "complete"), "--consensus-dir", str(tmp_path / "complete-gold"),
                            "--report", str(tmp_path / "complete.md")]) == 0
    with pytest.raises(ValueError, match="separadamente"):
        analyze(out / "gold_sample.csv", {}, tmp_path / "missing", tmp_path / "missing.md")
    with pytest.raises(ValueError, match="fora do intervalo"):
        interpretation(1.5)
