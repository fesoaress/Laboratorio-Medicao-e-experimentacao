"""Testes das metricas RQ01-RQ06."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.metrics.rq01_rq02 import (
    calculate_repository_age_days,
    normalize_merged_pull_requests,
)
from src.metrics.rq03_rq04 import (
    calculate_days_since_last_update,
    normalize_release_count,
)
from src.metrics.rq05_rq06 import (
    LANGUAGE_NOT_INFORMED,
    calculate_closed_issues_ratio,
    normalize_primary_language,
)


class MetricsTest(unittest.TestCase):
    def test_repository_age_from_github_date(self) -> None:
        age = calculate_repository_age_days(
            "2020-01-01T00:00:00Z",
            reference_datetime=datetime(2020, 1, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(age, 10)

    def test_days_since_last_update_uses_dates(self) -> None:
        days = calculate_days_since_last_update(
            "2020-01-05T23:30:00Z",
            reference_datetime=datetime(2020, 1, 10, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(days, 5)

    def test_counter_normalization_rejects_negative_values(self) -> None:
        self.assertEqual(normalize_merged_pull_requests("7"), 7)
        self.assertEqual(normalize_release_count(0), 0)

        with self.assertRaises(ValueError):
            normalize_merged_pull_requests(-1)

        with self.assertRaises(ValueError):
            normalize_release_count(-1)

    def test_language_absent_is_not_informed(self) -> None:
        self.assertEqual(normalize_primary_language(None), LANGUAGE_NOT_INFORMED)
        self.assertEqual(
            normalize_primary_language({"name": "Python"}),
            "Python",
        )

    def test_closed_issues_ratio_zero_total_is_undefined(self) -> None:
        self.assertIsNone(calculate_closed_issues_ratio(0, 0))
        self.assertEqual(calculate_closed_issues_ratio(10, 7), 0.7)

        with self.assertRaises(ValueError):
            calculate_closed_issues_ratio(3, 4)


if __name__ == "__main__":
    unittest.main()
