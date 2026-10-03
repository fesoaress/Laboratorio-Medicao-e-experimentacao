"""Testes determinísticos da análise obrigatória das RQ01 e RQ02."""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analysis.rq01_rq02 import (
    build_summary,
    calculate_rq01_statistics,
    calculate_rq02_statistics,
    generate_figures,
    save_summary,
    validate_required_columns,
)


class Rq01AnalysisTest(unittest.TestCase):
    def test_statistics_include_missing_quartiles_and_extremes(self) -> None:
        dataframe = pd.DataFrame(
            {
                "repository_age_days": [1, 2, None, 3, 4],
                "merged_pull_requests": [0, 1, 2, 3, 4],
            }
        )

        statistics = calculate_rq01_statistics(dataframe)

        self.assertEqual(statistics["total"], 5)
        self.assertEqual(statistics["valid"], 4)
        self.assertEqual(statistics["missing"], 1)
        self.assertEqual(statistics["minimum"], 1)
        self.assertEqual(statistics["maximum"], 4)
        self.assertEqual(statistics["median"], 2.5)
        self.assertEqual(statistics["q1"], 1.75)
        self.assertEqual(statistics["q3"], 3.25)
        self.assertEqual(statistics["iqr"], 1.5)
        self.assertAlmostEqual(statistics["standard_deviation"], math.sqrt(5 / 3))
        self.assertAlmostEqual(statistics["median_years"], 2.5 / 365.25)


class Rq02AnalysisTest(unittest.TestCase):
    def test_statistics_count_zeros_and_missing_values(self) -> None:
        dataframe = pd.DataFrame(
            {
                "repository_age_days": [10, 20, 30, 40, 50],
                "merged_pull_requests": [0, 0, None, 10, 20],
            }
        )

        statistics = calculate_rq02_statistics(dataframe)

        self.assertEqual(statistics["total"], 5)
        self.assertEqual(statistics["valid"], 4)
        self.assertEqual(statistics["missing"], 1)
        self.assertEqual(statistics["zeros"], 2)
        self.assertEqual(statistics["minimum"], 0)
        self.assertEqual(statistics["maximum"], 20)
        self.assertEqual(statistics["median"], 5)
        self.assertEqual(statistics["q1"], 0)
        self.assertEqual(statistics["q3"], 12.5)


class AnalysisValidationTest(unittest.TestCase):
    def test_required_column_validation_lists_missing_column(self) -> None:
        dataframe = pd.DataFrame({"repository_age_days": [1, 2]})

        with self.assertRaisesRegex(ValueError, "merged_pull_requests"):
            validate_required_columns(dataframe)

    def test_non_numeric_value_is_not_silently_treated_as_missing(self) -> None:
        dataframe = pd.DataFrame(
            {
                "repository_age_days": [1, "inválido"],
                "merged_pull_requests": [0, 1],
            }
        )

        with self.assertRaisesRegex(ValueError, "não numérico"):
            calculate_rq01_statistics(dataframe)


class AnalysisArtifactsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dataframe = pd.DataFrame(
            {
                "repository_age_days": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                "merged_pull_requests": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1000],
            }
        )
        self.rq01 = calculate_rq01_statistics(self.dataframe)
        self.rq02 = calculate_rq02_statistics(self.dataframe)

    def test_summary_has_expected_long_structure(self) -> None:
        summary = build_summary(self.rq01, self.rq02)

        self.assertEqual(list(summary.columns), ["rq", "statistic", "value", "unit"])
        self.assertEqual(set(summary["rq"]), {"RQ01", "RQ02"})
        self.assertEqual(len(summary), 30)
        self.assertEqual(
            summary.loc[
                (summary["rq"] == "RQ02") & (summary["statistic"] == "zeros"),
                "value",
            ].iloc[0],
            8,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "summary.csv"
            save_summary(summary, output_path)
            reloaded = pd.read_csv(output_path)
            self.assertEqual(list(reloaded.columns), list(summary.columns))
            self.assertEqual(len(reloaded), 30)

    def test_figure_generation_creates_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            generated = generate_figures(self.dataframe, self.rq02, output_dir)
            generated_names = {path.name for path in generated}

            self.assertEqual(
                generated_names,
                {
                    "rq01_age_histogram.png",
                    "rq01_age_boxplot.png",
                    "rq02_merged_prs_histogram.png",
                    "rq02_merged_prs_boxplot.png",
                    "rq02_merged_prs_log_histogram.png",
                },
            )
            for path in generated:
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
