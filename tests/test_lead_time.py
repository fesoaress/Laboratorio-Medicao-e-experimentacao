from dataclasses import replace

import pytest

from src.commits import ReleaseInterval
from src.metrics import calculate_lead_time, summarize_hours
from src.temporal import Commit, Release


def test_professor_example_and_iqr(lead_time_example):
    result = calculate_lead_time((lead_time_example,))
    assert result.by_release.count == 1
    assert result.by_release.median_hours == 13 * 24
    assert result.by_release.iqr_hours == 0
    assert [v["lead_time_hours"] for v in result.commit_values] == [312, 120, 24]
    assert result.by_commit.median_hours == 120
    assert (result.by_commit.q1_hours, result.by_commit.q3_hours, result.by_commit.iqr_hours) == (72, 216, 144)


def test_variant_b_pools_all_commits_instead_of_release_medians(lead_time_example):
    later = Release(3, "v1.2", "2025-03-16T00:00:00Z", "next")
    commit = Commit("later", "2025-03-15T00:00:00Z", "2025-03-15T12:00:00Z", "fix")
    result = calculate_lead_time((lead_time_example, ReleaseInterval(later, lead_time_example.release, (commit,))))
    assert result.by_release.median_hours == 168
    assert result.by_commit.median_hours == 72  # [24, 24, 120, 312]
    assert result.by_commit.count == 4


def test_old_author_date_is_not_filtered_by_window(lead_time_example):
    old = replace(lead_time_example.commits[0], author_date="2024-12-01T00:00:00Z")
    result = calculate_lead_time((replace(lead_time_example, commits=(old,)),))
    assert result.by_release.median_hours == 104 * 24


def test_first_release_and_empty_interval_have_missing_not_zero_metrics(lead_time_example):
    first = ReleaseInterval(lead_time_example.previous_release, None, status="no_previous_release")
    empty = replace(lead_time_example, commits=())
    result = calculate_lead_time((first, empty))
    assert result.releases_without_predecessor == result.releases_without_new_commits == 1
    assert result.by_commit.count == result.by_release.count == 0
    assert result.by_release.median_hours is None
    assert result.by_commit.iqr_hours is None


def test_zero_duration_is_a_real_observation_and_timezones_are_normalized(lead_time_example):
    commit = replace(lead_time_example.commits[0], author_date="2025-03-14T21:00:00-03:00")
    result = calculate_lead_time((replace(lead_time_example, commits=(commit,)),))
    assert result.by_commit.median_hours == 0
    assert result.by_commit.count == 1


def test_committer_date_does_not_replace_author_date(lead_time_example):
    assert calculate_lead_time((lead_time_example,)).by_release.median_hours == 312


def test_duplicate_commit_within_release_counts_once(lead_time_example):
    result = calculate_lead_time((replace(lead_time_example, commits=lead_time_example.commits * 2),))
    assert result.by_commit.count == 3


def test_same_sha_in_distinct_releases_preserves_observations(lead_time_example):
    second = replace(lead_time_example, release=replace(lead_time_example.release, release_id=3))
    assert calculate_lead_time((lead_time_example, second)).by_commit.count == 6


def test_compare_404_skips_only_affected_release_and_counts_it(lead_time_example):
    ignored = replace(lead_time_example, release=replace(lead_time_example.release, release_id=3),
                      commits=(), status="ignored_compare_404", error_status=404, error_detail="HTTP 404")
    result = calculate_lead_time((ignored, lead_time_example))
    assert result.releases_ignored_compare_404 == 1
    assert result.by_release.count == 1 and result.by_release.median_hours == 312
    assert result.by_commit.count == 3 and result.by_commit.median_hours == 120
    assert result.releases_without_new_commits == 0


def test_all_compare_404_intervals_have_missing_not_zero_statistics(lead_time_example):
    ignored = replace(lead_time_example, commits=(), status="ignored_compare_404", error_status=404)
    result = calculate_lead_time((ignored,))
    assert result.releases_ignored_compare_404 == 1
    assert result.by_release.count == result.by_commit.count == 0
    assert result.by_release.median_hours is result.by_commit.median_hours is None


def test_other_http_errors_cannot_be_misclassified_as_404(lead_time_example):
    invalid = replace(lead_time_example, status="ignored_compare_404", error_status=503)
    with pytest.raises(ValueError, match="completamente"):
        calculate_lead_time((invalid,))


@pytest.mark.parametrize("mutation,match", [
    (lambda i: replace(i, status="error"), "completamente"),
    (lambda i: replace(i, previous_release=None), "completamente"),
    (lambda i: replace(i, previous_release=replace(i.previous_release, published_at="2025-04-01T00:00:00Z")), "depois"),
    (lambda i: replace(i, commits=(replace(i.commits[0], author_date="2025-03-16T00:00:00Z"),)), "negativo"),
    (lambda i: replace(i, commits=(replace(i.commits[0], author_date="2025-03-02T00:00:00"),)), "fuso"),
])
def test_invalid_interval_is_not_silently_dropped(lead_time_example, mutation, match):
    with pytest.raises(ValueError, match=match):
        calculate_lead_time((mutation(lead_time_example),))


def test_duplicate_releases_and_inconsistent_commits_rejected(lead_time_example):
    with pytest.raises(ValueError, match="duplicada"):
        calculate_lead_time((lead_time_example, lead_time_example))
    bad = replace(lead_time_example.commits[0], author_date="2025-03-01T00:00:00Z")
    with pytest.raises(ValueError, match="inconsistentes"):
        calculate_lead_time((replace(lead_time_example, commits=(*lead_time_example.commits, bad)),))


@pytest.mark.parametrize("values,expected", [([], (None, None, None)), ([7], (7, 7, 0)),
    ([0, 10], (2.5, 7.5, 5)), ([0, 10, 20, 30, 40], (10, 30, 20))])
def test_linear_quartiles(values, expected):
    result = summarize_hours(iter(values))
    assert (result.q1_hours, result.q3_hours, result.iqr_hours) == expected
