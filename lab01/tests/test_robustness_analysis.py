"""Testes da contribuição metodológica de robustez da Sprint 3."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analysis.robustness_analysis import (
    analyze_robustness,
    build_outlier_records,
    build_robustness_summary,
    calculate_percent_change,
    run_robustness_analysis,
)


class RobustnessIqrTest(unittest.TestCase):
    def test_identifies_upper_outlier(self) -> None:
        result = analyze_robustness(pd.Series([1, 2, 3, 4, 100]))

        self.assertEqual(result.outlier_count, 1)
        self.assertEqual(result.filtered_maximum, 4)

    def test_identifies_lower_outlier(self) -> None:
        result = analyze_robustness(pd.Series([0, 10, 11, 12, 13]))

        self.assertEqual(result.outlier_count, 1)
        self.assertEqual(result.filtered_minimum, 10)

    def test_series_without_outliers_is_unchanged_in_comparison(self) -> None:
        result = analyze_robustness(pd.Series([1, 2, 3, 4]))

        self.assertEqual(result.outlier_count, 0)
        self.assertEqual(result.original_mean, result.filtered_mean)
        self.assertEqual(result.original_median, result.filtered_median)

    def test_all_equal_values_have_no_outliers(self) -> None:
        result = analyze_robustness(pd.Series([7, 7, 7, 7, 7]))

        self.assertEqual(result.iqr, 0)
        self.assertEqual(result.lower_bound, 7)
        self.assertEqual(result.upper_bound, 7)
        self.assertEqual(result.outlier_count, 0)

    def test_zero_original_returns_undefined_percent_change(self) -> None:
        result = analyze_robustness(pd.Series([0, 0, 0, 0]))

        self.assertEqual(result.original_mean, 0)
        self.assertEqual(result.mean_absolute_change, 0)
        self.assertIsNone(result.mean_percent_change)
        self.assertIsNone(result.median_percent_change)
        self.assertIsNone(calculate_percent_change(0, 1))

    def test_missing_values_are_counted_but_not_analyzed(self) -> None:
        result = analyze_robustness(pd.Series([1, None, 2, pd.NA]))

        self.assertEqual(result.total, 4)
        self.assertEqual(result.valid, 2)
        self.assertEqual(result.missing, 2)

    def test_empty_series_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "ao menos um valor"):
            analyze_robustness(pd.Series([], dtype=float))

    def test_zero_iqr_can_still_identify_a_distinct_extreme(self) -> None:
        result = analyze_robustness(pd.Series([5, 5, 5, 5, 100]))

        self.assertEqual(result.iqr, 0)
        self.assertEqual(result.outlier_count, 1)
        self.assertEqual(result.filtered_count, 4)

    def test_bounds_use_one_point_five_times_iqr(self) -> None:
        result = analyze_robustness(pd.Series([1, 2, 3, 4]))

        self.assertEqual(result.q1, 1.75)
        self.assertEqual(result.q3, 3.25)
        self.assertEqual(result.iqr, 1.5)
        self.assertEqual(result.lower_bound, -0.5)
        self.assertEqual(result.upper_bound, 5.5)

    def test_means_medians_changes_and_outlier_percentage(self) -> None:
        result = analyze_robustness(pd.Series([1, 2, 3, 4, 100]))

        self.assertEqual(result.outlier_percentage, 20)
        self.assertEqual(result.original_mean, 22)
        self.assertEqual(result.filtered_mean, 2.5)
        self.assertEqual(result.original_median, 3)
        self.assertEqual(result.filtered_median, 2.5)
        self.assertEqual(result.mean_absolute_change, 19.5)
        self.assertAlmostEqual(result.mean_percent_change, -88.63636363636364)
        self.assertEqual(result.median_absolute_change, 0.5)
        self.assertAlmostEqual(result.median_percent_change, -16.666666666666664)

    def test_input_series_is_not_modified(self) -> None:
        series = pd.Series([1.0, None, 2.0, 100.0])
        original = series.copy(deep=True)

        analyze_robustness(series)

        pd.testing.assert_series_equal(series, original)

    def test_non_numeric_value_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "não numérico"):
            analyze_robustness(pd.Series([1, "inválido", 2]))

    def test_outlier_records_include_reasons_and_repository_names(self) -> None:
        dataframe = pd.DataFrame(
            {
                "name_with_owner": ["a/low", "b/one", "c/two", "d/three", "e/high"],
                "metric": [0, 10, 11, 12, 100],
            }
        )
        result = analyze_robustness(dataframe["metric"])

        outliers = build_outlier_records(
            dataframe,
            rq="RQXX",
            value_column="metric",
            result=result,
        )

        self.assertEqual(set(outliers["repository"]), {"a/low", "e/high"})
        self.assertEqual(
            set(outliers["reason"]),
            {"below_lower_bound", "above_upper_bound"},
        )

    def test_end_to_end_creates_separate_artifacts(self) -> None:
        dataframe = pd.DataFrame(
            {
                "name_with_owner": [f"owner/repo-{index}" for index in range(10)],
                "repository_age_days": [10, 20, 30, 40, 50, 60, 70, 80, 90, 1000],
                "merged_pull_requests": [0, 1, 2, 3, 4, 5, 6, 7, 8, 1000],
            }
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            input_path = directory / "input.csv"
            summary_path = directory / "robustness.csv"
            outliers_path = directory / "outliers.csv"
            figure_path = directory / "comparison.png"
            dataframe.to_csv(input_path, index=False)

            results, artifacts = run_robustness_analysis(
                input_path=input_path,
                summary_path=summary_path,
                outliers_path=outliers_path,
                figure_path=figure_path,
            )

            self.assertEqual(set(results), {"RQ01", "RQ02"})
            self.assertEqual(set(artifacts), {summary_path, outliers_path, figure_path})
            self.assertTrue(all(path.is_file() for path in artifacts))
            summary = pd.read_csv(summary_path)
            self.assertEqual(
                list(summary.columns), ["rq", "metric", "value", "unit"]
            )
            self.assertEqual(len(summary), 52)
            self.assertGreater(figure_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
