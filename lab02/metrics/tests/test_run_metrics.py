import csv
import sys

from lab02.metrics.run_metrics import (
    CSV_COLUMNS,
    collect_cyclomatic,
    collect_loc,
    normalize_treatment,
    parse_args,
    save_json_result,
    upsert_csv_row,
)


def test_treatment_is_canonical_across_metrics_and_trials():
    assert normalize_treatment("AI") == "IA"
    assert normalize_treatment(" ia ") == "IA"
    assert normalize_treatment("Manual") == "Manual"


def test_cli_parses_traceability_fields():
    args = parse_args(
        [
            "solucao.py",
            "--participant",
            "P",
            "--kata",
            "K",
            "--treatment",
            "AI",
            "--trial-id",
            "trial-1",
            "--issue",
            "23",
        ]
    )
    assert args.treatment == "IA"
    assert args.trial_id == "trial-1"
    assert args.issue == "23"


def test_cyclomatic_average_uses_methods_not_class_aggregate(tmp_path):
    solution = tmp_path / "solucao.py"
    solution.write_text(
        "class Regra:\n"
        "    def decidir(self, valor):\n"
        "        if valor:\n"
        "            return 1\n"
        "        return 0\n\n"
        "def simples():\n"
        "    return 1\n",
        encoding="utf-8",
    )

    result = collect_cyclomatic(solution, [sys.executable, "-m", "radon"])

    assert result["analyzed_functions"] == 2
    assert result["avg_cyclomatic_complexity"] == 1.5
    assert sorted(item["name"] for item in result["functions"]) == ["decidir", "simples"]


def test_csv_upsert_removes_preexisting_duplicate_key(tmp_path):
    csv_path = tmp_path / "metrics.csv"
    old_row = {column: "" for column in CSV_COLUMNS}
    old_row.update({"participant": "P", "kata": "K", "treatment": "IA", "loc": 1})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerow(old_row)
        writer.writerow(old_row)

    new_row = dict(old_row, loc=2)
    upsert_csv_row(csv_path, new_row)

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["loc"] == "2"


def test_distinct_trial_ids_do_not_overwrite_repetition(tmp_path):
    csv_path = tmp_path / "metrics.csv"
    first = {column: "" for column in CSV_COLUMNS}
    first.update(
        {
            "participant": "P",
            "kata": "K",
            "treatment": "IA",
            "trial_id": "trial-1",
        }
    )
    second = dict(first, trial_id="trial-2")

    upsert_csv_row(csv_path, first)
    upsert_csv_row(csv_path, second)

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["trial_id"] for row in rows] == ["trial-1", "trial-2"]


def test_json_names_do_not_collide_within_same_second(tmp_path):
    result = {"participant": "Pessoa Teste", "kata": "kata1", "treatment": "IA"}
    first = save_json_result(result, tmp_path)
    second = save_json_result(result, tmp_path)
    assert first != second
    assert first.is_file() and second.is_file()


def test_radon_syntax_error_is_preserved_instead_of_dropping_trial(tmp_path):
    solution = tmp_path / "solucao.py"
    solution.write_text("def quebrada(:\n", encoding="utf-8")
    command = [sys.executable, "-m", "radon"]

    cyclomatic = collect_cyclomatic(solution, command)
    loc = collect_loc(solution, command)

    assert cyclomatic["avg_cyclomatic_complexity"] is None
    assert cyclomatic["error"]
    assert loc["loc"] is None
    assert loc["error"]
