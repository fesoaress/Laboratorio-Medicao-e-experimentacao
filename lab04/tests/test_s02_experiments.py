"""Regression tests for Lab04 S02 Q1 and Q2 (Issue #81)."""

import csv
import math

import numpy as np
import pytest
from scipy.stats import binomtest, norm

from lab04.src.s02_experiments import (
    DEFAULT_P_VALUES, OUTPUT_COLUMNS, run_experiments, write_results_csv,
)


def test_reproducibility_and_output_schema():
    first = run_experiments(200, DEFAULT_P_VALUES, repetitions=500, seed=42)
    second = run_experiments(200, DEFAULT_P_VALUES, repetitions=500, seed=42)
    assert first == second
    assert len(first) == 6
    assert all(set(row) == set(OUTPUT_COLUMNS) for row in first)
    assert [row["effect_pp"] for row in first] == [0, 2.5, 5, 7.5, 10, 15]
    assert all(row["n"] == 200 and row["repetitions"] == 500 for row in first)


def test_both_tests_share_exact_same_sample_counts():
    n, p_true, reps, seed = 30, 0.17, 50, 68
    row = run_experiments(n, [p_true], repetitions=reps, seed=seed)[0]
    counts = np.random.default_rng(seed).binomial(n, p_true, size=reps)
    expected_exact = sum(
        binomtest(int(k), n, 0.05, alternative="greater").pvalue < 0.05
        for k in counts
    )
    expected_z = sum(
        norm.sf((k / n - 0.05) / math.sqrt(0.05 * 0.95 / n)) < 0.05
        for k in counts
    )
    assert row["binomial_rejections"] == expected_exact
    assert row["z_rejections"] == expected_z
    assert row["binomial_rejection_rate"] == expected_exact / reps
    assert row["z_rejection_rate"] == expected_z / reps


def test_q1_is_at_zero_effect_and_q2_has_increasing_effects():
    rows = run_experiments(200, [0.05, 0.10, 0.20], repetitions=1000)
    assert rows[0]["effect_pp"] == 0
    assert all(0 <= row["z_rejection_rate"] <= 1 for row in rows)
    assert all(0 <= row["binomial_rejection_rate"] <= 1 for row in rows)
    assert rows[-1]["z_rejection_rate"] > rows[0]["z_rejection_rate"]
    assert rows[-1]["binomial_rejection_rate"] > rows[0]["binomial_rejection_rate"]


def test_extreme_true_probabilities():
    low, high = run_experiments(200, [0, 1], repetitions=20)
    assert (low["z_rejections"], low["binomial_rejections"]) == (0, 0)
    assert (high["z_rejections"], high["binomial_rejections"]) == (20, 20)


def test_alpha_stricter_does_not_increase_rejections():
    low_alpha = run_experiments(200, [0.05, 0.15], repetitions=200, alpha=0.01)
    high_alpha = run_experiments(200, [0.05, 0.15], repetitions=200, alpha=0.05)
    for low, high in zip(low_alpha, high_alpha):
        assert low["z_rejections"] <= high["z_rejections"]
        assert low["binomial_rejections"] <= high["binomial_rejections"]


@pytest.mark.parametrize("params", [
    {"n": 0}, {"n": 2.5}, {"n": True},
    {"repetitions": 0}, {"repetitions": 3.5},
    {"seed": -2}, {"seed": True},
    {"p0": 0}, {"p0": 1}, {"p0": float("nan")},
    {"alpha": 0}, {"alpha": 1},
    {"p_values": []}, {"p_values": [float("nan")]},
    {"p_values": [-0.1]}, {"p_values": [1.1]},
    {"p_values": [True]}, {"p_values": None},
])
def test_invalid_inputs(params):
    kwargs = {"n": 200, "p_values": [0.05], "repetitions": 20}
    kwargs.update(params)
    with pytest.raises(ValueError):
        run_experiments(**kwargs)


def test_csv_roundtrip_and_columns(tmp_path):
    rows = run_experiments(200, [0.05, 0.10], repetitions=100)
    output = write_results_csv(rows, tmp_path / "results" / "data.csv")
    with output.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == list(OUTPUT_COLUMNS)
        loaded = list(reader)
    assert len(loaded) == 2
    assert float(loaded[0]["effect_pp"]) == 0
    assert float(loaded[1]["p_true"]) == pytest.approx(0.10)
    assert int(loaded[0]["repetitions"]) == 100
