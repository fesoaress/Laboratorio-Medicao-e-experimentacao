"""Regressões de inferência/reamostragem da #74, com oráculos independentes."""

from itertools import cycle, permutations, product
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import s03_bootstrap as boot, s03_inference as inf
from src.s03_descriptive import METRICS, load_data


@pytest.mark.parametrize("count", [-2, -1, 0, 2.5, True, np.bool_(True), np.nan, np.inf])
def test_spearman_rejects_invalid_permutation_counts(count):
    with pytest.raises(ValueError, match="permutações"):
        inf.spearman([1, 2, 3], [3, 2, 1], permutations=count)


@pytest.mark.parametrize("count", [999, 1000.5, True, np.bool_(True), np.nan, np.inf])
def test_bootstrap_rejects_invalid_iteration_counts(count):
    with pytest.raises(ValueError, match="reamostragens"):
        boot.bootstrap([1, 2, 3], iterations=count)


@pytest.mark.parametrize("x,y", [
    ([1], [1, 2, 3]),
    ([1, 2, 3], [1]),
    ([[1, 2], [3, 4]], [[4, 3], [2, 1]]),
    ([1, 2, 3], [[1], [2], [3]]),
    (1, [1, 2, 3]),
])
@pytest.mark.parametrize("method", [inf.spearman, boot.bootstrap])
def test_paired_statistics_reject_misaligned_or_multidimensional_input(method, x, y):
    with pytest.raises(ValueError, match="vetores unidimensionais de mesmo tamanho"):
        method(x, y)


def test_bootstrap_median_rejects_matrix_instead_of_flattening_repositories():
    with pytest.raises(ValueError, match="vetor unidimensional"):
        boot.bootstrap([[1, 2], [3, 4]])


def test_numpy_integer_resampling_counts_are_supported():
    assert inf.spearman([1, 2, 3], [3, 2, 1], np.int64(9))["permutations"] == 9
    assert boot.bootstrap([1], iterations=np.int64(1000))["valid_replicates"] == 1000


def test_spearman_tied_ranks_count_both_tails_and_include_observed_boundary(monkeypatch):
    # x ranks = [1.5, 1.5, 3, 4]. Of the 24 labelled permutations of y,
    # two reach the most negative rho and two the most positive rho.
    # Keep the production Monte Carlo +1 correction: (4 + 1)/(24 + 1).
    orders = iter(permutations(range(4)))
    calls = []

    class EnumeratedPermutations:
        def permutation(self, values):
            calls.append(1)
            return values[list(next(orders))]

    monkeypatch.setattr(inf.np.random, "default_rng", lambda seed: EnumeratedPermutations())
    result = inf.spearman([1, 1, 2, 3], [4, 3, 2, 1], permutations=24)
    assert result["rho"] == pytest.approx(-3 / np.sqrt(10))
    assert result["p_permutation"] == pytest.approx(5 / 25)
    assert len(calls) == 24


def test_spearman_missingness_is_pairwise_and_does_not_impute_zero():
    result = inf.spearman([0, 1, np.nan, 2, 3, np.inf, 4],
                          [4, 3, 2, np.nan, 1, 8, 0], permutations=39)
    assert result == inf.spearman([0, 1, 3, 4], [4, 3, 1, 0], permutations=39)
    assert result["n"] == 4
    assert result["rho"] == pytest.approx(-1)
    assert 1 / 40 <= result["p_permutation"] <= 1


def test_spearman_all_missing_or_constant_after_pairwise_exclusion_is_undefined():
    for x, y, n in [([np.nan], [1], 0), ([1, 2, 3], [1, np.nan, np.inf], 1),
                    ([1, 2, 3, 4], [7, 7, 7, np.nan], 3)]:
        result = inf.spearman(x, y, permutations=9)
        assert result["n"] == n
        assert result["status"] == "insufficient_or_constant"
        assert result["rho"] is result["p"] is result["p_permutation"] is None


@pytest.mark.parametrize("invalid", [-.01, 1.01])
def test_holm_rejects_out_of_range_probabilities_without_mutating_rows(invalid):
    rows = [{"p": .01, "p_holm": .02}, {"p": invalid, "p_holm": .5}]
    original = [row.copy() for row in rows]
    with pytest.raises(ValueError, match="p-valores"):
        inf.holm(rows)
    assert rows == original


def test_holm_undefined_values_ties_boundaries_and_custom_fields():
    rows = [{"raw": p, "adjusted": "stale"} for p in [None, np.nan, np.inf, 1, .04, .01, .01, 0]]
    assert inf.holm(rows, "raw", "adjusted") is rows
    # Five finite hypotheses, sorted: 0, .01, .01, .04, 1.
    assert [r["adjusted"] for r in rows] == [None, None, None, 1, .08, .04, .04, 0]
    assert all("p_holm" not in row for row in rows)


