import csv

from lab02.metrics.run_metrics import CSV_COLUMNS
from lab02.simulations.islayder_s02.export_to_results import export_issue
from lab02.trials.storage import CYCLE_FIELDS, TRIAL_FIELDS


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_legacy_row(path, fields, row):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields[:-1])
        writer.writeheader()
        writer.writerow(row)


def test_export_keeps_simulation_explicit_and_idempotent(tmp_path):
    trials_csv = tmp_path / "trials.csv"
    cycles_csv = tmp_path / "trial_cycles.csv"
    metrics_csv = tmp_path / "metrics.csv"
    options = {
        "trials_csv": trials_csv,
        "cycles_csv": cycles_csv,
        "metrics_csv": metrics_csv,
    }

    for issue in (21, 24, 25, 26):
        assert export_issue(issue, **options) == f"SIM-S02-I{issue}"
    export_issue(21, **options)

    trials = read_rows(trials_csv)
    cycles = read_rows(cycles_csv)
    metrics = read_rows(metrics_csv)
    assert len(trials) == 4
    assert len(cycles) == 13
    assert len(metrics) == 4
    assert {row["trial_id"] for row in trials} == {f"SIM-S02-I{i}" for i in (21, 24, 25, 26)}
    assert {row["trial_id"] for row in cycles} == {row["trial_id"] for row in trials}
    assert {row["trial_id"] for row in metrics} == {row["trial_id"] for row in trials}
    assert all(row["source_kind"] == "observed_simulated" for row in trials + cycles + metrics)
    assert all(row["participante"] == "Islayder" for row in trials)
    assert all(row["status"].startswith("simulated-") for row in trials)
    assert all(not row["codigo_path"] and not row["iniciado_em"] for row in trials)
    assert all(not row["solution_path"] and not row["json_path"] for row in metrics)


def test_export_preserves_existing_observed_rows(tmp_path):
    trials_csv = tmp_path / "trials.csv"
    cycles_csv = tmp_path / "trial_cycles.csv"
    metrics_csv = tmp_path / "metrics.csv"
    write_legacy_row(trials_csv, TRIAL_FIELDS, {"trial_id": "real-1", "issue": "#22"})
    write_legacy_row(cycles_csv, CYCLE_FIELDS, {"trial_id": "real-1", "issue": "#22", "ciclo": "1"})
    write_legacy_row(metrics_csv, CSV_COLUMNS, {"trial_id": "real-1", "issue": "#22"})

    export_issue(21, trials_csv=trials_csv, cycles_csv=cycles_csv, metrics_csv=metrics_csv)

    for path in (trials_csv, cycles_csv, metrics_csv):
        rows = read_rows(path)
        original = next(row for row in rows if row["trial_id"] == "real-1")
        assert original["issue"] == "#22"
        assert original["source_kind"] == "observed"
