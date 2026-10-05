import pytest

from src.temporal import ObservationWindow


@pytest.fixture
def window():
    return ObservationWindow("2025-01-01", "2026-01-01")


@pytest.fixture
def lead_time_example():
    """Exemplo do professor: release em 15/03, commits em 02, 10 e 14/03."""
    from src.commits import ReleaseInterval
    from src.temporal import Commit, Release
    previous = Release(1, "v1.0", "2025-02-01T00:00:00Z", "base")
    current = Release(2, "v1.1", "2025-03-15T00:00:00Z", "head")
    commits = tuple(Commit(f"sha{day}", f"2025-03-{day:02}T00:00:00Z",
                           "2025-03-14T00:00:00Z", "change") for day in (2, 10, 14))
    return ReleaseInterval(current, previous, commits)