@pytest.fixture
def inference_data():
    rng = np.random.default_rng(7406)
    n = 80
    data = pd.DataFrame({field: rng.uniform(0, 1, n) for field, _, _ in METRICS.values()})
    data["stargazers_count"] = np.arange(n)
    data["contributors_count"] = np.repeat([1, 2, 3, 4], 20)
    data["repo_age_days"] = rng.permutation(n)
    # Strong factor relationships ensure mixing families would change results.
    data[METRICS["cfr_b"][0]] = data.repo_age_days / n
    data[METRICS["lt_release"][0]] = data.stargazers_count
    return data


def manual_holm(values):
    """Step-down arithmetic; deliberately does not call statsmodels/production."""
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted, largest = [None] * len(values), 0
    for position, index in enumerate(order):
        largest = max(largest, (len(values) - position) * values[index])
        adjusted[index] = min(1, largest)
    return adjusted


def test_run_corrects_two_correlations_and_rq06_families_separately(inference_data):
    correlations, tests, _, _ = inf.run(inference_data, permutations=39)
    assert correlations.outcome.tolist() == ["cfr_a", "cfr_b"]
    assert correlations.p_permutation_holm.tolist() == pytest.approx(manual_holm(correlations.p_permutation.tolist()))
    for family, count in (("primary_12", 12), ("supplementary_3", 3)):
        selected = tests.loc[tests.family == family]
        assert len(selected) == count
        assert selected.p_holm.tolist() == pytest.approx(manual_holm(selected.p.tolist()))
    combined = manual_holm(tests.p.tolist())
    assert not np.allclose(tests.p_holm, combined)


def test_run_keeps_global_quartiles_when_one_metric_has_missing_values(inference_data):
    _, _, _, original_cuts = inf.run(inference_data, permutations=9)
    altered = inference_data.copy(deep=True)
    altered.loc[:19, METRICS["lt_release"][0]] = np.nan
    _, tests, details, actual_cuts = inf.run(altered, permutations=9)
    pd.testing.assert_frame_equal(actual_cuts, original_cuts)
    stars = details.loc[(details.factor == "stargazers_count") & (details.metric == "lt_release")]
    assert stars.n.tolist() == [0, 20, 20, 20]
    assert stars.missing.tolist() == [20, 0, 0, 0]
    assert stars.iloc[0][["median", "q1", "q3", "iqr"]].isna().all()
    test = tests.loc[(tests.factor == "stargazers_count") & (tests.metric == "lt_release")].iloc[0]
    assert test.n == 60 and test.groups == 3 and test.status == "calculated"
    assert inference_data[METRICS["lt_release"][0]].notna().all()


def test_run_undefined_hypotheses_are_excluded_from_each_holm_family(inference_data):
    inference_data[METRICS["cfr_a"][0]] = np.nan
    correlations, tests, details, _ = inf.run(inference_data, permutations=9)
    undefined = tests.loc[tests.metric == "cfr_a"]
    assert undefined.p.isna().all() and undefined.p_holm.isna().all()
    assert undefined.n.tolist() == [0, 0, 0]
    assert undefined.status.tolist() == ["insufficient_groups"] * 3
    assert details.loc[details.metric == "cfr_a", "n"].sum() == 0
    assert pd.isna(correlations.loc[0, "p_permutation_holm"])
    assert correlations.loc[1, "p_permutation_holm"] == correlations.loc[1, "p_permutation"]
    primary = tests.loc[(tests.family == "primary_12") & tests.p.notna()]
    assert len(primary) == 9
    assert primary.p_holm.tolist() == pytest.approx(manual_holm(primary.p.tolist()))


def test_quartiles_are_right_closed_and_collapsed_ties_leave_no_artificial_split():
    labels, cuts = inf.groups_for([1, 2, 3, 4, 5, 6, 7, 8, 9, np.nan, np.inf, -np.inf])
    assert cuts.tolist() == [3, 5, 7]
    assert labels.tolist() == [0, 0, 0, 1, 1, 2, 2, 3, 3, -1, -1, -1]
    labels, cuts = inf.groups_for([1] * 12 + [2] * 4)
    assert cuts.tolist() == [1, 1.25]
    assert labels.tolist() == [0] * 12 + [2] * 4
    result = inf.compare_groups([np.array([1, 2, 3, 4, 5]), [], np.array([6, 7, 8, 9, 10])])
    assert result["test"] == "Mann–Whitney" and result["groups"] == 2


def test_cliff_delta_matches_pairwise_dominance_with_ties_missing_and_reversal():
    x, y = [1, 2, 2], [2, 2, 3]
    dominance = sum((a > c) - (a < c) for a in x for c in y) / (len(x) * len(y))
    result = inf.compare_groups([x + [np.nan], y + [np.inf], []])
    assert result["n"] == 6 and result["groups"] == 2
    assert result["effect_name"] == "Cliff_delta"
    assert dominance == pytest.approx(-5 / 9)
    assert result["effect"] == pytest.approx(dominance)
    assert inf.compare_groups([y, x])["effect"] == pytest.approx(-dominance)
    assert inf.compare_groups([x, x])["effect"] == 0


