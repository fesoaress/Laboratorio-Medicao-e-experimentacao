"""Focused statistical tests for Issue #78."""

import math

import numpy as np
import pytest
from scipy.stats import binomtest, norm

from lab04.src.example_s01 import build_example
from lab04.src.simulation import simulate_runs
from lab04.src.stat_tests import evaluate_tests


def test_simulation_is_reproducible_and_binary():
    first = simulate_runs(100, 0.15, seed=42)
    second = simulate_runs(100, 0.15, seed=42)
    assert np.array_equal(first, second)
    assert set(np.unique(first)).issubset({0, 1})


def test_simulation_boundary_probabilities():
    assert np.sum(simulate_runs(25, 0.0)) == 0
    assert np.sum(simulate_runs(25, 1.0)) == 25


@pytest.mark.parametrize("kwargs", [
    {"n": 0, "p": 0.05},
    {"n": 1.5, "p": 0.05},
    {"n": True, "p": 0.05},
    {"n": 30, "p": -0.1},
    {"n": 30, "p": 1.1},
    {"n": 30, "p": float("nan")},
    {"n": 30, "p": 0.05, "seed": -1},
])
def test_simulation_rejects_bad_parameters(kwargs):
    with pytest.raises(ValueError):
        simulate_runs(**kwargs)


def test_both_tests_use_same_sample_and_correct_formula():
    data = [1] * 4 + [0] * 26
    r = evaluate_tests(data, p0=0.05, alpha=0.05)
    assert (r["n"], r["k"]) == (30, 4)
    assert r["p_hat"] == pytest.approx(4 / 30)
    z = ((4 / 30) - 0.05) / math.sqrt(0.05 * 0.95 / 30)
    assert r["z_statistic"] == pytest.approx(z)
    assert r["z_p_value"] == pytest.approx(norm.sf(z))
    assert r["binomial_p_value"] == pytest.approx(binomtest(4, 30, 0.05, alternative="greater").pvalue)
    assert r["reject_z"] == (r["z_p_value"] < 0.05)
    assert r["reject_binomial"] == (r["binomial_p_value"] < 0.05)
    assert r["z_normal_approximation_caution"] is True


def test_expected_counts_and_one_sided_direction():
    r = evaluate_tests([0] * 100)
    assert r["z_expected_failures"] == pytest.approx(5)
    assert r["z_expected_successes"] == pytest.approx(95)
    assert r["z_p_value"] > 0.5
    assert r["binomial_p_value"] == pytest.approx(1)
    assert r["reject_z"] is False
    assert r["reject_binomial"] is False


def test_strong_signal_rejects_for_both_tests():
    r = evaluate_tests([1] * 25 + [0] * 75)
    assert r["reject_z"] is True
    assert r["reject_binomial"] is True


@pytest.mark.parametrize("data,p0,alpha", [
    ([], 0.05, 0.05),
    ([[0], [1]], 0.05, 0.05),
    ([0, 2], 0.05, 0.05),
    ([0, float("nan")], 0.05, 0.05),
    ([0, 1], 0, 0.05),
    ([0, 1], 1, 0.05),
    ([0, 1], 0.05, 0),
    ([0, 1], 0.05, 1),
])
def test_invalid_test_input(data, p0, alpha):
    with pytest.raises(ValueError):
        evaluate_tests(data, p0=p0, alpha=alpha)


def test_example_is_consistent_and_reproducible():
    example = build_example()
    assert example == build_example()
    assert sum(example["outcomes_0_success_1_failure"]) == example["tests"]["k"]
    assert example["dataset"].startswith("simulated")
