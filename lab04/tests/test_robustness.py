"""Q3 regression tests for small samples and exact rejection boundaries (#82)."""

import csv
import math
from pathlib import Path

import pytest
from scipy.stats import binom, norm

from lab04.src.robustness import (
    ALPHA, CRITICAL_N, P0, REFERENCE_N, REPETITIONS, SEED,
    null_rejection_regions, run_robustness,
)
from lab04.src.s02_experiments import DEFAULT_P_VALUES, OUTPUT_COLUMNS, write_results_csv


def test_q3_repeats_q1_and_q2_with_the_reference_parameters():
    rows = run_robustness()
    assert len(rows) == len(DEFAULT_P_VALUES) == 6
    assert [r["p_true"] for r in rows] == list(DEFAULT_P_VALUES)
    assert [r["effect_pp"] for r in rows] == [0, 2.5, 5, 7.5, 10, 15]
    assert all(r["n"] == CRITICAL_N and r["p0"] == P0 and r["alpha"] == ALPHA
               and r["seed"] == SEED and r["repetitions"] == REPETITIONS
               and set(r) == set(OUTPUT_COLUMNS) for r in rows)
    assert rows[0]["p_true"] == P0  # Q1 and zero-effect Q2 are the same scenario.
    assert rows == run_robustness()  # The seed reproduces the six scenarios.


def test_q1_q2_reference_csv_has_matching_design():
    path = Path(__file__).resolve().parents[1] / "results" / "s02_q1_q2.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 6
    assert [float(r["p_true"]) for r in rows] == list(DEFAULT_P_VALUES)
    assert all(int(r["n"]) == REFERENCE_N and float(r["p0"]) == P0
               and float(r["alpha"]) == ALPHA and int(r["seed"]) == SEED
               and int(r["repetitions"]) == REPETITIONS for r in rows)


def test_critical_condition_changes_actual_null_rejection_regions():
    small = null_rejection_regions(CRITICAL_N)
    large = null_rejection_regions(REFERENCE_N)
    assert small["expected_failures"] == pytest.approx(1.5)
    assert large["expected_failures"] == pytest.approx(10)
    assert (small["z_first_rejected_k"], small["binomial_first_rejected_k"]) == (4, 5)
    assert large["z_first_rejected_k"] == large["binomial_first_rejected_k"]
    assert small["z_actual_null_rejection"] > ALPHA
    assert small["binomial_actual_null_rejection"] < ALPHA
    assert large["z_actual_null_rejection"] == pytest.approx(
        large["binomial_actual_null_rejection"]
    )


@pytest.mark.parametrize("n", [CRITICAL_N, REFERENCE_N])
def test_analytical_thresholds_match_the_p_value_decision(n):
    regions = null_rejection_regions(n)
    for key, p_value in (
        ("z_first_rejected_k", lambda k: norm.sf((k / n - P0) / math.sqrt(P0 * (1 - P0) / n))),
        ("binomial_first_rejected_k", lambda k: binom.sf(k - 1, n, P0)),
    ):
        threshold = regions[key]
        assert p_value(threshold) < ALPHA
        assert p_value(threshold - 1) >= ALPHA


def test_monte_carlo_rates_track_exact_binomial_power():
    regions = null_rejection_regions(CRITICAL_N)
    rows = run_robustness()
    for row in rows:
        for test, first in (("z", regions["z_first_rejected_k"]),
                            ("binomial", regions["binomial_first_rejected_k"])):
            theoretical = binom.sf(first - 1, CRITICAL_N, row["p_true"])
            rate = row[f"{test}_rejection_rate"]
            se = math.sqrt(theoretical * (1 - theoretical) / REPETITIONS)
            assert abs(rate - theoretical) <= 5 * se + 1 / REPETITIONS
    assert rows[0]["z_rejection_rate"] > rows[0]["binomial_rejection_rate"]
    assert rows[2]["z_rejection_rate"] > rows[2]["binomial_rejection_rate"]


def test_q3_csv_uses_the_schema_expected_by_g3_g4(tmp_path):
    small = run_robustness(repetitions=200)
    path = write_results_csv(small, tmp_path / "s02_q3.csv")
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == list(OUTPUT_COLUMNS)
        rows = list(reader)
    assert len(rows) == 6
    assert {int(row["n"]) for row in rows} == {CRITICAL_N}
    assert [float(row["effect_pp"]) for row in rows] == [0, 2.5, 5, 7.5, 10, 15]


def test_recorded_q3_and_reference_load_for_g3_g4():
    from lab04.src.s02_results import (
        combine_conditions, load_s02_tables, power_table, type1_table,
    )

    directory = Path(__file__).resolve().parents[1] / "results"
    tables = load_s02_tables(directory)
    combined = combine_conditions([tables["q1_q2"], tables["q3"]])
    type1 = type1_table(combined).set_index("n")
    power = power_table(combined)
    assert len(power) == 12
    assert type1.loc[CRITICAL_N, "z_status"] == "liberal"
    assert type1.loc[CRITICAL_N, "binomial_status"] == "conservador"
    assert type1.loc[REFERENCE_N, "z_rate"] == pytest.approx(0.0448)
    assert type1.loc[CRITICAL_N, "z_rate"] == pytest.approx(0.0605)


@pytest.mark.parametrize("bad", [0, -1, 1.5, True])
def test_invalid_sample_size(bad):
    with pytest.raises(ValueError):
        null_rejection_regions(bad)


def test_invalid_repetitions_are_rejected_by_shared_engine():
    with pytest.raises(ValueError):
        run_robustness(repetitions=0)