def test_mann_whitney_all_ties_reports_undefined_instead_of_calculated_nan():
    result = inf.compare_groups([[7] * 5, [7] * 5])
    assert result["test"] == "Mann–Whitney"
    assert result["status"] == "constant"
    assert result["statistic"] is result["p"] is result["effect"] is None
    assert result["n"] == 10 and result["groups"] == 2


def test_kruskal_corrects_ties_and_effect_uses_only_finite_observations():
    # n=15, rank sums 15/40/65: H_uncorrected=12.5.
    # Three ties of size 5 give correction 1-360/3360=25/28, so H=14.
    groups = [[value] * 5 + [np.nan, np.inf] for value in (1, 2, 3)]
    result = inf.compare_groups(groups)
    assert result["n"] == 15 and result["groups"] == 3
    assert result["statistic"] == pytest.approx(14)
    assert result["effect"] == pytest.approx(1)
    assert result["effect_name"] == "epsilon_squared_H_over_n_minus_1"
    assert result["p"] == pytest.approx(np.exp(-7))  # chi-square survival, df=2.
    assert inf.compare_groups(groups[::-1]) == result
    groups[0] = [1] * 4 + [np.nan]
    insufficient = inf.compare_groups(groups)
    assert insufficient["status"] == "insufficient_group_size_min5"
    assert insufficient["n"] == 14 and insufficient["p"] is insufficient["effect"] is None


def test_bootstrap_pairwise_missingness_and_single_repository_median():
    result = boot.bootstrap([1, np.nan, 2, 3, 4, np.inf, 6], [6, 0, 5, np.nan, 3, 8, 1], iterations=1000)
    assert result == boot.bootstrap([1, 2, 4, 6], [6, 5, 3, 1], iterations=1000)
    assert result["n"] == 4
    single = boot.bootstrap([np.nan, 0, np.inf], iterations=1000)
    assert single["status"] == "calculated" and single["n"] == 1
    assert single["estimate"] == single["lower95"] == single["upper95"] == 0
    assert single["valid_replicates"] == 1000


def test_bootstrap_counts_constant_resamples_and_resamples_whole_pairs(monkeypatch):
    # Cycle through all 27 length-3 index tuples: 3 constant, 24 valid.
    # 1000 = 37*27 + 1, with the extra tuple (0,0,0) also constant.
    indices = cycle(product(range(3), repeat=3))
    calls = []

    class EnumeratedSamples:
        def integers(self, low, high, size):
            assert (low, high, size) == (0, 3, 3)
            calls.append(1)
            return np.array(next(indices))

    monkeypatch.setattr(boot.np.random, "default_rng", lambda seed: EnumeratedSamples())
    result = boot.bootstrap([1, 2, 3], [3, 2, 1], iterations=1000)
    assert len(calls) == result["iterations"] == 1000
    assert result["valid_replicates"] == 888
    assert [result[key] for key in ("estimate", "lower95", "upper95")] == pytest.approx([-1] * 3)


def test_bootstrap_percentile_interpolation_has_an_independent_finite_oracle(monkeypatch):
    # Exactly 25/950/25 samples with medians 0/1/2: type-7 percentile
    # indices are 24.975 and 974.025, on either side of the central plateau.
    samples = iter([[0] * 3] * 25 + [[1] * 3] * 950 + [[2] * 3] * 25)

    class FixedSamples:
        def integers(self, low, high, size):
            return np.array(next(samples))

    monkeypatch.setattr(boot.np.random, "default_rng", lambda seed: FixedSamples())
    result = boot.bootstrap([0, 1, 2], iterations=1000)
    assert result["estimate"] == 1
    assert result["valid_replicates"] == 1000
    assert result["lower95"] == pytest.approx(.975)
    assert result["upper95"] == pytest.approx(1.025)


def test_real_rq05_rq06_and_bootstrap_match_published_results():
    """Recompute only inference in memory; never rewrite the versioned CSVs."""
    data = load_data(Path("data/processed/s02/dataset_final_s02.csv"))
    original = data.copy(deep=True)
    correlations, tests, groups, cuts = inf.run(data, permutations=9999, seed=42)
    actual = dict(spearman=correlations, factor_tests=tests, factor_groups=groups,
                  factor_cutpoints=cuts, bootstrap=boot.run(data, iterations=2000, seed=42))
    for name, frame in actual.items():
        expected = pd.read_csv(Path("data/processed/s03") / f"{name}.csv")
        pd.testing.assert_frame_equal(frame, expected, check_dtype=False, check_exact=False,
                                      rtol=1e-12, atol=1e-14, obj=name)
    pd.testing.assert_frame_equal(data, original)
