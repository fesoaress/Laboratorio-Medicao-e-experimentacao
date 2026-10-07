import pytest

from src.metrics import (
    change_failure_rate_a, recovery_episodes, repository_recovery_time,
)
from src.workflow_runs import parse_workflow_run


def run(identifier, conclusion, started, updated=None, workflow_id=1, created=None):
    raw = {"id": identifier, "workflow_id": workflow_id, "head_branch": "main", "event": "push",
           "conclusion": conclusion, "created_at": created or started,
           "run_started_at": started, "updated_at": updated or started}
    return parse_workflow_run(raw, "main")


# --- CFR(a) ---

def test_cfr_a_matches_manual_fraction():
    runs = [run(1, "success", "2025-01-01T00:00:00Z"), run(2, "failure", "2025-01-02T00:00:00Z"),
            run(3, "failure", "2025-01-03T00:00:00Z"), run(4, "success", "2025-01-04T00:00:00Z")]
    result = change_failure_rate_a(runs)
    assert (result.successes, result.failures, result.cfr) == (2, 2, 0.5)


def test_cfr_a_ignored_conclusions_excluded_from_denominator():
    runs = [run(1, "success", "2025-01-01T00:00:00Z"), run(2, "cancelled", "2025-01-02T00:00:00Z"),
            run(3, "skipped", "2025-01-03T00:00:00Z")]
    result = change_failure_rate_a(runs)
    assert result.ignored == 2
    assert result.cfr == 0.0  # 0 failures / (1 success + 0 failures)


def test_cfr_a_no_valid_runs_is_none_not_zero():
    runs = [run(1, "cancelled", "2025-01-01T00:00:00Z")]
    assert change_failure_rate_a(runs).cfr is None


def test_cfr_a_empty_repository():
    assert change_failure_rate_a([]).cfr is None


# --- Tempo de recuperação (exemplo literal do enunciado, seção RQ04) ---

def test_recovery_time_matches_enunciado_example():
    runs = [
        run(1, "success", started="2025-01-01T09:00:00Z"),
        run(2, "failure", started="2025-01-01T10:00:00Z"),
        run(3, "failure", started="2025-01-01T10:30:00Z"),
        run(4, "success", started="2025-01-01T11:15:00Z", updated="2025-01-01T11:20:00Z"),
    ]
    episodes = recovery_episodes(runs)
    assert len(episodes) == 1
    assert episodes[0].failure_started_at == "2025-01-01T10:00:00Z"
    assert episodes[0].recovered_at == "2025-01-01T11:20:00Z"
    assert episodes[0].hours == pytest.approx(80 / 60)  # 1h20


def test_recovery_time_no_episode_without_prior_success():
    # Falhas logo no início da sequência observada, sem success anterior: sem início definido.
    runs = [run(1, "failure", "2025-01-01T10:00:00Z"), run(2, "success", "2025-01-01T11:00:00Z")]
    assert recovery_episodes(runs) == []


def test_recovery_time_censored_episode_never_recovers():
    runs = [run(1, "success", "2025-01-01T09:00:00Z"), run(2, "failure", "2025-01-01T10:00:00Z")]
    episodes = recovery_episodes(runs)
    assert episodes[0].recovered_at is None
    assert episodes[0].hours is None


def test_recovery_time_ignored_runs_do_not_interrupt_or_start_episodes():
    runs = [run(1, "success", "2025-01-01T09:00:00Z"), run(2, "cancelled", "2025-01-01T09:30:00Z"),
            run(3, "failure", "2025-01-01T10:00:00Z"), run(4, "success", "2025-01-01T11:00:00Z")]
    episodes = recovery_episodes(runs)
    assert len(episodes) == 1
    assert episodes[0].failure_started_at == "2025-01-01T10:00:00Z"


def test_recovery_time_separates_episodes_by_workflow():
    runs = [
        run(1, "success", "2025-01-01T09:00:00Z", workflow_id=1),
        run(2, "failure", "2025-01-01T10:00:00Z", workflow_id=1, updated="2025-01-01T10:05:00Z"),
        run(3, "success", "2025-01-01T12:00:00Z", workflow_id=1),
        run(4, "success", "2025-01-01T09:00:00Z", workflow_id=2),
        run(5, "failure", "2025-01-01T09:30:00Z", workflow_id=2),
    ]
    episodes = recovery_episodes(runs)
    assert {episode.workflow_id for episode in episodes} == {1, 2}
    assert sum(episode.hours is None for episode in episodes) == 1  # só o do workflow 2 fica censurado


def test_repository_recovery_time_median_and_censored_proportion():
    runs = [
        run(1, "success", "2025-01-01T00:00:00Z", workflow_id=1),
        run(2, "failure", "2025-01-01T01:00:00Z", workflow_id=1),
        run(3, "success", "2025-01-01T02:00:00Z", workflow_id=1),  # episódio: 1h
        run(4, "failure", "2025-01-01T05:00:00Z", workflow_id=1),
        run(5, "success", "2025-01-01T08:00:00Z", workflow_id=1),  # episódio: 3h
        run(6, "success", "2025-01-01T00:00:00Z", workflow_id=2),
        run(7, "failure", "2025-01-01T01:00:00Z", workflow_id=2),  # censurado
    ]
    summary = repository_recovery_time(recovery_episodes(runs))
    assert summary.n_episodes == 3
    assert summary.n_censored == 1
    assert summary.median_hours == 2.0  # mediana de (1, 3)
    assert summary.censored_proportion == pytest.approx(1 / 3)


def test_repository_recovery_time_no_episodes_is_none_not_zero():
    summary = repository_recovery_time([])
    assert (summary.median_hours, summary.censored_proportion) == (None, None)